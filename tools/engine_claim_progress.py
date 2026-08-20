#!/usr/bin/env python3
"""The UZDoom-retarget marking pass (Phase 3)'s honest coverage report.

Answers, per `maintainer/plans/2026-08-08_uzdoom_retarget_plan.md`'s "The schema change" table
plus the deferred-set refinement in `maintainer/plans/2026-08-14_uzdoom_retarget_phase3.md`:

    not yet migrated       still carries an anchored **Engine:** field, not in the deferred set
    deferred (on purpose)  anchored **Engine:**, but named in the deferred-set file -- Phase 3
                            deliberately leaves these on legacy Engine: because no real date/SHA
                            exists to write a Verified against: entry from (see the phase-3 plan's
                            "Decisions taken"), so Phase 5 re-verifies them instead of guessing
    marked, unverified     Applies to: has UZDoom=yes, Verified against: lacks a UZDoom entry
    (of which) unverified  a sub-tag of the above: Verified against: is the literal `none` --
    anywhere               no prior claim for ANY engine, so Phase 5's normal "compare against
                            the existing Zandronum-verified claim" procedure doesn't apply; these
                            need the inverted first-verification branch instead (Phase 5's C0
                            cohort). Additive -- every file here is also marked_unverified.
    fully re-verified      Verified against: names UZDoom
    Zandronum-only         Applies to: has UZDoom=no
    UZDoom=unknown         Applies to: has UZDoom=unknown -- lint-legal, but 3.5's rule permits
                            this only for genuinely cross-engine concept pages, never as an
                            "I didn't check" escape, and every use must land in the deferred set
                            too so Phase 5 picks it up
    inline (unanchored)    the literal text "**Engine:**" appears somewhere in the file but not
                            at the start of a line -- never a real field, always a bug (an
                            un-de-worded generated note, or a copy-pasted example) unless the file
                            is in EXCLUDED

This does NOT reimplement the engine-claim grammar: it imports lint_docs's own ENGINE_START_RE /
APPLIES_TO_START_RE / VERIFIED_AGAINST_START_RE / extract_all_fields and check_engine_claim, so
this report can never silently disagree with what the linter actually enforces.

Caution: the shell's `grep` on this machine is a ugrep wrapper that honors .gitignore, so a raw
`grep -r` sweep silently skips the gitignored maintainer/ directory -- this script walks the
filesystem itself (Path.rglob), never shells out to grep, so maintainer/ is seen and can be
correctly EXCLUDED on purpose rather than invisibly absent.

Usage:
    python3 tools/engine_claim_progress.py             human-readable summary
    python3 tools/engine_claim_progress.py --list CAT  list files in one category (see CATEGORIES)
    python3 tools/engine_claim_progress.py --check     nonzero exit on any inline **Engine:**
                                                        outside EXCLUDED, or an UZDoom=unknown file
                                                        outside the deferred set
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_docs as L  # noqa: E402
import sections as S  # noqa: E402

ROOT = S.ROOT

# Files that legitimately carry the literal text "**Engine:**" (or, in the schema examples,
# "**Applies to:**") forever -- schema documentation and maintainer-only planning docs, never a
# migration target. Kept as an explicit list, not a "starts with maintainer/" heuristic alone, so
# a new schema-example file added elsewhere has to be added here deliberately.
EXCLUDED = {
    ROOT / "shared" / "AUTHORING.md",
    ROOT / "shared" / "ARCHETYPES.md",
}
EXCLUDED_PREFIXES = (ROOT / "maintainer",)

# The deferred set: doc files Phase 3 deliberately leaves on legacy **Engine:** because no real
# date (Zandronum side) or SHA (UZDoom side) exists to stamp truthfully. Maintained by
# maintainer/tools/stamp_applies_to.py (step 3.2/3.3) as a flat list of repo-relative paths, one
# per line, blank lines and #-comments ignored. Absent before step 3.2 runs -- baseline reports
# with an empty deferred set, i.e. everything still on Engine: reads as "not yet migrated".
DEFERRED_SET_FILE = ROOT / "maintainer" / "deferred_set.txt"


def _is_excluded(path):
    if path in EXCLUDED:
        return True
    return any(path == p or p in path.parents for p in EXCLUDED_PREFIXES)


def load_deferred_set():
    if not DEFERRED_SET_FILE.is_file():
        return set()
    out = set()
    for line in DEFERRED_SET_FILE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add((ROOT / line).resolve())
    return out


def iter_all_md_files():
    """Every .md file in the tree, walked directly (never via a shelled-out grep -- see the
    module docstring). Includes maintainer/ so it can be positively excluded, not silently
    missed. Skips .git and .claude -- the latter is a Claude Code project-local scaffold
    directory, not repo content, and its contents may be sandbox-unreadable placeholder files
    that raise PermissionError on open() rather than silently vanishing."""
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts or ".claude" in path.parts:
            continue
        yield path


def classify(path, deferred_set):
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)

    inline_total = text.count("**Engine:**")
    engine_fields = L.extract_all_fields(text, L.ENGINE_START_RE)
    applies_fields = L.extract_all_fields(text, L.APPLIES_TO_START_RE)
    verified_fields = L.extract_all_fields(text, L.VERIFIED_AGAINST_START_RE)
    inline_unanchored = inline_total - len(engine_fields)

    applies_map = {}
    if applies_fields:
        applies_map, _problems = L.parse_applies_to(L._field_body(applies_fields[0]))
    verified_entries = []
    if verified_fields:
        verified_entries, _problems = L.parse_verified_against(L._field_body(verified_fields[0]))
    verified_engines = {e for e, *_r in verified_entries}

    excluded = _is_excluded(path)
    is_deferred = path.resolve() in deferred_set

    cats = []
    if excluded:
        cats.append("excluded")
    else:
        if engine_fields:
            cats.append("deferred" if is_deferred else "not_yet_migrated")
        elif applies_fields:
            uzd = applies_map.get("UZDoom")
            if uzd == "no":
                cats.append("zandronum_only")
            elif uzd == "unknown":
                cats.append("uzdoom_unknown")
                if not is_deferred:
                    cats.append("uzdoom_unknown_unaccounted")
            elif "UZDoom" in verified_engines:
                cats.append("fully_reverified")
            elif uzd == "yes":
                cats.append("marked_unverified")
                if not verified_entries:
                    # Phase 5 gap found 2026-08-15: marked_unverified also catches files whose
                    # Verified against: names Zandronum (a real prior claim, step 4's normal
                    # re-verify path applies) -- this refines it to files with *no* prior claim
                    # of any engine (**Verified against:** none), which need step 4's inverted
                    # first-verification branch instead. Additive, not a replacement: every
                    # unverified_anywhere file is also marked_unverified, so existing counts and
                    # any script keyed on "marked_unverified" don't change.
                    cats.append("unverified_anywhere")
            elif "N/A" in applies_map:
                # A compiler-only/engine-independent entry (Applies to: N/A - <reason>) has no
                # UZDoom= key at all, so none of the branches above fire for it -- without this,
                # every N/A file (11 as of the phase-3 marking pass) silently vanishes from every
                # category below, undercounting the "stamped" total against build_file_plan()'s.
                cats.append("na")
        if inline_unanchored > 0:
            cats.append("inline_unanchored")
    return rel, cats, inline_unanchored


CATEGORY_LABELS = {
    "not_yet_migrated": "not yet migrated (anchored Engine:, not deferred)",
    "deferred": "deferred on purpose (anchored Engine:, in the deferred set)",
    "marked_unverified": "marked, UZDoom unverified (Applies to: UZDoom=yes, no Verified-against entry)",
    "unverified_anywhere": "  of which, no prior claim at all (Verified against: none -- Phase 5's C0 cohort)",
    "fully_reverified": "fully re-verified (Verified against: names UZDoom)",
    "zandronum_only": "Zandronum-only (Applies to: UZDoom=no)",
    "na": "engine-independent (Applies to: N/A - compiler-only or similar)",
    "uzdoom_unknown": "UZDoom=unknown",
    "uzdoom_unknown_unaccounted": "UZDoom=unknown but NOT in the deferred set (3.5 violation)",
    "inline_unanchored": "inline **Engine:** outside a real field, outside EXCLUDED",
    "excluded": "excluded (schema examples / maintainer-only docs)",
}
CATEGORY_ORDER = [
    "not_yet_migrated", "deferred", "marked_unverified", "unverified_anywhere", "fully_reverified",
    "zandronum_only", "na", "uzdoom_unknown", "uzdoom_unknown_unaccounted", "inline_unanchored",
    "excluded",
]


def main():
    args = sys.argv[1:]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    list_cat = None
    if "--list" in args:
        i = args.index("--list")
        if i + 1 >= len(args):
            print("--list requires a category (see the summary output for names)", file=sys.stderr)
            return 2
        list_cat = args[i + 1]
        if list_cat not in CATEGORY_LABELS:
            print(f"unknown category {list_cat!r}. Valid: {', '.join(CATEGORY_ORDER)}", file=sys.stderr)
            return 2

    deferred_set = load_deferred_set()
    by_cat = {c: [] for c in CATEGORY_ORDER}
    for path in iter_all_md_files():
        rel, cats, _inline = classify(path, deferred_set)
        for c in cats:
            by_cat[c].append(rel)

    if list_cat is not None:
        for rel in by_cat[list_cat]:
            print(rel)
        return 0

    total_files = sum(1 for _ in iter_all_md_files())
    print(f"engine_claim_progress: {total_files} .md files scanned")
    if not DEFERRED_SET_FILE.is_file():
        print(f"  (no deferred-set file at {DEFERRED_SET_FILE.relative_to(ROOT)} yet -- "
              "everything still on Engine: reads as 'not yet migrated')")
    for c in CATEGORY_ORDER:
        print(f"  {len(by_cat[c]):4d}  {CATEGORY_LABELS[c]}")

    ok = True
    if by_cat["inline_unanchored"]:
        ok = False
        print("\nFAIL: inline **Engine:** found outside EXCLUDED:", file=sys.stderr)
        for rel in by_cat["inline_unanchored"]:
            print(f"  {rel}", file=sys.stderr)
    if by_cat["uzdoom_unknown_unaccounted"]:
        ok = False
        print("\nFAIL: UZDoom=unknown files not in the deferred set (violates the 3.5 rule):",
              file=sys.stderr)
        for rel in by_cat["uzdoom_unknown_unaccounted"]:
            print(f"  {rel}", file=sys.stderr)

    if check:
        if ok:
            print("\nengine_claim_progress --check: clean")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
