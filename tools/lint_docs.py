#!/usr/bin/env python3
"""Mechanical lint for the zdoom-agent-docs tree, across every section in sections.py.

Checks, per section with an existing INDEX.md:
  - every INDEX.md link into that section's own doc dirs resolves to a real file
  - every file in a CALLABLE/TABLE_NOTES/CONCEPT dir is linked from that section's INDEX.md
  - every such file has a Tier:, Provenance:, and Engine: field (see STRICT_HEADER_POSITION
    below for whether this also checks the block is positioned directly under the H1)
  - every TABLE_INVENTORY file carries a **Generated:** marker and every row's Tier column
    (if a Tier column exists) holds a valid tier letter
  - any **Source excerpt:** field cites the right LICENSE section (Zandronum -> SS3, zt-bcc/bcc
    -> SS4) and mentions LICENSE
  - no file quotes GPL-3.0 (UZDoom/GZDoom engine or ZScript stdlib) source verbatim -- this is a
    HARD error, unlike the softer heuristic warning for an uncredited Zandronum-style excerpt,
    because there is no license section that would make a GPL-3.0 excerpt acceptable here (see
    shared/AUTHORING.md's "Quoting engine/compiler source verbatim")
  - acs/INDEX.md's Families/Prose/Signature-only subsections stay alphabetically ordered (the one
    section with an established convention for this -- see sections.py's "ordered_headings")

Run after hand-editing any doc file, or after regenerating an inventory.

Usage:
    python3 tools/lint_docs.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections as S  # noqa: E402

ROOT = S.ROOT

# Flip this to True once every HEADER_BLOCK_ARCHETYPES file has its Tier:/Provenance:/Engine:
# block normalized to sit directly under the H1 (see the header-normalization step in the
# zdoom-agent-docs expansion plan). Until then this stays a lenient substring check, matching
# the tool's original acs-docs-only behavior.
STRICT_HEADER_POSITION = False

LINK_RE_TEMPLATE = r'\[[^\]]+\]\((?:{dirs})/[^)]+\)'
SECTION_ITEM_RE_TEMPLATE = r'^- \[([^\]]+)\]\((?:{dirs})/[^)]+\)'
HEADING_RE = re.compile(r'^#{2,3} ', re.M)
CODE_BLOCK_RE = re.compile(r'```[a-zA-Z]*\n(.*?)```', re.S)
SOURCE_EXCERPT_RE = re.compile(r'\*\*Source excerpt:\*\*(.*)')
GENERATED_RE = re.compile(r'\*\*Generated:\*\*')
H1_RE = re.compile(r'^# .+$', re.M)

# Heuristic only: tokens that show up in genuine Zandronum/zt-bcc/UZDoom/GZDoom C++ or ZScript
# stdlib source but essentially never in a hand-written ACS/BCS/DECORATE/ZScript usage example.
# False positives are expected (e.g. a lone "->" in prose) -- for Zandronum/zt-bcc this is why the
# check below is a warning, not a lint failure. For GPL-3.0 sources there is no legitimate
# verbatim use at all (see shared/AUTHORING.md), so the same token hit is a hard error there.
ENGINE_SOURCE_TOKENS = (
    "FUNC(", "case ACSF_", "case PCD_", "AActor", "NETWORK_", "SERVERCOMMANDS_",
    "ULONG ", "TArray", "FBehavior::", "GAMEMODE_", "static_cast<",
)
# Tokens specific enough to ZScript/GZDoom-family VM internals that they don't show up in
# hand-written ZScript usage examples or in Zandronum's older DECORATE-only codebase.
GPL_ONLY_TOKENS = (
    "DEFINE_FIELD(", "IMPLEMENT_CLASS(", "DECLARE_CLASS(", "PARAM_PROLOGUE",
    "ACTION_RETURN_", "PClass::FindActor(", "VMValue", "PFunction::",
)


def extract_section(text, heading):
    """Return the text between `heading` and the next level-2/3 heading (or end of file).
    None if `heading` isn't present at all."""
    idx = text.find(heading)
    if idx == -1:
        return None
    start = idx + len(heading)
    m = HEADING_RE.search(text, start)
    return text[start: m.start() if m else len(text)]


