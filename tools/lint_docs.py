#!/usr/bin/env python3
"""Mechanical lint for the zdoom-agent-docs tree, across every section in sections.py.

Checks, per section with an existing INDEX.md:
  - every INDEX.md link into that section's own doc dirs resolves to a real file
  - every file in a CALLABLE/TABLE_NOTES/CONCEPT dir is linked from that section's INDEX.md
  - every such file has a Tier:, Provenance:, and Applies to:/Verified against: pair (see
    STRICT_HEADER_POSITION below for whether this also checks the block is positioned directly
    under the H1)
  - every TABLE_INVENTORY file carries a **Generated:** marker and every row's Tier column
    (if a Tier column exists) holds a valid tier letter
  - any **Source excerpt:** field cites the right LICENSE section (Zandronum -> SS3, zt-bcc/bcc
    -> SS4) and mentions LICENSE
  - no file quotes GPL-3.0 (UZDoom/GZDoom engine or ZScript stdlib) source verbatim -- this is a
    HARD error, unlike the softer heuristic warning for an uncredited Zandronum-style excerpt,
    because there is no license section that would make a GPL-3.0 excerpt acceptable here (see
    shared/AUTHORING.md's "Quoting engine/compiler source verbatim")
  - no file cites both wikis across its Provenance: fields -- also a HARD error, because GFDL 1.2
    and CC BY-NC-SA 4.0 can't both be satisfied by one file, and every wiki-citing Provenance:
    field records an oldid= so it resolves to the revision it was built from (see
    shared/AUTHORING.md's "Wiki provenance"). Both look at EVERY Provenance: field in the file,
    not just the header block's -- a families/*.md carries one per member function.
  - acs/INDEX.md's Families/Prose/Signature-only subsections stay alphabetically ordered (the one
    section with an established convention for this -- see sections.py's "ordered_headings")

Run after hand-editing any doc file, or after regenerating an inventory.

Usage:
    python3 tools/lint_docs.py
"""
import contextlib
import io
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections as S  # noqa: E402

ROOT = S.ROOT

STRICT_HEADER_POSITION = True

LINK_RE_TEMPLATE = r'\[[^\]]+\]\((?:{dirs})/[^)]+\)'
SECTION_ITEM_RE_TEMPLATE = r'^- \[([^\]]+)\]\((?:{dirs})/[^)]+\)'
HEADING_RE = re.compile(r'^#{2,3} ', re.M)
# Captures the language tag as well as the body, because the C++ heuristic below is scoped by tag
# (see EXAMPLE_FENCE_TAGS). Digits/+/- are admitted so a `c++`-style tag is captured as itself
# rather than as a bare fence with `++` leading its body.
CODE_BLOCK_RE = re.compile(r'```([a-zA-Z0-9_+-]*)\n(.*?)```', re.S)
SOURCE_EXCERPT_START_RE = re.compile(r'^(?:\*\*)?Source excerpt:')
PROVENANCE_START_RE = re.compile(r'^(?:\*\*)?Provenance:')
# Either form a provenance line cites a wiki by: the prose name, or a bare URL. Matching only the
# prose name would miss a URL-only citation, which is the format most likely to show up next.
ZDOOM_WIKI_TOKENS = ("ZDoom Wiki", "zdoom.org/wiki")
ZANDRONUM_WIKI_TOKENS = ("Zandronum Wiki", "wiki.zandronum.com")
# The resolvable MediaWiki URL form every wiki-citing Provenance: field must carry, with a host
# matching the wiki it cites -- a page title or a locally-saved filename alone isn't reachable by
# anyone who clones this repo. `title=` is deliberately not required to be non-empty here; the
# per-host substring check below is what actually enforces "the right wiki, resolvably."
MEDIAWIKI_URL_MARKER = "/w/index.php?title="
ZDOOM_WIKI_HOST = "https://zdoom.org" + MEDIAWIKI_URL_MARKER
ZANDRONUM_WIKI_HOST = "https://wiki.zandronum.com" + MEDIAWIKI_URL_MARKER
WIKI_LICENSE_START_RE = re.compile(r'^(?:\*\*)?Wiki license:')
# The one registry of header-block field names. Both regexes below derive from it, and so does
# check_header_block's notion of where a block ends -- the list used to exist twice, and the two
# copies broke differently when they drifted: an unregistered field before Engine: truncated the
# block (so every file carrying it was reported as "Engine: isn't in the header block"), while one
# after Source excerpt: got absorbed as a continuation line, where the GPL check could then match
# "UZDoom" in the absorbed text and hard-error every legitimate Zandronum-excerpt file. Register a
# new field here and nowhere else.
HEADER_FIELDS = (
    "Tier", "Provenance", "Engine", "Applies to", "Verified against", "Compiler", "Bucket",
    "Source excerpt", "Generated", "Wiki license",
)
_FIELD_ALT = "|".join(HEADER_FIELDS)
# Field starts, in either the bold form the archetypes specify or the bare form some older files
# use; and the bold-only form, which is what anchors a header block under the H1.
HEADER_FIELD_RE = re.compile(rf'^(?:\*\*)?({_FIELD_ALT}):')
BOLD_HEADER_FIELD_RE = re.compile(rf'^\*\*({_FIELD_ALT}):\*\*')
GENERATED_RE = re.compile(r'\*\*Generated:\*\*')
H1_RE = re.compile(r'^# .+$', re.M)

# The engine claim, mid-migration. `Engine:` is the legacy single free-form field; it cannot say
# "exists on both engines, but only Zandronum's behavior was ever checked", which is the honest
# state of most of this tree. Its replacement splits that into two orthogonal fields. Both forms
# are legal until the marking pass retires the legacy one -- see shared/AUTHORING.md's "Engine
# scope" and maintainer/plans/2026-08-08_uzdoom_retarget_plan.md.
ENGINE_START_RE = re.compile(r'^(?:\*\*)?Engine:')
APPLIES_TO_START_RE = re.compile(r'^(?:\*\*)?Applies to:')
VERIFIED_AGAINST_START_RE = re.compile(r'^(?:\*\*)?Verified against:')
TIER_START_RE = re.compile(r'^(?:\*\*)?Tier:')
# The co-occurrence rule (Phase 3 step 3.7): `Applies to: UZDoom=no` must be backed by a real
# divergence writeup, not just the claim. Either heading form is accepted -- `## Engine-family
# divergence` for a file where the whole page is the divergence, `## Zandronum-specific: ...`
# (with or without a trailing description) for one where it's a subsection of a larger page.
DIVERGENCE_HEADING_RE = re.compile(r'^## (?:Engine-family divergence|Zandronum-specific)\b', re.M)
# Phase 4 step 4.5: the canonical H2 divergence-heading vocabulary is now fixed (see
# shared/AUTHORING.md's "Engine scope") -- DIVERGENCE_HEADING_RE's two forms above, plus
# `## Wiki/engine divergence[: <suffix>]` for the distinct wiki-vs-engine axis.
#
# Deliberately a denylist of specific retired phrasings, not a general "flag anything divergence-
# shaped" allowlist -- Phase 5.4 evaluated and rejected that approach on evidence (2026-08-17), not
# just deferred it. A tree-wide sweep for every H2 heading containing "divergence" found headings
# that are genuinely the same short-label shape but opposite verdicts on manual read of the section
# body: `## Fork divergence summary` was a real retired-vocabulary heading (its body is a rollup of
# engine-vs-engine property/flag differences -- canonicalized to `## Engine-family divergence: ...`
# during that sweep), while `## Known divergences and implementation notes` is an ordinary
# wrap-up-section title that happens to use the word "divergences" in prose and was correctly left
# alone. No heading-text-only regex can separate that pair -- doing so needed reading the section
# body, which a lint pass over header text alone cannot do. So this list only ever grows by adding
# a phrasing a real sweep found and fixed, the same way the original three entries did; it is not,
# and cannot safely become, a general "any non-canonical divergence heading" catch.
#
# The 2026-08-17 sweep added: `Wiki divergence(s)` (bare or with a trailing phrase/suffix),
# `Fork/wiki divergence(s)`, `Fork divergence` (as a short-label prefix, so `Fork divergence
# summary` is caught but `The big fork divergence: ...` is not -- that one was read and judged a
# genuine section title, not an attempted canonical marker, so it's deliberately not in this list),
# `Divergence from`, `Key divergence`, `Engine divergence` (the space after `Engine` matters -- it
# must not swallow the canonical `Engine-family divergence`, confirmed by a self-test fixture),
# `ZDoom/UZDoom/GZDoom family divergence`, `Behavior and fork divergence`, and `Zandronum additions
# and divergences`.
DEPRECATED_DIVERGENCE_HEADING_RE = re.compile(
    r'^## (Engine availability|Engine scope|Wiki/fork divergences?|Wiki divergences?|'
    r'Fork/wiki divergences?|Fork divergence|Divergence from|Key divergence|Engine divergence|'
    r'ZDoom/UZDoom/GZDoom family divergence|Behavior and fork divergence|'
    r'Zandronum additions and divergences)\b', re.M)

