# `fixed GetActorCeilingZ(int tid)`

**Tier:** A.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master`/`3.3-alpha` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`).
**Provenance:** wiki page `GetActorCeilingZ - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=35971`) + source-verified against `p_acs.cpp:12025-12030, 4445-4456`, `p_map.cpp:228-252` (3D-floor clamping in `P_FindFloorCeiling`), `p_map.cpp:6013-6044` (`P_AdjustFloorCeil` refresh behavior), and `actor.h:989` (ceilingz member comment). The 3D-floor-awareness and cached-value-refresh behavior were verified from source (not mentioned on the wiki but present in the fork). No wiki/fork divergence found.
**Bucket:** compiler builtin.

Gets the lowest ceiling point above an actor by TID. Compiler builtin (`PCD_GETACTORCEILINGZ`,
the Zandronum source's `src/p_acs.cpp:12025-12030`), implementation via the file-local
`SingleActorFromTID(int, AActor*)` helper (`p_acs.cpp:4445-4456`), which resolves the actor
and then extracts its `ceilingz` member.

- `ceilingz` (return value) — the lowest ceiling point above the actor, as a **fixed-point
  world coordinate**. This is an **absolute height, not a relative value** — the returned
  height is in the world's coordinate system (same units as `GetActorZ`, `GetActorFloorZ`).
  The value is **3D-floor-aware**: when an actor is inside a 3D floor, `ceilingz` is the
  bottom of the 3D floor (not the raw sector ceiling), giving the actual clearance above the
  actor. See `p_map.cpp:228-252` for the multi-sector ceiling clamping logic that includes
  3D floor checks. This cached value is refreshed whenever the actor's position is updated
  or a sector motion triggers `P_AdjustFloorCeil` (see `p_map.cpp:6013-6044`), ensuring the
  return value is current.
- `tid` — **`0` means "the activator"** (`SingleActorFromTID`'s `tid == 0` fallback, line
  4448); guarded against NULL activator (e.g. called from a script with no activator), which
  returns `0` silently rather than crashing.
- **Silent `0` conflation: bad TID, no activator, and legitimate ceiling height of exactly
  `0.0` are indistinguishable.** The function returns `0` when `actor == NULL` (either bad
  TID passed or `tid == 0` with no activator), and also returns `0` when an actor's actual
  ceiling is at world height `0.0`. This is the same pattern already documented for
  `ActivatorTID`/`GetSectorFloorZ` — all three have the same NULL/zero-value conflation at
  their root.
- **First-match-only on nonzero TID.** When `tid != 0`, this getter reads only the *first*
  actor matching that TID (`SingleActorFromTID` wraps the iterator in a single `Next()` call,
  line 4454). In projects where a TID is deliberately shared across many actors, a Get on a
  shared TID gives you only the first-spawned member, not all of them (unlike a Set operation
  on the same function, if one existed).

## Example (adapted from the wiki)

```c
script 124 ENTER
{
    while (TRUE)
    {
        Print (f:GetActorCeilingZ (0) - GetActorZ (0));
        Delay (1);
    }
}
```

This script continuously reports the player's clearance above its head in fixed-point units.

## See also

- `GetActorFloorZ` — identical structure, returns the floor instead of ceiling.
- `GetActorZ` — returns the actor's base position (bottom of its collision box).
