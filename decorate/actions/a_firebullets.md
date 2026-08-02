# `void A_FireBullets(angle spread_xy, angle spread_z, int numbullets, int damageperbullet, class<Actor> pufftype, int flags, fixed range)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_FireBullets` (retrieved 2026-07-31, oldid=53826) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1680-1694` and helper implementations.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FireBullets)` at `src/thingdef/thingdef_codeptr.cpp:1680`.

Defines a custom hitscan weapon attack, firing one or more bullets with optional spread and spawning an impact puff at the point of hit. The weapon's `AttackSound` is played on the weapon channel if the weapon exists.

**Engine-family divergence: This function differs significantly from the ZDoom-wiki ZScript version.** Zandronum's implementation takes 7 parameters and does not support spawning a simultaneous missile projectile (the wiki's `missile`, `Spawnheight`, and `Spawnofs_xy` parameters do not exist). Three of the wiki's nine `FBF_*` flags (`FBF_PUFFTARGET`, `FBF_PUFFMASTER`, `FBF_PUFFTRACER`) do not exist in Zandronum's enum and are not available.

## Parameters

- **`angle spread_xy`** — The random spread applied left and right, in angle units. When `FBF_EXPLICITANGLE` is not set, this is treated as the range for uniform random spread (applied as `Random2() * (spread_xy / 255)`, per integer-division semantics, not the ZScript floating-point formula). Default: 0.
- **`angle spread_z`** — The random spread applied up and down, in angle units. Same spread semantics as `spread_xy`. Default: 0.
- **`int numbullets`** — Count of bullets to fire. Special cases:
  - `0`: Fires one bullet with perfect accuracy, ignoring spread.
  - `1`: Fires one bullet with perfect accuracy if this is the first shot from the weapon (when `player.refire == 0`); otherwise applies normal spread. This is the "first-shot accuracy" behavior of the Doom Pistol and Chaingun.
  - `-1`: Fires one bullet, but with spread always applied, even on the first shot.
  - Negative values other than `-1` (e.g., `-2`, `-3`) are treated as their absolute value by the helper's `if (NumberOfBullets == -1)` check; values like `-2` pass through to the `for (i=0; i<numbullets; i++)` loop with a negative bound, firing **zero bullets** (this is a wiki/fork divergence: the wiki claims negative values behave like positive ones, but Zandronum only special-cases exactly `-1`).
  - Positive values > 1: Multiple bullets are fired, each with spread applied.
- **`int damageperbullet`** — Damage dealt per bullet. Unless `FBF_NORANDOM` is set, this is multiplied by `random(1, 3)` per bullet.
- **`class<Actor> pufftype`** — The actor class to spawn at impact. Default: `BulletPuff`. If null, defaults to the engine's `BulletPuff` class.
- **`int flags`** — Combination of zero or more `FBF_*` flags (combined with `|`). Available flags:
  - `FBF_USEAMMO` (1) — If set, consume ammo from the ready weapon. This is the default; passing `0` or other flags without this one disables ammo consumption.
  - `FBF_NORANDOM` (2) — If set, damage is not multiplied by `random(1, 3)`; the full `damageperbullet` is dealt per bullet.
  - `FBF_EXPLICITANGLE` (4) — If set, `spread_xy` and `spread_z` are used as explicit angle *offsets* rather than ranges for random spread.
  - `FBF_NOPITCH` (8) — If set, the vertical aim angle (pitch) is not adjusted to match the bullet slope; the attack fires horizontally.
  - `FBF_NOFLASH` (16) — If set, no weapon flash is shown (does not call `PlayAttacking2`).
  - `FBF_NORANDOMPUFFZ` (32) — If set, the puff is spawned at exact z coordinate without random vertical offset.
- **`fixed range`** — Maximum distance bullets can hit. Default: `0` (interpreted as `PLAYERMISSILERANGE`, which is 8192 map units).

## Behavior notes

- **Server-authoritative in networked play.** In client mode, this function returns early before firing (unless `cl_hitscandecalhack` or `CLIENT_ShouldPredictPuffs()` are set). The actual bullet traces are computed server-side.
- **Spread math divergence from ZScript.** Zandronum computes random spread as `Random2() * (spread / 255)` using integer division (spreading by `(spread_xy / 255)` first, then multiplying the random value). ZScript's floating-point version `spread_xy * Random2() / 255.` produces different results for small angles. This affects precision and weapon feel.
- **Cheat spread fan.** If the player has the `CF2_SPREAD` cheat enabled, two additional bullet fans are fired at ±ANGLE_45/3 (±15°) relative to the attack angle, in addition to the primary fire. This is a Zandronum-specific cheat feature.
- **Bot notifications.** The function checks the ready weapon's class name and sends bot-event notifications for hardcoded weapon names (`Pistol`, `Shotgun`, `Chaingun`, `SuperShotgun`, `Minigun`, `BFG10k`). Custom weapons with names other than these do not trigger bot events, even if they inherit from the standard weapons.
- **Requires a player.** The action early-returns if called on a non-player actor (`if (!self->player) return;`). In DECORATE, it compiles in any actor's state table but no-ops on decorations and monsters.

## Examples

```
Fire:
    TRIF A 5 Bright A_FireBullets(0, 0, 1, 45, "RiflePuff", FBF_USEAMMO|FBF_NORANDOM);
    TRIF B 5 Bright;
    TRIG A 10;
    TRIG B 0 A_ReFire;
    Goto Ready;
```

This fires a single bullet with no spread, 45 damage (no random multiplier), a rifle puff at impact, consuming ammo on each shot.
