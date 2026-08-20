# `A_RemoveTarget(int flags [, string filter [, string species]])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `A_RemoveTarget` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RemoveTarget&oldid=46800) + verified against UZDoom source's `src/playsim/p_actionfunctions.cpp:4346-4358`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** DECORATE action function (`DEFINE_ACTION_FUNCTION(AActor, A_RemoveTarget)`).

Removes the calling actor's target pointer from the map. The removal is governed by flag filters and optional class/species matching.

## Parameters

- **flags** — removal policy flags (see below). Default is 0 (remove monsters only).
- **filter** — optional actor class to match (e.g. `"Imp"`, `"Cyberdemon"`). If specified with no `RMVF_EXFILTER` flag, only targets of that class are removed. Default is `"None"` (no class filter).
- **species** — optional species name to match. If specified with no `RMVF_EXSPECIES` flag, only targets of that species are removed. Default is `"None"` (no species filter).

## Flags

- `RMVF_MISSILES` — allows removal of actors with the `MF_MISSILE` flag set.
- `RMVF_NOMONSTERS` — prevents removal of actors with the `MF3_ISMONSTER` flag set. With no flags set at all (the default), only monsters are removed, since the other type-checks below are each gated on their own flag bit and are off by default — the four type-checks are independent conditions OR'd together, not a priority order.
- `RMVF_MISC` — the underlying check is "not simultaneously flagged as both a monster and a missile" (`MF3_ISMONSTER` and `MF_MISSILE` both set), not "neither monster nor missile" as the name suggests. Since an actor is essentially never flagged as both at once, setting `RMVF_MISC` in practice allows removal of any actor regardless of type — it does not actually restrict removal to non-monster/non-missile objects.
- `RMVF_EVERYTHING` — removes the target regardless of its monster/missile/misc type. It does not bypass the class/species filter checks below.
- `RMVF_EXFILTER` — inverts the class filter: the target is removed if its class name does **not** match `filter`.
- `RMVF_EXSPECIES` — inverts the species filter: the target is removed if its species does **not** match `species`.
- `RMVF_EITHER` — uses OR logic for filter/species matching instead of AND: the target is removed if either its class matches `filter` **or** its species matches `species` (default is both must match).

## Behavior

- If the calling actor's `target` pointer is NULL, the function silently does nothing.
- Class and species filters are applied before type-flag checks: the target must pass both the class/species gate and the type gate to be removed. The `RMVF_EITHER` flag changes this to an OR gate for filter/species only (the type gates still apply).
- Removal uses `P_RemoveThing`, which calls `Destroy()` on the target and clears its level-statistics counters (kill/item/secret counts) as needed. It explicitly refuses to act if the target is a live player's own body, or if the target is not a placed map actor (e.g. an inventory item currently held by another actor) — in either case the pointer is left untouched even if the flag/filter checks above would otherwise select it for removal.

## See also

- [A_RemoveTracer](a_removetracer.md) — removes the `tracer` pointer instead of `target`.
- [A_RemoveMaster](a_removemaster.md) — removes the `master` pointer instead of `target`.
- [A_RemoveChildren](a_removechildren.md) — removes all spawned children (actors whose `master` points to the caller).
- [A_RemoveSiblings](a_removesiblings.md) — removes all siblings (actors with the same master as the caller).
