# `void A_CustomMissile(class<Actor> missiletype, float spawnheight = 32, int spawnofs_xy = 0, float angle = 0, int flags = 0, float pitch = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_CustomMissile` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_CustomMissile&oldid=49278) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1159` and `wadsrc/static/actors/actor.txt:206`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CustomMissile)` on `AActor` class (callable from any actor's state table).

A customizable projectile attack for non-player actors, typically used by monsters to launch a projectile at their target. **Fork divergence note:** This page describes a ZDoom Wiki source which documents GZDoom/UZDoom. Zandronum's version **does not include a 7th `ptr` parameter** to select the target actor — the target is always `self->target`. The wiki's deprecation notice (recommending `A_SpawnProjectile` instead) is GZDoom-family only and does not apply to Zandronum, where `A_CustomMissile` remains the standard missile-spawning action.

## Parameters

- **missiletype** — The class name of the projectile to fire (required).
- **spawnheight** — Raises the projectile spawn point on the actor by this amount in units. Default is `32`. Note: the wiki describes this as `double`, but Zandronum declares it as `float`.
- **spawnofs_xy** — Moves the projectile spawn point perpendicular to the actor's facing angle (to the right if positive, left if negative). Zandronum's implementation interprets this as an integer, while the wiki describes a double; the practical effect is likely rounding. Default is `0`.
- **angle** — Adds this much offset to the calculated aim angle at the target. Default is `0`.
- **flags** — Bitwise-OR combination of aim-mode flags and modifiers. See "Aim modes and flags" below. Default is `0`.
- **pitch** — Vertical aiming offset. Positive values aim downward, negative values aim upward. Only used when one of the pitch-control flags is set. Default is `0`.

## Aim modes and flags

The `flags` parameter's low 2 bits select one of three aim modes; the remaining bits control pitch and angle behavior. Constants are defined in `wadsrc/static/actors/constants.txt`.

### Aim modes (bits 0–1, value 0–2)

- **Aim mode 0 (neither flag set)** — Aim directly at the target. Performs a temporary position adjustment for better accuracy (adjusts `self`'s position, spawns the missile, then restores). Requires a valid `self->target`. This is the default.
- **Aim mode 1 (`CMF_AIMOFFSET`)** — Aim parallel to a reference trajectory (spawn height 32, xy-offset 0), correcting for the caller's actual spawnheight and spawnofs_xy. Useful for spawning multiple projectiles at once with consistent aim. Requires a valid target.
- **Aim mode 2 (`CMF_AIMDIRECTION`)** — Aim in a fixed direction specified by `angle` and `pitch`, ignoring the target entirely. No target required. Automatically implies `CMF_ABSOLUTEPITCH`. Useful for pattern-based or directed attacks.

### Pitch and angle flags

- **`CMF_ABSOLUTEPITCH`** — Treat the `pitch` parameter as an absolute value rather than an offset to the calculated aim pitch. (Implied by `CMF_AIMDIRECTION`.)
- **`CMF_OFFSETPITCH`** — Treat the `pitch` parameter as an offset to the calculated aim pitch.
- **`CMF_SAVEPITCH`** — Store the pitch value used for the missile in the spawned projectile's own `pitch` field (requires `CMF_AIMDIRECTION`, `CMF_ABSOLUTEPITCH`, or `CMF_OFFSETPITCH`).
- **`CMF_ABSOLUTEANGLE`** — Treat the `angle` parameter as an absolute value rather than an offset to the calculated aim angle. The calling actor's angle is still factored in.

### Ownership and tracking flags

- **`CMF_TRACKOWNER`** — When a projectile fires another projectile (e.g., an exploding missile that spawns secondary missiles), this flag ensures the secondary missile tracks back to the original owner for proper credit/infighting. Without this flag, the secondary missile points to the intermediate projectile as its owner, which can cause unintended behavior. Default Zandronum behavior (without this flag) preserves 2.0.x-era quirks for mod compatibility.
- **`CMF_CHECKTARGETDEAD`** — If the target is missing and the chosen aim mode requires a target (modes 0 or 1), abort the attack by transitioning the calling actor to its `See` state if one exists. (Monsters must have health above 0 to successfully enter a state.)

## Return value

None.

## Behavior notes

- **Target selection:** The missile always targets `self->target` in Zandronum (no pointer parameter). If `self->target` is `NULL` and the aim mode requires a target, the missile is not spawned and `CMF_CHECKTARGETDEAD` controls whether the actor transitions to `See` state.
- **Pitch calculations:** The wiki notes this function has "bad pitch calculations which needed to be preserved for backwards compatibility." Zandronum's pitch calculation logic is verifiable in the source `switch` block: aim modes 0 and 1 compute pitch from the trajectory to the target unless `CMF_ABSOLUTEPITCH` or `CMF_OFFSETPITCH` overrides it; aim mode 2 uses the provided pitch directly.
- **Network behavior (Zandronum-specific):** In client-mode (`NETWORK_InClientMode()`), the missile is spawned but tagged with `NETFL_CLIENTSIDEONLY` to prevent duplicate propagation. In server mode, a `SERVERCOMMANDS_SpawnMissile` command is broadcast to clients to ensure synchronization.
- **Homing missiles:** If the spawned projectile has `MF2_SEEKERMISSILE` set, its `tracer` field (used by `A_Tracer2` and similar homing actions) is automatically populated with the target actor.
- **Spectral (friendly) missiles:** If the missile has `MF4_SPECTRAL` set, its `FriendPlayer` field is set based on the target's player relationship to ensure proper spectral missile behavior.

## Examples

```text
// Simple missile attack (aim mode 0)
Missile:
    POSS E 10 A_FaceTarget
    POSS F 8 A_CustomMissile("NormalBullet", 48)
    POSS E 8
    Goto See

// Multiple projectiles at once using parallel aiming (aim mode 1)
SpreadMissile:
    DRON E 8
    DRON F 8 A_CustomMissile("Projectile", 32, -8, 0, CMF_AIMOFFSET)
    DRON F 8 A_CustomMissile("Projectile", 32, 8, 0, CMF_AIMOFFSET)
    DRON E 8
    Goto See

// Directed attack without a target (aim mode 2)
FixedAngleAttack:
    DEMON E 8 A_CustomMissile("DemonShot", 64, 0, 0, CMF_AIMDIRECTION, 0)
    DEMON F 8
    Goto See
```

## See also

- [Creating projectiles](../concepts/creating-projectiles.md) — Projectile flag bundles and state requirements.
- [Creating monsters](../concepts/creating-monsters.md) — Monster state requirements and action calling conventions.
- `A_FireCustomMissile` — weapon-variant action for firing projectiles from weapon state tables.
