# `bool CheckActorState(int tid, str statename [, bool exact])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** wiki page `CheckActorState - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-30, `https://zdoom.org/w/index.php?title=CheckActorState&oldid=45137`) + verified against `zcommon.bcs:1730` and Zandronum engine source (no case found in `src/p_acs.cpp` enum, 93–99 gap confirmed, default return verified at `src/p_acs.cpp:9059-9063`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -99, negative dispatch).

Checks whether an actor has a specified state. Per the ZDoom wiki, if `tid` is 0, the check is performed on the activator; `statename` is the state name to check for; and `exact` controls whether partial state name matches are accepted (default `false`). Confirmed present and matching this description in UZDoom's `src/playsim/p_acs.cpp`, `case ACSF_CheckActorState:` — resolves the actor via the standard `SingleActorFromTID(tid, ..., activator)` convention used tree-wide for tid-0-means-activator, looks up the state by name via `FindStateByString(statename, exact)`, and returns `false` if either the actor or the state name can't be resolved.

## Zandronum-specific: unimplemented function

**This function is declared in the zt-bcc source's `lib/zcommon.bcs:1730` but has no case in the Zandronum engine's `EACSFunctions` enum** (`src/p_acs.cpp:5360-5558`). The enum includes entries 1–92, then jumps directly from `ACSF_Warp = 92` to `ACSF_GetActorFloorTexture = 204` to `ACSF_ResetMap = 100`. **Entries 93–99 were skipped entirely during ZDoom's original development — a deliberate gap the enum's own comment documents: "/* Zandronum's - these must be skipped when we reach 99! */"** 

When called, `CheckActorState` falls through the dispatch to the default case (`src/p_acs.cpp:9059-9063`), which breaks and returns `0` without executing any state-check logic. **Every call to `CheckActorState` silently returns `0`, regardless of input.** This is indistinguishable from the actor genuinely lacking the state vs. the activator not existing (both would return `false` if implemented) — a potentially hazardous silent no-op.

The ZDoom wiki page describes correct semantics for ZDoom/GZDoom; porting code that relies on `CheckActorState` to Zandronum requires finding an alternate verification mechanism (e.g., reading a custom user variable or actor pointer that the target sets on state transitions) rather than a direct port of this call.

The same 93–99 gap affects `CheckProximity` (-98, documented separately in [checkproximity.md](checkproximity.md)), `SpawnParticle` (-96, documented in the [spawning family](../families/spawning.md)), and `GetMaxInventory` (-93, documented in the [inventory family](../families/inventory.md)) — four sibling functions, all unimplemented and all silently returning `0`.
