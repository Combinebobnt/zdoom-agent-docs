#!/usr/bin/env python3
"""Look up a callable's signature (or a table-inventory row) from this doc tree, across
every section by default.

Not a substitute for reading the full doc file -- this strips everything except the
signature and whatever parameter-level prose the doc actually contains, for the common
case of "what are the arguments and what do they mean" before writing a call. For a
Table-of-entries section (DECORATE flags, console cvars, etc.) it instead prints the
matching inventory row and points at a notes/ file if one exists.

Usage:
    python3 tools/lookup.py <name>                    # search every section
    python3 tools/lookup.py --section acs <name>      # scope to one section
    python3 tools/lookup.py --long <name>              # signature + parameter info

Resolution order within a section: a dedicated primary-callable file (functions/,
actions/, classes/ -- whichever the section uses), a families/*.md per-callable
heading, a weak whole-file inline mention (renames/aliases), an INDEX.md
"Signature-only (tier C)" entry (acs only, for now -- the only section with that
generated block), then a table-inventory row. Sections are tried in the order
declared in sections.py (acs first). Fails loudly if nothing hits anywhere -- this
tool never falls back to re-deriving an answer from a compiler/engine table this tree
hasn't verified yet.
"""
import argparse
import difflib
import re
import sys
import textwrap
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections as S  # noqa: E402

ROOT = S.ROOT

TIER_C_RE = re.compile(
    r'^-\s*`(\w+)`[^\n]*?Tier C \(signature only(?:, auto-generated)?\):\s*`([^`]+)`', re.M
)

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*\S)\s*$')
BOLD_PSEUDO_HEADING_RE = re.compile(r'^\*\*([A-Za-z][A-Za-z /]*)\*\*\s*:?\s*$')
PARAM_HEADING_RE = re.compile(r'^(Parameters|Arguments|Params)\b', re.I)
BULLET_START_RE = re.compile(r'^\s*[-*]\s+')
BULLET_TOKEN_RE = re.compile(
    r'^\s*[-*]\s+(?:\*\*`([A-Za-z_]\w*)`\*\*|`([A-Za-z_]\w*)`|\*\*([A-Za-z_]\w*)\*\*)'
)
FENCE_RE = re.compile(r'^\s*```')
SIG_SECTION_RE = re.compile(r'^#{1,6}\s+.*\b(Signature|Syntax)\b', re.I)
BOLD_SIG_RE = re.compile(r'^\*\*(Signature|Syntax)\s*:?\*\*', re.I)

# Optional leading return-type word + name + single-level parens. Every signature in this
# tree uses one flat pair of parens (optional args go in [...] inside them, never nested
# parens), so a non-nesting-aware regex is enough. A handful of docs write "Name (args)"
# with a space before the paren in a fenced code block (openmenu.md, sector_setfade.md),
# so a bare space can't be used to reject prose parentheticals -- that's _is_signature_shaped's
# job, based on what's actually inside the parens.
FULL_SIG_RE = re.compile(
    r'(?:\b(int|str|fixed|bool|raw|void)\s+)?\b([A-Za-z_]\w*)\s?\(([^()]*)\)'
)
TYPE_WORDS = {"int", "str", "fixed", "bool", "raw", "void", "array"}
NOISE_TOKENS = {"true", "false", "default"}
# Untyped-but-plausible param list, e.g. "tag, r, g, b[, desat]" -- no prose punctuation at all.
PLAUSIBLE_PARAMS_RE = re.compile(r'^[\w\s,\[\];]*$')
# A single comma-separated segment that is just "type" or "type identifier" -- used to
# require an actual typed-parameter *shape*, not merely the word "raw" or "void" occurring
# anywhere in a sentence ("a raw numeric call", "does nothing" -> no, but close: a bare
# word match on \b(raw)\b would hit "a raw numeric call" too).
TYPED_PART_RE = re.compile(r'^(int|str|fixed|bool|raw|void)(\s+[A-Za-z_]\w*)?$')


def _looks_typed(params):
    for part in params.split(","):
        part = part.strip().strip("[]").strip()
        if part and TYPED_PART_RE.match(part):
            return True
    return False


Sig = namedtuple("Sig", "name text params")
Result = namedtuple("Result", "signature file kind param_blocks shared_blocks note")
InventoryResult = namedtuple("InventoryResult", "name row header file notes_file")


def sig_candidates(line):
    out = []
    for m in FULL_SIG_RE.finditer(line):
        rettype, name, params = m.groups()
        prefix = f"{rettype} " if rettype else ""
        out.append(Sig(name, f"{prefix}{name}({params})", params))
    return out


