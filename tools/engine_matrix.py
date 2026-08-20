#!/usr/bin/env python3
"""ACS/BCS cross-engine triage classifier: for a compiler-declared or documented callable name,
answers "what happens if a zt-bcc-compiled object using this name is loaded under the other
engine" -- one of seven bins:

    both                     -- present, same number/opcode, on both engines
    zandronum-only-silent    -- Zandronum-only; the miss returns a silent 0/no-op on UZDoom
    zandronum-only-loud      -- Zandronum-only; UZDoom's interpreter has no case at all for the
                                 opcode and terminates the script with "Unknown P-Code"
    zandronum-only-wrong-opcode -- Zandronum-only; the SAME raw number is bound to a genuinely
                                 different, real UZDoom opcode/special/ACSF, which runs instead
    uzdoom-only              -- present on UZDoom, absent from Zandronum
    compiler-only            -- zt-bcc declares the name but neither engine implements it
    unresolved               -- couldn't establish a real-vs-real correspondence mechanically

Four name spaces feed this, each parsed from both engines where applicable (see
`shared/AUTHORING.md`'s "Locating the engine/compiler source" for the sources.local.md
resolution this reuses via gen_inventory.source_root):

    - base PCD opcodes        Zandronum `src/p_acs.h`, UZDoom `src/playsim/p_acs.cpp`
    - ACSF extension funcs    `enum EACSFunctions` in each engine's `p_acs.cpp`
    - action specials         `DEFINE_SPECIAL(` in each engine's `actionspecials.h`
    - compiler builtins       `g_funcs[]` in `zt-bcc/src/builtin.c` (already parsed by
                               gen_inventory._parse_gfuncs, reused here)

Usage:
    python3 tools/engine_matrix.py <name>       classify one name (resolves a doc name/alias via
                                                 lookup.py first, then falls back to a raw
                                                 compiler-table name if lookup finds nothing)
    python3 tools/engine_matrix.py --all        classify every compiler-declared name; print bin
                                                 counts and, for small bins, the full name list
    python3 tools/engine_matrix.py --bin <bin>  list every name in one bin (implies --all)
    python3 tools/engine_matrix.py --files      Phase 3 marking-pass dry run: classify every doc
                                                 file into a cohort and a proposed Applies to:/
                                                 Verified against: stamp (or "judgment", awaiting
                                                 step 3.5). Writes nothing.
    python3 tools/engine_matrix.py --check      determinism/schema self-check plus regression
                                                 assertions against the counts this tool was
                                                 built and verified against (see "Verification"
                                                 below) -- exits 1 on any mismatch
    python3 tools/engine_matrix.py --stale      Phase 5 prerequisite: for every doc file whose
                                                 Verified against: names UZDoom, checks whether the
                                                 UZDoom checkout has moved past the stamped SHA for
                                                 that file's source bucket -- i.e. whether a
                                                 "complete" sweep might already be out of date. The
                                                 fifth progress query, alongside
                                                 engine_claim_progress.py's four. Writes nothing.

Base-PCD-space caveat: `zandronum-only-loud` and the base-PCD flavor of `wrong-opcode` are
real bins in this engine (129/PCD_GETINVASIONWAVE, 130/PCD_GETINVASIONSTATE = loud;
381/PCD_GETTEAMPLAYERCOUNT vs PCD_LSPEC5EX = wrong-opcode -- see
`acs/concepts/zandronum-uzdoom-compat.md`), but per that same doc none of the three are
reachable from actual zt-bcc-compiled output: zt-bcc's own PCD table is ZDoom/UZDoom-numbered
throughout, so it never emits a Zandronum-only base opcode in the first place. This tool still
computes and reports them (real, mechanically-derived, not hardcoded from the doc) because a
future zt-bcc change or hand-assembled bytecode could make them reachable -- but expect them
empty for every *compiler-declared* (specials/ACSF/gfuncs) name today. For the ACSF and
action-special name spaces specifically, `zandronum-only-loud` is structurally unreachable by
construction, not just empirically empty: UZDoom's ACSF dispatch is a single top-level `case
PCD_CALLFUNC:` whose *inner* per-index switch falls through to a silent `return 0` on a miss
(confirmed by reading `src/playsim/p_acs.cpp`'s `CallFunction`) -- there is no path from an ACSF
miss to the "no case at all" condition that produces a loud failure; only a genuinely-unhandled
*base* PCD opcode can do that.

Verification (the numbers this tool was measured against while being built, 2026-08-13, UZDoom
@5a9b0ec511): action specials 225 both / 0 zandronum-only / 0 wrong-opcode / 37 uzdoom-only;
ACSF 89 both / 87 zandronum-only-silent (all in the reserved 100-199 CALLFUNC range, 0 outside
it) / 0 wrong-opcode / 33 uzdoom-only; base PCD opcodes: exactly the 3 already-catalogued
exceptions (118 wrong-opcode/aliased, 129+130 loud, 381 wrong-opcode), everything else `both`.
`--check` asserts these did not drift.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections as S  # noqa: E402
import lookup  # noqa: E402
from gen_inventory import source_root, _parse_special_table, _parse_gfuncs, _strip_comments  # noqa: E402

ROOT = S.ROOT

BINS = [
    "both",
    "zandronum-only-silent",
    "zandronum-only-loud",
    "zandronum-only-wrong-opcode",
    "uzdoom-only",
    "compiler-only",
    "unresolved",
]

# ---------------------------------------------------------------------------
# Name space 1: base PCD opcodes -- plain incrementing enums, so position IS the opcode number.
# Zandronum's list is index 0-381 (382 entries via PCODE_COMMAND_COUNT); UZDoom's is index
# 0-384 (385 entries) -- UZDoom's is a strict superset positionally except at the three known
# exception indices, not shorter, so "no entry at index N" never happens for N <= 381.
# ---------------------------------------------------------------------------


def _parse_pcd_enum(text):
    # Comments must go first: UZDoom's enum body has at least one inline comment that itself
    # mentions a PCD_ name ("// be given names like PCD_DUMMY."), which a naive regex over raw
    # text would count as a phantom extra enum member and silently shift every later index by
    # one -- caught by --check's index-381 assertion failing during development.
    text = _strip_comments(text)
    start = text.index("PCD_NOP,")
    end = text.index("PCODE_COMMAND_COUNT", start)
    names = re.findall(r'PCD_\w+', text[start:end])
    return {i: n for i, n in enumerate(names)}


def zandronum_pcd():
    return _parse_pcd_enum(source_root("zandronum").joinpath("src", "p_acs.h").read_text())


def uzdoom_pcd():
    return _parse_pcd_enum(
        source_root("uzdoom").joinpath("src", "playsim", "p_acs.cpp").read_text()
    )


def uzdoom_pcd_case_coverage():
    """Set of PCD_* names with an actual `case PCD_X:` in UZDoom's interpreter switch -- a name
    can exist in the enum (so *some* index is reserved for it) without the interpreter having a
    matching case at all, which is exactly the "loud unknown P-Code" failure mode."""
    text = source_root("uzdoom").joinpath("src", "playsim", "p_acs.cpp").read_text()
    return set(re.findall(r'case (PCD_\w+):', text))


def classify_pcd_space():
    """Returns {name: bin} for every Zandronum base-PCD name, by index. This is the only name
    space where `zandronum-only-loud` is actually reachable -- see module docstring."""
    zan, uzd = zandronum_pcd(), uzdoom_pcd()
    covered = uzdoom_pcd_case_coverage()
    out = {}
    for idx, name in zan.items():
        uzd_name = uzd.get(idx)
        if uzd_name is None:
            # Never observed (UZDoom's enum is positionally longer, not shorter) -- fall back to
            # loud, since an index UZDoom's enum doesn't reach at all can't have a case either.
            out[name] = "zandronum-only-loud"
        elif uzd_name == name:
            out[name] = "both"
        elif uzd_name in covered:
            # Same index, different real opcode, and UZDoom's interpreter actually handles it.
            out[name] = "zandronum-only-wrong-opcode"
        else:
            out[name] = "zandronum-only-loud"
    return out


# ---------------------------------------------------------------------------
# Name space 2: action specials -- `DEFINE_SPECIAL(name, number, minargs, maxargs, ...)`.
# ---------------------------------------------------------------------------

_DEFINE_SPECIAL_RE = re.compile(r'DEFINE_SPECIAL\(\s*(\w+)\s*,\s*(-?\d+)\s*,')


def _parse_specials_by_number(path):
    text = path.read_text(errors="replace")
    out = {}
    for m in _DEFINE_SPECIAL_RE.finditer(text):
        name, num = m.group(1), int(m.group(2))
        out.setdefault(num, []).append(name)
    return out


def zandronum_specials():
    return _parse_specials_by_number(source_root("zandronum") / "src" / "actionspecials.h")


def uzdoom_specials():
    return _parse_specials_by_number(
        source_root("uzdoom") / "src" / "playsim" / "actionspecials.h"
    )


# ---------------------------------------------------------------------------
# Name space 3: ACSF extension functions -- `enum EACSFunctions { ACSF_Name[=N], ... }`.
# ---------------------------------------------------------------------------

# ACSF_ is the correct prefix throughout Zandronum's own enum, except three entries at
# src/p_acs.cpp:5547-5549 (GetControlPointInfo, SetControlPointInfo, GetSkinProperty) that
# Zandronum's own source misspells ASCF_ -- consistently, in both the enum declaration and the
# `case` labels, so it's a real (if typo'd) identifier, not just a comment. Found 2026-08-14: the
# regex used to match ACSF_ only, silently skipping those three entries when counting position,
# which under-numbered every ACSF name after them by 3 (isplayercontestingcontrolpoint.md was
# stamped 182 instead of the correct 185 before this fix). Matching both prefixes keeps the
# running-index counter accurate regardless of which one a given entry uses.
_ACSF_ENTRY_RE = re.compile(r'(?:ACSF|ASCF)_(\w+)\s*(?:=\s*(-?\d+))?\s*,')


def _parse_acsf_by_number(path, enum_name="enum EACSFunctions"):
    text = path.read_text(errors="replace")
    start = text.index(enum_name)
    end = text.index("\n};", start)
    body = text[start:end]
    out = {}
    idx = 0
    for m in _ACSF_ENTRY_RE.finditer(body + ","):
        name, explicit = m.groups()
        if explicit is not None:
            idx = int(explicit)
        out.setdefault(idx, []).append(name)
        idx += 1
    return out


def zandronum_acsf():
    return _parse_acsf_by_number(source_root("zandronum") / "src" / "p_acs.cpp")


def uzdoom_acsf():
    return _parse_acsf_by_number(source_root("uzdoom") / "src" / "playsim" / "p_acs.cpp")


# ---------------------------------------------------------------------------
# Cross-tabulation for a number-keyed name space (specials or ACSF): same shape, same three
# real outcomes (both/zandronum-only/wrong-opcode), reused for both. The `loud` bin is not
# reachable here -- see module docstring's "structurally unreachable" note.
# ---------------------------------------------------------------------------


def _classify_numbered_space(zan_by_num, uzd_by_num, silent_bin):
    out = {}
    for num, names in zan_by_num.items():
        for name in names:
            uzd_names = {n.lower() for n in uzd_by_num.get(num, [])}
            if name.lower() in uzd_names:
                out[name] = "both"
            elif uzd_names:
                out[name] = "zandronum-only-wrong-opcode"
            else:
                out[name] = silent_bin
    for num, names in uzd_by_num.items():
        if num in zan_by_num:
            continue
        for name in names:
            out.setdefault(name, "uzdoom-only")
    return out


def classify_specials_space():
    return _classify_numbered_space(
        zandronum_specials(), uzdoom_specials(), silent_bin="zandronum-only-loud"
    )


def classify_acsf_space():
    return _classify_numbered_space(
        zandronum_acsf(), uzdoom_acsf(), silent_bin="zandronum-only-silent"
    )


# ---------------------------------------------------------------------------
# Name space 4: compiler builtins -- g_funcs[] entries have no engine table of their own.
# (gen_acs_signatures's tier-C generator gained a builtin Zan/UZD cross-reference of its own on
# 2026-08-20, but via positional zt-bcc g_deds[] matching, not this module's name-based PCD
# heuristic below -- the two are independent, not layered on each other.) Classify by a
# name-presence heuristic against the PCD space only, since that's the one name space a
# dedicated-opcode compiler builtin could plausibly correspond to; absent a match there this is
# reported `compiler-only`.
# ---------------------------------------------------------------------------


def classify_gfunc_space(zt_bcc_root):
    zan_pcd = {n.lower() for n in zandronum_pcd().values()}
    uzd_pcd = {n.lower() for n in uzdoom_pcd().values()}
    out = {}
    for name in _parse_gfuncs(zt_bcc_root):
        pcd_guess = f"pcd_{name}"
        in_zan, in_uzd = pcd_guess in zan_pcd, pcd_guess in uzd_pcd
        if in_zan and in_uzd:
            out[name] = "both"
        elif in_zan:
            # Bug found 2026-08-14, Phase 3 step 3.6: this used to hardcode
            # "zandronum-only-silent", but a gfunc name absent from UZDoom's PCD space is a base
            # PCD miss, not a CALLFUNC/ACSF miss -- classify_pcd_space's own logic says that's
            # LOUD (UZDoom's interpreter has no case at all -> "Unknown P-Code", script
            # terminates), never silent. Confirmed against acs/concepts/zandronum-uzdoom-compat.md,
            # which explicitly documents GetInvasionWave/GetInvasionState (the only two names this
            # branch currently produces) hitting the loud unknown-PCD path, not a silent 0 return.
            out[name] = "zandronum-only-loud"
        elif in_uzd:
            out[name] = "uzdoom-only"
        else:
            out[name] = "compiler-only"
    return out


# ---------------------------------------------------------------------------
# Tree-wide classification: every name zt-bcc's own compiler tables declare (special table +
# g_funcs), independent of whether it has a doc file yet.
# ---------------------------------------------------------------------------


def classify_all():
    zt_bcc_root = source_root("zt-bcc")
    special = _parse_special_table(zt_bcc_root)
    specials_bins = classify_specials_space()
    acsf_bins = classify_acsf_space()
    gfunc_bins = classify_gfunc_space(zt_bcc_root)
    # zt-bcc's zcommon.bcs and each engine's own DEFINE_SPECIAL/ACSF_ declarations don't always
    # agree on casing (zcommon.bcs's "Acs_Execute" vs actionspecials.h's "ACS_Execute") -- a
    # case-sensitive dict lookup here would wrongly report ~70 real, both-engine specials as
    # "unresolved" even though classify_specials_space()'s own per-number matching (which IS
    # case-insensitive) already correctly resolved them.
    specials_bins_ci = {n.lower(): b for n, b in specials_bins.items()}
    acsf_bins_ci = {n.lower(): b for n, b in acsf_bins.items()}

    # Numeric fallback, by raw slot number (not name). zt-bcc sometimes declares a name that
    # matches NEITHER engine's own identifier at the same slot -- e.g. zt-bcc's `ZDoom_Floor`
    # occupies ACSF slot 207, which UZDoom implements and calls `Floor`. A name-only lookup above
    # finds nothing for "zdoom_floor" and would wrongly report "compiler-only" even though the
    # slot is live. Bug found 2026-08-17 during the UZDoom-retarget audit: this cost 4 names
    # (ZDoom_Floor/Round/Ceil, Strcasecmp) a false "neither engine implements this" verdict.
    zan_specials_by_num = zandronum_specials()
    uzd_specials_by_num = uzdoom_specials()
    zan_acsf_by_num = zandronum_acsf()
    uzd_acsf_by_num = uzdoom_acsf()

    def numeric_fallback(index):
        if index > 0:
            zan_by_num, uzd_by_num = zan_specials_by_num, uzd_specials_by_num
            slot = index
        else:
            # ACSF slots 100-199 are Zandronum's OWN private extension block (`ACSF_ResetMap =
            # 100` through the low-180s, then a jump to ACSF_GetTeamScore = 19620) -- densely and
            # sequentially populated with real Zandronum-only functions that do NOT correspond to
            # whatever zt-bcc's zcommon.bcs guesses lives at that same raw number (e.g. zt-bcc's
            # `-149:CheckSolidFooting` lands on Zandronum's actual slot 149, `GetPredictableValue`
            # -- unrelated). A numeric match in [100,199] is coincidental slot reuse, not a real
            # correspondence, so the fallback excludes that band. Below 100 and at/above 200 are
            # both canonical GZDoom-family numbering shared with UZDoom (0-99 confirmed via the
            # ACSF_CheckActorState=99 boundary and the commented-out 100-106 reservation note;
            # 200+ anchored by `ACSF_CheckClass = 200`) -- numeric match there is a real
            # correspondence, e.g. `Strcasecmp` (-64) genuinely exists in both engines as `stricmp`.
            slot = -index
            if 100 <= slot <= 199:
                return None
            zan_by_num, uzd_by_num = zan_acsf_by_num, uzd_acsf_by_num
        in_zan, in_uzd = slot in zan_by_num, slot in uzd_by_num
        if in_zan and in_uzd:
            return "both"
        if in_uzd:
            return "uzdoom-only"
        if in_zan:
            return "zandronum-only-loud" if index > 0 else "zandronum-only-silent"
        return None

    out = {}
    for name, entry in special.items():
        by_num = specials_bins_ci if entry["index"] > 0 else acsf_bins_ci
        b = by_num.get(name.lower())
        if b is None:
            b = numeric_fallback(entry["index"])
        if b is not None:
            out[name] = b
        else:
            # Not found under any casing in either engine's own table, AND no engine implements
            # this slot number under any name -- a zt-bcc declaration neither engine implements,
            # i.e. genuinely compiler-only/dead, not an unresolved-mapping failure.
            out[name] = "compiler-only"
    for name, b in gfunc_bins.items():
        out.setdefault(name, b)
    return out


# ---------------------------------------------------------------------------
# Single-name resolution: doc name/alias first (via lookup.py), raw compiler-table name second.
# ---------------------------------------------------------------------------


def classify_name(name):
    """Returns (canonical_name, bin, note). `note` explains how the name was resolved when that
    isn't obvious from the name alone (e.g. a doc alias, or a name only zt-bcc's compiler table
    knows about)."""
    result, _key = lookup.resolve(name, "acs")
    canonical = name
    if result is not None:
        if hasattr(result, "name"):  # InventoryResult
            canonical = result.name
        elif getattr(result, "signature", None) is not None:  # Result (function/family/tier-c)
            canonical = result.signature.name

    all_bins = classify_all()
    for candidate in (canonical, name):
        if candidate in all_bins:
            return candidate, all_bins[candidate], None
        # Case-insensitive fallback -- compiler tables and doc casing don't always agree.
        for known, b in all_bins.items():
            if known.lower() == candidate.lower():
                return known, b, None

    pcd_bins = classify_pcd_space()
    pcd_name = name if name.upper().startswith("PCD_") else f"PCD_{name.upper()}"
    if pcd_name in pcd_bins:
        return pcd_name, pcd_bins[pcd_name], "matched as a base PCD opcode, not a compiler-table name"

    return name, "unresolved", "not found in any of the four name spaces"


# ---------------------------------------------------------------------------
# --files: per-doc-file cohort assignment for the Phase 3 marking pass.
#
# Proposes an Applies to:/Verified against: stamp for every doc file the tree-wide bulk stamp
# (maintainer/tools/stamp_applies_to.py, step 3.3) will actually write. Writes nothing itself --
# this is the dry run the phase-3 plan's step 3.2 requires before any file is touched. See
# maintainer/plans/2026-08-14_uzdoom_retarget_phase3.md's "Corrected cohort table" for the
# directory-by-directory rules this implements.
# ---------------------------------------------------------------------------
import lint_docs as _L  # noqa: E402

ZAN_VERSION = "3.2.1"
ZAN_SHA = "28f736fb3"
UZD_VERSION = "5.0.0-pre"  # settled step 3.1, see shared/AUTHORING.md's "Engine scope"
_DATE_RE = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")


def recover_zandronum_date(text):
    """Best-effort date recovery for the Zandronum-side Verified against: backfill.

    Checks an already-written **Verified against:** field FIRST, ahead of Provenance:/Engine: --
    load-bearing for idempotency, not just belt-and-suspenders: 9 of the 499 files have a
    recoverable date ONLY in their legacy Engine: field (nothing in Provenance:), and step 3.3's
    stamp deletes Engine: on write. Without this branch, re-running build_file_plan() against an
    already-stamped file would find no Provenance: date and no Engine: field left to fall back to,
    wrongly conclude "undated", and move an already-correctly-stamped file into the deferred set
    on the second run -- exactly the kind of drift stamp_applies_to.py's --check exists to catch,
    so this closes the hole rather than leaving --check to discover it.

    Falls back to Provenance: (432/499 files carry one there), then to the legacy Engine: field
    (9 files) -- see the phase-3 plan's "What was measured" table. None if none of the three
    yield a date, meaning this file needs the deferred-set treatment rather than a fabricated
    date."""
    for field in _L.extract_all_fields(text, _L.VERIFIED_AGAINST_START_RE):
        entries, _problems = _L.parse_verified_against(_L._field_body(field))
        for engine, _version, _sha, date in entries:
            if engine == "Zandronum":
                return date
    for field in _L.extract_all_fields(text, _L.PROVENANCE_START_RE):
        m = _DATE_RE.search(field)
        if m:
            return m.group(1)
    for field in _L.extract_all_fields(text, _L.ENGINE_START_RE):
        m = _DATE_RE.search(field)
        if m:
            return m.group(1)
    return None


def _read_inventory_table(path):
    """-> {name.lower(): {column: value}}, using sections.split_row (the only pipe-escape-aware
    reader -- see that function's own docstring on why a naive str.split('|') silently
    misaligns columns whose Flags cell contains an escaped `|`)."""
    if not path.is_file():
        return {}
    out, cols = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = S.split_row(line)
        if cols is None:
            if "UZD" in cells:
                cols = cells
            continue
        if not cells or set("".join(cells)) <= set("-: "):
            continue
        out[cells[0].strip("`").lower()] = dict(zip(cols, cells))
    return out


class _Inventories:
    """Lazily-loaded, namespace-scoped inventory tables. Namespace-scoped is load-bearing (see
    the phase-3 plan's finding 4): a bare cells[0]==name join across every table, the way
    lookup.py's _try_inventory_row does it, false-joins decorate/classes/health.md (the actor
    class Health) to actor-properties.md's unrelated `health` property row. Each accessor here is
    called only from the one doc directory it's actually valid for."""

    def __init__(self):
        self._cache = {}

    def _get(self, rel):
        if rel not in self._cache:
            self._cache[rel] = _read_inventory_table(ROOT / rel)
        return self._cache[rel]

    def actor_actions(self):
        return self._get("decorate/inventory/actor-actions.md")

    def actor_flags(self):
        return self._get("decorate/inventory/actor-flags.md")

    def actor_properties(self):
        return self._get("decorate/inventory/actor-properties.md")

    def console_cvars(self):
        return self._get("console/inventory/cvars.md")

    def console_ccmds(self):
        return self._get("console/inventory/ccmds.md")


