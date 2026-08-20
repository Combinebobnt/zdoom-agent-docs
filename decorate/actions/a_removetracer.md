# `A_RemoveTracer` (remove actor in tracer pointer)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `A_RemoveTracer` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RemoveTracer&oldid=46795) + verified against the UZDoom source's `src/playsim/p_actionfunctions.cpp:4365-4377`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_RemoveTracer)` in `src/playsim/p_actionfunctions.cpp` — callable from any actor's state table.

Removes the actor referenced by the calling actor's `tracer` pointer from the game world, with optional filtering by type, class, and species. A companion to `A_RemoveTarget`, `A_RemoveMaster`, `A_RemoveChildren`, and `A_RemoveSiblings` for selectively removing actors.

## Engine-family divergence

**This function does not exist in Zandronum.** It is a UZDoom/GZDoom-family addition and will not compile in Zandronum DECORATE. The Zandronum-only `A_RemoveTarget` and `A_RemoveMaster` exist but support only unconditional removal without parameters; they predate the wiki's advanced parameterized versions documented here.

## Signature

```text
void A_RemoveTracer(int flags = 0, class<Actor> filter = null, name species = "None")
```

## Parameters

### `flags` (int, optional, default: 0)

Bitfield controlling which actor types can be removed. Multiple flags can be combined using the bitwise OR operator (`|`). If no flags are set, no removal occurs.

- **`RMVF_MISSILES`** — Allows removal of actors with the `MF_MISSILE` flag set (projectile-type actors).
- **`RMVF_NOMONSTERS`** — Prevents removal of monsters (actors with `MF3_ISMONSTER` flag set). By default, monsters are removable; this flag disables that.
- **`RMVF_MISC`** — Allows removal when the actor is not *simultaneously* both a monster (`MF3_ISMONSTER`) and a missile (`MF_MISSILE`). Since no actor normally carries both flags at once, this condition is true for almost any actor — monsters and missiles included, not just decorations/pickups as the flag name might suggest. It is `!(ISMONSTER && MISSILE)`, not `!ISMONSTER && !MISSILE`.
- **`RMVF_EVERYTHING`** — Overrides all other flags and removes the actor regardless of type discrimination. When set, all other flag checks are bypassed.
- **`RMVF_EXFILTER`** — Inverts the `filter` class-name check; the tracer is only removed if its class name does **not** match the filter.
- **`RMVF_EXSPECIES`** — Inverts the `species` check; the tracer is only removed if its species does **not** match the species filter.
- **`RMVF_EITHER`** — Enables OR-logic for filter matching; the tracer is removed if either its class name matches `filter` OR its species matches `species`. Default behavior is AND-logic (must match both).

### `filter` (class<Actor>, optional, default: null)

Actor class filter, written in DECORATE as a bare class name or the literal `"None"`/omitted for no filter. If non-null, the tracer is only removed when its class is exactly this class (exact match — a subclass of `filter` does not count as a match). Default `null` means no class filtering.

### `species` (name, optional, default: "None")

Species name filter. If specified and not "None", the tracer is only removed if its species property matches this value. Empty string and "None" are equivalent to no filter.

## Behavior

When called:

1. Checks if the calling actor has a non-NULL `tracer` pointer. If NULL, the function returns silently with no effect.
2. Evaluates the `filter` (class name) and `species` checks against the tracer actor:
   - By default (without `RMVF_EXFILTER` / `RMVF_EXSPECIES`), both checks must pass for removal to proceed (AND logic).
   - With `RMVF_EITHER`, at least one must pass (OR logic).
   - With `RMVF_EXFILTER` and/or `RMVF_EXSPECIES`, the respective check is inverted (non-match required).
3. Applies type discrimination based on flags:
   - With `RMVF_EVERYTHING`, the actor is removed unconditionally (type checks skipped).
   - Otherwise, checks are applied in this order:
     - If `RMVF_MISC` is set and the actor is not simultaneously both a monster and a missile (true for almost any actor in practice), remove it.
     - If actor is a monster (`MF3_ISMONSTER` set) and `RMVF_NOMONSTERS` is NOT set, remove it.
     - If actor is a missile (`MF_MISSILE` set) and `RMVF_MISSILES` is set, remove it.