def param_names(params_str):
    names = set()
    for tok in re.findall(r'[A-Za-z_]\w*', params_str or ""):
        low = tok.lower()
        if low not in TYPE_WORDS and low not in NOISE_TOKENS:
            names.add(low)
    return names


def _is_signature_shaped(sig):
    p = sig.params.strip()
    if p == "":
        return True
    if "format-item" in sig.text:
        return True
    if _looks_typed(p):
        return True
    return bool(PLAUSIBLE_PARAMS_RE.match(p))


def _gather_stages(lines):
    """Candidate line groups in priority order: H1, Signature/Syntax section (fenced
    code preferred), bold Signature/Syntax line, first ~40 lines."""
    stage_h1 = [lines[0]] if lines else []

    stage_sig_section = []
    for i, l in enumerate(lines):
        if not SIG_SECTION_RE.match(l):
            continue
        limit = min(i + 15, len(lines))
        j = i
        while j < limit and not FENCE_RE.match(lines[j]):
            j += 1
        if j < limit:
            fenced = []
            k = j + 1
            while k < len(lines) and not FENCE_RE.match(lines[k]):
                if lines[k].strip():
                    fenced.append(lines[k].strip().rstrip(";"))
                k += 1
            stage_sig_section.extend(fenced)
        else:
            stage_sig_section.extend(lines[i : min(i + 12, len(lines))])

    stage_bold = [l for l in lines if BOLD_SIG_RE.match(l)]
    stage_early = lines[1:41]
    return [stage_h1, stage_sig_section, stage_bold, stage_early]


def find_signature(lines):
    """The file's own canonical signature, stage by stage (H1, then Signature/Syntax
    section, then bold Signature/Syntax line, then first ~40 lines). This deliberately
    does NOT search for a name match against the query -- doing so would let a
    disproven/prose mention of the query name outrank the file's real, canonical H1
    signature. The first shaped candidate in stage order is always what the doc itself
    presents as canonical.

    The last stage (first ~40 lines) is scanned strictly -- it must be an actual typed
    signature, not just "identifier(" -- because that stage is prose, not a heading a
    doc author deliberately marked as the signature.
    """
    stages = _gather_stages(lines)
    for stage_idx, stage in enumerate(stages):
        strict_early = stage_idx == len(stages) - 1
        for l in stage:
            for c in sig_candidates(l):
                if strict_early:
                    if c.params.strip() and _looks_typed(c.params):
                        return c
                elif _is_signature_shaped(c):
                    return c
    return None


def _heading_level(line):
    hm = HEADING_RE.match(line)
    return len(hm.group(1)) if hm else None


def _bold_pseudo_heading(line):
    m = BOLD_PSEUDO_HEADING_RE.match(line.strip())
    return m.group(1).strip() if m else None


def section_bounds(lines, heading_idx):
    """Expand to the full run of consecutive same-level headings containing heading_idx
    (family docs sometimes stack several signatures over one shared body), then find
    where the body ends (next heading at the same or a shallower level)."""
    level = _heading_level(lines[heading_idx])
    start = heading_idx
    while start > 0 and _heading_level(lines[start - 1]) == level:
        start -= 1
    end = heading_idx
    while end + 1 < len(lines) and _heading_level(lines[end + 1]) == level:
        end += 1
    body_start = end + 1
    body_end = len(lines)
    for j in range(body_start, len(lines)):
        lvl = _heading_level(lines[j])
        if lvl is not None and lvl <= level:
            body_end = j
            break
    return body_start, body_end


def extract_param_blocks(body_lines, param_tokens):
    """Contiguous bullet-list blocks that either sit under a Parameters/Arguments
    heading or pass the name-token gate (>=1 bullet's leading token is a declared
    parameter name). Returns each qualifying block verbatim, whole -- no per-bullet
    filtering, since a bullet like "the declared 5th argument is dead" doesn't lead
    with a param name but is genuinely parameter info."""
    raw_blocks = []
    current_heading = None
    i, n = 0, len(body_lines)
    while i < n:
        line = body_lines[i]
        hm = HEADING_RE.match(line)
        if hm:
            current_heading = hm.group(2)
            i += 1
            continue
        bh = _bold_pseudo_heading(line)
        if bh:
            current_heading = bh
            i += 1
            continue
        if BULLET_START_RE.match(line):
            heading_for_block = current_heading
            blk = []
            while i < n:
                cur = body_lines[i]
                if cur.strip() == "" or HEADING_RE.match(cur) or _bold_pseudo_heading(cur):
                    break
                blk.append(cur)
                i += 1
            raw_blocks.append((heading_for_block, blk))
            continue
        i += 1

    qualifying = []
    for heading_for_block, blk in raw_blocks:
        leads = set()
        for l in blk:
            m = BULLET_TOKEN_RE.match(l)
            if m:
                leads.add((m.group(1) or m.group(2) or m.group(3)).lower())
        is_param_heading = bool(heading_for_block and PARAM_HEADING_RE.match(heading_for_block.strip()))
        if is_param_heading or (leads & param_tokens):
            qualifying.append(blk)
    return qualifying


