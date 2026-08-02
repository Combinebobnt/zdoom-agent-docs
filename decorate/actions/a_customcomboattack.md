# `void A_CustomComboAttack(class<Actor> missiletype, float spawnheight, int damage, sound meleesound = "", name damagetype = "none", bool bleed = true)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_CustomComboAttack` (retrieved 2026-08-01, oldid=40208) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1416–1465`, `wadsrc/static/actors/actor.txt:264`, and `src/p_enemy.cpp:245–280`.
**Bucket:** Action function, defined on `AActor` (callable from any actor's state table).

A customizable combo attack for monsters that adapts based on range. The calling actor faces its target, then performs either a melee attack (if the target is within melee range) or fires a projectile (if out of range and a missile type is specified). Does nothing if there is no current target.

## Fork divergence — wiki type mismatch

The ZDoom Wiki page describing this function (oldid=40208) uses `string` types for `missiletype`, `meleesound`, and `damagetype`, but Zandronum's actual declaration uses `class<Actor>`, `sound`, and `name` respectively. The wiki signature predates any known divergence in this function across ZDoom-family engines; a current wiki revision was not checked and may differ further.

## Server-side behavior (Zandronum fork divergence)

**Facing happens before the network gate:** The action immediately calls `A_FaceTarget`, which runs on both server and client. The rest of the attack (range check, damage, missile spawn) is server-side only — the function returns immediately on a client unless it called `A_FaceTarget` first. This differs from the typical pattern of gating the entire action before any side effects.

On a Zandronum client, the function returns immediately after this point (`if (NETWORK_InClientMode()) return;`), preventing any further execution. The server broadcasts successful missile spawns to clients via `SERVERCOMMANDS_SpawnMissile` to keep the simulated world in sync; melee damage and sounds are not explicitly broadcast but are handled by the standard damage and sound propagation mechanisms.

## Parameters

- **missiletype** — The class name of the projectile to spawn if the target is out of melee range. Takes `class<Actor>` type. If `null` or omitted and the target is out of range, the attack does nothing (silent no-op). Required for ranged branch.
- **spawnheight** — Height offset for the spawned projectile, in map units. Takes `float` type. The actual spawn height is adjusted to `self->z + spawnheight + self->GetBobOffset()` to account for bobbing (relevant for monsters with `FLOATBOB` or similar movement).
- **damage** — Damage inflicted in a melee hit, before randomization. Takes `int` type. The wiki describes this as being passed to the melee attack; the actual damage depends on what `P_DamageMobj` does with it (typically straight application with no additional modification, unlike `A_CustomPunch`'s random multiplier).
- **meleesound** — Sound to play on a successful melee hit. Takes `sound` type. Default is empty string (no sound). Played on the `CHAN_WEAPON` channel and replicated to clients in multiplayer (via the `true` parameter to `S_Sound`).
- **damagetype** — Type of damage dealt in melee. Takes `name` type. Default is `"none"`, which is silently converted to `NAME_Melee` at entry — **you cannot deal `"none"`-typed melee damage with this action**. Any other type (e.g. `"Fire"`, `"Plasma"`) is passed through to `P_DamageMobj`.
- **bleed** — Whether the target bleeds on a successful melee hit. Takes `bool` type. Default `true`. If `true`, calls `P_TraceBleed`, which may spawn blood decal actors on nearby walls. Uses the actual damage inflicted (`newdam`); if `newdam` is `0` (damage fully absorbed), bleeds using the original `damage` value instead — a hit that deals no actual damage still produces blood.

## Melee range check

The melee branch activates if `self->CheckMeleeRange()` returns `true`. This function performs several checks:

- **Distance:** The 2D distance (ignoring vertical gap) from the actor to its target must be less than `self->meleerange + target->radius`. `meleerange` is the actor's `MeleeRange` property (default 64 map units for typical monsters); adding the target's radius accounts for hitbox size.
- **Vertical clearance:** Unless the actor has the `MF5_NOVERTICALMELEERANGE` flag, the target must be within the actor's height. Target's z must be less than `self->z + self->height` (not above) and target's z + target height must be greater than `self->z` (not below).
- **Friendship:** The function returns `false` if the actor is friendly to its target (`IsFriend` check).
- **Sight:** The actor must have line-of-sight to the target (`P_CheckSight`); targets behind walls/obstacles fail this check.

If all checks pass, melee is used; otherwise the missile branch is attempted.

## Missile spawn and behavior

If out of melee range and `missiletype` is not null:

- **Spawn location:** The projectile is spawned at `self->x`, `self->y`, and `self->z + spawnheight + self->GetBobOffset()`. The implementation temporarily adjusts `self->z` during the spawn call to help the aiming calculation see the correct height, then restores it.
- **Targeting:** The projectile is spawned as if targeting `self->target` via `P_SpawnMissileXYZ`. The missile is aimed at the target.
- **Seeker missiles:** If the spawned projectile has the `MF2_SEEKERMISSILE` flag, the `tracer` field is automatically populated with the target actor, allowing homing actions like `A_Tracer2` to work.
- **Spawn collision:** The projectile passes through `P_CheckMissileSpawn`, which handles collision with geometry. On success, the server broadcasts the spawn to clients.
- **Silent failure:** If spawn fails (e.g., blocked), nothing else happens — no fallback, no sound, no error.

If the target is out of range and `missiletype` is null: the attack silently does nothing (no alternative fallback).

## Return value

None (returns immediately on client after `A_FaceTarget`).

## Interaction with actor properties and flags

- **`meleerange` property:** Controls the distance threshold. Default 64 units. Monsters can override this via the `MeleeRange` property.
- **`MF5_NOVERTICALMELEERANGE` flag:** Disables vertical-clearance check in melee range evaluation.
- **Target pointer:** Requires `self->target` to be non-null; does nothing otherwise.
- **`MF2_SEEKERMISSILE` flag on projectile:** Automatically sets `tracer` to the target.

## Examples

From the wiki example, reproducing the Baron of Hell's combo attack:

```decorate
Melee:

Missile:
  BOSS EF 8 A_FaceTarget
  BOSS G 8 A_CustomComboAttack("BaronBall", 32, 10 * random(1, 8), "baron/melee")
  Goto See
```

This spawns either a melee attack (dealing `10–80` damage) or a `BaronBall` projectile, depending on range. The `8` spawn height places the missile origin 8 units above the actor's center (before adding bobbing offset). The `"baron/melee"` sound is played on a successful melee hit.

A more explicit two-pronged example:

```decorate
Attack:
  DMON E 8 A_FaceTarget
  DMON F 8 A_CustomComboAttack("DemonShot", 24, 20, "demon/melee", "Melee")
  DMON E 8
  Goto See
```

This deals 20 melee damage of type `"Melee"`, spawns `DemonShot` if out of range, and plays `"demon/melee"` on hit. The projectile spawns at height 24 above the actor's position.

## See also

- [`A_CustomMeleeAttack`](a_custommeleeattack.md) — melee-only variant (simpler, no projectile fallback).
- [`A_CustomMissile`](a_custommissile.md) — projectile-only variant with more configuration options (aim modes, flags).
- [Creating monsters](../concepts/creating-monsters.md) — Monster attack state design and action calling conventions.
- [Creating projectiles](../concepts/creating-projectiles.md) — Projectile flag bundles and state requirements.