4. Calls `P_RemoveThing` to handle the actual removal.

## NULL tracer check

The function safely checks whether `tracer != NULL` before attempting removal. Calling `A_RemoveTracer` on an actor with no tracer (or with a tracer pointing to a destroyed actor) is harmless and has no effect.

## Type discrimination logic

The type checks in the implementation use this structure:

- `RMVF_EVERYTHING`: Removes regardless of all other flags.
- `RMVF_MISC`: Removes actors that are not simultaneously both a monster AND a missile — since that combination essentially never occurs, this flag in practice matches monsters and missiles too, not just the "misc" (decoration/pickup) category its name implies.
- Monster check: Removes if `MF3_ISMONSTER` is set and `RMVF_NOMONSTERS` is not set.
- Missile check: Removes if `MF_MISSILE` is set and `RMVF_MISSILES` is set.

Note that an actor can pass multiple type checks, potentially triggering removal multiple times in the implementation; this is a minor inefficiency in the source but not observable in behavior (removal is idempotent).

## Network behavior

In UZDoom/GZDoom-family multiplayer, `P_RemoveThing` broadcasts actor destruction to clients. The removal is **server-authoritative** — the server decides which actors to remove, and clients receive the destruction command.

## Related actions

- **`A_RemoveTarget`** — Removes the calling actor's target pointer (UZDoom/GZDoom-family only).
- **`A_RemoveMaster`** — Removes the calling actor's master pointer.
- **`A_RemoveChildren`** — Removes all actors spawned by the calling actor (children).
- **`A_RemoveSiblings`** — Removes all actors that share the calling actor's master (siblings, not including the caller).
- **`A_KillTracer`** — Kills the tracer (forces it into Death state) without removing it from the world.

## Example (UZDoom/GZDoom DECORATE)

A homing projectile that removes other projectiles it passes through:

```text
ACTOR HomingBolt : FastProjectile
{
    Speed 40
    Damage 20
    Projectile
    +SEEKERMISSILE
    Spawn:
        BOLT A 1 A_Tracer2
        Loop
    Death:
        BOLX A 6 BRIGHT
        BOLX B 6 BRIGHT
        Stop
    XDeath:
        // Remove any projectiles we collided with
        TNT1 A 0 A_RemoveTracer(RMVF_MISSILES)
        BOLX A 6 BRIGHT
        BOLX B 6 BRIGHT
        Stop
}
```

A spawned monster that removes itself when it returns to its spawner:

```text
ACTOR SummonedDemon : Demon
{
    Speed 15
    Radius 20
    Height 56
    Missile:
        // Check if still alive and tracer points to spawner
        DEM2 H 5 A_Tracer2
        Loop
    Death:
        // Clean up the spawner relationship before dying
        DEM2 I 8 A_RemoveTracer(RMVF_EVERYTHING)
        DEM2 J 8 A_Scream
        DEM2 K 6 A_NoBlocking
        DEM2 L 6
        DEM2 M -1
        Stop
}
```

Filtering by class name — only remove a tracer if it's a specific projectile type:

```text
ACTOR ProjectileEater : CacodemonBall
{
    Projectile
    Spawn:
        CACP A 1
        Loop
    Death:
        // Only remove BFG balls, leaving other projectiles alone
        CACP B 4 A_RemoveTracer(RMVF_EVERYTHING, "BFGBall")
        CACP C 4
        Stop
}
```

Using species filtering and inverted checks:

```text
ACTOR BossMinionDispel : Actor
{
    Projectile
    Speed 20
    Damage 0  // This is just a trigger
    Spawn:
        MISL A 1
        Loop
    Death:
        // Remove the tracer UNLESS it's a boss-type actor
        MISL B 4 A_RemoveTracer(RMVF_EVERYTHING | RMVF_EXSPECIES, "None", "Boss")
        Stop
}
```