# ---------------------------------------------------------------------------
# Section-aware file discovery. Each section may name its primary-callable
# directory differently (acs: functions/, decorate: actions/, zscript: classes/),
# but always uses "families" for the grouped-callable directory -- see
# shared/ARCHETYPES.md's Archetype 1.
# ---------------------------------------------------------------------------

def _callable_dir_names(section_key):
    dirs = S.SECTIONS[section_key]["dirs"]
    primary = [d for d, a in dirs.items() if a == S.CALLABLE and Path(d).name != "families"]
    families = [d for d, a in dirs.items() if a == S.CALLABLE and Path(d).name == "families"]
    return primary, families


def _index_link_paths(section_key):
    """(primary_paths, family_paths) actually linked from one section's INDEX.md."""
    section = S.SECTIONS[section_key]
    index_path = ROOT / section["index"]
    primary_dirs, family_dirs = _callable_dir_names(section_key)
    primary_names = {Path(d).name for d in primary_dirs}
    family_names = {Path(d).name for d in family_dirs}
    if not index_path.is_file() or not (primary_names or family_names):
        return [], []
    text = index_path.read_text()
    all_names = "|".join(re.escape(n) for n in (primary_names | family_names))
    link_re = re.compile(r'\[[^\]]+\]\(((?:' + all_names + r')/[^)]+)\)')
    primary, families = set(), set()
    for m in link_re.finditer(text):
        rel = m.group(1)
        path = (index_path.parent / rel).resolve()
        if not path.is_file():
            continue
        top = rel.split("/", 1)[0]
        (primary if top in primary_names else families).add(path)
    return sorted(primary), sorted(families)


def _section_order(section_key):
    if section_key is not None:
        return [section_key]
    return list(S.SECTIONS.keys())


def _try_function_file(name, section_key):
    for path in _index_link_paths(section_key)[0]:
        if path.stem.lower() == name.lower():
            lines = path.read_text().splitlines()
            sig = find_signature(lines)
            if sig is None:
                return Result(None, path, "file-nosig", [], [], None)
            tokens = param_names(sig.params)
            blocks = extract_param_blocks(lines[1:], tokens)
            note = None if sig.name.lower() == name.lower() else f"real name: {sig.name}"
            return Result(sig, path, "file", blocks, [], note)
    return None


def _func_heading_indices(lines):
    """Indices of headings in a family file that themselves carry a real function
    signature (used to bound where "shared traits" prose ends and per-function
    sections begin)."""
    out = []
    for i, line in enumerate(lines):
        hm = HEADING_RE.match(line)
        if not hm:
            continue
        if any(_is_signature_shaped(c) and c.params.strip() for c in sig_candidates(hm.group(2))):
            out.append(i)
    return out


def _try_family_file(name, section_key):
    for path in _index_link_paths(section_key)[1]:
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines):
            hm = HEADING_RE.match(line)
            if not hm:
                continue
            match = None
            for c in sig_candidates(hm.group(2)):
                if c.name.lower() == name.lower():
                    match = c
                    break
            if match is None:
                continue
            body_start, body_end = section_bounds(lines, i)
            tokens = param_names(match.params)
            own_blocks = extract_param_blocks(lines[body_start:body_end], tokens)

            func_idxs = _func_heading_indices(lines)
            shared_end = min(func_idxs) if func_idxs else i
            shared_blocks = extract_param_blocks(lines[1:shared_end], tokens)

            return Result(match, path, "family", own_blocks, shared_blocks, None)
    return None


