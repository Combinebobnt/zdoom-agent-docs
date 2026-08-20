#!/usr/bin/env python3
"""Generate/refresh the Table-of-entries (archetype 2) inventory files, and ACS's
"Signature-only (tier C)" block, from engine/compiler source -- see shared/ARCHETYPES.md.

Every extractor below reads engine/compiler source located via sources.local.md (falling back to
a same-named sibling directory next to this repo, same resolution rule as
shared/AUTHORING.md's "Locating the engine/compiler source"). Regeneration PRESERVES the Tier and
Notes columns of existing inventory rows by name key, and reports added/removed/changed entries --
never silently drops a hand-promoted Tier or a linked notes/ file.

Usage:
    python3 tools/gen_inventory.py <target> [--check]

Targets:
    decorate-flags        decorate/inventory/actor-flags.md
    decorate-properties   decorate/inventory/actor-properties.md
    decorate-actions      decorate/inventory/actor-actions.md
    console-cvars         console/inventory/cvars.md
    console-ccmds         console/inventory/ccmds.md
    acs-signatures        acs/INDEX.md's "Signature-only (tier C)" block
    all                   every target above

--check: regenerate in memory and diff against the committed file; exit 1 on any difference
instead of writing. Use this in CI-less verification the same way tools/lint_docs.py is used.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections as S  # noqa: E402
import lookup  # noqa: E402  (reused for _known_names -- the ACS "already documented" set)

ROOT = S.ROOT


# ---------------------------------------------------------------------------
# Source-checkout resolution -- mirrors shared/AUTHORING.md's "Locating the
# engine/compiler source" (sources.local.md, then a sibling directory, then give up).
# ---------------------------------------------------------------------------

def _read_sources_local():
    path = ROOT / "sources.local.md"
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        m = re.match(r'\|\s*`([\w.-]+)`\s*\|[^|]*\|\s*([^|]*)\|', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val:
                out[key] = Path(val).expanduser()
    return out


_SOURCES = _read_sources_local()


def source_root(key):
    if key in _SOURCES and _SOURCES[key].is_dir():
        return _SOURCES[key]
    sibling = ROOT.parent / key
    if sibling.is_dir():
        return sibling
    print(f"gen_inventory.py: no source configured or found for '{key}' -- "
          f"set it in sources.local.md or place a sibling '../{key}' directory", file=sys.stderr)
    sys.exit(1)


def iter_cpp_files(root):
    return sorted(root.rglob("*.cpp"))


# ---------------------------------------------------------------------------
# Generic table rendering with preserve-by-key merge.
# ---------------------------------------------------------------------------

def _row_key(cells, key_idx):
    return tuple(cells[i] if i < len(cells) else "" for i in key_idx)


def parse_existing_table(text, key_idx=(0,)):
    """Return {key: full_row_cells_list} for a generated inventory file's table, or {} if the
    file doesn't exist / has no table yet. `key_idx` is a tuple of column indices forming the
    row's identity -- (0,) (just the first column) unless a name alone isn't unique, e.g.
    DECORATE properties are class-scoped and the same name can legitimately repeat with a
    different class (see gen_decorate_properties)."""
    rows = [l for l in text.splitlines() if l.strip().startswith("|")]
    if len(rows) < 3:
        return {}, []
    header = S.split_row(rows[0])
    out = {}
    for row in rows[2:]:
        cells = S.split_row(row)
        if cells:
            out[_row_key(cells, key_idx)] = cells
    return out, header


def render_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(S.escape_cell(c) for c in row) + " |")
    return "\n".join(lines)


TIER_LINE_RE = re.compile(r'^\*\*Tier:\*\*\s*([ABC])\b', re.M)


def curated_cell(section_dir, curated_subdir, *slug_candidates):
    """(tier, notes-link) read straight from a curated actions//notes/ doc's own `**Tier:**`
    stamp, for the first `slug_candidates` entry that exists as `<curated_subdir>/<slug>.md`
    under `section_dir` -- or (None, None) if none of them do. This is the auto-pickup
    ARCHETYPES.md describes ("let the next generator run pick up the change from the notes/
    directory's presence") -- the curated file is the source of truth for its own tier, so a
    hit here always overrides a stale preserved cell rather than losing to it."""
    for slug in slug_candidates:
        path = section_dir / curated_subdir / f"{slug}.md"
        if path.is_file():
            m = TIER_LINE_RE.search(path.read_text())
            if m:
                return m.group(1), f"[notes](../{curated_subdir}/{slug}.md)"
    return None, None


def build_inventory_file(title, generated_note, header, new_rows, existing_path, preserve_cols,
                          key_idx=(0,), defaults=None):
    """new_rows: list of row-cell-lists in HEADER order. A preserve_cols cell (e.g. Tier, Notes)
    left as "" is filled from any existing row sharing the same key (see parse_existing_table's
    `key_idx`) so a hand-promoted Tier or Notes link survives regeneration, falling back to
    `defaults` (e.g. {"Tier": "C"}) if there's no existing row either. A preserve_cols cell the
    caller already filled in (e.g. via curated_cell() finding a notes/actions file) is left
    untouched -- freshly-detected beats a stale preserved value, which is what lets a curated
    file's tier promotion actually take effect on the next regen instead of needing a one-off
    hand-edit of the generated row. Returns the full file text."""
    defaults = defaults or {}
    existing_rows, existing_header = ({}, [])
    if existing_path.is_file():
        existing_rows, existing_header = parse_existing_table(existing_path.read_text(), key_idx)

    preserve_idx = [header.index(c) for c in preserve_cols if c in header]
    default_by_idx = {header.index(c): v for c, v in defaults.items() if c in header}
    merged = []
    added, removed, changed = [], [], []
    new_keys = {_row_key(r, key_idx) for r in new_rows}
    for row in new_rows:
        key = _row_key(row, key_idx)
        old = existing_rows.get(key)
        merged_row = list(row)
        for i in preserve_idx:
            if merged_row[i]:
                continue  # already authoritatively set (curated-file detection) -- keep it
            if old and i < len(old) and old[i]:
                merged_row[i] = old[i]
            elif i in default_by_idx:
                merged_row[i] = default_by_idx[i]
        if old:
            if old != merged_row:
                changed.append(key)
        else:
            added.append(key)
        merged.append(merged_row)
    for key in existing_rows:
        if key not in new_keys:
            removed.append(key)

    body = render_table(header, merged)
    text = f"# {title}\n\n{generated_note}\n\n{body}\n"
    return text, {"added": added, "removed": removed, "changed": changed}


def _fmt_key(key):
    return "/".join(key) if isinstance(key, tuple) else str(key)


def emit_diff_report(name, stats):
    if stats["added"]:
        print(f"{name}: +{len(stats['added'])} added", file=sys.stderr)
    if stats["removed"]:
        shown = ", ".join(_fmt_key(k) for k in stats["removed"][:10])
        print(f"{name}: -{len(stats['removed'])} removed: {shown}"
              + (" ..." if len(stats["removed"]) > 10 else ""), file=sys.stderr)
    if stats["changed"]:
        print(f"{name}: ~{len(stats['changed'])} changed (non-preserved column)", file=sys.stderr)
    if not (stats["added"] or stats["removed"] or stats["changed"]):
        print(f"{name}: no changes", file=sys.stderr)


def write_or_check(path, text, check):
    if check:
        if not path.is_file() or path.read_text() != text:
            print(f"CHECK FAILED: {path.relative_to(ROOT)} differs from a fresh regeneration", file=sys.stderr)
            return False
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(f"wrote {path.relative_to(ROOT)}", file=sys.stderr)
    return True


# ---------------------------------------------------------------------------
# decorate-flags
# ---------------------------------------------------------------------------

# The closing brace isn't reliably on its own line -- Zandronum's InventoryFlags table ends
# `DEFINE_DEPRECATED_FLAG(INTERHUBSTRIP),};` with no newline before `};`, which silently made an
# earlier `\n\};`-anchored version of this regex swallow the next table's contents too (found by
# noticing a WeaponFlags-only flag showing up mislabeled under the InventoryFlags table name).
FLAG_TABLE_RE = re.compile(r'static\s+FFlagDef\s+(\w+)\s*\[\s*\]\s*=?\s*\n?\{(.*?)\};', re.S)
DEFINE_FLAG_RE = re.compile(r'DEFINE_FLAG\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)')
DEFINE_FLAG2_RE = re.compile(r'DEFINE_FLAG2\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)')
# UZDoom-only macros (not in Zandronum's thingdef_data.cpp): DEFINE_PROTECTED_FLAG/2 are the
# read-only-from-ACS variant of DEFINE_FLAG/2 (adds VARF_ReadOnly|VARF_InternalAccess -- irrelevant
# to a name-presence table, so treated identically). DEFINE_FLAG2_DEPRECATED adds a trailing
# version argument after the same 4-arg shape as DEFINE_FLAG2.
DEFINE_PROTECTED_FLAG_RE = re.compile(r'DEFINE_PROTECTED_FLAG\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)')
DEFINE_PROTECTED_FLAG2_RE = re.compile(r'DEFINE_PROTECTED_FLAG2\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)')
DEFINE_FLAG2_DEPRECATED_RE = re.compile(
    r'DEFINE_FLAG2_DEPRECATED\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,'
)
# Zandronum's DEFINE_DEPRECATED_FLAG(name)/DEFINE_DUMMY_FLAG(name) take one arg; UZDoom's take a
# second (version/bool) arg, e.g. DEFINE_DEPRECATED_FLAG(MISSILEMORE, MakeVersion(4, 13, 0)) --
# match up to the first comma-or-close-paren so both engines' call shapes are covered.
DEFINE_DEP_FLAG_RE = re.compile(r'DEFINE_DEPRECATED_FLAG\(\s*(\w+)\s*[,)]')
DEFINE_DUMMY_FLAG_RE = re.compile(r'DEFINE_DUMMY_FLAG\(\s*(\w+)\s*[,)]')


def _strip_comments(text):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//[^\n]*', '', text)
    return text


def _extract_flags_from_file(path):
    """Return {flag_name: (table, class, field)} for every DEFINE_FLAG*/DEFINE_DEPRECATED_FLAG/
    DEFINE_DUMMY_FLAG call inside a named FFlagDef table in one thingdef_data.cpp-shaped file.
    Table names vary across engines (Zandronum's ActorFlags vs UZDoom's ActorFlagDefs, etc.) --
    callers that just need a flat name set for presence-checking don't care."""
    text = path.read_text()
    out = {}
    for m in FLAG_TABLE_RE.finditer(text):
        table_name, body = m.group(1), _strip_comments(m.group(2))
        for fm in DEFINE_FLAG_RE.finditer(body):
            prefix, name, cls, field = fm.groups()
            out[name] = (table_name, cls, field)
        for fm in DEFINE_FLAG2_RE.finditer(body):
            symbol, name, cls, field = fm.groups()
            out[name] = (table_name, cls, field)
        for fm in DEFINE_PROTECTED_FLAG_RE.finditer(body):
            prefix, name, cls, field = fm.groups()
            out[name] = (table_name, cls, field)
        for fm in DEFINE_PROTECTED_FLAG2_RE.finditer(body):
            symbol, name, cls, field = fm.groups()
            out[name] = (table_name, cls, field)
        for fm in DEFINE_FLAG2_DEPRECATED_RE.finditer(body):
            symbol, name, cls, field = fm.groups()
            out[name] = (table_name, cls, field)
        for fm in DEFINE_DEP_FLAG_RE.finditer(body):
            out.setdefault(fm.group(1), (table_name, "(deprecated)", ""))
        for fm in DEFINE_DUMMY_FLAG_RE.finditer(body):
            out.setdefault(fm.group(1), (table_name, "(dummy)", ""))
    return out


def gen_decorate_flags(check):
    zan_file = source_root("zandronum") / "src" / "thingdef" / "thingdef_data.cpp"
    uzd_file = source_root("uzdoom") / "src" / "scripting" / "thingdef_data.cpp"
    zan_flags = _extract_flags_from_file(zan_file)
    uzd_flags = _extract_flags_from_file(uzd_file) if uzd_file.is_file() else {}

    decorate_dir = ROOT / "decorate"
    header = ["Flag", "Table", "Class", "Field", "Zan", "UZD", "Tier", "Notes"]
    rows = []
    for name in sorted(zan_flags, key=str.lower):
        table, cls, field = zan_flags[name]
        uzd = "yes" if name in uzd_flags else "—"
        tier, notes = curated_cell(decorate_dir, "notes", name.lower())
        rows.append([name, table, cls, field, "yes", uzd, tier or "", notes or ""])

    note = (
        "**Generated:** by `python3 tools/gen_inventory.py decorate-flags` from the Zandronum "
        "source's `src/thingdef/thingdef_data.cpp` (`DEFINE_FLAG`/`DEFINE_FLAG2`/"
        "`DEFINE_DEPRECATED_FLAG`/`DEFINE_DUMMY_FLAG` across its five flag tables), "
        "cross-referenced against the UZDoom source's `src/scripting/thingdef_data.cpp` by name "
        "for the `UZD` column (also matching UZDoom-only `DEFINE_PROTECTED_FLAG`/"
        "`DEFINE_PROTECTED_FLAG2`/`DEFINE_FLAG2_DEPRECATED`) -- do not hand-edit rows; add a "
        "`../notes/<flag>.md` file and its `Tier`/`Notes` cell is picked up automatically from "
        "that file's own `Tier:` stamp on the next regen. Extraction reads the Zandronum source "
        "as its base (confirmed present for every row); UZDoom presence is a name "
        "cross-reference only (the `UZD` column), not independently behavior-verified. "
        "**Tier:** per row (defaults to C until a `notes/` file promotes it)."
    )
    path = ROOT / "decorate" / "inventory" / "actor-flags.md"
    text, stats = build_inventory_file("DECORATE actor flags", note, header, rows, path,
                                        ["Tier", "Notes"], defaults={"Tier": "C"})
    emit_diff_report("decorate-flags", stats)
    return write_or_check(path, text, check)


# ---------------------------------------------------------------------------
# UZDoom ZScript source helpers -- most DECORATE properties and many action
# functions moved out of C++ into wadsrc/static/zscript/**/*.zs. Only name
# (and, for actions, arity) is ever extracted here, never backing-field or
# body text -- UZDoom/GZDoom source is GPL-3.0 and this tree may never quote
# it verbatim (see decorate/AGENTS.md).
# ---------------------------------------------------------------------------

# `class`/`extend class` are case-insensitive keywords like the rest of ZScript -- ~50 files
# spell it `Class Name : Parent` (capital C), e.g. visualthinker.zs's `Class VisualThinker :
# Thinker native`.
_ZS_CLASS_OPEN_RE = re.compile(r'^[ \t]*(?:extend\s+)?class\s+(\w+)\b[^{;]*\{', re.M | re.I)


def uzdoom_zscript_root():
    return source_root("uzdoom") / "wadsrc" / "static" / "zscript"


def iter_zs_files(root):
    return sorted(root.rglob("*.zs"))


def _iter_zs_class_bodies(text):
    """Yield (class_name, body_text) for every top-level `class Name [: Parent] { ... }` or
    `extend class Name { ... }` block, matching brace depth -- bodies routinely contain nested
    braces from if/for/state blocks, so a non-greedy up-to-first-`}` regex would truncate early.
    Forward declarations (`class Name;`, no body) don't match the open-brace anchor and are
    skipped, same as a plain class scan would skip them."""
    for m in _ZS_CLASS_OPEN_RE.finditer(text):
        cls = m.group(1)
        start = m.end()
        depth = 1
        i = start
        n = len(text)
        while i < n and depth > 0:
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
            i += 1
        yield cls, text[start:i - 1]


# ---------------------------------------------------------------------------
# decorate-properties
# ---------------------------------------------------------------------------

DEFINE_PROPERTY_RE = re.compile(r'^DEFINE_PROPERTY\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)', re.M)
DEFINE_CLASS_PROPERTY_RE = re.compile(r'^DEFINE_CLASS_PROPERTY\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)', re.M)
DEFINE_CLASS_PROPERTY_PREFIX_RE = re.compile(
    r'^DEFINE_CLASS_PROPERTY_PREFIX\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)', re.M
)


def _extract_properties_from_file(path):
    """Keyed by (name, class), not name alone -- DECORATE properties are class-scoped, and the
    same name is legitimately re-declared for different classes with a different spec (198 raw
    declarations, only 151 unique names) -- keying by name alone silently collapsed 47 of them
    to whichever class's declaration happened to be read last. Value is (spec, kind, bare_name,
    prefix); bare_name is the plain name a `class-property-prefix` row was assembled from (e.g.
    `attackzoffset` for `player.attackzoffset`) and prefix is the dotted prefix itself
    (`player`), or None for the other two kinds -- ZScript's `property` declarations never carry
    the DECORATE-facing dotted prefix baked into the name (`property AttackZOffset:
    AttackZOffset;`, not `player.AttackZOffset`; the prefix instead comes from a separate
    `property prefix: Player;` declaration on the class), so matching the dotted key verbatim
    against the UZD side always misses -- see `_extract_zs_properties_from_tree`, which needs
    both parts to build the matching (prefix, name) pairing from that mechanism."""
    text = _strip_comments(path.read_text())
    out = {}
    for pm in DEFINE_PROPERTY_RE.finditer(text):
        name, spec, cls = pm.groups()
        out[(name, cls)] = (spec, "property", name, None)
    for pm in DEFINE_CLASS_PROPERTY_RE.finditer(text):
        name, spec, cls = pm.groups()
        out[(name, cls)] = (spec, "class-property", name, None)
    for pm in DEFINE_CLASS_PROPERTY_PREFIX_RE.finditer(text):
        prefix, name, spec, cls = pm.groups()
        out[(f"{prefix}.{name}", cls)] = (spec, "class-property-prefix", name, prefix)
    return out


# ZScript's `property` keyword is case-insensitive like the rest of the language -- 17 of 176
# declarations in the tree are spelled `Property` (capital P), e.g. actor.zs's
# `Property ExplosionDamage: ExplosionDamage;`.
ZS_PROPERTY_RE = re.compile(r'^[ \t]*property\s+(\w+)\s*:\s*([^;]+);', re.M | re.I)


def _extract_zs_properties_from_tree(root):
    """Returns (exact, prefixed): `exact` is a {(name.lower(), class)} presence set from every
    `property Name: field[, field...];` declaration; `prefixed` is a {(prefix.lower(),
    name.lower())} set covering classes that declare `property prefix: X;` -- ZScript's own
    mechanism for "this class's properties are written `X.name` in DECORATE" (e.g.
    `BasicArmorBonus` declares `property prefix: Armor;`, so its `property MaxAbsorb: ...;`
    is DECORATE's `armor.maxabsorb`). Zandronum's C++ `DEFINE_CLASS_PROPERTY_PREFIX` macro bakes
    the dotted name in directly with no such per-class indirection, so this is the only way to
    recover the (prefix, name) pairing from the ZScript side -- a bare-name-only, any-class,
    any-kind fallback was tried first and rejected: `rune.type` (Zandronum, genuinely absent from
    UZDoom) matched UZDoom's unrelated `powerup.type`/`DynamicLight`'s `type` purely because both
    share the generic bare name "type", which is exactly the false-presence failure mode a dotted
    prefix exists to prevent in the first place.

    ZScript property names are PascalCase (`property Health: health;`) where Zandronum's C++
    DEFINE_PROPERTY macro uses the backing-field-style name (`DEFINE_PROPERTY(health, I,
    Actor)`); DECORATE property names are case-insensitive at the language level, so an
    exact-case match would misreport genuinely-present properties (health, woundhealth,
    floatspeed, ...) as absent. Only the property name (and, for `prefix`, the class's declared
    prefix target) are extracted, never the backing-field text on the right of the `:` -- see the
    module-level comment above `uzdoom_zscript_root` on why."""
    exact = set()
    prefixed = set()
    for path in iter_zs_files(root):
        text = _strip_comments(path.read_text(errors="replace"))
        for cls, body in _iter_zs_class_bodies(text):
            names = []
            prefix = None
            for pm in ZS_PROPERTY_RE.finditer(body):
                name, value = pm.group(1), pm.group(2).strip()
                if name.lower() == "prefix":
                    prefix = value
                    continue
                names.append(name)
                exact.add((name.lower(), cls))
            if prefix and prefix.lower() != "none":
                for name in names:
                    prefixed.add((prefix.lower(), name.lower()))
    return exact, prefixed


def gen_decorate_properties(check):
    zan_file = source_root("zandronum") / "src" / "thingdef" / "thingdef_properties.cpp"
    uzd_file = source_root("uzdoom") / "src" / "scripting" / "thingdef_properties.cpp"
    zan_props = _extract_properties_from_file(zan_file)
    uzd_props_cpp = _extract_properties_from_file(uzd_file) if uzd_file.is_file() else {}
    zs_root = uzdoom_zscript_root()
    uzd_props_zs, uzd_prefixed_zs = (
        _extract_zs_properties_from_tree(zs_root) if zs_root.is_dir() else (set(), set())
    )
    uzd_present = {(name.lower(), cls) for (name, cls) in uzd_props_cpp} | uzd_props_zs
    # class-scoped exact match misses `class-property-prefix` rows on principle -- ZScript's
    # `property` declarations never carry the DECORATE dotted prefix baked into the name (see
    # _extract_properties_from_file) -- so those match by (prefix, bare name) instead, pulled
    # from the C++ side's own DEFINE_CLASS_PROPERTY_PREFIX prefix argument and the ZScript side's
    # `property prefix: X;` mechanism (_extract_zs_properties_from_tree). NOT a bare-name-only,
    # any-class fallback -- that was tried and rejected (see that function's docstring) because
    # dotted properties routinely reuse generic bare names (`type`, `mode`, `strength`) across
    # unrelated prefixes, which a class-blind name match collides on.
    uzd_prefixed = {
        (p.lower(), n.lower())
        for (_dotted, cls), (_spec, kind, n, p) in uzd_props_cpp.items()
        if kind == "class-property-prefix"
    } | uzd_prefixed_zs

    decorate_dir = ROOT / "decorate"
    header = ["Property", "Kind", "Class", "Param spec", "Zan", "UZD", "Tier", "Notes"]
    rows = []
    for name, cls in sorted(zan_props, key=lambda k: (k[0].lower(), k[1].lower())):
        spec, kind, bare_name, prefix = zan_props[(name, cls)]
        if (name.lower(), cls) in uzd_present:
            uzd = "yes"
        elif kind == "class-property-prefix" and (prefix.lower(), bare_name.lower()) in uzd_prefixed:
            uzd = "yes"
        else:
            uzd = "—"
        tier, notes = curated_cell(decorate_dir, "notes", f"{name.lower()}-{cls.lower()}", name.lower())
        rows.append([name, kind, cls, spec, "yes", uzd, tier or "", notes or ""])

    note = (
        "**Generated:** by `python3 tools/gen_inventory.py decorate-properties` from the "
        "Zandronum source's `src/thingdef/thingdef_properties.cpp` (`DEFINE_PROPERTY`/"
        "`DEFINE_CLASS_PROPERTY`), cross-referenced against the UZDoom source's "
        "`src/scripting/thingdef_properties.cpp` **and** every `property Name: field;` "
        "declaration under `wadsrc/static/zscript/` (case-insensitive by name -- ZScript uses "
        "PascalCase property names over a differently-cased backing field) for the `UZD` "
        "column -- a `player.`/`armor.`/etc.-prefixed row (`class-property-prefix` in the `Kind` "
        "column) matches by (prefix, bare name) against the UZD side rather than the dotted key "
        "verbatim, since ZScript's `property` declarations never carry that DECORATE-facing "
        "dotted prefix baked into the name -- the prefix instead comes from a separate `property "
        "prefix: X;` declaration on the ZScript class. Deliberately NOT a bare-name-only, "
        "any-class match: dotted properties routinely reuse generic bare names (`type`, `mode`, "
        "`strength`) across unrelated prefixes, which a class-blind name match would collide on. "
        "**Known residual gap:** "
        "the exact (name, class) match for the other two `Kind`s doesn't account for the two "
        "engines nesting a property at different points in the class hierarchy (e.g. Zandronum "
        "registers `maxabsorb` on `Armor` directly; UZDoom's ZScript declares it on `Armor`'s "
        "subclass `BasicArmorBonus`) -- a `UZD: —` on one of those rows can mean genuinely "
        "absent, or present-but-unmatched; spot-check before trusting it as an absence. "
        "properties are class-scoped, and the same name is legitimately redeclared with a "
        "different spec for a different class (e.g. `translation`), so `Property` alone is not "
        "unique in this table; `Property`+`Class` together are. `Param spec` is the property's "
        "raw parameter-type-code string from the macro call, not yet decoded into plain type "
        "names -- do not hand-edit rows; add a `../notes/<property>.md` file instead (or "
        "`<property>-<class>.md` if the same name needs separate notes per class) and its "
        "`Tier`/`Notes` cell is picked up automatically on the next regen. Extraction reads the "
        "Zandronum source as its base (confirmed present for every row); UZDoom presence is a "
        "name cross-reference only (the `UZD` column). **Tier:** per row."
    )
    path = ROOT / "decorate" / "inventory" / "actor-properties.md"
    text, stats = build_inventory_file("DECORATE actor properties", note, header, rows, path,
                                        ["Tier", "Notes"], key_idx=(0, 2), defaults={"Tier": "C"})
    emit_diff_report("decorate-properties", stats)
    return write_or_check(path, text, check)


# ---------------------------------------------------------------------------
# decorate-actions
# ---------------------------------------------------------------------------

ACTION_FUNC_RE = re.compile(r'^DEFINE_ACTION_FUNCTION(_PARAMS)?\(\s*(\w+)\s*,\s*(\w+)\s*\)', re.M)

# ZScript method declaration for a known action name: optional modifier keywords, one or more
# comma-separated return types (ZScript allows multi-value returns, e.g. `bool, Actor
# A_SpawnItemEx(...)`), the name, a parameter list, then `;` (native, no body) or `{` (real body).
# Deliberately excludes flow-control keywords (return/if/while/...) from the "return type"
# position so a call site like `return A_Jump(...);` isn't mistaken for a declaration. The name
# itself is NOT hardcoded to an `A_` prefix -- Zandronum's own DEFINE_ACTION_FUNCTION table
# includes non-`A_`-prefixed entries too (`ACS_NamedExecute` and friends, `SetFOV`), so the
# pattern is built per-call from the actual known Zandronum-side name set (see
# `_zs_action_decl_re_for`) rather than guessed at from a naming convention.
_ZS_TYPE_TOK = r'[A-Za-z_]\w*(?:\s*<[^<>]*>)?'
_ZS_MODIFIERS = (
    r'(?:(?:native|action|virtual|override|final|abstract|static|clearscope|ui|play|internal|'
    # deprecated(...)'s message argument can itself contain "()", e.g.
    # deprecated("4.3", "Use A_StartSound() instead") -- allow one level of nested parens so the
    # naive [^)]* form doesn't truncate at that inner ")" and desync the rest of the match.
    r'protected|private|deprecated\((?:[^()]*(?:\([^()]*\)[^()]*)*)\))\s+)*'
)
_ZS_ACTION_EXCLUDE_RETURN_TOK = {"return", "if", "while", "for", "switch", "case", "else", "do"}


def _zs_action_decl_re_for(names):
    """Group 1 captures only the LAST return-type token (see module comment above); group 2 is
    the matched name, restricted by alternation to the given known-name set rather than a general
    `A_\\w+` guess, since ZScript declarations aren't otherwise distinguishable from an ordinary
    method with a call-shaped statement somewhere in a 45k-line tree."""
    alternation = "|".join(re.escape(n) for n in names)
    return re.compile(
        rf'^[ \t]*{_ZS_MODIFIERS}(?:{_ZS_TYPE_TOK}\s*,\s*)*({_ZS_TYPE_TOK})\s+'
        rf'\b({alternation})\b\s*\(([^)]*)\)\s*(?:const\s*)?(?:;|\{{)',
        re.M,
    )


def _extract_actions_from_tree(root):
    out = {}
    for path in iter_cpp_files(root):
        text = path.read_text(errors="replace")
        for m in ACTION_FUNC_RE.finditer(text):
            has_params, cls, name = m.groups()
            if name not in out:
                rel = path.relative_to(root)
                line = text.count("\n", 0, m.start()) + 1
                out[name] = (cls, "yes" if has_params else "no", f"{rel}:{line}")
    return out


def _extract_zs_actions_from_tree(root, known_names):
    """Returns a {name} presence set for every DECLARED (not called) method matching one of
    `known_names` somewhere in wadsrc/static/zscript/**/*.zs -- most DECORATE action functions
    moved out of C++ into ZScript, declared as ordinary class methods rather than a dedicated
    macro, so there is no single table to key off the way DEFINE_ACTION_FUNCTION provides for the
    C++ side. Only the name is extracted, never the declaration/body text (see
    decorate/AGENTS.md)."""
    if not known_names:
        return set()
    decl_re = _zs_action_decl_re_for(known_names)
    out = set()
    for path in iter_zs_files(root):
        text = _strip_comments(path.read_text(errors="replace"))
        for m in decl_re.finditer(text):
            return_tok, name = m.group(1), m.group(2)
            if return_tok.lower() in _ZS_ACTION_EXCLUDE_RETURN_TOK:
                continue
            out.add(name)
    return out


def gen_decorate_actions(check):
    zan_root = source_root("zandronum") / "src"
    uzd_root = source_root("uzdoom") / "src"
    zan_actions = _extract_actions_from_tree(zan_root)
    uzd_actions_cpp = _extract_actions_from_tree(uzd_root) if uzd_root.is_dir() else {}
    zs_root = uzdoom_zscript_root()
    uzd_actions_zs = (
        _extract_zs_actions_from_tree(zs_root, zan_actions.keys()) if zs_root.is_dir() else set()
    )
    uzd_present = set(uzd_actions_cpp) | uzd_actions_zs

    decorate_dir = ROOT / "decorate"
    header = ["Action", "Class", "Takes args", "Zan", "UZD", "Tier", "Notes"]
    rows = []
    for name in sorted(zan_actions, key=str.lower):
        cls, has_params, _loc = zan_actions[name]
        uzd = "yes" if name in uzd_present else "—"
        tier, notes = curated_cell(decorate_dir, "actions", name.lower())
        rows.append([name, cls, has_params, "yes", uzd, tier or "", notes or ""])

    note = (
        "**Generated:** by `python3 tools/gen_inventory.py decorate-actions` from every "
        "`DEFINE_ACTION_FUNCTION`/`DEFINE_ACTION_FUNCTION_PARAMS` call tree-wide in the Zandronum "
        "source's `src/` (spread across ~85 files -- see `../AGENTS.md`'s bucket table), "
        "cross-referenced against the UZDoom source's `src/` tree **and** every matching "
        "declared class method under `wadsrc/static/zscript/` (most DECORATE actions moved out "
        "of C++ into ZScript) by name for the `UZD` column. "
        "`Takes args` records whether the action was declared with the `_PARAMS` macro variant "
        "(i.e. callable with DECORATE arguments) -- do not hand-edit rows; use `../actions/"
        "<name>.md` for a full writeup (archetype 1) once one earns its cost, same as `a_look.md` "
        "-- its `Tier`/`Notes` cell is picked up automatically on the next regen. Extraction "
        "reads the Zandronum source as its base (confirmed present for every row); UZDoom "
        "presence is a name cross-reference only (the `UZD` column). **Tier:** per row."
    )
    path = ROOT / "decorate" / "inventory" / "actor-actions.md"
    text, stats = build_inventory_file("DECORATE action functions", note, header, rows, path,
                                        ["Tier", "Notes"], defaults={"Tier": "C"})
    emit_diff_report("decorate-actions", stats)
    return write_or_check(path, text, check)


# ---------------------------------------------------------------------------
# console-cvars / console-ccmds
# ---------------------------------------------------------------------------

CVAR_RE = re.compile(r'^(CUSTOM_CVAR|CVAR)\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*([^,]+),\s*([^)]+)\)', re.M)
# UZDoom-only: the "D" (documented) macro family adds a trailing description string. `CVARD`/
# `CUSTOM_CVARD` are (type,name,def,flags,descr) -- 5 args, console name == C++ name, same as
# CVAR_RE's capture-group layout. `CVARD_NAMED`/`CUSTOM_CVARD_NAMED` are
# (type,name,cname,def,flags,descr) -- 6 args, and the engine-visible name is `cname` (arg 3), not
# `name` (arg 2). Confirmed against src/common/console/c_cvars.h: `CVARD(type,name,def,flags,descr)`
# expands to `CVARD_NAMED(type,name,name,def,flags,descr)`, so the plain forms are genuinely a
# distinct (fewer-args) macro, not the same call with an extra parameter -- reading arg 3 for a
# plain CVARD/CUSTOM_CVARD line would misparse the `def` field as the console name.
CVARD_RE = re.compile(r'^(CUSTOM_CVARD|CVARD)\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*([^,]+),\s*([^,]+),', re.M)
CVARD_NAMED_RE = re.compile(
    r'^(CUSTOM_CVARD_NAMED|CVARD_NAMED)\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*([^,]+),\s*([^,]+),', re.M)
# A handful of cvars bypass the CVAR/CUSTOM_CVAR macros entirely and construct an F*CVar directly
# (e.g. `FIntCVar msglevel ("msg", 0, CVAR_ARCHIVE);`) -- the engine-visible cvar name is the
# quoted string literal, not the C++ variable name, so this needs its own pattern and its own
# capture-group layout rather than reusing CVAR_RE.
RAW_CVAR_RE = re.compile(r'^F(Bool|Int|Float|String)CVar\s+\w+\s*\(\s*"(\w+)"\s*,\s*([^,]+),\s*([^)]+)\)', re.M)
CCMD_RE = re.compile(r'^CCMD\s*\(\s*(\w+)\s*\)', re.M)


def _extract_cvars_from_tree(root):
    out = {}
    for path in iter_cpp_files(root):
        text = path.read_text(errors="replace")
        for m in CVAR_RE.finditer(text):
            kind, ctype, name, default, flags = m.groups()
            if name not in out:
                rel = path.relative_to(root)
                line = text.count("\n", 0, m.start()) + 1
                out[name] = (ctype.strip(), "custom" if kind == "CUSTOM_CVAR" else "plain",
                             flags.strip().replace("\n", " "), f"{rel}:{line}")
        for m in CVARD_RE.finditer(text):
            kind, ctype, name, default, flags = m.groups()
            if name not in out:
                rel = path.relative_to(root)
                line = text.count("\n", 0, m.start()) + 1
                out[name] = (ctype.strip(), "custom" if kind == "CUSTOM_CVARD" else "plain",
                             flags.strip().replace("\n", " "), f"{rel}:{line}")
        for m in CVARD_NAMED_RE.finditer(text):
            kind, ctype, _cppname, cname, default, flags = m.groups()
            if cname not in out:
                rel = path.relative_to(root)
                line = text.count("\n", 0, m.start()) + 1
                out[cname] = (ctype.strip(), "custom" if kind == "CUSTOM_CVARD_NAMED" else "plain",
                              flags.strip().replace("\n", " "), f"{rel}:{line}")
        for m in RAW_CVAR_RE.finditer(text):
            ctype, name, default, flags = m.groups()
            if name not in out:
                rel = path.relative_to(root)
                line = text.count("\n", 0, m.start()) + 1
                out[name] = (ctype.strip(), "plain", flags.strip().replace("\n", " "), f"{rel}:{line}")
    return out


def _extract_ccmds_from_tree(root):
    out = {}
    for path in iter_cpp_files(root):
        text = path.read_text(errors="replace")
        for m in CCMD_RE.finditer(text):
            name = m.group(1)
            if name not in out:
                rel = path.relative_to(root)
                line = text.count("\n", 0, m.start()) + 1
                out[name] = f"{rel}:{line}"
    return out


def gen_console_cvars(check):
    zan_root = source_root("zandronum") / "src"
    uzd_root = source_root("uzdoom") / "src"
    zan_cvars = _extract_cvars_from_tree(zan_root)
    uzd_cvars = _extract_cvars_from_tree(uzd_root) if uzd_root.is_dir() else {}

    console_dir = ROOT / "console"
    header = ["CVar", "Type", "Kind", "Flags", "Zan", "UZD", "Tier", "Notes"]
    rows = []
    for name in sorted(zan_cvars, key=str.lower):
        ctype, kind, flags, _loc = zan_cvars[name]
        uzd = "yes" if name in uzd_cvars else "—"
        tier, notes = curated_cell(console_dir, "notes", name.lower())
        rows.append([name, ctype, kind, flags, "yes", uzd, tier or "", notes or ""])

    note = (
        "**Generated:** by `python3 tools/gen_inventory.py console-cvars` from every "
        "`CVAR`/`CUSTOM_CVAR` declaration tree-wide in the Zandronum source's `src/` (~197 files "
        "declare at least one -- see `../AGENTS.md`), plus a handful of cvars declared via a raw "
        "`F*CVar` constructor bypassing those macros (e.g. `skill`/`msg`/`noise` -- the "
        "engine-visible name is the constructor's quoted string argument, not the C++ variable "
        "name); UZDoom's own equivalent of the bypass is the `CVARD`/`CUSTOM_CVARD` \"documented\" "
        "macro family, whose `_NAMED` variants (`CVARD_NAMED`/`CUSTOM_CVARD_NAMED`) also split the "
        "console name from the C++ variable name -- both matched for the `UZD` column, "
        "cross-referenced against the UZDoom source's "
        "`src/` tree by name for the `UZD` column. `Flags` is the raw flag-macro expression from "
        "the declaration (e.g. `CVAR_ARCHIVE | CVAR_NOSETBYACS`), not yet decoded per-flag -- see "
        "`zandronum/docs/commands.txt` for prose meaning. Do not hand-edit rows; use "
        "`../notes/<name>.md` instead -- its `Tier`/`Notes` cell is picked up automatically on "
        "the next regen. Extraction reads the Zandronum source as its base (confirmed present "
        "for every row); UZDoom presence is a name cross-reference only (the `UZD` column). "
        "**Tier:** per row."
    )
    path = ROOT / "console" / "inventory" / "cvars.md"
    text, stats = build_inventory_file("Console variables (CVars)", note, header, rows, path,
                                        ["Tier", "Notes"], defaults={"Tier": "C"})
    emit_diff_report("console-cvars", stats)
    return write_or_check(path, text, check)


def gen_console_ccmds(check):
    zan_root = source_root("zandronum") / "src"
    uzd_root = source_root("uzdoom") / "src"
    zan_ccmds = _extract_ccmds_from_tree(zan_root)
    uzd_ccmds = _extract_ccmds_from_tree(uzd_root) if uzd_root.is_dir() else {}

    console_dir = ROOT / "console"
    header = ["Command", "Zan", "UZD", "Tier", "Notes"]
    rows = []
    for name in sorted(zan_ccmds, key=str.lower):
        uzd = "yes" if name in uzd_ccmds else "—"
        tier, notes = curated_cell(console_dir, "notes", name.lower())
        rows.append([name, "yes", uzd, tier or "", notes or ""])

    note = (
        "**Generated:** by `python3 tools/gen_inventory.py console-ccmds` from every `CCMD` "
        "declaration tree-wide in the Zandronum source's `src/`, cross-referenced against the "
        "UZDoom source's `src/` tree by name for the `UZD` column. See "
        "`zandronum/docs/commands.txt` for first-party prose on what a given command does -- the "
        "preferred source for `notes/` entries over re-deriving behavior from each command's own "
        "(often large) implementation function; a `../notes/<name>.md` file's `Tier`/`Notes` "
        "cell is picked up automatically on the next regen. Do not hand-edit rows. Extraction "
        "reads the Zandronum source as its base (confirmed present for every row); UZDoom "
        "presence is a name cross-reference only (the `UZD` column). **Tier:** per row."
    )
    path = ROOT / "console" / "inventory" / "ccmds.md"
    text, stats = build_inventory_file("Console commands (CCMDs)", note, header, rows, path,
                                        ["Tier", "Notes"], defaults={"Tier": "C"})
    emit_diff_report("console-ccmds", stats)
    return write_or_check(path, text, check)


# ---------------------------------------------------------------------------
# acs-signatures -- regenerates acs/INDEX.md's "Signature-only (tier C)" block.
# ---------------------------------------------------------------------------

SPECIAL_ENTRY_RE = re.compile(
    r'^(-?\d+):(\w+)\(([^)]*)\)(?::(\w+))?(:0)?,?\s*$', re.M
)
GFUNC_ENTRY_RE = re.compile(r'\{\s*"(\w+)"\s*,\s*"([a-z;]*)"\s*\}')
TYPE_NAMES = {"i": "int", "r": "raw", "f": "fixed", "b": "bool", "s": "str"}


def _render_params(required, optional):
    req = ", ".join(required)
    if optional:
        opt = ", ".join(optional)
        return f"{req}[, {opt}]" if req else f"[{opt}]"
    return req


def _parse_special_table(zt_bcc_root):
    text = (zt_bcc_root / "lib" / "zcommon.bcs").read_text()
    start = text.index("\nspecial")
    body = text[start:]
    entries = {}
    for m in SPECIAL_ENTRY_RE.finditer(body):
        index, name, params_raw, rettype, zero = m.groups()
        index = int(index)
        if ";" in params_raw:
            req_raw, opt_raw = params_raw.split(";", 1)
        else:
            req_raw, opt_raw = params_raw, ""
        required = [p.strip() for p in req_raw.split(",") if p.strip()]
        optional = [p.strip() for p in opt_raw.split(",") if p.strip()]
        return_type = rettype if rettype else "raw"  # special-table quirk: no type -> raw
        sig = f"{return_type} {name}({_render_params(required, optional)})"
        entries[name] = {"index": index, "sig": sig, "not_callable": bool(zero)}
    return entries


def _decode_gfunc_format(fmt):
    ret = "void"
    i = 0
    if not (i >= len(fmt) or fmt[i] == ';'):
        ret = TYPE_NAMES.get(fmt[i], fmt[i])
        i += 1
    required, optional, opt = [], [], False
    if i < len(fmt) and fmt[i] == ';':
        i += 1
        while i < len(fmt):
            c = fmt[i]
            if c == ';':
                opt = True
            else:
                (optional if opt else required).append(TYPE_NAMES.get(c, c))
            i += 1
    return ret, required, optional


def _parse_gfuncs(zt_bcc_root):
    """`g_funcs[]`'s own name strings are all-lowercase (`"acs_executewait"`) -- there is no
    proper-case name table anywhere in zt-bcc source; the PascalCase spelling every existing
    tier-C entry and the ZDoom wiki use (`ACS_ExecuteWait`) is a naming convention external to
    this table. Returns {lowercase_name: (ret, required, optional)} -- callers apply a casing
    map (see gen_acs_signatures) before rendering."""
    text = (zt_bcc_root / "src" / "builtin.c").read_text()
    entries = {}
    for m in GFUNC_ENTRY_RE.finditer(text):
        name, fmt = m.groups()
        entries[name] = _decode_gfunc_format(fmt)
    return entries


def _require_names(path, names):
    """Hard-fail rather than silently render an empty extraction as absence -- a moved/renamed
    engine source file or a regex broken by an upstream refactor must stop the run, not produce
    340 bullets asserting a whole engine's worth of false negatives (see gen_acs_signatures's
    Zan/UZD pair, which prints a name-presence verdict for every cross-referenced bullet)."""
    if not names:
        print(f"gen_inventory.py: found zero names in {path} -- extractor regex likely stale "
              f"against upstream source, refusing to regenerate on empty data", file=sys.stderr)
        sys.exit(1)
    return names


def _actionspecials_names(root, rel_path):
    path = root / rel_path
    if not path.is_file():
        print(f"gen_inventory.py: expected {path} -- has the engine source moved?", file=sys.stderr)
        sys.exit(1)
    text = path.read_text()
    names = {m.group(1) for m in re.finditer(r'DEFINE_SPECIAL\(\s*(\w+)\s*,', text)}
    return _require_names(path, names)


# (?:ACSF|ASCF) -- Zandronum's own EACSFunctions enum misspells three entries ASCF_ (GetControlPointInfo,
# SetControlPointInfo, GetSkinProperty at src/p_acs.cpp:5547-5549), consistently in both the enum and the
# `case` labels -- a real (if typo'd) identifier, not a comment. ACSF_-only matching silently dropped
# those three and, separately from this generator, was already found and fixed in engine_matrix.py's
# _ACSF_ENTRY_RE (2026-08-14) -- ported here for the first time, since gen_acs_signatures never picked up
# that fix. UZDoom's own enum spells the prefix correctly throughout; the alternation is a no-op there.
def _acsf_names(root, rel_path):
    path = root / rel_path
    if not path.is_file():
        print(f"gen_inventory.py: expected {path} -- has the engine source moved?", file=sys.stderr)
        sys.exit(1)
    text = path.read_text()
    m = re.search(r'enum EACSFunctions\s*\{(.*?)\n\};', text, re.S)
    if m is None:
        print(f"gen_inventory.py: 'enum EACSFunctions' not found in {path} -- extractor regex "
              f"likely stale against upstream source", file=sys.stderr)
        sys.exit(1)
    names = {m2.group(1) for m2 in re.finditer(r'(?:ACSF|ASCF)_(\w+)', m.group(1))}
    return _require_names(path, names)


def _gfuncs_pcd_names(zt_bcc_root):
    """{lowercase g_funcs[] name: canonical 'PCD_NAME'} for every builtin that resolves to
    exactly one engine dispatch opcode -- positional, not name-derived. zt-bcc's own
    t_create_builtins()/setup_func() (builtin.c) binds g_funcs[entry] to g_deds[entry] by array
    position for entry < len(g_deds); several g_funcs entries are source-level aliases whose PCD
    doesn't match their own name this way -- BlueCount/BlueScore/RedCount/RedScore compile to
    PCD_BLUETEAMCOUNT/PCD_BLUETEAMSCORE/PCD_REDTEAMCOUNT/PCD_REDTEAMSCORE (BlueTeamCount's/etc.'s
    own opcodes; PCD_BLUECOUNT/PCD_BLUESCORE don't exist at all), confirmed via g_deds[29..36]
    lining up with g_funcs[29..36] one-for-one. A name-matching `case PCD_<OWN_NAME>:` scan
    (tried first) missed exactly these four, reporting them as an undeterminable multi-PCD
    builtin alongside genuine cases like Print/Log -- this positional approach is what
    t_create_builtins itself does, so it's exact rather than a name heuristic.

    Entries at or beyond len(g_deds) (the format-function bucket -- Print/Log/HudMessage/
    PrintBold/HudMessageBold/StrParam -- and the interned-function bucket -- ACS_ExecuteWait/
    ACS_NamedExecuteWait) compile to a multi-instruction sequence with no single opcode and are
    deliberately excluded, not matched to a made-up single PCD."""
    text = (zt_bcc_root / "src" / "builtin.c").read_text()

    def array_body(name):
        start = text.index(name + "[] = {") + len(name + "[] = {")
        end = text.index("\n};", start)
        return text[start:end]

    ded_pcds = [f"PCD_{m.group(1)}" for m in re.finditer(r'PCD_(\w+)', array_body("g_deds"))]
    func_names = [m.group(1) for m in GFUNC_ENTRY_RE.finditer(array_body("g_funcs"))]
    if len(func_names) < len(ded_pcds):
        print("gen_inventory.py: g_funcs[] has fewer entries than g_deds[] in builtin.c -- "
              "layout changed upstream, positional PCD mapping is unsafe", file=sys.stderr)
        sys.exit(1)
    return _require_names(zt_bcc_root / "src" / "builtin.c",
                           {func_names[i].lower(): ded_pcds[i] for i in range(len(ded_pcds))})


def _pcd_case_names(root, rel_path):
    """Every `PCD_<NAME>` this engine's p_acs.cpp dispatches via a `case PCD_<NAME>:` label."""
    path = root / rel_path
    if not path.is_file():
        print(f"gen_inventory.py: expected {path} -- has the engine source moved?", file=sys.stderr)
        sys.exit(1)
    text = path.read_text()
    names = {f"PCD_{m.group(1)}" for m in re.finditer(r'case\s+PCD_(\w+)\s*:', text)}
    return _require_names(path, names)


def gen_acs_signatures(check):
    zt_bcc_root = source_root("zt-bcc")
    zandronum_root = source_root("zandronum")
    uzdoom_root = source_root("uzdoom")

    special = _parse_special_table(zt_bcc_root)
    gfuncs = _parse_gfuncs(zt_bcc_root)
    # Lower-cased: zcommon.bcs and the engine tables don't always agree on casing for the same
    # name (e.g. zcommon.bcs's "Acs_LockedExecute" vs actionspecials.h's "ACS_LockedExecute") --
    # matching is case-insensitive per ACS/BCS convention throughout this tree, and a
    # case-sensitive check here would wrongly report a real, working special as absent.
    special_names = {n.lower() for n in _actionspecials_names(zandronum_root, "src/actionspecials.h")}
    acsf_names = {n.lower() for n in _acsf_names(zandronum_root, "src/p_acs.cpp")}
    # UZDoom's engine-side tables live under src/playsim/ instead of bare src/ -- structurally
    # identical layout otherwise, confirmed and documented in acs/AGENTS.md's bucket table.
    uzd_special_names = {n.lower() for n in _actionspecials_names(uzdoom_root, "src/playsim/actionspecials.h")}
    uzd_acsf_names = {n.lower() for n in _acsf_names(uzdoom_root, "src/playsim/p_acs.cpp")}
    gfuncs_pcd = _gfuncs_pcd_names(zt_bcc_root)
    zan_pcd_cases = _pcd_case_names(zandronum_root, "src/p_acs.cpp")
    uzd_pcd_cases = _pcd_case_names(uzdoom_root, "src/playsim/p_acs.cpp")

    # {lowercase: preferred-case} covering every name this tree already knows about (documented
    # functions/families AND existing tier-C bullets) -- the only source of canonical PascalCase
    # spelling for compiler builtins, since g_funcs[] itself only has lowercase names (see
    # _parse_gfuncs). A name genuinely new to this run (not in the map at all) keeps its
    # source-native casing, which is only ever lowercase for the compiler-builtin bucket.
    casing_map = lookup._known_names("acs")

    # Deliberately NOT the same set as casing_map's keys: that includes existing tier-C names
    # too (which must stay eligible for regeneration), whereas "documented" here means
    # lookup.py's full resolution stack finds a real doc -- a dedicated functions/*.md, a
    # families/*.md heading, OR a weak inline mention (e.g. "NamedExecuteClientScript" is only
    # ever mentioned in prose inside executeclientscript.md, never its own heading) -- any of
    # which means the name is promoted out of tier C for good. Only a bare `_try_tier_c` hit
    # (or no hit at all) leaves a name eligible for (re)generation here.
    all_candidate_names = set(gfuncs) | set(special)
    documented = set()
    for raw_name in all_candidate_names:
        display = casing_map.get(raw_name.lower(), raw_name)
        result, _ = lookup.resolve(display, "acs")
        if result is not None and result.kind != "tier-c":
            documented.add(raw_name.lower())

    bullets = {}
    for name, (ret, required, optional) in gfuncs.items():
        if name.lower() in documented:
            continue
        display = casing_map.get(name.lower(), name)
        sig = f"{ret} {display}({_render_params(required, optional)})"
        # Zan/UZD pair only for a builtin with exactly one opcode (see _gfuncs_pcd_names) -- a
        # format-function/interned-function builtin (Print, Log, StrParam, ACS_ExecuteWait, ...)
        # has no single PCD to check and keeps the bare bucket.
        pcd = gfuncs_pcd.get(name.lower())
        bucket = "compiler builtin"
        if pcd is not None:
            zan_hit, uzd_hit = pcd in zan_pcd_cases, pcd in uzd_pcd_cases
            bucket += f"; Zan: {'yes' if zan_hit else 'no'}, UZD: {'yes' if uzd_hit else 'no'}"
        bullets[display] = f"- `{display}` ({bucket}) — Tier C (signature only, auto-generated): `{sig}`"
    for raw_name, entry in special.items():
        if raw_name.lower() in documented:
            continue
        name = casing_map.get(raw_name.lower(), raw_name)
        entry["sig"] = entry["sig"].replace(raw_name, name, 1)
        idx = entry["index"]
        if idx > 0:
            zan_hit, uzd_hit = raw_name.lower() in special_names, raw_name.lower() in uzd_special_names
            bucket = f"action special, index {idx}; Zan: {'yes' if zan_hit else 'no'}, UZD: {'yes' if uzd_hit else 'no'}"
            if entry["not_callable"]:
                bucket += "; not script-callable"
        else:
            zan_hit, uzd_hit = raw_name.lower() in acsf_names, raw_name.lower() in uzd_acsf_names
            bucket = f"extension function, index {idx}; Zan: {'yes' if zan_hit else 'no'}, UZD: {'yes' if uzd_hit else 'no'}"
        bullets[name] = f"- `{name}` ({bucket}) — Tier C (signature only, auto-generated): `{entry['sig']}`"

    index_path = ROOT / "acs" / "INDEX.md"
    old_text = index_path.read_text()
    heading = "### Signature-only (tier C)"
    idx = old_text.index(heading)
    body_start = idx + len(heading)
    m = re.search(r'\n#{2,3} ', old_text[body_start:])
    body_end = body_start + m.start() if m else len(old_text)
    old_body = old_text[body_start:body_end]

    # Preserve an existing bullet only if its name isn't in EITHER source table at all (e.g.
    # CreateTranslation -- a hand-added compiler keyword with no table entry). A name that IS in
    # a table but got excluded from `bullets` because it's now documented elsewhere (a real
    # functions/*.md, a family heading, or a weak inline mention) must NOT be preserved here --
    # that would resurrect a stale tier-C entry for something already promoted out of tier C.
    table_names_lower = {n.lower() for n in all_candidate_names}
    existing_bullet_re = re.compile(r'^-\s*`(\w+)`.*$', re.M)
    preserved = 0
    for m2 in existing_bullet_re.finditer(old_body):
        name = m2.group(1)
        if name not in bullets and name.lower() not in table_names_lower:
            bullets[name] = m2.group(0)
            preserved += 1

    new_bullets = sorted(bullets.values(), key=lambda l: re.search(r'`(\w+)`', l).group(1).lower())
    # First paragraph of the old body (the static explanatory note) is preserved verbatim.
    note_match = re.match(r'(.*?\n)\n(?=- `)', old_body, re.S)
    note = note_match.group(1) if note_match else old_body.split("\n- `", 1)[0]
    new_body = f"{note}\n" + "\n".join(new_bullets) + "\n"
    new_text = old_text[:body_start] + new_body + old_text[body_end:]

    print(f"acs-signatures: {len(bullets)} tier-C entries ({preserved} preserved hand-written)", file=sys.stderr)
    return write_or_check(index_path, new_text, check)


TARGETS = {
    "decorate-flags": gen_decorate_flags,
    "decorate-properties": gen_decorate_properties,
    "decorate-actions": gen_decorate_actions,
    "console-cvars": gen_console_cvars,
    "console-ccmds": gen_console_ccmds,
    "acs-signatures": gen_acs_signatures,
}


def main():
    args = sys.argv[1:]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    if not args:
        print(__doc__)
        sys.exit(1)
    target = args[0]
    targets = list(TARGETS) if target == "all" else [target]
    if target != "all" and target not in TARGETS:
        print(f"unknown target {target!r}; choices: {', '.join(TARGETS)}, all", file=sys.stderr)
        sys.exit(1)
    ok = True
    for t in targets:
        ok = TARGETS[t](check) and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
