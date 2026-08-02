# `A_CheckLOF(state jump [, int flags [, fixed range [, fixed minrange [, angle angle [, angle pitch [, fixed offsetheight [, fixed offsetwidth [, int ptr_target]]]]]]])`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_CheckLOF` (retrieved 2026-08-01, oldid=45092) + verified against
the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4046-4209` and flag enum at `src/thingdef/thingdef_codeptr.cpp:3931-3964`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CheckLOF)` — callable from any actor's state table.

Performs a line-of-fire hitscan test to check whether a path between the calling actor and a target (or a specified point) is blocked by other actors. Jumps to a state if the test succeeds (the target is reachable, or optionally another actor is in the way).

## Parameters

- **`jump`** (state) — Jump target if the test succeeds. Required.
- **`flags`** (int, default 0) — Flag set controlling what the test considers "blocking" and how the trace is positioned. See "Flags" below. Flags can be combined with `|` (bitwise OR).
- **`range`** (fixed, default 0) — Maximum distance for the check, in map units. If 0, defaults to `PLAYERMISSILERANGE` (for player actors) or `MISSILERANGE` (for monsters). Unlike the wiki's float notation, this is fixed-point (32.16 fixed; written as a decimal in DECORATE source).
- **`minrange`** (fixed, default 0) — If set, the check fails (does not jump) if an obstruction is closer than this distance. Also fixed-point.
- **`angle`** (angle, default 0) — Offset the trace direction by this angle (horizontal). Uses the engine's `angle_t` type; the wiki's notation as `float` is imprecise. Positive values rotate counterclockwise.
- **`pitch`** (angle, default 0) — Offset the trace direction by this angle (vertical). `angle_t` type. When the target is unknown and `CLOFF_ALLOWNULL` is set, pitch is not automatically calculated — to set an absolute pitch without a target, use expressions like `-pitch + <expression>`.
- **`offsetheight`** (fixed, default 0) — Offset the trace origin vertically, in map units (fixed-point). If `CLOFF_MUL_HEIGHT` is set, this multiplies the actor's height (accounting for player crouch) rather than being an absolute offset.
- **`offsetwidth`** (fixed, default 0) — Offset the trace origin horizontally (side-to-side), in map units (fixed-point). Positive values shift the origin to the right, negative to the left. If `CLOFF_MUL_WIDTH` is set, this multiplies the actor's radius instead. Aim is not automatically adjusted for this offset.
- **`ptr_target`** (int, default `AAPTR_DEFAULT`) — Which actor pointer to aim at: `AAPTR_DEFAULT` uses the calling actor's target (or the player for player actors), or specify `AAPTR_NULL` to cast the ray without a target (requires `CLOFF_ALLOWNULL`).

## Flags