_INV = _Inventories()

# cohort name -> True if it is fully mechanical (a proposed Applies to: exists); False if it
# still needs step 3.5's judgment (proposal is None).
SCRIPTED_COHORTS = {
    "acs_both", "acs_zandronum_only", "acs_zandronum_only_loud", "acs_uzdoom_only",
    "acs_compiler_only", "decorate_actions_joined", "decorate_actions_unjoined_uzdoom_only",
    "decorate_notes_joined", "console_notes_yes", "zscript_blanket",
}
JUDGMENT_COHORTS = {
    "acs_unresolved", "acs_family_unresolved", "decorate_notes_joined_dash",
    "decorate_notes_unjoined", "decorate_classes_unjoined", "decorate_families_unjoined",
    "console_notes_dash", "concepts_judgment",
}


# Hand-resolved during step 3.5, for names/families classify_name() can't resolve mechanically
# (a compiler keyword/macro with no opcode of its own, or a family-file slug that was never a
# real symbol name to begin with) -- see maintainer/plans/2026-08-14_uzdoom_retarget_phase3.md's
# "Decisions taken" for how each was worked out. Keeps the knowledge in the tool, per the plan's
# own instruction, rather than only in the doc files' own prose.
ACS_NAME_OVERRIDES = {
    # strcpy: a compiler keyword/expression (no ACSF/PCD name of its own), compiles to one of
    # four opcodes chosen by destination storage class -- all four confirmed "both".
    "strcpy": ("acs_both", {"UZDoom": "yes", "Zandronum": "yes"}),
}
ACS_FAMILY_OVERRIDES = {
    # All members individually resolved via classify_name() against their real per-member
    # signatures (not the family-file slug, which was never a real symbol name).
    "actor-position-getters": ("acs_both", {"UZDoom": "yes", "Zandronum": "yes"}),  # 3/3 both
    "actor-velocity-getters": ("acs_both", {"UZDoom": "yes", "Zandronum": "yes"}),  # 3/3 both
    "cvar": ("acs_both", {"UZDoom": "yes", "Zandronum": "yes"}),  # 8/8 both
    "plane-trigger": ("acs_both", {"UZDoom": "yes", "Zandronum": "yes"}),  # 2/2 both
    # script-execution: Acs_NamedExecuteWait resolves compiler-only by bare name (a zt-bcc macro,
    # no opcode of its own) but both of its expansion components (Acs_NamedExecute, an ACSF; and
    # PCD_SCRIPTWAITNAMED, a base PCD) are "both" -- so all 4 members are effectively portable.
    "script-execution": ("acs_both", {"UZDoom": "yes", "Zandronum": "yes"}),  # 4/4 both (1 via macro)
    "database": ("acs_zandronum_only", {"UZDoom": "no", "Zandronum": "yes"}),  # 15/15 silent
    "login-account": ("acs_zandronum_only", {"UZDoom": "no", "Zandronum": "yes"}),  # 2/2 silent
    # inventory: 15/16 both; GetMaxInventory is the outlier (uzdoom-only -- dead on Zandronum,
    # live on UZDoom, the one member where the divergence runs the opposite direction from every
    # other reserved-range case in this tree). File-level claim follows the majority; the
    # member's own section carries the exception, per shared/ARCHETYPES.md's family convention.
    "inventory": ("acs_both", {"UZDoom": "yes", "Zandronum": "yes"}),
    # lump-io: 5/6 zandronum-only-silent; LumpReadArray is unreachable from zt-bcc source on
    # EITHER engine (a compiler-toolchain limitation, not an engine-family one) and is excluded
    # from this claim entirely, documented in its own section.
    "lump-io": ("acs_zandronum_only", {"UZDoom": "no", "Zandronum": "yes"}),
    # zdoom-math-stubs: 3/3 uzdoom-only -- dead on Zandronum (no enum entry, falls to
    # `default: return 0`), real and implemented on UZDoom (ACSF_Floor/Round/Ceil at 207-209).
    # Corrected 2026-08-17 (UZDoom-retarget audit): previously "N/A, neither engine implements
    # it", sourced from a now-fixed engine_matrix.py name-matching bug that missed UZDoom's
    # un-prefixed Floor/Round/Ceil identifiers at the same numeric slots. See the doc file's own
    # "Tooling note" section for the full story.
    "zdoom-math-stubs": ("acs_uzdoom_only", {"UZDoom": "yes", "Zandronum": "no"}),
}


