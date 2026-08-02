# `void A_FireCustomMissile(class<Actor> missiletype, angle angle = 0, bool useammo = false, int spawnofs_xy = 0, fixed spawnheight = 0, bool aimatangle = false, angle pitch = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_FireCustomMissile` (retrieved 2026-07-31, oldid=45025) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1739–1815`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FireCustomMissile)` on `AActor` class (callable from any actor's state table).

Fires a projectile from a player's weapon or a CustomInventory. **This action is player-only** — it silently does nothing when called from non-player actors. **Fork divergence note:** This page describes the ZDoom Wiki, which documents GZDoom/UZDoom. Zandronum's signature and behavior differ significantly from the wiki: parameter 5 is a single boolean (`aimatangle`), not a flags field; the wiki's `FPF_*` flag constants do not exist in Zandronum and produce incorrect behavior if passed as integers. The wiki also describes a deprecation warning (recommending `A_FireProjectile`); this warning is GZDoom-family only and does not apply to Zandronum, where `A_FireCustomMissile` is the standard weapon-variant projectile action.

## Parameters

- **missiletype** — The class name of the projectile to fire (required).
- **angle** — Adjusts horizontal aiming. Behavior depends on `aimatangle` (see "Aiming behavior" below). Default is `0`.
- **useammo** — If true and the weapon has ammo, deducts ammo cost before firing. If ammo runs out, the action returns without firing. Default is `false`.
- **spawnofs_xy** — Moves the projectile spawn point perpendicular to the actor's facing angle, in the plane parallel to the ground. Positive values offset to the right, negative to the left. Zandronum interprets this as an integer. Default is `0`.
- **spawnheight** — Raises the projectile spawn point vertically (in fixed-point units) before firing. Default is `0`.
- **aimatangle** — Affects how the `angle` parameter is used when aiming. See "Aiming behavior" below. Default is `false`.
- **pitch** — Vertical aiming adjustment. Subtracts from the player's current pitch before firing; positive values aim downward, negative values aim upward. Only effective when autoaim is present or when manually aiming. Default is `0`.

## Aiming behavior

The `aimatangle` parameter controls how the `angle` parameter is applied:

- **`aimatangle = false` (default)** — The player aims a projectile toward their target (with autoaim if enabled). The `angle` parameter offsets the projectile's final trajectory angle. Internally, the missile is spawned with its calculated aim, then the velocity vector is rotated by the `angle` offset (preserving speed while changing direction).
- **`aimatangle = true`** — The `angle` parameter is added directly to the actor's facing angle before spawning the projectile, bypassing aim refinement.

## Return value

None.

## Behavior notes

- **Player-only requirement:** The action checks `if (!self->player) return;` at entry, so it is only callable from player pawn actors in `Fire`, `Hold`, `AltFire`, `AltHold`, or similar weapon states. Non-player actors calling this action silently do nothing and do not fire a projectile.
- **Ammo depletion:** When `useammo` is true and the actor has a ready weapon, `DepleteAmmo(weapon->bAltFire, true)` is called. If this returns false (ammo exhausted), the action returns without firing. If `useammo` is false, ammo is never checked regardless of weapon state.
- **Weapon requirement:** The ammo check uses `player->ReadyWeapon`, so firing happens only if a weapon is equipped (or `useammo` is false).
- **Network handling:** The action checks `NETWORK_ShouldActorNotBeSpawned()` to avoid spawning client-side-only actor types. The spawned projectile is broadcast via `SERVERCOMMANDS_SpawnMissileExact()` in server mode.
- **Spread cheat:** If the player has the `CF2_SPREAD` cheat flag set, three projectiles fire instead of one: the primary at `shootangle`, and two additional projectiles at ±15° (ANGLE_45 / 3) offsets. All three use the same aiming logic.
- **Spectral (friendly) missiles:** If the spawned projectile has `MF4_SPECTRAL` set, its `health` field is set to `-1` to enable friendly-fire semantics.
- **Homing missiles:** If the spawned projectile has `MF2_SEEKERMISSILE` set, its `tracer` field is automatically populated with the autoaimed target actor (if any).

## Examples

```
// Simple missile attack
Fire:
    WGUN A 0 A_FireCustomMissile("MyMissile")
    WGUN A 6
    Goto Ready

// Fire with ammo consumption
Fire:
    RIFL A 0 A_FireCustomMissile("Bullet", 0, true)
    RIFL A 10
    Goto Ready

// Fire with vertical aiming adjustment
Fire:
    ROCKETLAUNCHER A 0 A_FireCustomMissile("Rocket", 0, false, 0, 0, false, -16)
    ROCKETLAUNCHER A 8
    Goto Ready

// Fire with angle offset (aimatangle = false, offset velocity direction)
Fire:
    WGUN A 0 A_FireCustomMissile("WideShot", 15, false, 0, 0, false)
    WGUN A 6
    Goto Ready
```

## See also

- [A_CustomMissile](a_custommissile.md) — monster-variant projectile action for non-player actors.
- [Creating weapons](../concepts/creating-weapons.md) — weapon state names and firing-state semantics.
- [Creating projectiles](../concepts/creating-projectiles.md) — projectile flags and state requirements.
