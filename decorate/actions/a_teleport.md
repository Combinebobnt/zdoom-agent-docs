# `A_Teleport` (actor teleportation)

**Tier:** A
**Engine:** Zandronum 3.2.1 (limited feature set; UZDoom/GZDoom-family have significantly more flags and options)
**Provenance:** ZDoom Wiki `A_Teleport` (retrieved 2026-08-01, oldid=44219) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5221-5289`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Teleport)` in `src/thingdef/thingdef_codeptr.cpp`.

Attempts to teleport the calling actor to a random `SpecialSpot`-derived actor (or any actor type specified via `targettype`) within a specified distance range. On successful teleport, spawns a fog actor at the departure location and optionally jumps the actor to a specified state. Fails silently (no state jump) if no valid spot is found or if the target state does not exist.

## Engine divergence (important)

**Zandronum vs. UZDoom/GZDoom-family:** The wiki page describes ZDoom/UZDoom behavior, which includes many flags and parameters that **do not exist in Zandronum 3.2.1**. See "Zandronum-only parameters and flags" below. If you are writing DECORATE for Zandronum, only use the listed flags and parameters; others will be silently ignored or cause compilation errors.

## Signature (Zandronum)

```
state, bool A_Teleport(state teleportstate = NULL, class targettype = BossSpot, 
                       class fogtype = TeleportFog, int flags = 0, 
                       fixed mindist = 0, fixed maxdist = 0)
```

Note: The wiki lists a 7th parameter `ptr` for actor-pointer semantics (determining who gets teleported) and many additional flags. These **do not exist in Zandronum**.

## Parameters (Zandronum only)

### `teleportstate` (state, optional)

The state label to jump to after a successful teleport. If `NULL`, omitted, or does not exist on the calling actor, the function defaults to looking for a "Teleport" state. If no "Teleport" state exists either, the function returns without jumping to any state.

- **Note:** Empty string (`""`) on the wiki means "use Teleport state"; Zandronum accepts `NULL` for the same effect.

### `targettype` (actor class, optional)

The actor class to search for as a valid teleport destination. Must be `SpecialSpot`-derived. Defaults to `BossSpot` if `NULL` or omitted. The function uses `DSpotState::GetSpotWithMinMaxDistance()` to find a random instance of this class within the distance range.

### `fogtype` (actor class, optional)

The actor class to spawn at the departure location (the actor's old position before teleporting). Defaults to `TeleportFog` if `NULL` or omitted. Pass `NULL` or use the `TF_NOSRCFOG` flag to disable fog spawning at the source.

### `flags` (int, optional)

Bitfield controlling teleport behavior. Flags are combined using `|`. **Only 2 flags exist in Zandronum**; see "Flags listed in the wiki but NOT in Zandronum" for a complete list of what this section does *not* support.

#### Zandronum-only flags (Zandronum 3.2.1)

- `TF_TELEFRAG` (1) — Allow the teleporting actor to telefrag (instantly kill) any actor already occupying the destination spot. Without this flag, teleportation fails if the destination is occupied.

- `TF_RANDOMDECIDE` (2) — Randomly fail teleportation based on the actor's current health ratio, like `A_Srcr2Decide`. Uses the following decision table (health as a fraction of spawn health, mapped to success chance):

  | Health / SpawnHealth | Success probability |
  |---|---|
  | 8/8 or more | 0% (always fail) |
  | 7/8 | 6.25% |
  | 6/8 | 12.5% |
  | 4/8 | 25% |
  | 1/8 | 46.875% |
  | Less than 1/8 | 75% |

  This simulates a "desperation teleport" pattern where weak or injured actors are more likely to escape.

### `mindist` (fixed, optional)

The minimum distance the teleport destination must be from the calling actor's current position. Defaults to 0 (no minimum). Measured in map units (same scale as actor radius/height).

### `maxdist` (fixed, optional)

The maximum distance the teleport destination may be from the calling actor's current position. Defaults to 0, which means **no maximum limit** (can teleport to any distance). If `maxdist > 0`, destinations beyond this range are skipped.

## Teleportation process

1. If `TF_RANDOMDECIDE` is set, consult the health-ratio table above; if the roll fails, return without teleporting.
2. Resolve the `teleportstate` label (use specified state, or default to "Teleport", or fail if not found).
3. Get or create the global `DSpotState` (actor spot registry used during map load).
4. Search for a random actor of type `targettype` (defaulting to `BossSpot`) within the `mindist`–`maxdist` range.
5. If found, attempt to move the actor via `P_TeleportMove()` (with `TF_TELEFRAG` gating telefrag behavior).
6. On success:
   - Spawn `fogtype` (if not NULL) at the old position.
   - Jump to `teleportstate`.
   - Set the actor's Z position to floor level.
   - **Zero out the actor's velocity** (stops all movement; the wiki's `TF_KEEPVELOCITY` flag does *not exist in Zandronum*).
   - Set the actor's angle to face the spot's angle.
