# `void A_CustomMissile(class<Actor> missiletype, float spawnheight = 32, int spawnofs_xy = 0, float angle = 0, int flags = 0, float pitch = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_CustomMissile` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_CustomMissile&oldid=49278) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1159` and `wadsrc/static/actors/actor.txt:206`; corrections from `src/thingdef/thingdef_codeptr.cpp:105-124,1159-1305`, `src/actor.h:901-904`, `src/p_mobj.cpp:1705` and `src/p_mobj.cpp:7217-7262`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CustomMissile)` on `AActor` class (callable from any actor's state table).

A customizable projectile attack for non-player actors, typically used by monsters to launch a projectile at their target. **Fork divergence note:** This page describes a ZDoom Wiki source which documents GZDoom/UZDoom. Zandronum's version **does not include a 7th `ptr` parameter** to select the target actor — the target is always `self->target`. The wiki's deprecation notice (recommending `A_SpawnProjectile` instead) is GZDoom-family only and does not apply to Zandronum, where `A_CustomMissile` remains the standard missile-spawning action.

## Parameters

- **missiletype** — The class name of the projectile to fire (required).
- **spawnheight** — Raises the projectile spawn point on the actor by this amount in units. Default is `32`. Note: the wiki describes this as `double`, but Zandronum declares it as `float`.
- **spawnofs_xy** — Moves the projectile spawn point perpendicular to the actor's facing angle (to the right if positive, left if negative). Zandronum reads this as an `int`, while the wiki describes a double; a fractional value is truncated toward zero. Default is `0`.
- **angle** — Adds this much offset to the calculated aim angle at the target. Default is `0`.
- **flags** — Bitwise-OR combination of aim-mode flags and modifiers. See "Aim modes and flags" below. Default is `0`.
- **pitch** — Vertical aim in degrees. Unlike the usual actor pitch convention, positive values aim **upward** and negative values aim downward (the "bad pitch" kept for compatibility; see Behavior notes). Only affects the flight path when `CMF_ABSOLUTEPITCH` or `CMF_OFFSETPITCH` is set (or aim mode 2); `CMF_SAVEPITCH` can still store it. Default is `0`.

## Aim modes and flags

The `flags` parameter's low 2 bits select one of three aim modes (a value of 3 behaves like mode 0); the remaining bits control pitch and angle behavior. Constants are defined in `wadsrc/static/actors/constants.txt`.

### Aim modes (bits 0–1, value 0–2)

