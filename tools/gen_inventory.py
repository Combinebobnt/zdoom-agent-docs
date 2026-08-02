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
DEFINE_DEP_FLAG_RE = re.compile(r'DEFINE_DEPRECATED_FLAG\(\s*(\w+)\s*\)')
DEFINE_DUMMY_FLAG_RE = re.compile(r'DEFINE_DUMMY_FLAG\(\s*(\w+)\s*\)')


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
        "for the `UZD` column -- do not hand-edit rows; add a `../notes/<flag>.md` file and its "
        "`Tier`/`Notes` cell is picked up automatically from that file's own `Tier:` stamp on "
        "the next regen. **Engine:** Zandronum 3.2.1 confirmed present for every row; UZDoom "
        "4.15pre presence per the `UZD` column only, not independently behavior-verified. "
        "**Tier:** per row (defaults to C until a `notes/` file promotes it)."
    )
    path = ROOT / "decorate" / "inventory" / "actor-flags.md"
    text, stats = build_inventory_file("DECORATE actor flags", note, header, rows, path,
                                        ["Tier", "Notes"], defaults={"Tier": "C"})
    emit_diff_report("decorate-flags", stats)
    return write_or_check(path, text, check)


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
    to whichever class's declaration happened to be read last."""
    text = _strip_comments(path.read_text())
    out = {}
    for pm in DEFINE_PROPERTY_RE.finditer(text):
        name, spec, cls = pm.groups()
        out[(name, cls)] = (spec, "property")
    for pm in DEFINE_CLASS_PROPERTY_RE.finditer(text):
        name, spec, cls = pm.groups()
        out[(name, cls)] = (spec, "class-property")
    for pm in DEFINE_CLASS_PROPERTY_PREFIX_RE.finditer(text):
        prefix, name, spec, cls = pm.groups()
        out[(f"{prefix}.{name}", cls)] = (spec, "class-property-prefix")
    return out