7. On failure (no spot found, or teleport blocked despite `TF_TELEFRAG`), return silently with no state jump.

## Flags listed in the wiki but **NOT in Zandronum**

The following flags appear in the ZDoom/UZDoom wiki but are **not defined in Zandronum** and will cause a compilation error or be silently ignored (depending on how they are referenced):

- `TF_FORCED` — ignore obstacles in the destination
- `TF_KEEPVELOCITY` — preserve actor velocity after teleport (Zandronum always zeros velocity)
- `TF_KEEPANGLE` — preserve actor angle instead of facing the destination spot's angle
- `TF_KEEPORIENTATION` — equivalent to `TF_KEEPVELOCITY | TF_KEEPANGLE`
- `TF_USESPOTZ` — use the destination spot's Z position instead of flooring
- `TF_NOSRCFOG` — skip spawning fog at departure location
- `TF_NODESTFOG` — skip spawning fog at destination
- `TF_NOFOG` — equivalent to `TF_NOSRCFOG | TF_NODESTFOG`
- `TF_USEACTORFOG` — use custom fog types from actor properties
- `TF_NOJUMP` — do not jump to state after teleport
- `TF_OVERRIDE` — allow teleporting even if actor has `NOTELEPORT` flag
- `TF_SENSITIVEZ` — fail teleport instead of adjusting Z position to avoid obstacles

If you need any of these behaviors in Zandronum, you will need to implement a custom action function or design a workaround (e.g., manually setting actor properties before calling a simpler `A_Teleport`).

## Related functions and concepts

- **`SpecialSpot`** — base actor class for teleport destination spots. Custom spots can inherit from `SpecialSpot` and be passed as `targettype`.
- **`BossSpot`** — the default teleport destination type if `targettype` is not specified.
- **`TeleportFog`** — the default fog actor spawned at departure and/or destination. Can be customized via the `fogtype` parameter.
- **`A_Srcr2Decide`** — another action that uses a health-ratio-based random decision (the basis for `TF_RANDOMDECIDE` logic).

## Special notes

### Network behavior (Zandronum multiplayer)

Teleportation is **server-authoritative**: only the server executes the actual move; clients receive the result via network updates and position synchronization.

### Interaction with NOTELEPORT flag

By default, Zandronum respects the `NOTELEPORT` actor flag — an actor with this flag will *not* teleport even if `A_Teleport` is called. There is no `TF_OVERRIDE` flag in Zandronum to bypass this (that flag exists in GZDoom/UZDoom but not here).

### Z-position adjustment

If the destination spot's Z position would place the actor inside a solid (floor or ceiling), Zandronum automatically adjusts the Z position upward to clear the obstruction. There is no `TF_SENSITIVEZ` flag to change this behavior — Zandronum always does the adjustment (the wiki's flag would make it fail instead).

## Example (Zandronum DECORATE)

```
actor TeleportImp : DoomImp 601
{
  States
  {
  Spawn:
    TROO AB 10 A_Look
    Loop
  See:
    TROO AABBCCDD 3 A_Chase("Melee", "Missile")
    TROO A 0 A_Jump(200, "Teleport")
    Loop
  Teleport:
    TROO A 0 A_Teleport("See", "ImpSpot")
    Loop
  Melee:
  Missile:
    TROO EF 8 A_FaceTarget
    TROO G 6 A_TroopAttack
    Goto See
  }
}

actor ImpSpot : SpecialSpot 600
{
  +INVISIBLE
}
```

This example shows a simple teleportation pattern: the actor randomly decides (via `A_Jump`) to call `A_Teleport`, which searches for an `ImpSpot` actor to teleport to. On success, it resumes the "See" state; on failure, it continues looping in the current state. No state labeled "Teleport" is defined on the actor, so the function uses the "See" state instead.

## Wiki page source

This entry was adapted from the ZDoom Wiki page on `A_Teleport` (oldid=44219). The wiki describes features ahead of Zandronum 3.2.1 — notably the additional flags and the `ptr` parameter. Zandronum's simpler implementation supports only the core teleportation mechanic and the two listed flags.