def _classify_acs(path, section_dir):
    name = path.stem
    if name.lower() in ACS_NAME_OVERRIDES:
        cohort, applies = ACS_NAME_OVERRIDES[name.lower()]
        return cohort, applies, "hand-resolved override, see ACS_NAME_OVERRIDES"
    if section_dir == "acs/families" and name in ACS_FAMILY_OVERRIDES:
        cohort, applies = ACS_FAMILY_OVERRIDES[name]
        return cohort, applies, "hand-resolved override, see ACS_FAMILY_OVERRIDES"
    canonical, b, note = classify_name(name)
    if b == "both":
        return "acs_both", {"UZDoom": "yes", "Zandronum": "yes"}, note
    if b == "zandronum-only-silent":
        return "acs_zandronum_only", {"UZDoom": "no", "Zandronum": "yes"}, note
    if b == "zandronum-only-loud":
        # Distinct cohort from the silent case: the divergence prose describes an opposite
        # failure mode (UZDoom's interpreter has no case at all for the opcode and terminates the
        # script with "Unknown P-Code", vs. a silent 0 return) -- the two cohorts share the same
        # Applies to: direction but need different placeholder text.
        return "acs_zandronum_only_loud", {"UZDoom": "no", "Zandronum": "yes"}, note
    if b == "uzdoom-only":
        return "acs_uzdoom_only", {"UZDoom": "yes", "Zandronum": "no"}, note
    if b == "compiler-only":
        return "acs_compiler_only", {"N/A": "zt-bcc-declared, neither engine implements it"}, note
    cohort = "acs_family_unresolved" if section_dir == "acs/families" else "acs_unresolved"
    return cohort, None, note


