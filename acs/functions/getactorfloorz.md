# `fixed GetActorFloorZ(int tid)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `GetActorFloorZ - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=GetActorFloorZ&oldid=46774`) + source-verified against `p_acs.cpp:12018-12023, 4445-4456`, `builtin.c:121` signature, `p_map.cpp:1461-1493` 3D-floor handling, and `p_mobj.cpp:4957` spawn-time floor initialization. The function's 3D-floor awareness and the specific midpoint-based selection rule are verified directly from source and represent a **wiki/fork divergence**: the wiki's description "highest floor point underneath the actor" omits the midpoint test and `FF_SOLID` gate, which means a 3D floor only raises `floorz` if the actor is actually standing on it (or partially inside it), not unconditionally if it's above the actor. All other claims (fixed-point return, `tid=0` activator fallback, silent-0 failure conflation, blockmap timing) check out or are consistent with the source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Gets an actor's floor contact height (the highest solid surface it's resting on or intersecting with). Compiler builtin (`PCD_GETACTORFLOORZ`, the Zandronum source's `src/p_acs.cpp:12018-12023`), implementation via the file-local `SingleActorFromTID(int, AActor*)` helper (`p_acs.cpp:4445-4456`), which resolves the actor and returns its `floorz` member — a fixed-point world coordinate updated whenever the engine calls `P_CheckPosition`/`P_TryMove`/`P_FindFloorCeiling`.

- `floorz` (return value) — **a fixed-point world coordinate**, the height of the solid surface the actor is resting on or touching. **This is 3D-floor aware** — when solid 3D floors (`FF_SOLID | FF_EXISTS`) are present, the engine picks the one that the actor's midpoint is standing closest to (per the midpoint test at `p_map.cpp:1478-1481`: `abs(actor.z - (ff_bottom + (ff_top - ff_bottom)/2))` must be less than the vertical distance from the actor's top to the same midpoint), not the unconditional highest floor. This is subtly different from the wiki's "highest floor point underneath the actor" — an actor beneath a 3D floor gets the sector floor, not the 3D floor's top. **Contrast:** `GetSectorFloorZ(tag, x, y)` is *not* 3D-floor aware; it samples the sector's floor plane directly.
  - When called on a spectator or actor with `IsNoClip2()` enabled, the 3D-floor check is skipped entirely (`p_map.cpp:1463`), so `floorz` reflects only the raw sector floor.
- `tid` — **`0` means "the activator"** (`SingleActorFromTID`'s `tid == 0` fallback, line 4448); guarded against NULL activator (e.g. called from an `OPEN` script with no activator), which returns `0` silently rather than crashing. Nonzero `tid` resolves via the first matching actor from an iterator, or NULL if no match exists.
- **Silent `0` conflation: bad TID, no activator, and genuine floor at height `0.0` are all indistinguishable.** The function returns `0` when `actor == NULL` (either bad TID or `tid == 0` with no activator), and also returns `0` when an actor legitimately stands on a sector floor at absolute Z coordinate `0.0` — a common map height. Since `0` is a valid height, callers **cannot use `0` as a failure sentinel**. Idiomatic existence checks use `IsTidUsed(tid)` or explicit `GetActorZ(tid) != 0 || IsTidUsed(tid)` patterns instead.
- **Blockmap initialization caveat (wiki-asserted, source-consistent but not fully traced):** The wiki states "The actor must be in the blockmap for this to be updated after spawn." The mechanism is that `floorz` is only initialized/refreshed when `P_CheckPosition`, `P_TryMove`, or `P_FindFloorCeiling` is called for that actor. For map-spawned actors, this call is delayed until after the actor is fully placed (per the `FFCF_ONLYSPAWNPOS` flag at `p_mobj.cpp:4957`), so reading `floorz` on a freshly-spawned actor from script (before any movement) can return a stale or uninitialized value. This affects callers reading spot/destination TIDs before those actors have moved, as seen in real project code.

## Example (adapted from the wiki)

```acs
script 124 ENTER
{
    while (TRUE)
    {
        // Print the activator's height above ground (clearance from floor)
        Print(f:GetActorZ(0) - GetActorFloorZ(0));
        Delay(1);
    }
}
```

This matches a common usage pattern (`(GetActorZ(tid) - GetActorFloorZ(tid)) == 0` as a ground-contact check) and is the idiomatic way to measure 3D clearance accounting for 3D floors.