| Flag | Behavior |
|---|---|
| **`CLOFF_NOAIM_VERT`** | Disable vertical aiming (use the actor's current pitch instead of calculating toward the target). |
| **`CLOFF_NOAIM_HORZ`** | Disable horizontal aiming (use the actor's current angle instead of calculating toward the target). |
| **`CLOFF_AIM_VERT_NOOFFSET`** | When aiming vertically at the target, do not correct for `offsetheight` — aim from whatever height the other flags indicate. |
| **`CLOFF_NOAIM`** (combo) | Shorthand for `CLOFF_NOAIM_VERT \| CLOFF_NOAIM_HORZ`. |
| **`CLOFF_FROMBASE`** | Move the trace origin to the actor's feet (base z-coordinate) instead of the default hitscan height (approximately the actor's middle). |
| **`CLOFF_MUL_HEIGHT`** | Multiply `offsetheight` by the actor's height (accounting for player crouching if applicable). A value of 2 and a radius of 32 results in a 64-unit offset. Has no effect if `offsetheight` is 0. |
| **`CLOFF_MUL_WIDTH`** | Multiply `offsetwidth` by the actor's radius instead of using it as an absolute offset. A value of 2 and a radius of 32 results in a 64-unit offset. Has no effect if `offsetwidth` is 0. |
| **`CLOFF_JUMPENEMY`** | Allow jump if an **enemy** (hostile actor) is in the line of fire. |
| **`CLOFF_JUMPFRIEND`** | Allow jump if a **friendly** (non-hostile actor) is in the line of fire. |
| **`CLOFF_JUMPOBJECT`** | Allow jump if a **non-actor** (decoration, projectile, etc.) is in the line of fire. |
| **`CLOFF_JUMPNONHOSTILE`** | Allow jump if an actor in the way is **not attacking** the calling actor. Combined with `CLOFF_JUMPENEMY`/`CLOFF_JUMPFRIEND`, this filters which actors trigger the jump. |
| **`CLOFF_SKIPENEMY`** | Treat enemy actors in the path as if they are not present (transparent to the trace). |
| **`CLOFF_SKIPFRIEND`** | Treat friendly actors in the path as if they are not present. |
| **`CLOFF_SKIPOBJECT`** | Treat non-actors in the path as if they are not present. |
| **`CLOFF_SKIPNONHOSTILE`** | Treat non-attacking actors as if they are not present. |
| **`CLOFF_SKIPOBSTACLES`** (combo) | Shorthand for `CLOFF_SKIPENEMY \| CLOFF_SKIPFRIEND \| CLOFF_SKIPOBJECT \| CLOFF_SKIPNONHOSTILE`. Partial overriding is allowed (e.g., `CLOFF_SKIPOBSTACLES \| CLOFF_JUMPFRIEND` skips most actors but still jump on friendlies). |
| **`CLOFF_MUSTBESHOOTABLE`** | Only consider actors that have the `SHOOTABLE` or `NONSHOOTABLE` flags (filters out non-combat-relevant decorations). Does not apply to the target actor itself. |
| **`CLOFF_MUSTBEGHOST`** | Only consider **ghost** actors (filters out non-ghosts). Does not apply to the target. |
| **`CLOFF_IGNOREGHOST`** | Ignore **ghost** actors (opposite of above). Does not apply to the target. |
| **`CLOFF_MUSTBESOLID`** | Only consider **solid** actors. Does not apply to the target. |
| **`CLOFF_JUMP_ON_MISS`** | Jump if the ray hits a wall, floor, or ceiling within range, even if the target itself is not directly hit. Useful for checking for obstacles rather than line-of-sight. |
| **`CLOFF_SKIPTARGET`** | The target actor does not block the ray — other filters like `CLOFF_MUSTBESHOOTABLE` only apply to intercepting actors, not the target. If the ray reaches the target without hitting anything else, the jump does not trigger; use with other `CLOFF_JUMP*` flags to jump on obstacles instead. |
| **`CLOFF_BEYONDTARGET`** | Requires `CLOFF_SKIPTARGET`. Trace past the target actor to check for further obstacles. Only useful combined with other jump qualifiers to detect obstacles *beyond* the target. |
| **`CLOFF_ALLOWNULL`** | Cast the ray even if the target pointer is null. When there is no target, the calling actor's current angle and pitch are used regardless of `CLOFF_NOAIM_*` flags. |
| **`CLOFF_CHECKPARTIAL`** | Perform the check even if the target is actually out of range (beyond `range`). Useful if you want to detect closer intercepting actors regardless of whether the target itself is reachable. |

## Zandronum-specific notes

**Missing parameters (ZDoom/GZDoom extension):** The original ZDoom wiki documents a 10th parameter `offsetforward` which does not exist in Zandronum's implementation. The function signature here is the complete Zandronum arity.

**Missing flags (ZDoom/GZDoom extensions):** The wiki also lists `CLOFF_SETTARGET`, `CLOFF_SETMASTER`, and `CLOFF_SETTRACER` — none of which are present in Zandronum. These flags silently do nothing if used in this engine; do not rely on them to set pointer relationships.

**Anonymous action blocks:** The wiki's opening note about jump functions behaving differently inside anonymous functions is not relevant to Zandronum's DECORATE — anonymous `{ ... }` action blocks are a ZScript/GZDoom extension and do not exist in this fork.

**Network synchronization:** This function is server-side only in multiplayer — the client-mode check (`NETWORK_InClientModeAndActorNotClientHandled`) returns immediately, and the actor update is sent per `CLIENTUPDATE_FRAME`.

## Examples

Check if the calling actor can "see" its target at a maximum distance of 1500 units, ignoring obstacles except the target itself:

```
A_CheckLOF("Attack", CLOFF_SKIPOBSTACLES, 1500)
```

(The example from the wiki, with a `ShotgunGuy` variant.)

Check if there is any enemy between the calling actor and its target (jump if blocked by an enemy):

```
A_CheckLOF("Blocked", CLOFF_JUMPENEMY)
```

Check if there is solid geometry between the actor and its target (using `CLOFF_JUMP_ON_MISS`):

```
A_CheckLOF("HasObstacle", CLOFF_SKIPOBSTACLES | CLOFF_JUMP_ON_MISS, 2000)
```