ENGINE_VOCAB = ("UZDoom", "GZDoom", "Zandronum", "zt-bcc", "acc")
# Deliberately no "partial": "exists on both, behaves differently" is `yes` plus an
# `## Engine-family divergence` section. An undefined enum value in a lint-enforced grammar is
# how thirty files end up meaning three different things.
APPLIES_VALUES = ("yes", "no", "unknown")
REQUIRED_APPLIES_KEYS = ("UZDoom", "Zandronum")
_ENGINE_ALT = "|".join(re.escape(e) for e in ENGINE_VOCAB)
# Versions in this tree are too varied to enumerate (5.0.0-pre, 4.15pre, 3.2.1, 0.10.0-alpha-8),
# so the version is one non-space token; SHAs run 7-40 hex chars.
VERIFIED_ENTRY_RE = re.compile(
    rf'^(?P<engine>{_ENGINE_ALT})\s+(?P<version>\S+)\s+@(?P<sha>[0-9a-f]{{7,40}})'
    rf'\s+\((?P<date>\d{{4}}-\d{{2}}-\d{{2}})\)$'
)
APPLIES_PAIR_RE = re.compile(rf'^(?P<engine>{_ENGINE_ALT})=(?P<value>[A-Za-z/]+)$')
NA_RE = re.compile(r'^N/A\b')
EM_DASH = "—"
# Engines whose source is GPL-3.0 and may therefore never be quoted verbatim here.
GPL_ENGINE_RE = re.compile(r'\bUZDoom\b|\bGZDoom\b')
# Sources this tree may quote verbatim, each with the LICENSE section that permits it.
PERMITTED_EXCERPT_SOURCES = (("Zandronum", "§3"), ("zt-bcc", "§4"), ("bcc", "§4"))

# Heuristic only: tokens that show up in genuine Zandronum/zt-bcc/UZDoom/GZDoom C++ or ZScript
# stdlib source but essentially never in a hand-written ACS/BCS/DECORATE/ZScript usage example.
# False positives are expected (e.g. a lone "->" in prose) -- for Zandronum/zt-bcc this is why the
# check below is a warning, not a lint failure. For GPL-3.0 sources there is no legitimate
# verbatim use at all (see shared/AUTHORING.md), so the same token hit is a hard error there.
ENGINE_SOURCE_TOKENS = (
    "FUNC(", "case ACSF_", "case PCD_", "AActor", "NETWORK_", "SERVERCOMMANDS_",
    "ULONG ", "TArray", "FBehavior::", "GAMEMODE_", "static_cast<",
    # Added 2026-08-14. The original list caught 0 field-less files while a hand sweep found 8
    # quoting Zandronum source with no field -- each miss needing a different token, because the
    # list was assembled from ACS-VM code and these files quote actor/console/fixed-point code.
    "RUNTIME_CLASS", "inline ", "Printf", "SDWORD", "const char", "sizeof",
)
# The subset of ENGINE_SOURCE_TOKENS specific enough to survive being pointed at an
# EXAMPLE_FENCE_TAGS fence. Step 4 (2026-08-14) scoped the full heuristic away from those tags
# because `Printf`, `->` and `::` fire constantly on legitimate ZScript/DECORATE examples
# (`Console.Printf`, `Goto Super::Missile`) -- 9 false positives. These are the tokens that cannot
# appear in hand-written ACS/DECORATE/ZScript at all. Deliberately excludes `Printf`, `inline `,
# `const char`, `sizeof` and both CPP_OPERATOR_RES patterns, which are exactly the FP sources step 4
# removed. Measured 2026-08-19 against all 197 exemption-tagged fences in the tree: 0 hits, so this
# adds no standing noise.
EXEMPT_RESCAN_TOKENS = (
    "FUNC(", "case ACSF_", "case PCD_", "AActor", "NETWORK_", "SERVERCOMMANDS_",
    "ULONG ", "TArray", "FBehavior::", "GAMEMODE_", "static_cast<", "RUNTIME_CLASS", "SDWORD",
)
# `->` and `::` are the two most productive C++ signals and the reason 6 of those 8 went unseen,
# but as bare substrings they are far too generic: they also match a signature's return arrow
# (`Sector_Set3dFloor(...) -> int`), BNF notation (`<clause> ::= ...`), a DECORATE `Goto
# Super::Missile`, a `::` inside a string literal, and a comment that literally reads "no ->".
# Requiring an identifier character on BOTH sides keeps the member-access and scope-resolution
# forms that only real C++ has (`self->health`, `Super::Tick`) and drops every case above.
CPP_OPERATOR_RES = (re.compile(r'\w->\w'), re.compile(r'\w::\w'))
# Tags the C++ heuristic SKIPS: the mod-authoring languages, where a tag is the author positively
# asserting "example code in this language" -- exactly what the excerpt rule exempts, and scanning
# them yields only false positives (`Console.Printf` in a ZScript example is a call, not stdlib).
#
# Deliberately a deny-list, not an allow-list of ("", "c", "cpp"). An allow-list fails OPEN: a
# fence tagged `c++`, `cc`, `hpp`, or simply mistyped is not in it and would be skipped silently,
# which is the one direction this check must never fail. Anything unrecognized gets scanned.
#
# GPL_ONLY_TOKENS is deliberately NOT scoped this way and keeps scanning every fence including
# `zscript` -- but see that tuple's own comment for how far its protection actually reaches.
EXAMPLE_FENCE_TAGS = ("acs", "bcs", "decorate", "zscript")
# An explicit allow-list, unlike EXAMPLE_FENCE_TAGS' deny-list above, and deliberately so: this
# one gates a hard ERROR, so it must fail OPEN on an unrecognized tag rather than erroring on a
# ```text or ```ini fence nobody meant as an assertion. The deny-list gates a warning and fails
# closed for the opposite reason.
EXCERPT_REQUIRED_FENCE_TAGS = ("c", "cpp", "c++", "cc", "cxx", "h", "hpp")
# Tokens specific enough to ZScript/GZDoom-family VM internals that they don't show up in
# hand-written ZScript usage examples or in Zandronum's older DECORATE-only codebase.
#
# SCOPE WARNING, measured 2026-08-14: every token here is a C++ VM-internal marker, so this tuple
# catches GPL-3.0 source written in C++ and NOT the ZScript standard library, which is written in
# ZScript. Checked against all 294 files under UZDoom's wadsrc/static/zscript: **0** contain any
# token below. A real stdlib class body pasted into a fence is silent here. GPL_ZSCRIPT_RES below
# closes part of that gap.
GPL_ONLY_TOKENS = (
    "DEFINE_FIELD(", "IMPLEMENT_CLASS(", "DECLARE_CLASS(", "PARAM_PROLOGUE",
    "ACTION_RETURN_", "PClass::FindActor(", "VMValue", "PFunction::",
)