def _try_weak_inline(name, section_key):
    """Last-resort tier for a name that only ever appears as a signature-shaped
    mention inside prose (aliases, or a family intro), not in any heading. This scans
    every line of every doc file unrestricted, so it must gate on shape -- without it,
    ordinary prose matches the FULL_SIG_RE name+parens pattern just as well as a real
    call, and gets reported as that name's "signature"."""
    primary, families = _index_link_paths(section_key)
    for path in primary + families:
        lines = path.read_text().splitlines()
        for line in lines:
            for c in sig_candidates(line):
                if c.name.lower() == name.lower() and _is_signature_shaped(c):
                    tokens = param_names(c.params)
                    blocks = extract_param_blocks(lines[1:], tokens)
                    note = f"found only as an inline mention in {path.relative_to(ROOT)}; best-effort"
                    return Result(c, path, "weak", blocks, [], note)
    return None


def _try_tier_c(name, section_key):
    """Only acs/INDEX.md currently has a generated 'Signature-only (tier C)' block --
    see sections.py's ordered_headings. Other sections fall through cleanly."""
    if not S.SECTIONS[section_key].get("ordered_headings"):
        return None
    index_path = ROOT / S.SECTIONS[section_key]["index"]
    if not index_path.is_file():
        return None
    text = index_path.read_text()
    for m in TIER_C_RE.finditer(text):
        if m.group(1).lower() == name.lower():
            params = ""
            pm = re.search(r'\(([^()]*)\)', m.group(2))
            if pm:
                params = pm.group(1)
            sig = Sig(m.group(1), m.group(2), params)
            note = "tier C — signature only. No parameter documentation available."
            return Result(sig, None, "tier-c", [], [], note)
    return None


def _try_inventory_row(name, section_key):
    """Archetype 2 (Table-of-entries): search every inventory/*.md table's first column
    for a case-insensitive match, then check for a matching notes/<name>.md file."""
    dirs = S.SECTIONS[section_key]["dirs"]
    inv_dirs = [d for d, a in dirs.items() if a == S.TABLE_INVENTORY]
    notes_dirs = [d for d, a in dirs.items() if a == S.TABLE_NOTES]
    for inv_dir in inv_dirs:
        inv_path = ROOT / inv_dir
        if not inv_path.is_dir():
            continue
        for table_file in sorted(inv_path.glob("*.md")):
            rows = [l for l in table_file.read_text().splitlines() if l.strip().startswith("|")]
            if len(rows) < 3:
                continue
            header = S.split_row(rows[0])
            for row in rows[2:]:
                cells = S.split_row(row)
                if cells and cells[0].lower() == name.lower():
                    notes_file = None
                    for notes_dir in notes_dirs:
                        candidate = ROOT / notes_dir / f"{name.lower()}.md"
                        if candidate.is_file():
                            notes_file = candidate
                            break
                    return InventoryResult(cells[0], cells, header, table_file, notes_file)
    return None


RESOLVERS = (_try_function_file, _try_family_file, _try_weak_inline, _try_tier_c, _try_inventory_row)


def resolve(name, section_key=None):
    for key in _section_order(section_key):
        for finder in RESOLVERS:
            result = finder(name, key)
            if result is not None:
                return result, key
    return None, None


def _known_names(section_key):
    """Every name this tool would resolve on the first (non-weak) tiers for one section,
    lower-cased name -> preferred display casing. Only computed on a lookup failure."""
    by_lower = {}

    def add(preferred):
        low = preferred.lower()
        current = by_lower.get(low)
        if current is None or (current.islower() and not preferred.islower()):
            by_lower[low] = preferred

    primary, families = _index_link_paths(section_key)
    for path in primary:
        add(path.stem)
        sig = find_signature(path.read_text().splitlines())
        if sig:
            add(sig.name)
    for path in families:
        for line in path.read_text().splitlines():
            hm = HEADING_RE.match(line)
            if not hm:
                continue
            for c in sig_candidates(hm.group(2)):
                add(c.name)
    if S.SECTIONS[section_key].get("ordered_headings"):
        index_path = ROOT / S.SECTIONS[section_key]["index"]
        if index_path.is_file():
            for m in TIER_C_RE.finditer(index_path.read_text()):
                add(m.group(1))
    dirs = S.SECTIONS[section_key]["dirs"]
    for inv_dir in (d for d, a in dirs.items() if a == S.TABLE_INVENTORY):
        inv_path = ROOT / inv_dir
        if not inv_path.is_dir():
            continue
        for table_file in inv_path.glob("*.md"):
            rows = [l for l in table_file.read_text().splitlines() if l.strip().startswith("|")]
            for row in rows[2:]:
                cells = S.split_row(row)
                if cells and cells[0]:
                    add(cells[0])
    return by_lower


