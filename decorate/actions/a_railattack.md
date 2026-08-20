# `A_RailAttack` (weapon railgun beam attack)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_RailAttack` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RailAttack&oldid=53912) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1926-1983` and `wadsrc/static/actors/shared/inventory.txt:14`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RailAttack)` in `src/thingdef/thingdef_codeptr.cpp`.

Fires a rail beam attack (hitscan, piercing beam with particle trail). Only works when called from a player pawn's weapon state table — silently returns (no-op) if the actor lacks a player. The beam pierces all targets along its path by default (can be limited with `RGF_NOPIERCING`).

## Signature

```text
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

## Engine-family divergence: full wiki parameter and flag set present

UZDoom implements `A_RailAttack` as a ZScript `action` method on the shared weapon/inventory
state-provider class (`wadsrc/static/zscript/actors/inventory/stateprovider.zs`), which builds an
`FRailParams` struct and hands off to a native `RailAttack`/`P_RailAttack` (`src/playsim/p_map.cpp`)
for the actual trace/damage/trail work. The "Differences from ZDoom/GZDoom" section above is
accurate for Zandronum, but all three features it lists as wiki-only are genuinely implemented on
UZDoom, not just declared:

- `RGF_NORANDOMPUFFZ` is a working flag: the native code translates it into a puff-spawn flag
  (`PF_NORANDOMZ`) that suppresses the puff's normal randomized Z offset.
- `spiraloffset` is a real 17th parameter (default `270`) that is passed all the way through to
  `P_DrawRailTrail` (`src/playsim/p_effect.cpp`), which uses it as the starting angle for the
  spiral particle trail — it is not ignored.
- `limit` is a real 18th parameter (default `0`, meaning unlimited) that caps how many actors the
  beam can pierce before stopping, independent of `RGF_NOPIERCING` — the native trace callback
  stops once the hit count reaches `limit` when `limit` is nonzero.

## Engine-family divergence: color defaults and no player/team-color override

UZDoom's signature defaults `color1`/`color2` to the integer `0` rather than Zandronum's `""` —
consistent with the existing "Parameter defaults" bullet above — and on UZDoom a `0` genuinely
means "random gray" for both colors: `P_DrawRailTrail` (`src/playsim/p_effect.cpp`) independently
resolves `color1 == 0 ? -1 : ParticleColor(color1)` for the outer spiral and
`color2 == 0 ? -1 : ParticleColor(color2)` for the inner core (`-1` being the particle system's
"pick a random shade of gray" sentinel), with no further special-casing anywhere in the rail-attack
code path.

This is a real behavioral divergence, not just a default-syntax one. Zandronum's rail-attack helper
(`P_RailAttackWithPossibleSpread` in `src/p_map.cpp`, which `A_RailAttack` calls before reaching
`P_RailAttack` proper) contains an additional player-sourced special case that UZDoom has no
equivalent of: when the calling actor is a player and both colors evaluate to `0` — which is
exactly what Zandronum's `""` default evaluates to — it substitutes the firing player's own
client-configured railgun color for the outer/spiral color (or, if the player is on a team in a
team-based gamemode, the *team's* configured railgun color for the outer color and the player's own
color for the inner/core color) instead of leaving the beam colorless. UZDoom's `TEAMINFO` parser
(`src/gamedata/teaminfo.cpp`) does accept a `RailColor` key, but it's grouped with several others
that are scanned and discarded — the value is never stored on the team struct, and nothing in
UZDoom's rail-attack code path, native or ZScript, ever reads a per-team or per-player rail color
back out. A UZDoom railgun left at default colors is therefore genuinely colorless/random-gray for
both the spiral and the core, with no per-player or per-team override of any kind, unlike a
player-fired Zandronum railgun at default colors.

## Engine-family divergence: no client/server authority split

The "Network behavior (multiplayer)" section above describes Zandronum-only architecture. UZDoom's
native rail-attack code has no equivalent of Zandronum's client-mode early-return, no
unlagged-clientside-draw escape hatch, and no clientside-only network-flag bypass — grepped
tree-wide, UZDoom has none of the client/server authority primitives those checks rely on. The beam
trace, damage, and trail spawn all run through one unified code path with no
server-authoritative/client-prediction distinction to speak of.

One related but separate difference: UZDoom's ammo-depletion check additionally requires the
calling state to be a weapon PSprite state (the same state-type guard used by every other
ammo-consuming action in its state-provider class), on top of `useammo` being true and a valid
ready weapon being present. Zandronum's equivalent check has no such state-type guard and does not
verify the ready weapon is non-null either — it depletes ammo unconditionally whenever `UseAmmo` is
true. Concretely: calling `A_RailAttack` with `useammo` true from a state that isn't part of the
weapon's own PSprite chain (e.g. an actor state, or a state pointer invoked outside normal
weapon-fire dispatch) silently skips ammo depletion on UZDoom, while Zandronum's unconditional call
would still attempt it.

## Related functions

- **`A_CustomRailgun`** — Monster-facing variant with target aiming (`aim` parameter) and fewer parameters. Defined in the same file.

## Examples

### Basic railgun (centered, full beam)

```text
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

```text
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