def _classify_decorate_actions(path):
    row = _INV.actor_actions().get(path.stem.lower())
    if row is None:
        # No inventory row at all -- genuinely UZDoom-only per the 13 files confirmed in the
        # phase-3 plan's finding list (their own Engine: field already says so; this cohort
        # trusts that prior confirmation rather than re-deriving it from prose text, which is
        # exactly the kind of text-sniffing that misclassified 4 console files during planning --
        # see this module's own dev history / the plan's corrected deferred-set count).
        return "decorate_actions_unjoined_uzdoom_only", {"UZDoom": "yes", "Zandronum": "no"}, \
            "no actor-actions.md row; treated as UZDoom-only per prior confirmation, not re-derived"
    uzd = "yes" if row.get("UZD") == "yes" else "no"
    return "decorate_actions_joined", {"UZDoom": uzd, "Zandronum": "yes"}, f"actor-actions.md row, UZD={row.get('UZD')!r}"


def _classify_decorate_notes(path):
    name = path.stem.lower()
    for table_name, table in (("actor-flags.md", _INV.actor_flags()),
                               ("actor-properties.md", _INV.actor_properties())):
        row = table.get(name)
        if row is None:
            continue
        if row.get("UZD") == "yes":
            return "decorate_notes_joined", {"UZDoom": "yes", "Zandronum": "yes"}, f"{table_name} row, UZD=yes"
        # UZD: -- on a curated note is not trustworthy on its own (the phase-3 plan's finding 1
        # proved the extractor itself can be wrong) -- needs step 3.5's per-file check, not a
        # mechanical UZDoom=no stamp.
        return "decorate_notes_joined_dash", None, f"{table_name} row, UZD=--  needs 3.5 verification"
    return "decorate_notes_unjoined", None, "no flags/properties row (checked both tables)"


