# `A_RailAttack` (weapon railgun beam attack)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_RailAttack` (retrieved 2026-08-01, oldid=53912) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1926-1983` and `wadsrc/static/actors/shared/inventory.txt:14`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RailAttack)` in `src/thingdef/thingdef_codeptr.cpp`.

Fires a rail beam attack (hitscan, piercing beam with particle trail). Only works when called from a player pawn's weapon state table — silently returns (no-op) if the actor lacks a player. The beam pierces all targets along its path by default (can be limited with `RGF_NOPIERCING`).

## Signature

```
action void A_RailAttack(int damage, int spawnofs_xy = 0, int useammo = true, color color1 = "", color color2 = "", int flags = 0, float maxdiff = 0, class<Actor> pufftype = "BulletPuff", float spread_xy = 0, float spread_z = 0, float range = 0, int duration = 0, float sparsity = 1.0, float driftspeed = 1.0, class<Actor> spawnclass = "none", float spawnofs_z = 0)
```

## Parameters

### `damage` (int)

Damage per target hit. Applied once to each actor along the beam path, unless `RGF_NOPIERCING` stops the beam at the first hit. No default — must be supplied.

### `spawnofs_xy` (int, optional, default 0)

Horizontal screen offset in map units (from the player's centered viewpoint) where the beam originates. Positive values shift left, negative shift right. Used for dual-gun effects or off-center firing. Default is 0 (centered).

### `useammo` (int, optional, default 1)

Whether to deplete weapon ammo on firing. If true (nonzero) and the weapon runs out of ammo before the attack resolves, the function returns without firing. Depletion checks `ReadyWeapon->DepleteAmmo()` and happens regardless of whether the beam actually hits anything. Default is true (1).

### `color1` (color, optional, default "")

Color of the spiral particle trail surrounding the beam. Empty string `""` makes the spiral invisible; `0` draws it in a random shade of gray (selected at beam-fire time, not per particle). Accepts RRGGBB hex, named colors from `X11R6RGB` lump, or any ZScript color constant. Default is `""` (invisible).

### `color2` (color, optional, default "")

Color of the core/center beam. Empty string `""` makes the core invisible; `0` draws it in a random shade of gray. Same color formats as `color1`. Default is `""` (invisible).

### `flags` (int, optional, default 0)

Bitfield controlling rail behavior. Flags are combined with `|`. Zandronum defines five flags:

#### Zandronum flags (Zandronum 3.2.1)

- `RGF_SILENT` (1) — Suppresses the weapon's attack sound. Without this flag, the weapon fires with its `AttackSound` property.

- `RGF_NOPIERCING` (2) — Stops the beam at the first enemy hit, rather than passing through all targets. Useful for single-target railguns; by default the beam pierces all actors in its path.

- `RGF_EXPLICITANGLE` (4) — Treats `spread_xy` and `spread_z` as explicit firing angles (in degrees, added directly to aim direction) rather than maximum random deviation. Without this flag, spreads are applied as random offsets (angles chosen randomly from ±0 to ±spread value).

- `RGF_FULLBRIGHT` (8) — Rail particles render at full brightness, ignoring sector lighting. Without this flag, particles fade with the map's light levels.

- `RGF_CENTERZ` (16) — Vertical offset (`spawnofs_z`) originates from half the player's height (adjusted downward when crouched) rather than from the `Player.AttackZOffset` property. Without this flag, offset is applied relative to the attack Z-offset property.

#### Flags in ZDoom wiki not present in Zandronum

- `RGF_NORANDOMPUFFZ` — Listed in upstream ZDoom/GZDoom docs but **not exported in Zandronum 3.2.1**. Treating it as a raw integer will have no effect.

### `maxdiff` (float, optional, default 0.0)

Jagged/lightning-like distortion of the beam path. Higher values increase warping; 0 produces a perfectly straight beam. Internally used to randomize beam segmentation. Default is 0.0 (straight).

### `pufftype` (class<Actor>, optional, default "BulletPuff")

Actor class spawned where the beam hits (impact effect). By default, the puff only appears in rare circumstances (e.g., hitting a dormant/invisible monster) unless the puff actor has the `ALWAYSPUFF` flag. Regardless of visibility, the puff's `DamageType` property is still applied to targets, enabling custom damage type handling. Puffs with `ALWAYSPUFF` spawn on floor/ceiling hits. Default is `BulletPuff`.

### `spread_xy` (float, optional, default 0.0)

Horizontal (yaw) aiming spread. Interpreted as:
- If `RGF_EXPLICITANGLE` is set: explicit angle offset in degrees, added to the aimed direction.
- Otherwise: maximum random horizontal deviation; actual spread = `random(±spread_xy)` degrees.

Default is 0.0 (no spread).

### `spread_z` (float, optional, default 0.0)

Vertical (pitch) aiming spread. Same semantics as `spread_xy`, but for up/down aiming. Default is 0.0 (no spread).

### `range` (float, optional, default 0.0)

Maximum distance in map units the beam travels before vanishing. Set to 0 to use the engine default of 8192 map units. Default is 0.0 (uses 8192).

### `duration` (int, optional, default 0)

Lifetime of rail particles in tics (1/35 second each). Set to 0 to use the engine default of 35 tics (1 second). Default is 0 (uses 35 tics).

### `sparsity` (float, optional, default 1.0)

Distance between individual trail particles as a multiplier. Values < 1.0 pack particles closer together (denser trail); > 1.0 space them farther apart (sparser trail). A multiplier of 0 defaults to 1.0. Default is 1.0 (normal spacing).

### `driftspeed` (float, optional, default 1.0)

Speed at which particles drift away from their spawn point along the beam path, as a multiplier. Higher values make the trail dissipate/widen more quickly. Default is 1.0 (normal drift).

### `spawnclass` (class<Actor>, optional, default "none")

If non-null (not `"none"`), spawn this actor class along the beam trail instead of using particle effects. Actors spawn at intervals determined by `sparsity` (units apart along the beam). Each spawned actor inherits the shooter's pitch and is linked as an owned actor (preventing self-damage from the trail). **Warning:** Spawning many actors per tic (especially additive-renderstyle actors) causes severe performance loss. Using `level.SpawnParticle()` in ZScript or custom particle effects is **strongly recommended** for complex visual trails. Default is `"none"` (use particle effects).

### `spawnofs_z` (float, optional, default 0.0)

Vertical screen offset in map units (from the player's aimed height) where the beam originates. Positive values shift the beam origin upward, negative downward. Offset is applied from the `Player.AttackZOffset` property by default (shifted when crouched), or from half the player's height if `RGF_CENTERZ` is set. Default is 0.0 (no offset).

## Behavior notes

### Player-pawn-only constraint

The function checks `if (!self->player) return;` before proceeding. This means:
- The function silently does nothing when called from a monster's state table.
- It only works in player weapon states or player-state-specific actions.
- The `ReadyWeapon` check assumes a weapon is equipped; no additional check is performed if `ReadyWeapon` is NULL (though this is rare in normal gameplay).

### Ammo depletion timing

Ammo is depleted **before** the beam fires. If `useammo` is true and the weapon has 0 ammo, the function returns without firing, preventing even silent/flagged attacks from being audible.

### Network behavior (multiplayer)

In Zandronum multiplayer mode:
- **Server-side determination:** The server calculates the beam path and damage; clients receive the result.
- **Client-side unlagged:** If the server enables client-side unlagging (via `UNLAGGED_DrawRailClientside()`), clients may render their own rail beam locally for latency compensation, but damage is still authoritative on the server.
- **Client-mode escape:** Actors with `NETFL_CLIENTSIDEONLY` flag can fire locally without server involvement.

### Spread calculation

Spread is applied *per call* (when the state executes the action), not per particle:
- Without `RGF_EXPLICITANGLE`: `actual_angle = aimed_angle + random(±spread_xy * 255/255) = aimed_angle + random(±spread_xy)` degrees (random in integer range, then scaled to degrees).
- With `RGF_EXPLICITANGLE`: `actual_angle = aimed_angle + spread_xy` (explicit offset, no randomization).

### Differences from ZDoom/GZDoom

The ZDoom Wiki page documents upstream ZDoom/GZDoom features not present in Zandronum 3.2.1:

- **`RGF_NORANDOMPUFFZ` flag:** Does not exist in Zandronum. The puff Z-offset is always randomized (within reason).
- **`spiraloffset` parameter:** Not in Zandronum — spiral always starts at a fixed angle.
- **`limit` parameter:** Not in Zandronum — pierce limit is not configurable (always pierces all targets unless `RGF_NOPIERCING` is set).
- **Parameter defaults:** Zandronum's `color1` and `color2` default to empty string `""`, not the integer `0` that ZScript accepts as a synonym for "random gray."

When using this action, ensure DECORATE syntax — `A_RailAttack(damage, spawnofs_xy, useammo, color1, color2, ...)` — not ZScript syntax (which supports named arguments and has a different parameter order for some values).

## Related functions

- **`A_CustomRailgun`** — Monster-facing variant with target aiming (`aim` parameter) and fewer parameters. Defined in the same file.

## Examples

### Basic railgun (centered, full beam)

```
actor SimpleRailgun : Weapon
{
  Default
  {
    Weapon.SelectionOrder 100;
    Weapon.SlotNumber 6;
    Weapon.AmmoType "Clip";
    Weapon.AmmoUse 1;
    AttackSound "weapons/rbeam";
  }

  States
  {
  Ready:
    RLGN B 1 A_WeaponReady;
    Loop;

  Deselect:
    RLGN B 1 A_Lower;
    Loop;

  Select:
    RLGN B 1 A_Raise;
    Loop;

  Fire:
    RLGN C 4;
    RLGN D 4 bright A_RailAttack(20, 0, 1, "ffff00", "ffff00");
    RLGN E 4 bright;
    RLGN F 4;
    TNT1 A 0 A_ReFire;
    Goto Ready;
  }
}
```

This fires a gold beam (`"ffff00"`) with 20 damage, centered, using ammo, with no spread or special effects.

### Railgun with spread and custom puff

```
A_RailAttack(
  15,            // damage
  0,             // spawnofs_xy
  1,             // useammo
  "0088ff",      // color1 (blue spiral)
  "00ccff",      // color2 (light blue core)
  RGF_FULLBRIGHT | RGF_EXPLICITANGLE,  // flags
  2.0,           // maxdiff (jagged beam)
  "ElectricPuff", // pufftype
  5.0,           // spread_xy (±5 degrees horizontal)
  2.0,           // spread_z (±2 degrees vertical)
  16384,         // range (2x default)
  70,            // duration (2 seconds)
  0.8,           // sparsity (denser trail)
  1.5            // driftspeed (particles spread faster)
);
```

This fires a jagged, denser electric blue beam with random spread, custom puff, and extended range.