def gen_decorate_properties(check):
    zan_file = source_root("zandronum") / "src" / "thingdef" / "thingdef_properties.cpp"
    uzd_file = source_root("uzdoom") / "src" / "scripting" / "thingdef_properties.cpp"
    zan_props = _extract_properties_from_file(zan_file)
    uzd_props = _extract_properties_from_file(uzd_file) if uzd_file.is_file() else {}

    decorate_dir = ROOT / "decorate"
    header = ["Property", "Kind", "Class", "Param spec", "Zan", "UZD", "Tier", "Notes"]
    rows = []
    for name, cls in sorted(zan_props, key=lambda k: (k[0].lower(), k[1].lower())):
        spec, kind = zan_props[(name, cls)]
        uzd = "yes" if (name, cls) in uzd_props else "—"
        tier, notes = curated_cell(decorate_dir, "notes", f"{name.lower()}-{cls.lower()}", name.lower())
        rows.append([name, kind, cls, spec, "yes", uzd, tier or "", notes or ""])

    note = (
        "**Generated:** by `python3 tools/gen_inventory.py decorate-properties` from the "
        "Zandronum source's `src/thingdef/thingdef_properties.cpp` (`DEFINE_PROPERTY`/"
        "`DEFINE_CLASS_PROPERTY`), cross-referenced against the UZDoom source's "
        "`src/scripting/thingdef_properties.cpp` by (name, class) for the `UZD` column -- "
        "properties are class-scoped, and the same name is legitimately redeclared with a "
        "different spec for a different class (e.g. `translation`), so `Property` alone is not "
        "unique in this table; `Property`+`Class` together are. `Param spec` is the property's "
        "raw parameter-type-code string from the macro call, not yet decoded into plain type "
        "names -- do not hand-edit rows; add a `../notes/<property>.md` file instead (or "
        "`<property>-<class>.md` if the same name needs separate notes per class) and its "
        "`Tier`/`Notes` cell is picked up automatically on the next regen. **Engine:** "
        "Zandronum 3.2.1 confirmed present for every row; UZDoom presence per the `UZD` column "
        "only. **Tier:** per row."
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


def gen_decorate_actions(check):
    zan_root = source_root("zandronum") / "src"
    uzd_root = source_root("uzdoom") / "src"
    zan_actions = _extract_actions_from_tree(zan_root)
    uzd_actions = _extract_actions_from_tree(uzd_root) if uzd_root.is_dir() else {}

    decorate_dir = ROOT / "decorate"
    header = ["Action", "Class", "Takes args", "Zan", "UZD", "Tier", "Notes"]
    rows = []
    for name in sorted(zan_actions, key=str.lower):
        cls, has_params, _loc = zan_actions[name]
        uzd = "yes" if name in uzd_actions else "—"
        tier, notes = curated_cell(decorate_dir, "actions", name.lower())
        rows.append([name, cls, has_params, "yes", uzd, tier or "", notes or ""])

    note = (
        "**Generated:** by `python3 tools/gen_inventory.py decorate-actions` from every "
        "`DEFINE_ACTION_FUNCTION`/`DEFINE_ACTION_FUNCTION_PARAMS` call tree-wide in the Zandronum "
        "source's `src/` (spread across ~85 files -- see `../CLAUDE.md`'s bucket table), "
        "cross-referenced against the UZDoom source's `src/` tree by name for the `UZD` column. "
        "`Takes args` records whether the action was declared with the `_PARAMS` macro variant "
        "(i.e. callable with DECORATE arguments) -- do not hand-edit rows; use `../actions/"
        "<name>.md` for a full writeup (archetype 1) once one earns its cost, same as `a_look.md` "
        "-- its `Tier`/`Notes` cell is picked up automatically on the next regen. **Engine:** "
        "Zandronum 3.2.1 confirmed present for every row; UZDoom presence per the `UZD` column "
        "only. **Tier:** per row."
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
        "declare at least one -- see `../CLAUDE.md`), plus a handful of cvars declared via a raw "
        "`F*CVar` constructor bypassing those macros (e.g. `skill`/`msg`/`noise` -- the "
        "engine-visible name is the constructor's quoted string argument, not the C++ variable "
        "name), cross-referenced against the UZDoom source's "
        "`src/` tree by name for the `UZD` column. `Flags` is the raw flag-macro expression from "
        "the declaration (e.g. `CVAR_ARCHIVE | CVAR_NOSETBYACS`), not yet decoded per-flag -- see "
        "`zandronum/docs/commands.txt` for prose meaning. Do not hand-edit rows; use "
        "`../notes/<name>.md` instead -- its `Tier`/`Notes` cell is picked up automatically on "
        "the next regen. **Engine:** Zandronum 3.2.1 confirmed present for every row; UZDoom "
        "presence per the `UZD` column only. **Tier:** per row."
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
        "cell is picked up automatically on the next regen. Do not hand-edit rows. **Engine:** "
        "Zandronum 3.2.1 confirmed present for every row; UZDoom presence per the `UZD` column "
        "only. **Tier:** per row."
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


def _actionspecials_names(zandronum_root):
    text = (zandronum_root / "src" / "actionspecials.h").read_text()
    return {m.group(1) for m in re.finditer(r'DEFINE_SPECIAL\(\s*(\w+)\s*,', text)}


def _acsf_names(zandronum_root):
    text = (zandronum_root / "src" / "p_acs.cpp").read_text()
    m = re.search(r'enum EACSFunctions\s*\{(.*?)\n\};', text, re.S)
    body = m.group(1) if m else ""
    return {m2.group(1) for m2 in re.finditer(r'ACSF_(\w+)', body)}


def gen_acs_signatures(check):
    zt_bcc_root = source_root("zt-bcc")
    zandronum_root = source_root("zandronum")

    special = _parse_special_table(zt_bcc_root)
    gfuncs = _parse_gfuncs(zt_bcc_root)
    # Lower-cased: zcommon.bcs and the Zandronum engine tables don't always agree on casing for
    # the same name (e.g. zcommon.bcs's "Acs_LockedExecute" vs actionspecials.h's
    # "ACS_LockedExecute") -- matching is case-insensitive per ACS/BCS convention throughout
    # this tree, and a case-sensitive check here would wrongly report a real, working special as
    # absent from the engine.
    special_names = {n.lower() for n in _actionspecials_names(zandronum_root)}
    acsf_names = {n.lower() for n in _acsf_names(zandronum_root)}

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
        bullets[display] = f"- `{display}` (compiler builtin) — Tier C (signature only, auto-generated): `{sig}`"
    for raw_name, entry in special.items():
        if raw_name.lower() in documented:
            continue
        name = casing_map.get(raw_name.lower(), raw_name)
        entry["sig"] = entry["sig"].replace(raw_name, name, 1)
        idx = entry["index"]
        if idx > 0:
            bucket = f"action special, index {idx}"
            if raw_name.lower() not in special_names:
                bucket += "; not in this engine's special table"
            if entry["not_callable"]:
                bucket += "; not script-callable"
        else:
            bucket = f"extension function, index {idx}"
            if raw_name.lower() not in acsf_names:
                bucket += "; not in this engine's ACSF enum"
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