def check_alphabetical_order(section_key, index_text, ok_list):
    ordered = S.SECTIONS[section_key].get("ordered_headings")
    if not ordered:
        return
    for label, heading in ordered.items():
        section = extract_section(index_text, heading)
        if section is None:
            print(f"LINT: {section_key}/INDEX.md is missing the {heading!r} heading", file=sys.stderr)
            ok_list.append(False)
            continue
        items = re.findall(r'^- \[([^\]]+)\]\([^)]+\)', section, re.M)
        prev_key, prev_item = None, None
        for item in items:
            key = item.lower()
            if prev_key is not None and key < prev_key:
                print(
                    f"LINT: {section_key}/INDEX.md's {label!r} section is out of alphabetical "
                    f"order: {prev_item!r} appears before {item!r}",
                    file=sys.stderr,
                )
                ok_list.append(False)
            prev_key, prev_item = key, item


def check_header_block(path, text, ok_list):
    """CALLABLE / TABLE_NOTES / CONCEPT files: Tier:/Provenance:/Engine: must be present, and
    (once STRICT_HEADER_POSITION is on) positioned as a block directly under the H1."""
    rel = path.relative_to(ROOT)
    missing = []
    if "Tier:" not in text:
        missing.append("Tier:")
    if "Provenance:" not in text and "**Provenance" not in text:
        missing.append("Provenance:")
    if "Engine:" not in text:
        missing.append("Engine:")
    for field in missing:
        print(f"LINT: {rel} has no {field} line", file=sys.stderr)
        ok_list.append(False)
    if missing or not STRICT_HEADER_POSITION:
        return

    h1 = H1_RE.search(text)
    if not h1:
        print(f"LINT: {rel} has no H1 heading to anchor its header block to", file=sys.stderr)
        ok_list.append(False)
        return
    # The header block is the first non-blank run of lines after the H1; every bold-field line
    # in it must appear before the first line of real prose.
    after = text[h1.end():].lstrip("\n")
    lines = after.split("\n")
    block_end = 0
    for i, line in enumerate(lines):
        if line.strip() == "":
            continue
        if re.match(r'^\*\*(Tier|Provenance|Engine|Bucket|Source excerpt|Generated):\*\*', line):
            block_end = i + 1
            continue
        break
    block_text = "\n".join(lines[:block_end])
    for field in ("Tier:", "Provenance:", "Engine:"):
        if field not in block_text and f"**{field}" not in block_text:
            print(
                f"LINT: {rel} has a {field} field but it isn't in the header block directly "
                "under the H1 (see shared/ARCHETYPES.md's header-block format)",
                file=sys.stderr,
            )
            ok_list.append(False)


def check_source_excerpt_and_gpl(path, text, ok_list):
    rel = path.relative_to(ROOT)
    excerpt_match = SOURCE_EXCERPT_RE.search(text)
    blocks = CODE_BLOCK_RE.findall(text)
    joined = "\n".join(blocks)

    gpl_named = excerpt_match and re.search(r'\bUZDoom\b|\bGZDoom\b', excerpt_match.group(1))
    gpl_token_hit = any(tok in joined for tok in GPL_ONLY_TOKENS)
    if gpl_named or gpl_token_hit:
        print(
            f"LINT: {rel} appears to quote GPL-3.0 (UZDoom/GZDoom/ZScript stdlib) source "
            "verbatim -- not allowed under any circumstance, paraphrase instead (see "
            "shared/AUTHORING.md's \"Quoting engine/compiler source verbatim\")",
            file=sys.stderr,
        )
        ok_list.append(False)
        return

    if excerpt_match:
        claim = excerpt_match.group(1)
        valid_zandronum = "Zandronum" in claim and "§3" in claim
        valid_ztbcc = ("zt-bcc" in claim or "bcc" in claim) and "§4" in claim
        if not (valid_zandronum or valid_ztbcc):
            print(
                f"LINT: {rel}'s **Source excerpt:** field doesn't clearly cite LICENSE §3 "
                "(Zandronum) or §4 (zt-bcc/bcc) -- see shared/AUTHORING.md's \"Quoting "
                "engine/compiler source verbatim\"",
                file=sys.stderr,
            )
            ok_list.append(False)
        if "LICENSE" not in claim:
            print(f"LINT: {rel}'s **Source excerpt:** field doesn't link back to LICENSE", file=sys.stderr)
            ok_list.append(False)
    elif any(tok in joined for tok in ENGINE_SOURCE_TOKENS):
        print(
            f"LINT-WARN: {rel} has a fenced code block that looks like verbatim engine source "
            "but no **Source excerpt:** field -- heuristic, may be a false positive (a usage "
            "example, a comment, a signature). Check by hand before adding one.",
            file=sys.stderr,
        )