- **Aim mode 0 (neither flag set)** — Aim directly at the target. Performs a temporary position adjustment for better accuracy (adjusts `self`'s position, spawns the missile, then restores). Requires a valid `self->target`. This is the default.
- **Aim mode 1 (`CMF_AIMOFFSET`)** — Aim parallel to a reference trajectory (spawn height 32, xy-offset 0), correcting for the caller's actual spawnheight and spawnofs_xy. Useful for spawning multiple projectiles at once with consistent aim. Requires a valid target.
- **Aim mode 2 (`CMF_AIMDIRECTION`)** — Aim in a fixed direction specified by `angle` and `pitch`, ignoring the target entirely. No target required. Automatically implies `CMF_ABSOLUTEPITCH`. Useful for pattern-based or directed attacks.

### Pitch and angle flags

- **`CMF_ABSOLUTEPITCH`** — Treat the `pitch` parameter as an absolute value rather than an offset to the calculated aim pitch. (Implied by `CMF_AIMDIRECTION`.)
- **`CMF_OFFSETPITCH`** — Treat the `pitch` parameter as an offset to the calculated aim pitch.
- **`CMF_SAVEPITCH`** — Store the pitch value in the spawned projectile's own `pitch` field. With `CMF_OFFSETPITCH` that is the combined (aim plus offset) pitch. In aim modes 0 and 1 without `CMF_ABSOLUTEPITCH`/`CMF_OFFSETPITCH`, the raw `pitch` parameter is stored without affecting the flight path.
- **`CMF_ABSOLUTEANGLE`** — Use the `angle` parameter as the projectile's absolute world angle instead of adding it to the calculated aim angle. Neither the aim at the target nor the caller's facing affects the horizontal direction (the caller's facing still positions the `spawnofs_xy` offset, and the vertical aim is unchanged).

### Ownership and tracking flags

- **`CMF_TRACKOWNER`** — When the caller is itself a projectile, the new missile's owner (`target`) is walked back through the chain of projectiles to the first non-projectile, so kill credit and infighting go to the original shooter. This happens even without the flag while the caller still has `MISSILE` set. The flag makes the check also count actors whose class default has `MISSILE`, so the walk-back still works after the calling projectile has exploded (`P_ExplodeMissile` clears `MISSILE`). Without the flag in that case, the exploded projectile itself becomes the owner.
- **`CMF_CHECKTARGETDEAD`** — If the aim target (on Zandronum always `self->target`) is `NULL` and the aim mode needs a target (not mode 2), jump the caller to its `See` state if it has one. Despite the name, only a missing target triggers this: a dead but still-referenced target is fired at normally. Zandronum jumps unconditionally; UZDoom skips the jump for a monster whose health is 0 or less.

## Return value

None.

## Behavior notes

- **Target selection:** The missile always targets `self->target` in Zandronum (no pointer parameter). If `self->target` is `NULL` and the aim mode requires a target, the missile is not spawned and `CMF_CHECKTARGETDEAD` controls whether the actor transitions to `See` state.
- **Pitch calculations:** The wiki notes this function has "bad pitch calculations which needed to be preserved for backwards compatibility." In practice: aim modes 0 and 1 use the vertical velocity of the trajectory to the target. `CMF_ABSOLUTEPITCH` replaces it with `pitch`, `CMF_OFFSETPITCH` adds `pitch` to it, and aim mode 2 always uses `pitch` as absolute. In all three, positive `pitch` means upward, the reverse of the normal actor pitch sign.
- **Aim origin:** Mode 0 temporarily moves the caller to the offset position before aiming, so the offset is accounted for. Mode 1 spawns at the offset point but computes the direction from the caller's own origin, so several offset shots fly parallel.
- **Network behavior (Zandronum-specific):** Spawning is filtered first. A client only runs the spawn when the caller or the missile class is `NETFL_CLIENTSIDEONLY`, and then tags the missile `NETFL_CLIENTSIDEONLY`. The server skips such client-side-only spawns entirely. For a normal server-side spawn, the server sends `SERVERCOMMANDS_SpawnMissile` to clients.
- **Homing missiles:** If the caller is not a projectile and the spawned projectile has `SEEKERMISSILE`, its `tracer` is set to the caller's `target`. When the caller is a projectile, the caller's `tracer` is copied instead, but only under a flag test that differs by engine: Zandronum tests `SEEKERMISSILE`'s bit against the caller's first flags word (the bit `STEALTH` uses), UZDoom tests the caller's `SEEKERMISSILE`.
- **Spectral (friendly) missiles:** If the missile has `MF4_SPECTRAL` set, its `FriendPlayer` field is set based on the target's player relationship to ensure proper spectral missile behavior.

## Examples

```text
// Simple missile attack (aim mode 0)
Actor FireballZombie : ZombieMan
{
  States
  {
  Missile:
    POSS E 10 A_FaceTarget
    POSS F 8 A_CustomMissile("DoomImpBall", 32)
    POSS E 8
    Goto See
  }
}

// Two parallel shots from either side (aim mode 1)
Actor TwinShotImp : DoomImp
{
  States
  {
  Missile:
    TROO EF 8 A_FaceTarget
    TROO G 0 A_CustomMissile("DoomImpBall", 32, -8, 0, CMF_AIMOFFSET)
    TROO G 6 A_CustomMissile("DoomImpBall", 32, 8, 0, CMF_AIMOFFSET)
    Goto See
  }
}

// Fixed-direction spread, 10 degrees upward, relative to facing (aim mode 2)
Actor FanBaron : BaronOfHell
{
  States
  {
  Missile:
    BOSS EF 8 A_FaceTarget
    BOSS G 0 A_CustomMissile("BaronBall", 32, 0, -15, CMF_AIMDIRECTION, 10)
    BOSS G 8 A_CustomMissile("BaronBall", 32, 0, 15, CMF_AIMDIRECTION, 10)
    Goto See
  }
}
```

## See also

- [Creating projectiles](../concepts/creating-projectiles.md) — Projectile flag bundles and state requirements.
- [Creating monsters](../concepts/creating-monsters.md) — Monster state requirements and action calling conventions.
- `A_FireCustomMissile` — weapon-variant action for firing projectiles from weapon state tables.