def _classify_console_notes(path):
    name = path.stem.lower()
    row = _INV.console_cvars().get(name) or _INV.console_ccmds().get(name)
    if row is None:
        return "console_notes_dash", None, "not found in cvars.md or ccmds.md"
    if row.get("UZD") == "yes":
        return "console_notes_yes", {"UZDoom": "yes", "Zandronum": "yes"}, "inventory row, UZD=yes"
    return "console_notes_dash", None, "inventory row, UZD=--  needs 3.5 verification against UZDoom source"


# Hand-resolved during step 3.5: every name here was checked against UZDoom's
# wadsrc/static/zscript source directly (grepped for `class <Name> ` / `class <Name>:`), since
# neither carries an ACSF/PCD/g_funcs identity for engine_matrix's own name spaces to resolve.
# All 11 are standard DECORATE/ZScript base classes (not Zandronum extensions), confirmed present
# under the same name on both engines. powerprotection.md is deliberately absent -- still
# genuinely unresolved (undated, deferred to Phase 5), not an oversight.
DECORATE_CLASS_OVERRIDES = {
    name: {"UZDoom": "yes", "Zandronum": "yes"}
    for name in (
        "custominventory", "health", "inventory", "key", "mapmarker", "mapspot", "playerpawn",
        "powerup", "randomspawner", "switchabledecoration", "teleportfog",
    )
}
# face-pointer: A_FaceTarget/A_FaceTracer/A_FaceMaster all confirmed UZD: yes in
# decorate/inventory/actor-actions.md. weapon-light: A_Light/A_Light0/A_Light1/A_Light2/
# A_LightInverse likewise all UZD: yes (the file's own header already noted A_Light was
# spot-checked against UZDoom before this pass; the other four confirm the same via the
# inventory, not re-derived).
DECORATE_FAMILY_OVERRIDES = {
    "face-pointer": {"UZDoom": "yes", "Zandronum": "yes"},
    "weapon-light": {"UZDoom": "yes", "Zandronum": "yes"},
}


def classify_doc_file(path):
    """-> (cohort, applies_or_None, note). `applies` is a ready-to-stamp Applies to: dict (or the
    N/A form) for a SCRIPTED_COHORTS member, None for a JUDGMENT_COHORTS member awaiting step
    3.5. Never raises on an unrecognized directory -- returns cohort "uncategorized" so a new
    section/directory added later shows up as something to triage, not a silent crash."""
    rel = path.relative_to(ROOT)
    parts = rel.parts

    if parts[0] == "zscript" and parts[1] in ("classes", "concepts"):
        return "zscript_blanket", {"UZDoom": "yes", "Zandronum": "no"}, \
            "ZScript does not exist in Zandronum at all"
    if parts[0] == "acs" and parts[1] in ("functions", "families"):
        return _classify_acs(path, f"{parts[0]}/{parts[1]}")
    if parts[0] == "decorate" and parts[1] == "actions":
        return _classify_decorate_actions(path)
    if parts[0] == "decorate" and parts[1] == "notes":
        return _classify_decorate_notes(path)
    if parts[0] == "decorate" and parts[1] == "classes":
        if path.stem in DECORATE_CLASS_OVERRIDES:
            return "decorate_classes_unjoined", DECORATE_CLASS_OVERRIDES[path.stem], \
                "hand-resolved override, see DECORATE_CLASS_OVERRIDES -- confirmed present in " \
                "UZDoom's wadsrc/static/zscript source by name"
        return "decorate_classes_unjoined", None, "class name, not a flag/property/action -- namespace-scoped, never joined"
    if parts[0] == "decorate" and parts[1] == "families":
        if path.stem in DECORATE_FAMILY_OVERRIDES:
            return "decorate_families_unjoined", DECORATE_FAMILY_OVERRIDES[path.stem], \
                "hand-resolved override, see DECORATE_FAMILY_OVERRIDES -- every member confirmed " \
                "present on both engines via the actor-actions inventory"
        return "decorate_families_unjoined", None, "family topic name, not name-resolvable"
    if parts[0] == "console" and parts[1] == "notes":
        return _classify_console_notes(path)
    if len(parts) >= 2 and parts[-2] == "concepts":
        return "concepts_judgment", None, "concept page, not name-resolvable"
    return "uncategorized", None, f"no cohort rule for {rel} -- add one before trusting phase-3 coverage"


def iter_cohort_files():
    """Every doc file the marking pass has to decide something for -- i.e. every file
    lint_docs.py would check header/engine claims on (CALLABLE/TABLE_NOTES/CONCEPT archetypes),
    across every section, in section-dir order. Deliberately mirrors lint_docs.lint_section's own
    directory walk rather than a blanket rglob, so this never picks up a TABLE_INVENTORY file (no
    per-file engine claim to stamp) or shared/concepts (walked separately, same as lint_docs.py
    does)."""
    for section in S.SECTIONS.values():
        for dir_rel, archetype in section["dirs"].items():
            if archetype not in S.HEADER_BLOCK_ARCHETYPES:
                continue
            dir_path = ROOT / dir_rel
            if not dir_path.is_dir():
                continue
            for path in sorted(dir_path.glob("*.md")):
                yield path
    shared_dir = ROOT / S.SHARED_CONCEPTS_DIR
    if shared_dir.is_dir():
        for path in sorted(shared_dir.glob("*.md")):
            yield path


def build_file_plan():
    """-> list of dicts, one per doc file: path, cohort, kind (scripted/judgment/uncategorized),
    applies, zan_date_recovered, needs_zandronum_date, deferred (bool), note. The single source of
    truth both `--files` (reporting) and maintainer/tools/stamp_applies_to.py (writing) build on,
    so the dry run and the actual stamp can never silently disagree."""
    plan = []
    for path in iter_cohort_files():
        text = path.read_text(encoding="utf-8")
        cohort, applies, note = classify_doc_file(path)
        if cohort in SCRIPTED_COHORTS:
            kind = "scripted"
        elif cohort in JUDGMENT_COHORTS:
            kind = "judgment"
        else:
            kind = "uncategorized"
        zan_date = recover_zandronum_date(text)
        # Does this file's eventual stamp need a Zandronum Verified against: entry? Known for
        # SCRIPTED_COHORTS from `applies`; for a JUDGMENT_COHORTS file the direction isn't decided
        # yet, so this conservatively presumes Zandronum=yes (matches this tree's actual
        # composition -- the large majority of judgment-cohort files describe something that also
        # exists on Zandronum) and may shrink once step 3.5 resolves the real direction, exactly
        # as the phase-3 plan's "Decisions taken" section notes.
        if applies is not None:
            needs_zan_date = applies.get("Zandronum") == "yes"
        else:
            needs_zan_date = True
        deferred = needs_zan_date and zan_date is None
        plan.append({
            "path": path.relative_to(ROOT),
            "cohort": cohort,
            "kind": kind,
            "applies": applies,
            "zan_date": zan_date,
            "needs_zan_date": needs_zan_date,
            "deferred": deferred,
            "note": note,
        })
    return plan


