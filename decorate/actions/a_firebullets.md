# `void A_FireBullets(angle spread_xy, angle spread_z, int numbullets, int damageperbullet, class<Actor> pufftype, int flags, fixed range)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_FireBullets` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_FireBullets&oldid=53826) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1680-1694` and helper implementations (`:1504-1552`, `:1554-1677`), `wadsrc/static/actors/shared/inventory.txt:12`, `src/g_shared/a_artifacts.cpp:2423-2429`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FireBullets)` at `src/thingdef/thingdef_codeptr.cpp:1680`.

Defines a custom hitscan weapon attack, firing one or more bullets with optional spread and spawning an impact puff at the point of hit. The weapon's `AttackSound` is played on the weapon channel if the weapon exists.

**Engine-family divergence: This function differs significantly from the ZDoom-wiki ZScript version.** Zandronum's implementation takes 7 parameters and does not support spawning a simultaneous missile projectile (the wiki's `missile`, `Spawnheight`, and `Spawnofs_xy` parameters do not exist). Three of the wiki's nine `FBF_*` flags (`FBF_PUFFTARGET`, `FBF_PUFFMASTER`, `FBF_PUFFTRACER`) do not exist in Zandronum's enum and are not available.

## Parameters

- **`angle spread_xy`** — The random spread applied left and right, in angle units. When `FBF_EXPLICITANGLE` is not set, this is treated as the range for uniform random spread (applied as `Random2() * (spread_xy / 255)`, per integer-division semantics, not the ZScript floating-point formula). Required: it has no default.
- **`angle spread_z`** — The random spread applied up and down, in angle units. Same spread semantics as `spread_xy`. Required: it has no default.
- **`int numbullets`** — Count of bullets to fire. Special cases:
  - `0`: Fires one bullet with perfect accuracy, ignoring spread.
  - `1`: Fires one bullet with perfect accuracy if this is the first shot from the weapon (when `player.refire == 0`); otherwise applies normal spread. This is the "first-shot accuracy" behavior of the Doom Pistol and Chaingun.
  - `-1`: Fires one bullet, but with spread always applied, even on the first shot.
  - Negative values other than `-1` (e.g., `-2`, `-3`) are not normalized: the helper only rewrites exactly `-1` to `1`, so values like `-2` reach the `for (i=0; i<numbullets; i++)` loop with a negative bound and fire **zero bullets** (ammo, flash and sound still happen) (this is a wiki/fork divergence: the wiki claims negative values behave like positive ones, but Zandronum only special-cases exactly `-1`).
  - Positive values > 1: Multiple bullets are fired, each with spread applied.
- **`int damageperbullet`** — Damage dealt per bullet. Unless `FBF_NORANDOM` is set, this is multiplied by `random(1, 3)` per bullet.
- **`class<Actor> pufftype`** — The actor class to spawn at impact. Default: `BulletPuff`. If null, defaults to the engine's `BulletPuff` class.
- **`int flags`** — Combination of zero or more `FBF_*` flags (combined with `|`). Available flags:
  - `FBF_USEAMMO` (1) — If set, consume ammo from the ready weapon. If it lacks enough ammo (and infinite ammo is off), the action returns without firing. This is the default; passing `0` or other flags without this one disables ammo consumption.
  - `FBF_NORANDOM` (2) — If set, damage is not multiplied by `random(1, 3)`; the full `damageperbullet` is dealt per bullet.
  - `FBF_EXPLICITANGLE` (4) — If set, `spread_xy` and `spread_z` are used as explicit angle *offsets* rather than ranges for random spread.
  - `FBF_NOPITCH` (8) — If set, no bullet slope is computed (no autoaim, view pitch ignored), so the base pitch is 0 and the attack fires horizontally before any `spread_z`.
  - `FBF_NOFLASH` (16) — If set, no weapon flash is shown (does not call `PlayAttacking2`).
  - `FBF_NORANDOMPUFFZ` (32) — If set, the puff is spawned at exact z coordinate without random vertical offset.
- **`fixed range`** — Maximum distance bullets can hit. Default: `0` (interpreted as `PLAYERMISSILERANGE`, which is 8192 map units).

## Behavior notes