def suggest(name, section_key, n=3, cutoff=0.6):
    """Closest known name(s) to an unresolved query, for a "Did you mean" hint. Searches
    every section if none was specified. Matching is case-insensitive but suggestions are
    shown in their documented casing."""
    by_lower = {}
    for key in _section_order(section_key):
        by_lower.update(_known_names(key))
    matches = difflib.get_close_matches(name.lower(), by_lower.keys(), n=n, cutoff=cutoff)
    return [by_lower[m] for m in matches]


TERM_WIDTH = 80
BULLET_LINE_RE = re.compile(r'^(\s*)[-*]\s+(.*)$')


def _parse_bullet_tree(blk_lines):
    """Turn a flat, verbatim source block into a tree of {"text": ..., "children": [...]},
    keyed purely by *relative* indentation -- source docs aren't consistent about exactly
    how many spaces per nesting level, so a deeper indent than the current bullet always
    means "child of the current bullet" regardless of the exact column."""
    roots = []
    stack = []  # [(indent, node)], outermost first
    for raw in blk_lines:
        m = BULLET_LINE_RE.match(raw)
        if m:
            indent = len(m.group(1))
            node = {"text": m.group(2).rstrip(), "children": []}
            while stack and stack[-1][0] >= indent:
                stack.pop()
            (stack[-1][1]["children"] if stack else roots).append(node)
            stack.append((indent, node))
        elif stack and raw.strip():
            stack[-1][1]["text"] += " " + raw.strip()
    return roots


def _render_bullet_tree(nodes, width=TERM_WIDTH, level=0):
    indent = "  " * level
    out = []
    for node in nodes:
        text = re.sub(r'\s+', ' ', node["text"]).strip()
        wrapped = textwrap.wrap(
            text, width=width, initial_indent=f"{indent}- ", subsequent_indent=f"{indent}  "
        )
        out.extend(wrapped or [f"{indent}-"])
        out.extend(_render_bullet_tree(node["children"], width=width, level=level + 1))
    return out


def format_bullet_block(blk, width=TERM_WIDTH):
    return _render_bullet_tree(_parse_bullet_tree(blk), width=width)


def format_output(result, long):
    if isinstance(result, InventoryResult):
        lines = [f"{h}: {v}" for h, v in zip(result.header, result.row)]
        if not long:
            return "; ".join(lines)
        out = list(lines)
        if result.notes_file:
            out.append(f"(see {result.notes_file.relative_to(ROOT)} for prose)")
        else:
            out.append(f"(no notes file yet -- see {result.file.relative_to(ROOT)})")
        return "\n".join(out)

    if result.signature is None:
        loc = result.file.relative_to(ROOT) if result.file else "INDEX.md"
        return f"(no callable signature documented — see {loc})"

    if not long:
        return result.signature.text

    lines = [result.signature.text]
    if result.note:
        lines.append(f"({result.note})")

    if result.kind != "tier-c":
        lines.append("")
        if result.param_blocks:
            lines.append("Parameters:")
            for blk in result.param_blocks:
                lines.extend(format_bullet_block(blk))
        else:
            loc = result.file.relative_to(ROOT) if result.file else "INDEX.md"
            lines.append(f"(no parameter section found — see {loc})")

        if result.shared_blocks:
            lines.append("")
            lines.append(f"Shared across family ({result.file.relative_to(ROOT)}):")
            for blk in result.shared_blocks:
                lines.extend(format_bullet_block(blk))

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        prog="lookup.py",
        description=(
            "Looks up <name> in this doc tree -- a callable's signature, or a table-inventory "
            "row -- across every section by default (add --section to scope to one)."
        ),
    )
    ap.add_argument("name", nargs="?", help="function/flag/property/cvar name, case-insensitive")
    ap.add_argument(
        "--section", choices=sorted(S.SECTIONS.keys()), default=None,
        help="scope the search to one section instead of trying all of them",
    )
    ap.add_argument(
        "--long", action="store_true", help="also print parameter info, not just the signature"
    )
    args = ap.parse_args()

    if args.name is None:
        ap.print_help()
        sys.exit(0)

    result, found_in = resolve(args.name, args.section)
    if result is None:
        print(f"lookup.py: '{args.name}' not found{' in ' + args.section if args.section else ''}", file=sys.stderr)
        suggestions = suggest(args.name, args.section)
        if suggestions:
            print(f"Did you mean: {', '.join(suggestions)}?", file=sys.stderr)
        sys.exit(1)

    print(format_output(result, args.long))
    sys.exit(0)


if __name__ == "__main__":
    main()