def _print_files_report(plan):
    by_cohort = {}
    for entry in plan:
        by_cohort.setdefault(entry["cohort"], []).append(entry)
    total = len(plan)
    deferred = [e for e in plan if e["deferred"]]
    stamped_now = [e for e in plan if e["kind"] == "scripted" and not e["deferred"]]
    print(f"engine_matrix.py --files: {total} doc files")
    print()
    for cohort in sorted(by_cohort):
        entries = by_cohort[cohort]
        d = sum(1 for e in entries if e["deferred"])
        print(f"  {cohort:42} {len(entries):4d}  (deferred: {d})")
    print()
    print(f"  scripted, stamped in 3.3 now:  {len(stamped_now)}")
    print(f"  deferred (no recoverable Zandronum date): {len(deferred)}")
    print(f"  judgment/uncategorized, not yet stamped:  "
          f"{total - len(stamped_now) - len(deferred)}")
    print(f"  reconciliation: {len(stamped_now)} + {len(deferred)} + "
          f"{total - len(stamped_now) - len(deferred)} = {total}")
    uncategorized = [e for e in plan if e["kind"] == "uncategorized"]
    if uncategorized:
        print("\n  UNCATEGORIZED (no cohort rule -- fix before trusting this report):")
        for e in uncategorized:
            print(f"    {e['path']}")


# ---------------------------------------------------------------------------
# --stale: Phase 5's staleness query (maintainer/plans/2026-08-08_uzdoom_retarget_plan.md's
# "Phase 5" section calls this a hard prerequisite, built before the sweep starts). SHAs are
# never retro-updated as the sweep runs across many sessions, so without this a "complete" sweep
# is a set of claims of unknown freshness -- exactly the failure the SHA stamp exists to prevent.
#
# Deliberately coarse: mapped by doc *directory* (the same parts[0]/parts[1] dispatch
# classify_doc_file() already uses), not by the individual engine symbol a file documents. A
# file's own free-form **Bucket:** field (e.g. "DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Warp) in
# `src/thingdef/thingdef_codeptr.cpp`") is prose written for a human, not a parseable path -- over
# 140 distinct phrasings exist across the tree, most naming Zandronum's paths (which differ from
# UZDoom's: DECORATE actions moved from `src/thingdef/thingdef_codeptr.cpp` to
# `src/playsim/p_actionfunctions.cpp` + `src/scripting/thingdef*.cpp`, and further to ZScript
# under `wadsrc/static/zscript/` for many). A coarse per-directory bucket errs toward reporting
# more files stale than strictly necessary, never fewer -- the safe direction for a query whose
# job is "don't silently trust an old claim".
# ---------------------------------------------------------------------------
import subprocess  # noqa: E402

BUCKET_PATHS = {
    ("acs", "functions"): ("src/playsim/p_acs.cpp", "src/playsim/actionspecials.h"),
    ("acs", "families"): ("src/playsim/p_acs.cpp", "src/playsim/actionspecials.h"),
    ("acs", "concepts"): ("src/playsim/p_acs.cpp", "src/playsim/actionspecials.h"),
    ("decorate", "actions"): (
        "src/playsim/p_actionfunctions.cpp", "src/scripting/thingdef.cpp",
        "src/scripting/thingdef_data.cpp", "wadsrc/static/zscript/",
    ),
    ("decorate", "notes"): ("src/scripting/thingdef_properties.cpp", "src/scripting/thingdef_data.cpp"),
    ("decorate", "classes"): ("wadsrc/static/zscript/",),
    ("decorate", "families"): ("wadsrc/static/zscript/",),
    ("decorate", "concepts"): ("wadsrc/static/zscript/", "src/scripting/"),
    ("console", "notes"): ("src/",),
    ("console", "concepts"): ("src/",),
    ("zscript", "classes"): ("wadsrc/static/zscript/",),
    ("zscript", "concepts"): ("wadsrc/static/zscript/",),
    ("mapinfo", "concepts"): ("src/",),
    ("cvarinfo", "concepts"): ("src/",),
    ("gldefs", "concepts"): ("src/",),
    ("sbarinfo", "concepts"): ("src/",),
    ("sprites", "concepts"): ("src/",),
    ("shared", "concepts"): ("src/",),
}


def bucket_paths_for(rel_path):
    """-> tuple of UZDoom-checkout-relative paths to check for staleness, or () if this
    directory has no bucket rule yet (reported separately, never silently skipped)."""
    parts = rel_path.parts
    if len(parts) >= 2 and parts[-2] == "concepts":
        return BUCKET_PATHS.get((parts[0], "concepts"), ())
    if len(parts) >= 2:
        return BUCKET_PATHS.get((parts[0], parts[1]), ())
    return ()


def _uzdoom_verified_entry(text):
    """-> (version, sha, date) from this file's Verified against: field, or None if it carries
    no UZDoom entry yet (nothing to check staleness against)."""
    fields = _L.extract_all_fields(text, _L.VERIFIED_AGAINST_START_RE)
    if not fields:
        return None
    entries, _problems = _L.parse_verified_against(_L._field_body(fields[0]))
    for engine, version, sha, date in entries:
        if engine == "UZDoom":
            return version, sha, date
    return None


def _git_log_since(uzdoom_root, sha, paths):
    """-> count of commits in (sha, HEAD] touching any of paths, or None if the SHA itself
    isn't reachable (rewritten history, wrong checkout) -- distinct from 0, which means clean."""
    cmd = ["git", "-C", str(uzdoom_root), "log", "--oneline", f"{sha}..HEAD", "--", *paths]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    return len(lines)


def run_stale():
    """-> list of dicts (one per UZDoom-stamped doc file), each with path/sha/date/paths/
    commits_since (None = SHA unreachable, i.e. check this by hand)."""
    uzdoom_root = source_root("uzdoom")
    out = []
    for path in iter_cohort_files():
        text = path.read_text(encoding="utf-8")
        entry = _uzdoom_verified_entry(text)
        if entry is None:
            continue
        version, sha, date = entry
        rel = path.relative_to(ROOT)
        paths = bucket_paths_for(rel)
        commits_since = _git_log_since(uzdoom_root, sha, paths) if paths else None
        out.append({
            "path": rel, "version": version, "sha": sha, "date": date,
            "paths": paths, "commits_since": commits_since,
        })
    return out


def _print_stale_report(entries):
    print(f"engine_matrix.py --stale: {len(entries)} doc files carry a UZDoom Verified against: stamp")
    if not entries:
        print("  (none yet -- Phase 5 hasn't stamped any file. This query becomes useful once it has.)")
        return
    no_bucket = [e for e in entries if not e["paths"]]
    unreachable = [e for e in entries if e["paths"] and e["commits_since"] is None]
    stale = [e for e in entries if e["commits_since"] is not None and e["commits_since"] > 0]
    fresh = [e for e in entries if e["commits_since"] == 0]
    print(f"  fresh (no commits since stamp):  {len(fresh)}")
    print(f"  stale (commits landed since):    {len(stale)}")
    print(f"  SHA unreachable (check by hand): {len(unreachable)}")
    print(f"  no bucket-path rule (add one):   {len(no_bucket)}")
    if stale:
        print("\n  STALE:")
        for e in sorted(stale, key=lambda e: -e["commits_since"]):
            print(f"    {e['path']}  ({e['commits_since']} commits since @{e['sha']}, stamped {e['date']})")
    if unreachable:
        print("\n  SHA UNREACHABLE:")
        for e in unreachable:
            print(f"    {e['path']}  (@{e['sha']})")
    if no_bucket:
        print("\n  NO BUCKET RULE:")
        for e in no_bucket:
            print(f"    {e['path']}")


