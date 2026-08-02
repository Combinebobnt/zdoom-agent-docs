# `A_RemoveTarget(int flags [, string filter [, string species]])`

**Tier:** A
**Engine:** UZDoom 4.15pre / GZDoom-family — does not exist in Zandronum
**Provenance:** ZDoom Wiki `A_RemoveTarget` (retrieved 2026-08-01, oldid=46800) + verified against UZDoom source's `src/playsim/p_actionfunctions.cpp:4346-4358`.
**Bucket:** DECORATE action function (`DEFINE_ACTION_FUNCTION(AActor, A_RemoveTarget)`).

Removes the calling actor's target pointer from the map. The removal is governed by flag filters and optional class/species matching.

## Parameters

- **flags** — removal policy flags (see below). Default is 0 (remove monsters only).
- **filter** — optional actor class to match (e.g. `"Imp"`, `"Cyberdemon"`). If specified with no `RMVF_EXFILTER` flag, only targets of that class are removed. Default is `"None"` (no class filter).
- **species** — optional species name to match. If specified with no `RMVF_EXSPECIES` flag, only targets of that species are removed. Default is `"None"` (no species filter).

## Flags

- `RMVF_MISSILES` — allows removal of actors with the `MF_MISSILE` flag set.
- `RMVF_NOMONSTERS` — prevents removal of actors with the `MF3_ISMONSTER` flag set. By default, monsters **are** the only category allowed for removal (overriding any other flags).
- `RMVF_MISC` — allows removal of actors that are neither monsters nor missiles.
- `RMVF_EVERYTHING` — overrides all other filters and removes the target unconditionally, regardless of type.
- `RMVF_EXFILTER` — inverts the class filter: the target is removed if its class name does **not** match `filter`.
- `RMVF_EXSPECIES` — inverts the species filter: the target is removed if its species does **not** match `species`.
- `RMVF_EITHER` — uses OR logic for filter/species matching instead of AND: the target is removed if either its class matches `filter` **or** its species matches `species` (default is both must match).

## Behavior

- If the calling actor's `target` pointer is NULL, the function silently does nothing.
- Removal uses `P_RemoveThing`, which completely eliminates the target from the map and any object-tracking lists (corpse queue, etc.).
- Class and species filters are applied before type-flag checks: the target must pass both the class/species gate and the type gate to be removed. The `RMVF_EITHER` flag changes this to an OR gate for filter/species only (the type gates still apply).

## See also

- [A_RemoveTracer](a_removetracer.md) — removes the `tracer` pointer instead of `target`.
- [A_RemoveMaster](a_removemaster.md) — removes the `master` pointer instead of `target`.
- [A_RemoveChildren](a_removechildren.md) — removes all spawned children (actors whose `master` points to the caller).
- [A_RemoveSiblings](a_removesiblings.md) — removes all siblings (actors with the same master as the caller).