# ZScript-shaped signals for the gap GPL_ONLY_TOKENS's scope warning documents (Phase 5 step 5.2,
# 2026-08-15). Two kinds of hit, deliberately reported together rather than as separate checks:
#
# 1. `SPDX-License-Identifier: GPL` -- every one of the 294 files under UZDoom's
#    wadsrc/static/zscript carries this header verbatim (measured: 294/294). Catches a whole-file
#    or header-inclusive paste completely, but a snippet paste (the more realistic risk -- quoting
#    one class body, not a whole file) won't retain it.
# 2. ZScript's own `native` declaration syntax -- but bare `\bnative\b` is NOT safe on its own:
#    DECORATE has its own unrelated `native` keyword (`ACTOR Key : Inventory native`,
#    `action native A_Raise()`), which this doc tree's own hand-written syntax-reference fences
#    legitimately use 8 times. The patterns below require a ZScript-specific shape around
#    `native` (a scope keyword immediately before/after it, or a type keyword after it) that
#    DECORATE's forms never produce, plus three narrower ZScript-only call/decl shapes
#    (`readonly<...>`, `deprecated("...")`, `version("...")`).
#
# Measured against the same 294-file corpus: the non-header patterns alone (i.e. what a snippet
# paste without the header would still trip) cover 55/294 (19%) -- a real, if partial, reduction
# in an already-partial signal, not full coverage. Measured against every fence in this doc tree
# (all tags, matching GPL_ONLY_TOKENS's own unscoped reach): 0 false positives, including the 8
# DECORATE `native` fences the bare-word version would have wrongly flagged.
GPL_ZSCRIPT_RES = (
    re.compile(r'SPDX-License-Identifier:\s*GPL'),
    re.compile(
        r'\bnative\s+(?:play|ui)\b'
        r'|\b(?:static|clearscope|virtualscope|virtual|override)\s+native\b'
        r'|\bnative\s+(?:readonly|void|bool|int|double|float|string|class|array|let|'
        r'vector[23]|name|sound|state|textureid|color)\b',
        re.I,
    ),
    re.compile(r'\breadonly\s*<'),
    re.compile(r'\bdeprecated\s*\(\s*["\']', re.I),
    re.compile(r'\bversion\s*\(\s*["\']'),
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


def _err(rel, message, ok_list):
    print(f"LINT: {rel} {message}", file=sys.stderr)
    ok_list.append(False)


def _field_body(field_text):
    """The field's value, marker stripped and whitespace-joined. Joining is not cosmetic: 84
    Engine: fields already wrap across source lines and 5 start their value on the line after the
    marker, so any grammar check run on line 1 alone would read a truncated value."""
    body = re.sub(rf'^(?:\*\*)?(?:{_FIELD_ALT}):(?:\*\*)?', '', field_text, count=1)
    return " ".join(body.split())


def _split_prose(body):
    """Free prose is allowed after an em-dash. Split it off before parsing -- prose legitimately
    contains the commas and semicolons the grammars use as separators."""
    parts = re.split(rf'\s{EM_DASH}\s', body, maxsplit=1)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")


def parse_applies_to(body):
    """-> ({engine: value}, [problems]). `N/A - <reason>` is the engine-independent form, for an
    entry whose subject genuinely isn't a property of any one engine (a compiler codegen bug, say):
    it can't honestly assert UZDoom= or Zandronum= either way."""
    data, prose = _split_prose(body)
    if NA_RE.match(data):
        if not prose:
            return {}, ["uses `N/A` without a reason after an em-dash"]
        return {"N/A": prose}, []
    out, problems = {}, []
    for chunk in [c.strip() for c in data.split(",") if c.strip()]:
        m = APPLIES_PAIR_RE.match(chunk)
        if not m:
            problems.append(
                f"has {chunk!r}, which isn't `<engine>=<value>` with engine in "
                f"{'/'.join(ENGINE_VOCAB)}"
            )
            continue
        engine, value = m.group("engine"), m.group("value")
        if value not in APPLIES_VALUES:
            problems.append(
                f"has {chunk!r}, but the only values are {'/'.join(APPLIES_VALUES)} "
                "(there is deliberately no `partial` -- use `yes` plus an "
                "`## Engine-family divergence` section)"
            )
            continue
        if engine in out:
            problems.append(f"names {engine} twice")
        out[engine] = value
    for required in REQUIRED_APPLIES_KEYS:
        if required not in out:
            problems.append(f"has no `{required}=` key (both UZDoom= and Zandronum= are required)")
    return out, problems


def parse_verified_against(body):
    """-> ([(engine, version, sha, date)], [problems]). The literal `none` is legal, for an entry
    that reads no engine at all (a compiler-only finding)."""
    data, _prose = _split_prose(body)
    if data.lower() == "none":
        return [], []
    out, problems = [], []
    for chunk in [c.strip() for c in data.split(";") if c.strip()]:
        m = VERIFIED_ENTRY_RE.match(chunk)
        if not m:
            problems.append(
                f"has {chunk!r}, which isn't `<engine> <version> @<sha> (YYYY-MM-DD)`"
            )
            continue
        try:
            date.fromisoformat(m.group("date"))
        except ValueError:
            problems.append(f"has {chunk!r}, whose date isn't a real calendar date")
            continue
        out.append((m.group("engine"), m.group("version"), m.group("sha"), m.group("date")))
    return out, problems


def check_engine_claim(rel, block_text, ok_list):
    """Exactly one engine claim per file: the `**Applies to:**`/`**Verified against:**` pair.

    The legacy single-field `**Engine:**` form was fully retired by the UZDoom retarget's Phase 5
    sweep (2026-08-17) -- `grep -rl '^\\*\\*Engine:\\*\\*'` over every doc file (excluding this
    tree's own schema examples) reaches zero. A new `Engine:` field is now a hard error, not a
    legal alternate form.

    Presence is tested by anchored field extraction over the header block, never by a substring
    search over the whole file -- a file once passed this check because the literal text
    "Engine:" happened to appear in a prose sentence explaining why it had no such field.
    """
    engine = extract_all_fields(block_text, ENGINE_START_RE)
    applies = extract_all_fields(block_text, APPLIES_TO_START_RE)
    verified = extract_all_fields(block_text, VERIFIED_AGAINST_START_RE)

    if engine:
        _err(rel, "carries a **Engine:** field -- retired by the UZDoom retarget's Phase 5 sweep; "
                  "use **Applies to:**/**Verified against:** instead (see shared/AUTHORING.md's "
                  "\"Engine scope\")", ok_list)
    if applies and not verified:
        _err(rel, "has **Applies to:** but no **Verified against:** -- the pair is atomic, since "
                  "where a feature exists and whose source was read are separate claims", ok_list)
    if verified and not applies:
        _err(rel, "has **Verified against:** but no **Applies to:**", ok_list)
    if not engine and not (applies or verified):
        _err(rel, "has no engine claim -- needs **Applies to:** + **Verified against:**", ok_list)
    for fields, name in ((engine, "Engine"), (applies, "Applies to"),
                         (verified, "Verified against")):
        if len(fields) > 1:
            _err(rel, f"has {len(fields)} **{name}:** fields in its header block (expected 1)",
                 ok_list)

    applies_map = {}
    if applies:
        applies_map, problems = parse_applies_to(_field_body(applies[0]))
        for problem in problems:
            _err(rel, f"'s **Applies to:** field {problem}", ok_list)
    if verified:
        entries, problems = parse_verified_against(_field_body(verified[0]))
        for problem in problems:
            _err(rel, f"'s **Verified against:** field {problem}", ok_list)
        for engine_name, *_rest in entries:
            if applies_map.get(engine_name) == "no":
                _err(rel, f"'s **Verified against:** names {engine_name}, but **Applies to:** "
                          f"says {engine_name}=no -- don't stamp a version for an engine the "
                          "entry says it isn't on", ok_list)
    return applies_map


def check_divergence_cooccurrence(rel, text, applies_map, ok_list):
    """`Applies to: UZDoom=no` is a claim that the feature was checked for and found absent -- it
    must co-occur with a real `## Engine-family divergence`/`## Zandronum-specific: ...` section,
    not just the bare claim (Phase 3 step 3.7). Only `no` triggers this: `yes` says nothing about
    divergence, and `unknown` is deliberately the escape hatch for genuinely cross-cutting pages
    (see maintainer/plans/2026-08-14_uzdoom_retarget_phase3.md's 3.5 "Rule on `unknown`")."""
    if applies_map.get("UZDoom") != "no":
        return
    if not DIVERGENCE_HEADING_RE.search(text):
        _err(rel, "'s **Applies to:** says UZDoom=no but the file has no "
                  "`## Engine-family divergence`/`## Zandronum-specific: ...` section -- a `no` "
                  "claim needs the writeup, not just the field", ok_list)


def check_divergence_heading_forms(rel, text, ok_list):
    """Pin a denylist of specific retired divergence-heading phrasings (Phase 4 step 4.5, extended
    Phase 5.4). Runs on every doc file regardless of its engine claim -- unlike
    check_divergence_cooccurrence, which only fires on `UZDoom=no`, a retired heading form is wrong
    on sight no matter what the file's Applies to: says.

    Deliberately NOT a general "any non-canonical divergence-shaped heading" check -- see
    DEPRECATED_DIVERGENCE_HEADING_RE's own comment for why that's evaluated and rejected, not just
    not-yet-built: distinguishing an attempted canonical marker from an ordinary heading that
    happens to use the word "divergence" requires reading the section body, which this function
    (header text only) cannot do."""
    m = DEPRECATED_DIVERGENCE_HEADING_RE.search(text)
    if m:
        _err(rel, f"'s `## {m.group(1)}` heading is a retired form -- use "
                  "`## Engine-family divergence[: <suffix>]`, `## Zandronum-specific: <suffix>`, "
                  "or `## Wiki/engine divergence[: <suffix>]` instead (see shared/AUTHORING.md's "
                  "\"Engine scope\")", ok_list)


def check_header_block(path, text, ok_list):
    """CALLABLE / TABLE_NOTES / CONCEPT files: Tier:, Provenance:, and an engine claim must be
    present, and (once STRICT_HEADER_POSITION is on) positioned as a block directly under the H1.
    The engine claim itself is check_engine_claim's job, since it now has two legal forms."""
    rel = path.relative_to(ROOT)
    missing = []
    if not extract_all_fields(text, TIER_START_RE):
        missing.append("Tier:")
    if not extract_all_fields(text, PROVENANCE_START_RE):
        missing.append("Provenance:")
    for field in missing:
        print(f"LINT: {rel} has no {field} line", file=sys.stderr)
        ok_list.append(False)
    if not STRICT_HEADER_POSITION:
        applies_map = check_engine_claim(rel, text, ok_list)
        check_divergence_cooccurrence(rel, text, applies_map, ok_list)
        check_divergence_heading_forms(rel, text, ok_list)
        return

    h1 = H1_RE.search(text)
    if not h1:
        print(f"LINT: {rel} has no H1 heading to anchor its header block to", file=sys.stderr)
        ok_list.append(False)
        return
    # The header block runs from the H1 to the first line of real prose. A field routinely wraps
    # across several lines (acs/functions/delay.md's Bucket: takes three), so a line that is
    # neither blank nor a field start still belongs to the block while a field is open -- reading
    # it as prose instead ends the block early and fails ~21 correctly-formatted files. A field
    # closes at a blank line or at the next field start, matching extract_all_fields' boundary
    # exactly; a blank line closes the field but not the block, since fields are legitimately
    # written as blank-separated paragraphs.
    after = text[h1.end():].lstrip("\n")
    lines = after.split("\n")
    block_end = 0
    in_field = False
    for i, line in enumerate(lines):
        if line.strip() == "":
            in_field = False
            continue
        if BOLD_HEADER_FIELD_RE.match(line):
            in_field = True
            block_end = i + 1
            continue
        if in_field:
            block_end = i + 1
            continue
        break
    block_lines = lines[:block_end]
    block_text = "\n".join(block_lines)
    applies_map = check_engine_claim(rel, block_text, ok_list)
    check_divergence_cooccurrence(rel, text, applies_map, ok_list)
    check_divergence_heading_forms(rel, text, ok_list)
    if missing:
        return
    for field in ("Tier:", "Provenance:"):
        if field not in block_text and f"**{field}" not in block_text:
            print(
                f"LINT: {rel} has a {field} field but it isn't in the header block directly "
                "under the H1 (see shared/ARCHETYPES.md's header-block format)",
                file=sys.stderr,
            )
            ok_list.append(False)
    # One field per line (shared/ARCHETYPES.md). Not cosmetic: extract_all_fields only sees a
    # field that starts its own line, so a Provenance: packed onto the end of a Tier: line is
    # invisible to the wiki-provenance and wiki-license checks that read it.
    for line in block_lines:
        if len(re.findall(rf'\*\*(?:{_FIELD_ALT}):\*\*', line)) > 1:
            print(
                f"LINT: {rel} packs more than one header field onto one line -- one field per "
                "line (see shared/ARCHETYPES.md's header-block format). Line starts: "
                f"{line[:60]!r}",
                file=sys.stderr,
            )
            ok_list.append(False)


def _gpl_engine_context(text):
    """True when this file's author plausibly had GPL-3.0 engine source open.

    Keyed on `Verified against:` -- the field that means "someone read this engine". The legacy
    `Engine:` field it replaced is retired tree-wide and is now its own hard error (see
    check_engine_claim), so it no longer needs a branch here.

    Deliberately NOT keyed on `Applies to:`: nearly every file says UZDoom=yes, which states where
    a feature exists, not what anyone read. Keying on it would make the stern message
    near-universal and therefore ignored."""
    for field in extract_all_fields(text, VERIFIED_AGAINST_START_RE):
        if GPL_ENGINE_RE.search(field):
            return True
    return False


def check_source_excerpt_and_gpl(path, text, ok_list):
    """The claim-text checks below use extract_all_fields rather than a single-line regex
    because a **Source excerpt:** field wraps across lines as readily as a Provenance field
    does, and the consequence of missing the wrap here is worse than a cosmetic miss: a UZDoom/
    GZDoom admission or a missing LICENSE citation landing on the field's second line would
    silently escape the hard-error check below it exists to satisfy. This convention is
    currently one field per file tree-wide (checked directly, not assumed) -- unlike
    Provenance, which genuinely repeats per member in a families/*.md file -- so only the first
    field is evaluated; a file that duplicates the field is a shape this tree doesn't otherwise
    use and should drop the duplicate rather than have both validated."""
    rel = path.relative_to(ROOT)
    excerpt_fields = extract_all_fields(text, SOURCE_EXCERPT_START_RE)
    claim = excerpt_fields[0] if excerpt_fields else None
    blocks = CODE_BLOCK_RE.findall(text)
    # Every fence, whatever its tag -- what GPL_ONLY_TOKENS scans.
    joined = "\n".join(body for _, body in blocks)
    # Only the fences that could hold verbatim C++ -- what the ENGINE_SOURCE_TOKENS heuristic
    # scans. See EXAMPLE_FENCE_TAGS for why the two surfaces differ.
    cpp_joined = "\n".join(body for tag, body in blocks
                           if tag.lower() not in EXAMPLE_FENCE_TAGS)

    gpl_named = claim and GPL_ENGINE_RE.search(claim)
    gpl_token_hit = any(tok in joined for tok in GPL_ONLY_TOKENS)
    gpl_zscript_hit = any(r.search(joined) for r in GPL_ZSCRIPT_RES)
    if gpl_named or gpl_token_hit or gpl_zscript_hit:
        print(
            f"LINT: {rel} appears to quote GPL-3.0 (UZDoom/GZDoom/ZScript stdlib) source "
            "verbatim -- not allowed under any circumstance, paraphrase instead (see "
            "shared/AUTHORING.md's \"Quoting engine/compiler source verbatim\")",
            file=sys.stderr,
        )
        ok_list.append(False)
        return

    if not claim and any(tag.lower() in EXCERPT_REQUIRED_FENCE_TAGS for tag, _ in blocks):
        msg = (f"LINT: {rel} has a ```c/```cpp fenced block -- a C/C++ tag asserts the block is "
               "engine/compiler source, which requires a **Source excerpt:** field citing LICENSE "
               "§3 (Zandronum) or §4 (zt-bcc/bcc). If it's really a usage example, retag it "
               "(```acs/```decorate/```zscript); if it's a restatement, drop the fence and write "
               "prose.")
        if _gpl_engine_context(text):
            msg += (" And if that block is UZDoom/GZDoom/ZScript-stdlib source, no field can "
                    "legalize it at all -- remove it and paraphrase.")
        print(msg + " See shared/AUTHORING.md's \"Quoting engine/compiler source verbatim\".",
              file=sys.stderr)
        ok_list.append(False)
        return

    if claim:
        if not any(name in claim and section in claim
                   for name, section in PERMITTED_EXCERPT_SOURCES):
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
        # The licensing invariant is about whose source sits in the fence, not which engines were
        # read -- so a file may legitimately be re-verified against UZDoom while still quoting
        # Zandronum. That combination is exactly where someone re-reading behavior on a GPL-3.0
        # engine is most likely to paste the wrong source into an already-blessed excerpt, so it
        # warns rather than passing silently. A warning, not an error: making it an error would
        # force deletion of a legally-quoted permissive excerpt the moment its entry is
        # re-verified, which is what the re-verification sweep does to nearly every file.
        if any(GPL_ENGINE_RE.search(f)
               for f in extract_all_fields(text, VERIFIED_AGAINST_START_RE)):
            print(
                f"LINT-WARN: {rel} is verified against a GPL-3.0 engine (UZDoom/GZDoom) and also "
                "carries a **Source excerpt:** field. That's legal only while the fenced source "
                "is Zandronum's or zt-bcc's, not the engine that was just read -- confirm by "
                "hand. See shared/AUTHORING.md's \"Quoting engine/compiler source verbatim\".",
                file=sys.stderr,
            )
    elif (any(tok in cpp_joined for tok in ENGINE_SOURCE_TOKENS)
          or any(r.search(cpp_joined) for r in CPP_OPERATOR_RES)):
        if _gpl_engine_context(text):
            print(
                f"LINT-WARN: {rel} has a fenced code block that looks like verbatim engine "
                "source, and this file's engine claim names UZDoom/GZDoom -- if that block is "
                "UZDoom/GZDoom/ZScript-stdlib source it is GPL-3.0 and must be REMOVED and "
                "paraphrased. No **Source excerpt:** field can legalize it; there is no LICENSE "
                "section that would apply. (Heuristic -- a Zandronum-sourced block in the same "
                "file is still fine with the field.)",
                file=sys.stderr,
            )
        else:
            print(
                f"LINT-WARN: {rel} has a fenced code block that looks like verbatim engine source "
                "but no **Source excerpt:** field -- heuristic, may be a false positive (a usage "
                "example, a comment, a signature). Check by hand before adding one.",
                file=sys.stderr,
            )

    # Independent of the if/elif chain above (deliberately not a return): an acs/decorate/zscript
    # tag exempts a fence from the ENGINE_SOURCE_TOKENS/CPP_OPERATOR_RES heuristic entirely, on the
    # premise that the tag is the author asserting "this is a hand-written usage example". Nothing
    # previously verified that assertion. This rescan checks it with a narrower, exemption-safe
    # token subset (see EXEMPT_RESCAN_TOKENS), and runs even when `claim` fired above, since a
    # laundered stdlib paste into a file that already discloses an unrelated Zandronum excerpt
    # would otherwise be silent.
    exempt_joined = "\n".join(body for tag, body in blocks
                               if tag.lower() in EXAMPLE_FENCE_TAGS)
    if any(tok in exempt_joined for tok in EXEMPT_RESCAN_TOKENS):
        msg = (
            f"LINT-WARN: {rel} has a fence tagged as a usage example (acs/bcs/decorate/zscript) "
            "but containing a token that only appears in engine source -- one of the two is "
            "wrong: retag it, add a **Source excerpt:** field, or paraphrase it."
        )
        if _gpl_engine_context(text):
            msg += (" And if that block is UZDoom/GZDoom/ZScript-stdlib source, no field can "
                    "legalize it at all -- remove it and paraphrase.")
        print(msg + " See shared/AUTHORING.md's \"Quoting engine/compiler source verbatim\".",
              file=sys.stderr)


def check_fence_tags(path, text, ok_list):
    """Every fence must carry a tag -- a hard error on an empty one. Deliberately its own function
    rather than a branch inside check_source_excerpt_and_gpl: that function `return`s early on both
    the GPL and EXCERPT_REQUIRED hard errors, so a check added inside it would be silently
    unreachable for exactly the files most likely to need it. A separate function has no ordering
    interaction with those returns at all.

    Deliberately does NOT introduce a closed tag vocabulary -- only the empty tag errors. A closed
    list would hard-error a legitimate future ```ini or ```json fence for zero safety benefit, and
    the tags that actually carry consequences (EXAMPLE_FENCE_TAGS, EXCERPT_REQUIRED_FENCE_TAGS) are
    already closed lists of their own."""
    rel = path.relative_to(ROOT)
    blocks = CODE_BLOCK_RE.findall(text)
    if any(tag == "" for tag, _ in blocks):
        print(
            f"LINT: {rel} has a fenced code block with no language tag -- every fence must carry "
            "one. Tag it acs/bcs/decorate/zscript (exemption tier: asserting a usage example), "
            "c/cpp/c++/cc/cxx/h/hpp (assertion tier: asserting engine/compiler source, requires a "
            "**Source excerpt:** field), or ```text (neutral default, for a block that is not an "
            "assertion in either direction). See shared/AUTHORING.md's \"Quoting engine/compiler "
            "source verbatim\".",
            file=sys.stderr,
        )
        ok_list.append(False)


def extract_all_fields(text, start_re, with_spans=False):
    """Return every field matching `start_re` in a file, as a list of (possibly multi-line)
    strings. A field routinely wraps across several source lines (a multi-page citation, or a
    long "verified against ..." tail), so each one is collected from its start line up to the
    next header field or the blank line ending the block -- a single-line match would miss the
    tail, which is exactly where a second wiki citation or a GPL-engine admission is likely to
    land in a field that started out looking clean.

    All matching fields, not just the header block's: a families/*.md file carries one
    Provenance per member function on top of its own, and reading only the first would inspect
    one of the seven in acs/families/lump-io.md.

    If with_spans is True, return (text, start_line, end_line) tuples instead of bare strings --
    0-indexed line numbers into text.split("\n"), end-exclusive, so lines[start_line:end_line]
    reconstructs the field. A caller that needs to insert content right after a specific field
    (e.g. a migration script placing **Wiki license:** after the first Provenance:) needs the
    same wrap-aware boundary this function already computes, not a re-derived heuristic that
    would disagree with lint on the files whose citation wraps across lines."""
    lines = text.split("\n")
    fields, collecting, collect_start = [], None, None
    for i, line in enumerate(lines):
        if collecting is not None:
            if not line.strip() or HEADER_FIELD_RE.match(line):
                fields.append(("\n".join(collecting), collect_start, i))
                collecting, collect_start = None, None
                # fall through: this same line may itself start the next field
            else:
                collecting.append(line)
                continue
        if start_re.match(line):
            collecting, collect_start = [line], i
    if collecting is not None:
        fields.append(("\n".join(collecting), collect_start, len(lines)))
    if with_spans:
        return fields
    return [f[0] for f in fields]


def extract_all_provenance(text):
    return extract_all_fields(text, PROVENANCE_START_RE)


def cites_zdoom_wiki(field):
    return any(tok in field for tok in ZDOOM_WIKI_TOKENS)


def cites_zandronum_wiki(field):
    return any(tok in field for tok in ZANDRONUM_WIKI_TOKENS)


def check_wiki_provenance(path, text, ok_list):
    """Two rules over a file's Provenance: fields, both from shared/AUTHORING.md's "Wiki
    provenance" (see LICENSE SS2 for the terms they exist to satisfy):

    1. A file may derive from the ZDoom Wiki (GFDL 1.2) or the Zandronum Wiki (CC BY-NC-SA 4.0),
       never both -- those two copyleft licenses are mutually incompatible, so a file citing both
       couldn't be licensed under either and no LICENSE section could rescue it. The license
       attaches to the FILE, so this is a union across every field: a header block citing one
       wiki and a member line citing the other is the realistic way the violation shows up.
    2. Every wiki-citing field individually carries the full resolvable MediaWiki URL form
       (`/w/index.php?title=...&oldid=N`, host matching the wiki it cites), not just a bare
       `oldid=` or a locally-saved filename -- a title/filename alone isn't reachable by anyone
       who clones this repo (see maintainer/tools/migrate_provenance_urls.py, which produced the
       current tree-wide form of these citations)."""
    rel = path.relative_to(ROOT)
    fields = extract_all_provenance(text)

    if any(cites_zdoom_wiki(f) for f in fields) and any(cites_zandronum_wiki(f) for f in fields):
        print(
            f"LINT: {rel} cites both the ZDoom Wiki (GFDL 1.2) and the Zandronum Wiki "
            "(CC BY-NC-SA 4.0) across its Provenance: fields -- mutually incompatible copyleft, "
            "so no single file can carry both. Split into one file per wiki (see "
            "shared/AUTHORING.md's \"Wiki provenance\")",
            file=sys.stderr,
        )
        ok_list.append(False)

    for field in fields:
        is_zdoom, is_zandronum = cites_zdoom_wiki(field), cites_zandronum_wiki(field)
        if not (is_zdoom or is_zandronum):
            continue
        host = ZDOOM_WIKI_HOST if is_zdoom else ZANDRONUM_WIKI_HOST
        if host in field and re.search(re.escape(host) + r'[^\s)]*&oldid=\d+', field):
            continue
        first = field.split("\n")[0][:90]
        if MEDIAWIKI_URL_MARKER in field:
            print(
                f"LINT: {rel} has a wiki-citing Provenance: field whose "
                f"{MEDIAWIKI_URL_MARKER} URL doesn't use the host this field's wiki citation "
                f"implies ({host!r}) -- wrong wiki's URL, or a typo'd host. Field starts: "
                f"{first!r} (see shared/AUTHORING.md's \"Wiki provenance\")",
                file=sys.stderr,
            )
        else:
            print(
                f"LINT: {rel} has a wiki-citing Provenance: field with no resolvable "
                f"{MEDIAWIKI_URL_MARKER}...&oldid=N URL -- a page title or filename alone "
                "doesn't resolve to the revision the entry was built from. Field starts: "
                f"{first!r} (see shared/AUTHORING.md's \"Wiki provenance\")",
                file=sys.stderr,
            )
        ok_list.append(False)


def check_wiki_license(path, text, ok_list):
    """LICENSE SS2 asks a file derived from a wiki page to carry a per-file pointer to the
    license that wiki's content is published under -- mirrors check_source_excerpt_and_gpl's
    SS3/SS4 check for verbatim engine/compiler excerpts (see shared/AUTHORING.md's "Wiki
    provenance"). A file citing no wiki must not carry the field either, since there'd be no
    LICENSE SS2 material for it to name."""
    rel = path.relative_to(ROOT)
    provenance_fields = extract_all_provenance(text)
    cites_zdoom = any(cites_zdoom_wiki(f) for f in provenance_fields)
    cites_zandronum = any(cites_zandronum_wiki(f) for f in provenance_fields)
    license_fields = extract_all_fields(text, WIKI_LICENSE_START_RE)

    if not (cites_zdoom or cites_zandronum):
        if license_fields:
            print(
                f"LINT: {rel} has a **Wiki license:** field but its Provenance: doesn't cite a "
                "wiki",
                file=sys.stderr,
            )
            ok_list.append(False)
        return

    if len(license_fields) != 1:
        print(
            f"LINT: {rel} cites a wiki but has {len(license_fields)} **Wiki license:** fields "
            "(expected exactly 1)",
            file=sys.stderr,
        )
        ok_list.append(False)
        return

    field = license_fields[0]
    if "LICENSE" not in field or "§2" not in field:
        print(
            f"LINT: {rel}'s **Wiki license:** field doesn't link back to LICENSE §2",
            file=sys.stderr,
        )
        ok_list.append(False)
    if cites_zdoom and "ZDoom Wiki" not in field:
        print(
            f"LINT: {rel}'s **Wiki license:** field doesn't name the ZDoom Wiki its "
            "Provenance: cites",
            file=sys.stderr,
        )
        ok_list.append(False)
    if cites_zandronum and "Zandronum Wiki" not in field:
        print(
            f"LINT: {rel}'s **Wiki license:** field doesn't name the Zandronum Wiki its "
            "Provenance: cites",
            file=sys.stderr,
        )
        ok_list.append(False)


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
                check_fence_tags(path, text, ok_list)
                check_wiki_provenance(path, text, ok_list)
                check_wiki_license(path, text, ok_list)
            elif archetype == S.TABLE_INVENTORY:
                check_inventory_table(path, text, ok_list)
                check_source_excerpt_and_gpl(path, text, ok_list)
                check_fence_tags(path, text, ok_list)
                check_wiki_provenance(path, text, ok_list)
                check_wiki_license(path, text, ok_list)


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
            check_fence_tags(path, text, ok_list)
            check_wiki_provenance(path, text, ok_list)
            check_wiki_license(path, text, ok_list)

    ok = not ok_list
    if ok:
        print(f"LINT: clean -- {total_files[0]} doc files across {len(S.SECTIONS)} sections, all linked, all tiered/provenanced.", file=sys.stderr)
    return ok


def _fixture(fields, body="Prose.\n"):
    return "# `void Thing(int a)`\n\n" + fields.strip("\n") + "\n\n" + body


_LEGACY = "**Tier:** A\n**Engine:** Zandronum 3.2.1\n**Provenance:** engine source.\n"
_PAIR = ("**Tier:** A\n"
         "**Applies to:** UZDoom=yes, Zandronum=yes\n"
         "**Verified against:** UZDoom 5.0.0-pre @fbad53bff5 (2026-08-08); "
         "Zandronum 3.2.1 @28f736fb3 (2026-07-28)\n"
         "**Provenance:** engine source.\n")
# Same pair, but only Zandronum's source was actually read -- "exists on both, only Zandronum's
# behavior checked" is the honest state of most of this tree (see shared/AUTHORING.md's "Engine
# scope"). Used by fixtures below that need a *valid* modern claim naming no GPL-3.0 engine, so
# they keep exercising the non-UZDoom-named branch of _gpl_engine_context now that _LEGACY (which
# used to serve that role) is itself a hard error.
_PAIR_ZAN_VERIFIED_ONLY = ("**Tier:** A\n"
                           "**Applies to:** UZDoom=yes, Zandronum=yes\n"
                           "**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)\n"
                           "**Provenance:** engine source.\n")
_EXCERPT_ZAN = ("**Source excerpt:** This file quotes Zandronum engine source verbatim; "
                "reproduced under Zandronum's own license terms - see [LICENSE](../../LICENSE) §3.\n")

# (name, file text, [substrings that must appear], must_be_clean)
# Substrings are deliberately short and stable -- matching full message text would make every
# later reword a self-test failure.
_SELF_TESTS = [
    ("legacy Engine: field is a hard error", _fixture(_LEGACY), ["retired"], False),
    ("legacy Engine: N/A is a hard error too", _fixture(
        "**Tier:** B\n**Engine:** N/A — a compiler bug, not an engine bug.\n"
        "**Provenance:** measured.\n"), ["retired"], False),
    ("new pair", _fixture(_PAIR), [], True),
    ("Verified against: none", _fixture(
        "**Tier:** B\n**Applies to:** UZDoom=yes, Zandronum=yes\n"
        "**Verified against:** none\n**Provenance:** measured.\n"), [], True),
    ("Applies to: N/A", _fixture(
        "**Tier:** B\n**Applies to:** N/A — a compiler codegen bug, engine-independent.\n"
        "**Verified against:** none\n**Provenance:** measured.\n"), [], True),
    ("prose after em-dash", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=yes, Zandronum=yes — name-level only "
        "(tools/engine_matrix.py, 2026-08-08)\n"
        "**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)\n"
        "**Provenance:** engine source.\n"), [], True),
    ("wrapped across lines", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=yes,\nZandronum=yes\n"
        "**Verified against:** UZDoom 5.0.0-pre @fbad53bff5\n(2026-08-08)\n"
        "**Provenance:** engine source.\n"), [], True),
    ("Applies to alone", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=yes, Zandronum=yes\n"
        "**Provenance:** engine source.\n"), ["pair is atomic"], False),
    ("Verified against alone", _fixture(
        "**Tier:** A\n**Verified against:** none\n**Provenance:** engine source.\n"),
     ["no **Applies to:**"], False),
    ("both forms at once", _fixture(
        "**Tier:** A\n**Engine:** Zandronum 3.2.1\n"
        "**Applies to:** UZDoom=yes, Zandronum=yes\n**Verified against:** none\n"
        "**Provenance:** engine source.\n"), ["retired"], False),
    ("no engine claim", _fixture("**Tier:** A\n**Provenance:** engine source.\n"),
     ["has no engine claim"], False),
    ("partial is not a value", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=partial, Zandronum=yes\n"
        "**Verified against:** none\n**Provenance:** engine source.\n"),
     ["deliberately no `partial`"], False),
    ("missing Zandronum key", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=yes\n**Verified against:** none\n"
        "**Provenance:** engine source.\n"), ["no `Zandronum=` key"], False),
    ("unknown engine", _fixture(
        "**Tier:** A\n**Applies to:** Skulltag=yes, UZDoom=yes, Zandronum=yes\n"
        "**Verified against:** none\n**Provenance:** engine source.\n"),
     ["isn't `<engine>=<value>`"], False),
    ("no @sha", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=yes, Zandronum=yes\n"
        "**Verified against:** UZDoom 5.0.0-pre (2026-08-08)\n**Provenance:** engine source.\n"),
     ["isn't `<engine> <version> @<sha>"], False),
    ("bad sha", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=yes, Zandronum=yes\n"
        "**Verified against:** UZDoom 5.0.0-pre @zzzzzzz (2026-08-08)\n"
        "**Provenance:** engine source.\n"), ["isn't `<engine> <version> @<sha>"], False),
    ("impossible date", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=yes, Zandronum=yes\n"
        "**Verified against:** UZDoom 5.0.0-pre @fbad53bff5 (2026-13-45)\n"
        "**Provenance:** engine source.\n"), ["isn't a real calendar date"], False),
    ("verified an engine marked absent", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=no, Zandronum=yes\n"
        "**Verified against:** UZDoom 5.0.0-pre @fbad53bff5 (2026-08-08)\n"
        "**Provenance:** engine source.\n"), ["says UZDoom=no"], False),
    # The excerpt claim names Zandronum ONLY. If it mentioned UZDoom anywhere, gpl_named would
    # hard-error first and this would silently stop testing the coexistence rule.
    ("UZDoom-verified + permissive excerpt warns", _fixture(_PAIR + _EXCERPT_ZAN),
     ["LINT-WARN", "also carries a **Source excerpt:**"], True),
    ("excerpt naming UZDoom source", _fixture(
        _PAIR + "**Source excerpt:** Quotes UZDoom source - see [LICENSE](../../LICENSE) §3.\n"),
     ["appears to quote GPL-3.0"], False),
    ("GPL tokens in a fence", _fixture(
        _PAIR + _EXCERPT_ZAN, "```cpp\nIMPLEMENT_CLASS(AActor, false, false)\n```\n"),
     ["appears to quote GPL-3.0"], False),
    ("excerpt naming no permitted source", _fixture(
        _PAIR + "**Source excerpt:** Quotes some source - see [LICENSE](../../LICENSE).\n"),
     ["doesn't clearly cite LICENSE §3"], False),
    # Step 3 (2026-08-19): EXCERPT_REQUIRED_FENCE_TAGS makes a field-less c/cpp-family fence a
    # hard error, ahead of (and instead of) the heuristic below -- a c/cpp tag is an assertion,
    # not a guess. The `return` after the new branch means these never reach ENGINE_SOURCE_TOKENS.
    ("c-tagged fence with no excerpt field hard-errors", _fixture(
        _PAIR, "```c\ncase ACSF_Thing:\n```\n"),
     ["requires a **Source excerpt:**"], False),
    ("c++-tagged fence with no excerpt field hard-errors", _fixture(
        _PAIR, "```c++\ncase ACSF_Thing:\n```\n"),
     ["requires a **Source excerpt:**"], False),
    ("cpp-tagged fence with a Zandronum excerpt field stays clean", _fixture(
        _PAIR_ZAN_VERIFIED_ONLY + _EXCERPT_ZAN, "```cpp\ncase ACSF_Thing:\n```\n"),
     [], True),
    ("acs-tagged fence with no excerpt field is exempt from the EXCERPT_REQUIRED rule", _fixture(
        _PAIR, "```acs\ncase ACSF_Thing:\n```\n"),
     ["only appears in engine source"], True),
    ("neutral-tagged fence with no excerpt field still only warns", _fixture(
        _PAIR_ZAN_VERIFIED_ONLY, "```text\nAActor *thing = nullptr;\n```\n"),
     ["Check by hand before adding one"], True),
    ("engine-source tokens, UZDoom-stamped", _fixture(
        _PAIR, "```text\ncase ACSF_Thing:\n```\n"),
     ["must be REMOVED and paraphrased"], True),
    ("engine-source tokens, Zandronum-stamped", _fixture(
        _PAIR_ZAN_VERIFIED_ONLY, "```text\ncase ACSF_Thing:\n```\n"),
     ["Check by hand before adding one"], True),
    # The 2026-08-14 detection-hole fix. The first two are the pair that must not collapse into
    # each other: a `zscript` fence is exempt from the C++ heuristic but never from the GPL rule.
    ("Printf in a zscript fence is exempt", _fixture(
        _PAIR, "```zscript\nConsole.Printf(\"hi %d\", i);\n```\n"), [], True),
    # Pins the PLUMBING -- that tag-scoping never reaches the GPL branch. It does NOT show that a
    # real stdlib paste is caught: `DEFINE_FIELD(` is C++, and the ZScript stdlib is ZScript, which
    # contains no GPL_ONLY_TOKENS at all. See that tuple's SCOPE WARNING.
    ("GPL tokens in a zscript fence still hard-error", _fixture(
        _PAIR, "```zscript\nDEFINE_FIELD(AActor, health)\n```\n"),
     ["appears to quote GPL-3.0"], False),
    # An unrecognized tag must be SCANNED, not skipped -- the deny-list's whole point.
    ("unknown fence tag is still scanned", _fixture(
        _PAIR_ZAN_VERIFIED_ONLY, "```cs\nEffectTics += 2;\nSuper::Tick();\n```\n"),
     ["Check by hand before adding one"], True),
    # Phase 5 step 5.2, 2026-08-15: GPL_ZSCRIPT_RES closes part of the "0 of 294" gap
    # GPL_ONLY_TOKENS's own comment documents -- ZScript stdlib class bodies GPL_ONLY_TOKENS's
    # C++-only tokens never catch. Each fires the hard error, tag-unscoped like GPL_ONLY_TOKENS.
    ("ZScript native field declaration hard-errors", _fixture(
        _PAIR, "```zscript\nstatic native void DamageSector(Sector sec, Actor source);\n```\n"),
     ["appears to quote GPL-3.0"], False),
    ("ZScript clearscope-native hard-errors", _fixture(
        _PAIR, "```zscript\nstatic clearscope native bool CheckLinedefVulnerable(Line def);\n```\n"),
     ["appears to quote GPL-3.0"], False),
    ("ZScript trailing 'native play' hard-errors", _fixture(
        _PAIR, "```zscript\nstruct HealthGroup native play\n{\n}\n```\n"),
     ["appears to quote GPL-3.0"], False),
    ("SPDX GPL header hard-errors even in a text-tagged fence", _fixture(
        _PAIR, "```text\n** SPDX-License-Identifier: GPL-3.0-or-later\n```\n"),
     ["appears to quote GPL-3.0"], False),
    ("readonly<...> hard-errors", _fixture(
        _PAIR, "```zscript\nreadonly<Actor> target;\n```\n"),
     ["appears to quote GPL-3.0"], False),
    # Regression pin for the false-positive fix found while building GPL_ZSCRIPT_RES: DECORATE has
    # its own unrelated `native` keyword, used 8 times in this doc tree's own hand-written syntax-
    # reference fences. A bare `\bnative\b` would wrongly hard-error all of these.
    ("DECORATE 'action native FuncName()' is not a ZScript native decl", _fixture(
        _PAIR, "```decorate\naction native A_Raise();\n```\n"), [], True),
    ("DECORATE trailing 'ACTOR X : Y native' is not a ZScript native decl", _fixture(
        _PAIR, "```decorate\nACTOR Key : Inventory native\n{\n}\n```\n"), [], True),
    ("member access in a text-tagged fence warns", _fixture(
        _PAIR_ZAN_VERIFIED_ONLY, "```text\nP_DamageMobj(self, NULL, NULL, self->health, DMG_FORCED);\n```\n"),
     ["Check by hand before adding one"], True),
    ("scope resolution in a text-tagged fence warns", _fixture(
        _PAIR_ZAN_VERIFIED_ONLY, "```text\nEffectTics += 2;\nSuper::Tick();\n```\n"),
     ["Check by hand before adding one"], True),
    # The three shapes that made `->`/`::` unusable as bare substrings. All must stay silent.
    ("signature return arrow is not member access", _fixture(
        _PAIR, "```text\nSector_Set3dFloor(int tag, int type) -> int\n```\n"), [], True),
    ("BNF ::= is not scope resolution", _fixture(
        _PAIR, "```text\n<clause>  ::= <begin> : <end> = <replacement>\n```\n"), [], True),
    ("DECORATE Goto Super:: in a tagged fence", _fixture(
        _PAIR, "```decorate\nMissile:\n    TNT1 A 0 A_Nothing\n    Goto Super::Missile\n```\n"),
     [], True),
    # Step 3.7's co-occurrence rule: `Applies to: UZDoom=no` demands a real divergence writeup.
    ("UZDoom=no with Engine-family divergence heading passes", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=no, Zandronum=yes\n"
        "**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)\n"
        "**Provenance:** engine source.\n",
        "Prose.\n\n## Engine-family divergence\n\nZandronum-only feature.\n"), [], True),
    ("UZDoom=no with Zandronum-specific: heading passes", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=no, Zandronum=yes\n"
        "**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)\n"
        "**Provenance:** engine source.\n",
        "Prose.\n\n## Zandronum-specific: private chat message color\n\nDetail.\n"), [], True),
    ("UZDoom=no without a divergence heading errors", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=no, Zandronum=yes\n"
        "**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)\n"
        "**Provenance:** engine source.\n"),
     ["needs the writeup"], False),
    ("UZDoom=yes needs no divergence heading", _fixture(_PAIR), [], True),
    ("UZDoom=unknown needs no divergence heading", _fixture(
        "**Tier:** A\n**Applies to:** UZDoom=unknown, Zandronum=yes\n"
        "**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)\n"
        "**Provenance:** engine source.\n"), [], True),
    ("Engine: field is a hard error even alongside a canonical divergence heading", _fixture(
        _LEGACY, "Prose.\n\n## Engine-family divergence\n\nZandronum-only feature.\n"),
     ["retired"], False),
    # Phase 4 step 4.5: the three retired heading forms error regardless of the file's engine
    # claim -- a UZDoom=yes fixture here, deliberately not UZDoom=no, since the point is that this
    # check fires independently of check_divergence_cooccurrence above.
    ("retired '## Engine availability' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Engine availability\n\nDetail.\n"), ["retired form"], False),
    ("retired '## Engine scope' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Engine scope\n\nDetail.\n"), ["retired form"], False),
    ("retired '## Engine scope note: X' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Engine scope note: dmflags3\n\nDetail.\n"), ["retired form"], False),
    ("retired '## Wiki/fork divergence' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Wiki/fork divergence\n\nDetail.\n"), ["retired form"], False),
    ("retired '## Wiki/fork divergence: X' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Wiki/fork divergence: parameters\n\nDetail.\n"),
     ["retired form"], False),
    # Phase 5.4 (2026-08-17): nine more retired forms found and fixed by a real tree-wide sweep,
    # added to the denylist as a regression pin -- NOT a general "any divergence-shaped heading"
    # rule, see DEPRECATED_DIVERGENCE_HEADING_RE's own comment for why that's rejected on evidence.
    ("retired '## Wiki divergence' (bare) heading errors", _fixture(
        _PAIR, "Prose.\n\n## Wiki divergence\n\nDetail.\n"), ["retired form"], False),
    ("retired '## Wiki divergences' (plural, trailing phrase) heading errors", _fixture(
        _PAIR, "Prose.\n\n## Wiki divergences in GZDoom/UZDoom\n\nDetail.\n"),
     ["retired form"], False),
    ("retired '## Fork/wiki divergences' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Fork/wiki divergences\n\nDetail.\n"), ["retired form"], False),
    ("retired '## Fork divergence summary' (trailing phrase) heading errors", _fixture(
        _PAIR, "Prose.\n\n## Fork divergence summary\n\nDetail.\n"), ["retired form"], False),
    ("retired '## Divergence from the wiki' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Divergence from the wiki\n\nDetail.\n"), ["retired form"], False),
    ("retired '## Key divergence: X' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Key divergence: `A_LightInverse`\n\nDetail.\n"),
     ["retired form"], False),
    # The near-miss pair that matters most: `Engine divergence` (retired, missing "-family") must
    # error, while `Engine-family divergence` (canonical, tested below) must not -- the space after
    # "Engine" in the retired pattern must not swallow the hyphenated canonical form.
    ("retired '## Engine divergence: X' heading errors (not '-family')", _fixture(
        _PAIR, "Prose.\n\n## Engine divergence: args[2] scaling\n\nDetail.\n"),
     ["retired form"], False),
    ("retired '## ZDoom/UZDoom/GZDoom family divergence' heading errors", _fixture(
        _PAIR, "Prose.\n\n## ZDoom/UZDoom/GZDoom family divergence\n\nDetail.\n"),
     ["retired form"], False),
    ("retired '## Behavior and fork divergence' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Behavior and fork divergence\n\nDetail.\n"), ["retired form"], False),
    ("retired '## Zandronum additions and divergences' heading errors", _fixture(
        _PAIR, "Prose.\n\n## Zandronum additions and divergences\n\nDetail.\n"),
     ["retired form"], False),
    # The other half of the near-miss pair: a heading that merely uses the word "divergence(s)" in
    # ordinary prose, not as an attempted canonical marker, must NOT error -- this is exactly the
    # class of heading the denylist-not-allowlist design decision was made to keep legal (see
    # DEPRECATED_DIVERGENCE_HEADING_RE's comment: this is the `Known divergences and implementation
    # notes` real-world case).
    ("ordinary heading using 'divergences' in prose is not a retired form", _fixture(
        _PAIR, "Prose.\n\n## Known divergences and implementation notes\n\nDetail.\n"), [], True),
    ("canonical '## Engine-family divergence' heading passes", _fixture(
        _PAIR, "Prose.\n\n## Engine-family divergence\n\nDetail.\n"), [], True),
    ("canonical '## Engine-family divergence: X' heading passes", _fixture(
        _PAIR, "Prose.\n\n## Engine-family divergence: dmflags3\n\nDetail.\n"), [], True),
    ("canonical '## Zandronum-specific: X' heading passes", _fixture(
        _PAIR, "Prose.\n\n## Zandronum-specific: netcode note\n\nDetail.\n"), [], True),
    ("canonical '## Wiki/engine divergence' heading passes", _fixture(
        _PAIR, "Prose.\n\n## Wiki/engine divergence\n\nDetail.\n"), [], True),
    ("canonical '## Wiki/engine divergence: X' heading passes", _fixture(
        _PAIR, "Prose.\n\n## Wiki/engine divergence: version availability\n\nDetail.\n"),
     [], True),
    # Step 5 Phase 1 (2026-08-19): EXEMPT_RESCAN_TOKENS closes the exemption tier's own detection
    # gap -- an acs/bcs/decorate/zscript tag no longer silences a real engine-source token with no
    # check at all. These first two confirm the rescan fires (as a warn, not a hard error) and,
    # since neither token is a GPL_ONLY_TOKENS/GPL_ZSCRIPT_RES member, that it's this new branch
    # doing the catching, not the pre-existing GPL check.
    ("TArray in a zscript-tagged fence trips the exemption-tier rescan", _fixture(
        _PAIR, "```zscript\nTArray<AActor*> targets;\n```\n"),
     ["only appears in engine source"], True),
    ("case ACSF_ in an acs-tagged fence trips the exemption-tier rescan", _fixture(
        _PAIR, "```acs\ncase ACSF_Thing:\n```\n"),
     ["only appears in engine source"], True),
    # These two are the load-bearing regression pins: step 4's false-positive fixes (Printf, ::)
    # must stay suppressed now that the exemption tier is rescanned at all.
    ("Console.Printf in a zscript fence does not trip the exemption-tier rescan", _fixture(
        _PAIR, "```zscript\nConsole.Printf(\"hi %d\", i);\n```\n"), [], True),
    ("Goto Super:: in a decorate fence does not trip the exemption-tier rescan", _fixture(
        _PAIR, "```decorate\nMissile:\n    TNT1 A 0 A_Nothing\n    Goto Super::Missile\n```\n"),
     [], True),
    # Step 5 Phase 3 (2026-08-19): check_fence_tags makes an empty fence tag a hard error -- the
    # rule this whole step exists to add, now that Phase 2 has swept the tree to zero untagged
    # fences and `text` is available as the honest neutral default.
    ("untagged fence is a hard error", _fixture(
        _PAIR, "```\nSome content.\n```\n"), ["no language tag"], False),
    # Pins that the neutral tier is genuinely neutral: a ```text fence with a real heuristic hit
    # still only warns (check_source_excerpt_and_gpl's own elif branch), and does NOT get treated
    # as an assertion-tier tag by check_fence_tags just because it now satisfies the tag-required
    # rule.
    ("text-tagged fence with a heuristic hit still only warns, not a hard error", _fixture(
        _PAIR_ZAN_VERIFIED_ONLY, "```text\nthing->health = 0;\n```\n"),
     ["Check by hand before adding one"], True),
]