def main():
    args = sys.argv[1:]
    check = "--check" in args
    args = [a for a in args if a != "--check"]

    if check:
        return _run_check()

    if "--stale" in args:
        _print_stale_report(run_stale())
        return

    if "--files" in args:
        plan = build_file_plan()
        _print_files_report(plan)
        return

    show_all = "--all" in args
    args = [a for a in args if a != "--all"]
    bin_filter = None
    if "--bin" in args:
        i = args.index("--bin")
        bin_filter = args[i + 1]
        args = args[:i] + args[i + 2:]
        show_all = True

    if show_all:
        all_bins = classify_all()
        if bin_filter:
            if bin_filter not in BINS:
                print(f"unknown bin {bin_filter!r}; choices: {', '.join(BINS)}", file=sys.stderr)
                sys.exit(1)
            for name in sorted(n for n, b in all_bins.items() if b == bin_filter):
                print(name)
            return
        counts = {b: 0 for b in BINS}
        for b in all_bins.values():
            counts[b] += 1
        for b in BINS:
            print(f"{b}: {counts[b]}")
        return

    if not args:
        print(__doc__)
        sys.exit(1)

    name, b, note = classify_name(args[0])
    line = f"{name}: {b}"
    if note:
        line += f"  ({note})"
    print(line)


