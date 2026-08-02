# `A_Remove(int pointer [, int flags [, class filter [, name species]]])`

**Tier:** A
**Engine:** UZDoom 4.15pre / GZDoom-family — does not exist in Zandronum
**Provenance:** ZDoom Wiki `A_Remove` (retrieved from saved page, verified 2026-08-01) + verified against UZDoom source's `src/playsim/p_actionfunctions.cpp:4458`.
**Bucket:** UZDoom action function (`src/playsim/p_actionfunctions.cpp:4458`). Dispatches to shared helper `DoRemove()` (`src/playsim/p_actionfunctions.cpp:4316`) with flags enum at `:4305`.

Removes an actor pointed to by a given actor pointer selector, optionally filtering by class and/or species. The pointer argument determines which actor is removed (target, master, tracer, a player, etc.), and optional flags and filters control what subset of the pointed actor matches the removal criteria.

**Engine availability note:** Zandronum does not have `A_Remove`. The closest Zandronum equivalents are the pointer-specific functions `A_RemoveMaster()` (no parameters), `A_RemoveTarget()`, `A_RemoveTracer()`, `A_RemoveChildren()`, and `A_RemoveSiblings()` — but these accept only a `removeall` bool parameter (in `A_RemoveChildren` and `A_RemoveSiblings`) or no parameters at all. They do not support the filtering, species-checking, or flag-based removal discrimination this function provides.

## Parameters

### `pointer` (int)
An actor pointer selector constant — one of `AAPTR_DEFAULT`, `AAPTR_NULL`, `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER`, `AAPTR_PLAYER_GETTARGET`, `AAPTR_PLAYER_GETCONVERSATION`, `AAPTR_PLAYER1` through `AAPTR_PLAYER8`, `AAPTR_FRIENDPLAYER`, or `AAPTR_GET_LINETARGET`. Selects which actor relative to the calling actor will be checked for removal. Evaluated at call time.

**Engine divergence:** Zandronum supports all the above except `AAPTR_GET_LINETARGET`, but also has Zandronum-specific selectors (`AAPTR_PLAYER_GETFLOATYICON`, `AAPTR_PLAYER_GETCAMERA`, `AAPTR_DAMAGE_SOURCE`, `AAPTR_DAMAGE_INFLICTOR`, `AAPTR_DAMAGE_TARGET`) that do not exist in UZDoom. Check your engine's `actorptrselect.h` for the full supported set.

### `flags` (int, optional, default 0)
A bitmask controlling which types of actors are removed and how filters are applied. Combines any of the following flags with `|`:

- `RMVF_MISSILES` — allows removal of actors with the `MISSILE` flag set. Without this flag, missiles are silently skipped.
- `RMVF_NOMONSTERS` — excludes actors with the `MONSTER` flag from removal. Without this flag, monsters are removed by default.
- `RMVF_MISC` — allows removal of actors that are neither missiles nor monsters (decorations, items, etc.). Without this flag, misc actors are silently skipped.
- `RMVF_EVERYTHING` — removes the actor regardless of type, overriding the above three flags' discrimination. **Important:** despite the wiki description of "overrides all other flags," the implementation does not short-circuit the other flag checks — `RMVF_EVERYTHING` simply also triggers removal, alongside the other active flags. Thus with `RMVF_EVERYTHING` set, the target is always removed (assuming the filter and species checks pass).
- `RMVF_EXFILTER` — inverts the `filter` class name check. The target is removed only if its class does **not** match the filter.
- `RMVF_EXSPECIES` — inverts the `species` check. The target is removed only if its species does **not** match the species argument.
- `RMVF_EITHER` — changes the logical combination of filter and species checks from AND (both must match) to OR (either must match). Without this flag, the target is removed only if both the filter class and species check pass; with it, the target is removed if either check passes.

**Default behavior (flags = 0):** only monsters (`MF3_ISMONSTER` flag) are removed; missiles and misc actors are silently skipped. This differs from the other sibling `A_Remove*` functions, which have simpler parameter signatures and no explicit "monsters by default" logic.

### `filter` (class, optional, default None)
The actor class name to match. The target is removed only if its class is the exact class or inherits from the class specified, unless `RMVF_EXFILTER` is set (which inverts the check). The string "None" is a no-op filter (matches everything).

### `species` (name, optional, default None)
The species name to match. The target is removed only if its `species` property equals the value specified, unless `RMVF_EXSPECIES` is set. The string "None" is a no-op filter.

## Examples

Remove the calling actor's target, but only if it is a missile:
```c
A_Remove(AAPTR_TARGET, RMVF_MISSILES)
```

Remove the calling actor's master, but do not remove if it is a monster:
```c
A_Remove(AAPTR_MASTER, RMVF_NOMONSTERS)
```

Remove the calling actor's tracer only if it is a `Demon` class or inherits from `Demon`:
```c
A_Remove(AAPTR_TRACER, 0, Demon)
```

Remove anything pointed to by `AAPTR_TARGET`, regardless of type:
```c
A_Remove(AAPTR_TARGET, RMVF_EVERYTHING)
```

Remove the first player's actor only if it has a specific species:
```c
A_Remove(AAPTR_PLAYER1, 0, None, "PlayerSpecies")
```

## See also

- `AAPTR` pointer selectors (in UZDoom's `src/playsim/actorptrselect.h`).
- `A_RemoveTarget`, `A_RemoveTracer`, `A_RemoveMaster`, `A_RemoveChildren`, `A_RemoveSiblings` — UZDoom equivalents with fixed pointer targets.
- Zandronum-only `A_RemoveMaster`, `A_RemoveChildren`, `A_RemoveSiblings` with simpler parameter sets.
