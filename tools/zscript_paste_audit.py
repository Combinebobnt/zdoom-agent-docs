#!/usr/bin/env python3
"""Verbatim-paste detector for UZDoom's ZScript standard library (`wadsrc/static/zscript`).

This closes a real gap `lint_docs.py` cannot: UZDoom/GZDoom source and the ZScript stdlib are
GPL-3.0 with no excerpt escape hatch at all (see shared/AUTHORING.md's "Quoting engine/compiler
source verbatim"), but `lint_docs.py`'s GPL heuristics score 0/294 (`GPL_ONLY_TOKENS`) and 55/294
for a snippet paste (`GPL_ZSCRIPT_RES`) against the real corpus -- there is effectively no signal
for the main case. This tool substitutes a direct line-level comparison against the corpus itself.

Scans every fenced code block in every `.md` file in the tree (not just `zscript`-tagged fences --
a stdlib paste is exactly as much of a violation sitting in an untagged or `text` fence, and step 5
retagged 33 previously-untagged fences inside zscript/ to `text` without auditing them). For each
fence, normalizes each line (strips `//` comments, collapses whitespace) and finds its longest run
of consecutive "significant" lines (len >= 12 after normalizing) that each appear verbatim
somewhere in the corpus. A run below THRESHOLD is noise -- generic boilerplate like
`override void Tick()` / `Super.Tick();` recurs verbatim by coincidence, not by copying.

THRESHOLD=3 is chosen from measured positive/negative controls, not guessed: real docs tree-wide
peak at a 2-line run (measured 2026-08-19, 113 zscript-tagged fences + every text/untagged fence),
while three synthetic pastes drawn from the real corpus -- a verbatim 12-line paste, the same
paste reindented with one identifier renamed, and a declaration-heavy `flagdef` paste -- score 8,
6, and 6 respectively. See --self-test, which pins exactly these three fixtures.

This is a queue-ordering tool, not a replacement for reading the fences -- a wholesale-renamed
paste can still fall under THRESHOLD. See maintainer/TODO.md's "ZScript stdlib-paste audit" entry.

A flag is a heuristic signal that needs a human read, not proof of a violation -- matching
lint_docs.py's own convention for its ENGINE_SOURCE_TOKENS/EXEMPT_RESCAN_TOKENS heuristics (warn,
don't hard-fail). So neither mode's exit code reflects flag count; `--check` exits non-zero only
on structural breakage (corpus not found). One flag is expected and already investigated as of
2026-08-19: `decorate/classes/custominventory.md`'s second `cpp` fence is `ACustomInventory::
TryPickup`, correctly tagged `cpp` with a `Source excerpt:` field citing Zandronum's
`a_pickups.cpp` under LICENSE §3. Its 3-line overlap with UZDoom's `actors/inventory/
stateprovider.zs:522-531` is convergent lineage -- UZDoom's ZScript port of the same original
logic -- not evidence of a paste from UZDoom's GPL source. Left untouched; expect this exact flag
every run, and read any *other* flag that shows up.

Usage:
    python3 tools/zscript_paste_audit.py            list every fence at or above THRESHOLD
    python3 tools/zscript_paste_audit.py --check     same, non-zero only if the corpus can't be found
    python3 tools/zscript_paste_audit.py --self-test run the three positive-control fixtures
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_inventory as G  # noqa: E402  (reused for source_root's sources.local.md resolution)

ROOT = Path(__file__).resolve().parent.parent

CODE_BLOCK_RE = re.compile(r'```([a-zA-Z0-9_+-]*)\n(.*?)```', re.S)
THRESHOLD = 3


def _normalize(line):
    line = re.sub(r'//.*$', '', line)
    return re.sub(r'\s+', ' ', line).strip()


def _significant(line):
    return len(line) >= 12


def build_corpus_index(corpus_root):
    """Return the set of every normalized, significant line across every corpus .zs file."""
    index = set()
    for path in corpus_root.rglob("*.zs"):
        for raw in path.read_text(errors="replace").splitlines():
            line = _normalize(raw)
            if _significant(line):
                index.add(line)
    return index


def longest_run(body, corpus_index):
    """Longest run of consecutive significant lines in `body` that all appear in corpus_index."""
    run = best = 0
    for raw in body.splitlines():
        line = _normalize(raw)
        if not _significant(line):
            continue
        if line in corpus_index:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def iter_fences():
    """Yield (Path, tag, body) for every fenced code block in every doc .md file, skipping the
    maintainer/ tree (local-only, gitignored, not part of the published/licensed surface) and any
    dotdir (.git, .claude -- tooling state, not doc content)."""
    for path in sorted(ROOT.rglob("*.md")):
        parts = path.relative_to(ROOT).parts
        if "maintainer" in parts or any(p.startswith(".") for p in parts):
            continue
        text = path.read_text()
        for tag, body in CODE_BLOCK_RE.findall(text):
            yield path, tag, body


def scan(corpus_index):
    """Return [(Path, tag, run_length)] for every fence at or above THRESHOLD, worst first. Every
    flag is reported -- see the module docstring for the one standing, already-investigated flag
    and why it stays unfiltered rather than suppressed."""
    flagged = []
    for path, tag, body in iter_fences():
        run = longest_run(body, corpus_index)
        if run >= THRESHOLD:
            flagged.append((path, tag, run))
    flagged.sort(key=lambda t: -t[2])
    return flagged


# ---------------------------------------------------------------------------
# Self-test: three positive controls, drawn live from the real corpus so a stale fixture can't
# quietly stop meaning anything. Mirrors lint_docs.py --self-test's "verified live, not just
# present" standard.
# ---------------------------------------------------------------------------

_ZS_KEYWORDS = frozenset((
    "native", "class", "void", "int", "bool", "double", "float", "string", "override", "virtual",
    "static", "const", "super", "self", "true", "false", "default", "states", "property",
    "action", "break", "continue", "return", "readonly", "private", "protected", "deprecated",
    "version", "mixin", "extend", "struct", "array", "sound", "actor", "vector2", "vector3",
    "abstract", "transient", "internal", "meta",
))


def _run_self_test(corpus_root):
    corpus_index = build_corpus_index(corpus_root)
    failures = 0

    # Fixture 1: verbatim paste of a dense line-run from a real stdlib file.
    src_files = sorted(corpus_root.rglob("*.zs"))
    best_window, best_start, best_file = 0, 0, None
    for path in src_files[:40]:  # sampling the whole corpus is unnecessary; any dense file works
        lines = path.read_text(errors="replace").splitlines()
        for i in range(len(lines) - 12):
            window = sum(1 for l in lines[i:i + 12] if _significant(_normalize(l)))
            if window > best_window:
                best_window, best_start, best_file = window, i, path
    if best_file is None:
        print("zscript_paste_audit.py --self-test: corpus produced no usable fixture", file=sys.stderr)
        return 1
    paste = "\n".join(best_file.read_text().splitlines()[best_start:best_start + 12])
    run1 = longest_run(paste, corpus_index)
    if run1 < 5:
        print(f"SELF-TEST FAIL: verbatim paste from {best_file.name} scored {run1}, expected >= 5",
              file=sys.stderr)
        failures += 1

    # Fixture 2: same paste, reindented, with its most common non-keyword identifier renamed --
    # the matcher's actual blind spot; still expected to flag, since most lines in a real paste
    # survive untouched. Keywords are excluded from candidacy: a light edit of a real paste
    # renames a variable, not a `native`/`class`/`void` that recurs by grammar, not by copying.
    ids = [i for i in re.findall(r'\b[a-z][A-Za-z0-9_]{4,}\b', paste) if i not in _ZS_KEYWORDS]
    counts = {}
    for i in ids:
        counts[i] = counts.get(i, 0) + 1
    if counts:
        target = max(counts, key=counts.get)
        mangled = re.sub(r'\b%s\b' % re.escape(target), 'myRenamedThing', paste.replace('\t', '  '))
        run2 = longest_run(mangled, corpus_index)
        if run2 < 5:
            print(f"SELF-TEST FAIL: reindented+renamed paste scored {run2}, expected >= 5",
                  file=sys.stderr)
            failures += 1

    # Fixture 3: declaration-heavy paste (flagdef lines), the TODO's historical near-miss case.
    flagdef_file = next((p for p in corpus_root.rglob("*.zs")
                          if "flagdef" in p.read_text(errors="replace").lower()), None)
    if flagdef_file is not None:
        fd_lines = [l for l in flagdef_file.read_text().splitlines() if "flagdef" in l.lower()][:10]
        run3 = longest_run("\n".join(fd_lines), corpus_index)
        if run3 < 5:
            print(f"SELF-TEST FAIL: flagdef paste from {flagdef_file.name} scored {run3}, "
                  f"expected >= 5", file=sys.stderr)
            failures += 1

    if failures:
        print(f"zscript_paste_audit.py --self-test: {failures} fixture(s) failed", file=sys.stderr)
        return 1
    print("zscript_paste_audit.py --self-test: clean -- 3 fixtures", file=sys.stderr)
    return 0


def main():
    corpus_root = G.source_root("uzdoom") / "wadsrc" / "static" / "zscript"
    if not corpus_root.is_dir():
        print(f"zscript_paste_audit.py: {corpus_root} not found -- check sources.local.md's "
              f"'uzdoom' entry", file=sys.stderr)
        sys.exit(1)

    if "--self-test" in sys.argv[1:]:
        sys.exit(_run_self_test(corpus_root))

    corpus_index = build_corpus_index(corpus_root)
    flagged = scan(corpus_index)
    for path, tag, run in flagged:
        print(f"FLAG: {path.relative_to(ROOT)} (```{tag or '(untagged)'}) -- "
              f"{run}-line verbatim run against UZDoom ZScript stdlib", file=sys.stderr)
    if not flagged:
        print(f"zscript_paste_audit.py: clean -- no fence >= {THRESHOLD}-line verbatim run",
              file=sys.stderr)
    # Exit code reflects whether the scan ran, not flag count -- see module docstring for why a
    # flag is a heuristic signal for a human read, not a pass/fail verdict.
    sys.exit(0)


if __name__ == "__main__":
    main()