def _run_check():
    ok = True

    def assert_eq(label, actual, expected):
        nonlocal ok
        if actual != expected:
            print(f"CHECK FAILED: {label} = {actual}, expected {expected}", file=sys.stderr)
            ok = False

    specials_bins = classify_specials_space()
    specials_counts = {b: 0 for b in BINS}
    for b in specials_bins.values():
        specials_counts[b] += 1
    assert_eq("action specials 'both'", specials_counts["both"], 225)
    assert_eq("action specials 'zandronum-only-loud'", specials_counts["zandronum-only-loud"], 0)
    assert_eq(
        "action specials 'zandronum-only-wrong-opcode'",
        specials_counts["zandronum-only-wrong-opcode"],
        0,
    )
    assert_eq("action specials 'uzdoom-only'", specials_counts["uzdoom-only"], 37)

    acsf_bins = classify_acsf_space()
    acsf_counts = {b: 0 for b in BINS}
    for b in acsf_bins.values():
        acsf_counts[b] += 1
    assert_eq("ACSF 'both'", acsf_counts["both"], 89)
    assert_eq("ACSF 'zandronum-only-silent'", acsf_counts["zandronum-only-silent"], 90)
    assert_eq("ACSF 'zandronum-only-wrong-opcode'", acsf_counts["zandronum-only-wrong-opcode"], 0)
    assert_eq("ACSF 'uzdoom-only'", acsf_counts["uzdoom-only"], 33)

    zan_acsf = zandronum_acsf()
    reserved = [num for num, names in zan_acsf.items() if acsf_bins.get(names[0]) == "zandronum-only-silent"]
    assert_eq("ACSF zandronum-only-silent all inside 100-199", all(100 <= n <= 199 for n in reserved), True)

    # Regression pin for the loud/silent gfunc-space bug found 2026-08-14 (Phase 3 step 3.6): a
    # gfunc name present only in Zandronum's PCD space must classify as zandronum-only-loud, not
    # the ACSF-space-only "silent" bin -- acs/concepts/zandronum-uzdoom-compat.md confirms these
    # two specific names hit the loud unknown-PCD path.
    gfunc_bins = classify_gfunc_space(source_root("zt-bcc"))
    assert_eq("gfunc space 'getinvasionwave' bin", gfunc_bins.get("getinvasionwave"), "zandronum-only-loud")
    assert_eq("gfunc space 'getinvasionstate' bin", gfunc_bins.get("getinvasionstate"), "zandronum-only-loud")
    assert_eq("gfunc space has no zandronum-only-silent entries",
              [n for n, b in gfunc_bins.items() if b == "zandronum-only-silent"], [])

    pcd_bins = classify_pcd_space()
    pcd_counts = {b: 0 for b in BINS}
    for b in pcd_bins.values():
        pcd_counts[b] += 1
    assert_eq("PCD 'both'", pcd_counts["both"], 378)
    assert_eq("PCD 'zandronum-only-loud'", pcd_counts["zandronum-only-loud"], 2)
    assert_eq("PCD 'zandronum-only-wrong-opcode'", pcd_counts["zandronum-only-wrong-opcode"], 2)
    assert_eq("PCD_GETINVASIONWAVE bin", pcd_bins.get("PCD_GETINVASIONWAVE"), "zandronum-only-loud")
    assert_eq("PCD_GETINVASIONSTATE bin", pcd_bins.get("PCD_GETINVASIONSTATE"), "zandronum-only-loud")
    assert_eq("PCD_GETTEAMPLAYERCOUNT bin", pcd_bins.get("PCD_GETTEAMPLAYERCOUNT"), "zandronum-only-wrong-opcode")
    assert_eq("PCD_ISMULTIPLAYER bin", pcd_bins.get("PCD_ISMULTIPLAYER"), "zandronum-only-wrong-opcode")

    # Determinism: classify_all() run twice must agree.
    a, b = classify_all(), classify_all()
    assert_eq("classify_all() determinism", a, b)

    # --files: regression counts against the phase-3 plan's step 3.2 dry run (measured
    # 2026-08-14). A drift here means either the doc tree changed (expected -- update the
    # assertions and note why in the plan file) or a cohort/join rule regressed (not expected --
    # investigate before updating the number).
    plan1 = build_file_plan()
    plan2 = build_file_plan()
    assert_eq("build_file_plan() determinism",
              [(e["path"], e["cohort"], e["applies"], e["deferred"]) for e in plan1],
              [(e["path"], e["cohort"], e["applies"], e["deferred"]) for e in plan2])
    assert_eq("--files total doc files", len(plan1), 518)
    uncategorized = [e for e in plan1 if e["kind"] == "uncategorized"]
    assert_eq("--files uncategorized files", [str(e['path']) for e in uncategorized], [])
    stamped_now = sum(1 for e in plan1 if e["kind"] == "scripted" and not e["deferred"])
    deferred = sum(1 for e in plan1 if e["deferred"])
    judgment = len(plan1) - stamped_now - deferred
    assert_eq("--files scripted+stamped-now", stamped_now, 412)
    # Updated 2026-08-16 (C4 wave 1): 3 files (acs-old-object-format.md, integer-arithmetic.md,
    # operators.md) gained a real Zandronum verification date this wave, moving them out of
    # "deferred" -- expected drift per this function's own doc-tree-changed case above, not a
    # cohort/join regression. acse-object-format.md stayed deferred (UZDoom-only stamp, no
    # Zandronum date recovered yet).
    # Updated 2026-08-17 (C5 pilot): console/notes/fov.md migrated off the legacy Engine: field
    # and gained a real Zandronum verification date, moving it out of "deferred" too.
    # Updated 2026-08-17 (C5 wave 1): 12 more deferred-set files migrated off the legacy Engine:
    # field, moving stamped_now/deferred/judgment per build_file_plan()'s own classification
    # (verified directly via a one-off build_file_plan() query, not hand-derived): 8 of the 12
    # landed in cohort acs_both/kind scripted (changelevel.md, changeskill.md, changesky.md,
    # gameskill.md, pickactor.md, sector_set3dfloor.md, sector_setcolor.md, setuservariable.md);
    # the other 4 (acs/families/spawning.md, acs/concepts/zandronum-uzdoom-compat.md,
    # acs/functions/checkautomap.md, acs/functions/line_setportal.md) land in kind=judgment
    # regardless of stamp completeness -- family/concept-cohort and acs_unresolved-cohort files
    # are judgment-kind by archetype, not by verification status. Of the 12,
    # line_setportal.md alone stays "deferred" (Applies to: UZDoom=yes/Zandronum=no, so it never
    # minted a Zandronum date) -- everything else now has a real Zandronum date.
    # Updated 2026-08-17 (C5 wave 2): 12 more deferred-set files migrated (verified via
    # build_file_plan() directly, same discipline as wave 1). 9 landed kind=scripted
    # (teleport_nofog.md, thing_setconversation.md, am_cheat.md, am_drawmapback.md, am_rotate.md,
    # am_showtriggerlines.md, autoaim.md, menu_load.md, menu_save.md); 3 landed kind=judgment
    # (cl_ticsperupdate.md, handicap.md, instagib.md -- all three Applies to: UZDoom=no/
    # Zandronum=yes). All 12 minted a real Zandronum date this wave (none stayed "deferred").
    # Updated 2026-08-17 (C5 wave 3): 13 more deferred-set files migrated (verified via
    # build_file_plan() directly). 5 landed kind=scripted (quickload.md, quicksave.md,
    # sv_aircontrol.md, sv_smartaim.md, teamdamage.md); 8 landed kind=judgment
    # (sv_coop_damagefactor.md, sv_defaultdmflags.md, sv_forbidvoteflags.md,
    # sv_forcelogintojoin.md, sv_forcerespawntime.md, sv_maxclients.md, sv_maxpacketsize.md,
    # sv_respawndelaytime.md -- all Applies to: UZDoom=no/Zandronum=yes). All 13 minted a real
    # Zandronum date this wave (none stayed "deferred").
    # Updated 2026-08-17 (C5 wave 4, the LAST C5 wave - deferred_set.txt is now fully empty per
    # engine_claim_progress.py's "deferred on purpose" reaching 0): 11 more files migrated. 2
    # landed kind=scripted (cvarinfo/concepts/declaration-syntax.md,
    # decorate/classes/powerprotection.md); 9 landed kind=judgment (concept/notes-cohort files,
    # judgment-kind by archetype regardless of stamp completeness, matching the wave-1 pattern).
    # Of the 11, only shared/concepts/persistent-storage-engine-divergence.md stayed "deferred" in
    # this narrower per-file sense (Applies to: UZDoom=yes/Zandronum=yes at the file level, but the
    # agent deliberately did not mint a fresh Zandronum date this pass, deferring to
    # acs/families/database.md's own stamp instead - by design, not an oversight). The other 2
    # files still counted "deferred" here (acse-object-format.md, acs/functions/line_setportal.md)
    # both predate this wave and were already understood (see the wave-1/C4-wave-1 comments above)
    # - this metric is intentionally narrower than engine_claim_progress.py's "deferred on
    # purpose" (deferred_set.txt membership), which IS now 0, meaning Phase 5's C5 cohort is fully
    # closed even though these 3 files still show up here for legitimate, already-documented
    # reasons.
    assert_eq("--files deferred (no recoverable Zandronum date)", deferred, 3)
    assert_eq("--files judgment/uncategorized", judgment, 103)
    by_cohort = {}
    for e in plan1:
        by_cohort[e["cohort"]] = by_cohort.get(e["cohort"], 0) + 1
    # 2026-08-17 (UZDoom-retarget audit): acs_compiler_only 11->10, acs_uzdoom_only 8->9 --
    # zdoom-math-stubs.md moved cohorts after fixing a classify_all() name-matching bug and its
    # own ACS_FAMILY_OVERRIDES entry (see that entry's comment and the doc's "Tooling note").
    # 2026-08-18 (WIKI_FETCH_QUEUE.md batch, 19 new tier-A/B files, one per intake HTML page):
    # acs_zandronum_only 36->53 (+17 new Zandronum-only extension functions), acs_unresolved
    # 2->4 (+2: checkscript.md/setmapusedstatus.md, both real Zandronum functions with no
    # zt-bcc table entry under any name at their numeric slot -- same class as the pre-existing
    # checkautomap.md already in this cohort, confirmed by direct numeric-slot inspection of
    # zcommon.bcs before writing either file, not just a name-search miss).
    expected_cohorts = {
        "acs_both": 148, "acs_compiler_only": 10, "acs_family_unresolved": 1,
        "acs_unresolved": 4, "acs_uzdoom_only": 9, "acs_zandronum_only": 53,
        "acs_zandronum_only_loud": 2,
        "concepts_judgment": 49, "console_notes_dash": 34, "console_notes_yes": 30,
        "decorate_actions_joined": 111, "decorate_actions_unjoined_uzdoom_only": 13,
        "decorate_classes_unjoined": 12, "decorate_families_unjoined": 2,
        "decorate_notes_joined": 2, "decorate_notes_joined_dash": 1,
        "decorate_notes_unjoined": 3, "zscript_blanket": 34,
    }
    assert_eq("--files cohort counts", by_cohort, expected_cohorts)

    # --stale: schema/determinism only -- deliberately NOT a pinned count. Unlike --files' cohort
    # counts (which only move when the doc tree's structure changes), the number of UZDoom-stamped
    # files grows on every single file Phase 5 touches across a 423-file sweep; pinning it here
    # would make this assertion fail on every wave for the expected reason (progress), which is
    # exactly the kind of "update the number and don't ask why" churn a regression pin exists to
    # avoid. Instead assert the shape stays sound: every stamped file resolves to a real
    # commits_since (int) or a documented reason it can't (None only for an unreachable SHA or a
    # missing bucket rule, never silently). Also exercises the actual machinery
    # (bucket_paths_for, _git_log_since) against a synthetic old SHA and a synthetic bogus SHA,
    # both known-stable rather than tied to whatever commit UZDoom's checkout is on.
    stale_entries = run_stale()
    assert_eq("--stale: at least the C0a pilot is stamped", len(stale_entries) >= 1, True)
    for e in stale_entries:
        if e["paths"] and e["commits_since"] is None:
            ok = False
            print(f"CHECK FAILED: --stale: {e['path']} has a bucket rule but an unresolved "
                  f"SHA @{e['sha']} -- investigate, don't silently ignore", file=sys.stderr)
        if not e["paths"]:
            ok = False
            print(f"CHECK FAILED: --stale: {e['path']} has no bucket-path rule -- add one to "
                  "BUCKET_PATHS", file=sys.stderr)
    assert_eq(
        "bucket_paths_for: acs/functions maps to a real bucket",
        bucket_paths_for(Path("acs/functions/foo.md")),
        ("src/playsim/p_acs.cpp", "src/playsim/actionspecials.h"),
    )
    assert_eq(
        "bucket_paths_for: unrecognized directory returns empty, not a crash",
        bucket_paths_for(Path("shared/nonexistent/foo.md")), (),
    )
    uzdoom_root = source_root("uzdoom")
    old_sha_commits = _git_log_since(uzdoom_root, "7346288bf5", ("src/playsim/p_acs.cpp",))
    assert_eq("_git_log_since: old SHA has commits since", old_sha_commits is not None and old_sha_commits > 0, True)
    assert_eq("_git_log_since: bogus SHA is unreachable, not a false zero",
              _git_log_since(uzdoom_root, "0000000000", ("src/playsim/p_acs.cpp",)), None)

    if ok:
        print("engine_matrix.py --check: clean")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