VALID_TIERS = {"A", "B", "C"}


def check_inventory_table(path, text, ok_list):
    rel = path.relative_to(ROOT)
    if not GENERATED_RE.search(text):
        print(f"LINT: {rel} is a table-inventory file but has no **Generated:** marker", file=sys.stderr)
        ok_list.append(False)
        return
    rows = [l for l in text.splitlines() if l.strip().startswith("|")]
    if not rows:
        return
    header_cells = S.split_row(rows[0])
    tier_idx = next((i for i, c in enumerate(header_cells) if c.lower() == "tier"), None)
    if tier_idx is None:
        return
    for row in rows[2:]:  # skip header + separator row
        cells = S.split_row(row)
        if len(cells) <= tier_idx:
            continue
        tier_val = cells[tier_idx]
        if tier_val and tier_val not in VALID_TIERS:
            print(f"LINT: {rel} has an invalid Tier value {tier_val!r} (expected A/B/C)", file=sys.stderr)
            ok_list.append(False)


def lint_section(section_key, section, ok_list, total_files):
    index_path = ROOT / section["index"]
    dirs = section["dirs"]
    dir_names = "|".join(re.escape(Path(d).name) for d in dirs)
    linked = set()

    if index_path.is_file():
        index_text = index_path.read_text()
        check_alphabetical_order(section_key, index_text, ok_list)
        link_re = re.compile(LINK_RE_TEMPLATE.format(dirs=dir_names))
        for m in re.finditer(r'\(((?:' + dir_names + r')/[^)]+)\)', index_text):
            rel = m.group(1)
            path = index_path.parent / rel
            linked.add(path.resolve())
            if not path.is_file():
                print(f"LINT: {section['index']} links to missing file: {rel}", file=sys.stderr)
                ok_list.append(False)
    else:
        index_text = None

    for dir_rel, archetype in dirs.items():
        dir_path = ROOT / dir_rel
        if not dir_path.is_dir():
            continue
        for path in sorted(dir_path.glob("*.md")):
            total_files[0] += 1
            if index_text is not None and path.resolve() not in linked:
                print(f"LINT: {path.relative_to(ROOT)} exists but isn't linked from {section['index']}", file=sys.stderr)
                ok_list.append(False)
            text = path.read_text()
            if archetype in S.HEADER_BLOCK_ARCHETYPES:
                check_header_block(path, text, ok_list)
                check_source_excerpt_and_gpl(path, text, ok_list)
            elif archetype == S.TABLE_INVENTORY:
                check_inventory_table(path, text, ok_list)
                check_source_excerpt_and_gpl(path, text, ok_list)


def lint():
    ok_list = []
    total_files = [0]
    for section_key, section in S.SECTIONS.items():
        lint_section(section_key, section, ok_list, total_files)

    # shared/concepts/ isn't owned by any one section, so it's linked from the root INDEX.md
    # instead of a section index -- check its files exist and pass the header-block checks, but
    # don't require a specific "linked from" file (root INDEX.md just points at the directory).
    shared_dir = ROOT / S.SHARED_CONCEPTS_DIR
    if shared_dir.is_dir():
        for path in sorted(shared_dir.glob("*.md")):
            total_files[0] += 1
            text = path.read_text()
            check_header_block(path, text, ok_list)
            check_source_excerpt_and_gpl(path, text, ok_list)

    ok = not ok_list
    if ok:
        print(f"LINT: clean -- {total_files[0]} doc files across {len(S.SECTIONS)} sections, all linked, all tiered/provenanced.", file=sys.stderr)
    return ok


def main():
    sys.exit(0 if lint() else 1)


if __name__ == "__main__":
    main()
