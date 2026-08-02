# `bool CheckActorState(int tid, str statename [, bool exact])`

Checks whether an actor has a specified state. Per the ZDoom wiki, if `tid` is 0, the check is performed on the activator; `statename` is the state name to check for; and `exact` controls whether partial state name matches are accepted (default `false`).

**Bucket:** extension function (index -99, negative dispatch).

## Not implemented in this fork

**This function is declared in the zt-bcc source's `lib/zcommon.bcs:1730` but has no case in the Zandronum engine's `EACSFunctions` enum** (`src/p_acs.cpp:5360-5558`). The enum includes entries 1–92, then jumps directly from `ACSF_Warp = 92` to `ACSF_GetActorFloorTexture = 204` to `ACSF_ResetMap = 100`. **Entries 93–99 were skipped entirely during ZDoom's original development — a deliberate gap the enum's own comment documents: "/* Zandronum's - these must be skipped when we reach 99! */"** 

When called, `CheckActorState` falls through the dispatch to the default case (`src/p_acs.cpp:9059-9063`), which breaks and returns `0` without executing any state-check logic. **Every call to `CheckActorState` silently returns `0`, regardless of input.** This is indistinguishable from the actor genuinely lacking the state vs. the activator not existing (both would return `false` if implemented) — a potentially hazardous silent no-op.

The ZDoom wiki page describes correct semantics for ZDoom/GZDoom; porting code that relies on `CheckActorState` to Zandronum requires finding an alternate verification mechanism (e.g., reading a custom user variable or actor pointer that the target sets on state transitions) rather than a direct port of this call.

The same 93–99 gap affects `CheckProximity` (-98, documented separately in [checkproximity.md](checkproximity.md)), `SpawnParticle` (-96, documented in the [spawning family](../families/spawning.md)), and `GetMaxInventory` (-93, documented in the [inventory family](../families/inventory.md)) — four sibling functions, all unimplemented and all silently returning `0`.

**Provenance:** wiki page `CheckActorState - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-30, `oldid=45137`) + verified against `zcommon.bcs:1730` and Zandronum engine source (no case found in `src/p_acs.cpp` enum, 93–99 gap confirmed, default return verified at `src/p_acs.cpp:9059-9063`). **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD, which is 3.3-alpha. A function absent from the newer snapshot is necessarily absent from the older target version, so the gap is stable). **Tier:** A.