- **Server-authoritative in networked play.** In client mode, this function returns early before firing (unless `cl_hitscandecalhack` or `CLIENT_ShouldPredictPuffs()` are set). The actual bullet traces are computed server-side.
- **Spread math divergence from ZScript.** Zandronum computes random spread as `Random2() * (spread / 255)` using integer division (spreading by `(spread_xy / 255)` first, then multiplying the random value). ZScript's floating-point version `spread_xy * Random2() / 255.` produces different results for small angles. This affects precision and weapon feel.
- **Spread rune fan.** If the player has `CF2_SPREAD` set, two additional bullet fans are fired at ±ANGLE_45/3 (±15°) relative to the attack angle, in addition to the primary fire. Ammo is only consumed once. The flag is set by the Spread rune powerup (`APowerSpread::InitEffect`, `src/g_shared/a_artifacts.cpp:2423-2429`), not a cheat. This is Zandronum-specific.
- **Bot notifications.** The function checks the ready weapon's class name and sends bot-event notifications for hardcoded weapon names (`Pistol`, `Shotgun`, `Chaingun`, `SuperShotgun`, `Minigun`, `BFG10k`). Custom weapons with names other than these do not trigger bot events, even if they inherit from the standard weapons.
- **Requires a player.** The action early-returns if called on a non-player actor (`if (!self->player) return;`). On Zandronum it is declared in `shared/inventory.txt`, so it only compiles in an `Inventory`-derived state table (a weapon's); a monster must use `A_CustomBulletAttack`.
- **Null `ReadyWeapon` is not guarded.** Outside client mode the bot-notification step calls `weapon->GetClass()` unconditionally (and a server also reads `weapon->AttackSound` for the sound broadcast), so firing from a player with no ready weapon, e.g. from a CustomInventory state, dereferences a null pointer. Zandronum only: UZDoom null-checks the weapon and has no bot step.

## Examples

```decorate
ACTOR Rifle : Pistol
{
  States
  {
  Fire:
    PISG A 4
    PISG B 6 Bright A_FireBullets(0, 0, 1, 45, "BulletPuff", FBF_USEAMMO|FBF_NORANDOM)
    PISG C 4
    PISG B 5 A_ReFire
    Goto Ready
  }
}
```

This fires a single bullet with no spread, 45 damage (no random multiplier), a bullet puff at impact, consuming ammo on each shot.

## Engine-family divergence: full wiki parameter set, extra flags, and floating-point spread math

UZDoom's `A_FireBullets` (`wadsrc/static/zscript/actors/inventory/stateprovider.zs`) is the full ZDoom-wiki ZScript version referenced in the intro paragraph above, not Zandronum's reduced 7-parameter variant: it takes the wiki's full 10-parameter signature, including `missile`, `Spawnheight`, and `Spawnofs_xy` for spawning a simultaneous projectile alongside the hitscan bullets (via `SpawnPlayerMissile`/`AimBulletMissile`). All nine `FBF_*` flags exist in UZDoom's `EFireBulletsFlags` enum (`wadsrc/static/zscript/constants.zs`), including the three Zandronum lacks: `FBF_PUFFTARGET`, `FBF_PUFFMASTER`, `FBF_PUFFTRACER`. Spread math also diverges from what's documented for Zandronum above: UZDoom multiplies the spread by a signed random value and divides by 255 in floating point — exactly the "ZScript floating-point formula" contrasted against Zandronum's integer-division formula in the "Spread math divergence from ZScript" bullet above, confirming that comparison directly from UZDoom source rather than the wiki page alone. Negative `numbullets` handling also diverges: UZDoom treats any negative value the same as `-1` (it rewrites any negative count to 1, then always applies spread) — it does not reproduce Zandronum's bug where negative values other than exactly `-1` fire zero bullets.

## Engine-family divergence: no client/server split, no bot notifications, no spread rune

UZDoom has no client/server authority split anywhere in its source tree (no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style construct exists at all) — the "Server-authoritative in networked play" behavior note above is Zandronum-only; on UZDoom the bullet traces are computed identically regardless of network role. UZDoom's implementation also has no hardcoded bot-notification system (`BOTS_PostWeaponFiredEvent`) — the "Bot notifications" behavior note above is Zandronum-only. It likewise has no `CF2_SPREAD` handling anywhere in its source — the "Spread rune fan" behavior note above is Zandronum-only, so exactly the requested number of bullets fires per call regardless of powerups. Ammo depletion also differs. UZDoom only applies it when the call originates from an actual weapon psprite state, not merely from a ready weapon existing. Zandronum has no such check: with `FBF_USEAMMO` it depletes the ready weapon's ammo whenever `ReadyWeapon` is non-null, including when called from a CustomInventory state.