def _run_self_test():
    """Fixtures for rules the tree does not yet exercise. Every rule the schema split adds is
    dormant until the marking pass stamps a real file, so without these the only evidence they
    work at all is that nothing changed."""
    failures = 0
    for name, text, expected, should_be_clean in _SELF_TESTS:
        ok_list, buf = [], io.StringIO()
        path = ROOT / "acs" / "functions" / "_selftest.md"
        with contextlib.redirect_stderr(buf):
            check_header_block(path, text, ok_list)
            check_source_excerpt_and_gpl(path, text, ok_list)
            check_fence_tags(path, text, ok_list)
        out = buf.getvalue()
        problems = []
        if bool(ok_list) == should_be_clean:
            problems.append("expected no hard errors" if should_be_clean
                            else "expected a hard error, got none")
        for substring in expected:
            if substring not in out:
                problems.append(f"missing {substring!r}")
        if not expected and should_be_clean and out.strip():
            problems.append(f"expected silence, got {out.strip()[:80]!r}")
        if problems:
            failures += 1
            print(f"SELF-TEST FAIL [{name}]: {'; '.join(problems)}", file=sys.stderr)
            if out.strip():
                print(f"    output: {out.strip()[:300]}", file=sys.stderr)
    if failures:
        print(f"lint_docs.py --self-test: {failures} of {len(_SELF_TESTS)} failed", file=sys.stderr)
        return 1
    print(f"lint_docs.py --self-test: clean -- {len(_SELF_TESTS)} fixtures", file=sys.stderr)
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        sys.exit(_run_self_test())
    sys.exit(0 if lint() else 1)


if __name__ == "__main__":
    main()
