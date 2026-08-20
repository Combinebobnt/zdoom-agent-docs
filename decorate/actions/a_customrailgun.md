# `A_CustomRailgun` (customizable rail attack for monsters)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_CustomRailgun` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CustomRailgun&oldid=53914) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1998` and `wadsrc/static/actors/constants.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CustomRailgun)` in `src/thingdef/thingdef_codeptr.cpp`.

Fires a customizable rail beam attack (hitscan, piercing beam with particle trail) for monsters or any non-weapon actor. Supports optional target aiming and velocity-leading calculations. The beam pierces all targets along its path by default (can be limited with `RGF_NOPIERCING`).

## Engine-family divergence

UZDoom's `A_CustomRailgun` (`src/playsim/p_actionfunctions.cpp`, `DEFINE_ACTION_FUNCTION(AActor, A_CustomRailgun)`) differs from the Zandronum-specific behavior described throughout this file in several ways:

- **The full 19-parameter signature is real.** UZDoom's native declaration (`wadsrc/static/zscript/actors/actor.zs`) matches the ZDoom Wiki's 19-parameter form exactly, adding `spiraloffset` (int, default `270`), `limit` (int, default `0`), and `veleffect` (double, default `3`) beyond the 16 parameters Zandronum accepts. The "Zandronum limitation" callout under Signature does not apply to UZDoom.
- **`spiraloffset` is genuinely configurable**, unlike Zandronum where the spiral always starts at a fixed 270-degree angle. The value is passed straight through to the particle-trail routine.
- **`veleffect` is genuinely configurable**, unlike Zandronum where the velocity-leading multiplier used in `aim` modes 1/2 is hardcoded to `3`.
- **`limit` is present in the signature but is a no-op.** The function parses a `limit` argument, but `p_actionfunctions.cpp` unconditionally overwrites it with `p.limit = 0` before calling `P_RailAttack`, discarding whatever was passed. The pierce limit cannot actually be configured through this parameter in the current UZDoom source, despite the signature matching the wiki.
- **`RGF_NORANDOMPUFFZ` is implemented** (`RAF_NORANDOMPUFFZ = 32` in `src/playsim/p_local.h`, honored in `P_RailAttack` to set `PF_NORANDOMZ` on the puff), unlike Zandronum 3.2.1 where it is not exported.
- **No client/server authority gating.** UZDoom's `A_CustomRailgun` has no equivalent of Zandronum's client-mode early return or unlagged position reconciliation — the function always runs to completion on every machine. UZDoom's source tree has no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style client/server split anywhere, so the "Network behavior (multiplayer)" subsection below does not apply.
- **No player-pawn railgun color override.** UZDoom has no equivalent of Zandronum's team/individual railgun-color substitution when called from a player pawn with `color1==0 && color2==0` — colors are always used as passed (or via the shared `0`-means-random-blue/gray default described under `color1`/`color2` below), regardless of who is calling. The "Player-pawn note" below does not apply.

Everything else described in this file — the `aim`/`spread_xy`/`spread_z`/`maxdiff`/`sparsity`/`driftspeed`/`spawnclass` parameters, the early return when `aim` is 1/2 with no target, `MF_STEALTH`/`MF_AMBUSH` handling, per-call (not per-particle) spread calculation, the `0`-means-random-color/`-1`(`"none"`)-means-invisible color semantics, and pierce vs. no-pierce via `RGF_NOPIERCING` — matches UZDoom's implementation.

## Signature

```text
action void A_CustomRailgun(int damage, int spawnofs_xy = 0, color color1 = "", color color2 = "", int flags = 0, int aim = 0, double maxdiff = 0, class<Actor> pufftype = "BulletPuff", double spread_xy = 0, double spread_z = 0, double range = 0, int duration = 0, double sparsity = 1.0, double driftspeed = 1.0, class<Actor> spawnclass = "none", double spawnofs_z = 0)
```

**Zandronum limitation:** This function accepts exactly **16 parameters**. The ZDoom Wiki describes a 19-parameter version (with `spiraloffset`, `limit`, and `veleffect`) not present in Zandronum. Attempting to pass additional parameters beyond the 16th will result in a parse error.

## Parameters

### `damage` (int)

Damage per target hit. Applied once to each actor along the beam path, unless `RGF_NOPIERCING` stops the beam at the first hit. No default — must be supplied.

### `spawnofs_xy` (int, optional, default 0)

Horizontal offset in map units (from the actor's center) where the beam originates. Negative values shift the beam to the actor's left, positive values shift it right. Used for off-center firing (e.g., dual rail effects on multi-limbed monsters). Default is 0 (centered).

### `color1` (color, optional, default "")

Color of the spiral particle trail surrounding the beam. Empty string `""` makes the spiral invisible; `0` draws it in a random shade of blue (selected at beam-fire time, not per particle). Accepts RRGGBB hex, named colors from `X11R6RGB` lump, or any DECORATE color constant. Default is `""` (invisible).

### `color2` (color, optional, default "")

Color of the core/center beam. Empty string `""` makes the core invisible; `0` draws it in a random shade of gray. Same color formats as `color1`. Default is `""` (invisible).

**Player-pawn note:** When called from a player pawn with both `color1==0` and `color2==0`, the engine overrides these with the player's railgun color settings (team color in team game modes, individual player color in deathmatch). This differs from the upstream ZDoom/GZDoom behavior of using random blue/gray shades.

### `flags` (int, optional, default 0)

Bitfield controlling rail behavior. Flags are combined with `|`. Zandronum defines five flags:

#### Zandronum flags (Zandronum 3.2.1)

- `RGF_SILENT` (1) — Suppresses the weapon/actor attack sound. Without this flag, the attack fires with the actor's `AttackSound` property (monsters/inventory), or the weapon's `AttackSound` (if called from a weapon).

- `RGF_NOPIERCING` (2) — Stops the beam at the first enemy hit, rather than passing through all targets. Useful for single-target railguns; by default the beam pierces all actors in its path.

- `RGF_EXPLICITANGLE` (4) — Treats `spread_xy` and `spread_z` as explicit firing angles (in degrees, added directly to aim direction) rather than maximum random deviation. Without this flag, spreads are applied as random offsets (angles chosen randomly from ±0 to ±spread value).

- `RGF_FULLBRIGHT` (8) — Rail particles render at full brightness, ignoring sector lighting. Without this flag, particles fade with the map's light levels.

- `RGF_CENTERZ` (16) — Vertical offset (`spawnofs_z`) originates from half the actor's height rather than from the actor's attack Z-offset (8 map units for non-players). Without this flag, offset is applied relative to the attack Z-offset.

#### Flags in ZDoom wiki not present in Zandronum

- `RGF_NORANDOMPUFFZ` — Listed in upstream ZDoom/GZDoom docs but **not exported in Zandronum 3.2.1**. Treating it as a raw integer will have no effect.

### `aim` (int, optional, default 0)

Determines the attack direction:

- `0` — Shoot in the direction the actor is looking (default). Does not require a target.

- `1` — Aim at the actor's current target, with velocity leading (the engine predicts target position by subtracting `target.velx * 3` and `target.vely * 3` to lead the shot). Returns silently without firing if the target is NULL.

- `2` — Aggressive leading aim: same as `1`, but also offsets the firing position relative to the aimed direction before re-aiming, creating a more direct "lead towards the actor's predicted position" effect. Returns silently without firing if the target is NULL.

### `maxdiff` (double, optional, default 0.0)

Jagged/lightning-like distortion of the beam path. Higher values increase warping; 0 produces a perfectly straight beam. Internally used to randomize beam segmentation. Default is 0.0 (straight).

### `pufftype` (class<Actor>, optional, default "BulletPuff")

Actor class spawned where the beam hits (impact effect). By default, the puff only appears in rare circumstances (e.g., hitting a dormant/invisible monster) unless the puff actor has the `ALWAYSPUFF` flag. Regardless of visibility, the puff's `DamageType` property is still applied to targets, enabling custom damage type handling. Default is `BulletPuff`.

### `spread_xy` (double, optional, default 0.0)

Horizontal (yaw) aiming spread. Interpreted as:
- If `RGF_EXPLICITANGLE` is set: explicit angle offset in degrees, added to the aimed direction.
- Otherwise: maximum random horizontal deviation; actual spread = `random(±spread_xy)` degrees.

Default is 0.0 (no spread).

### `spread_z` (double, optional, default 0.0)

Vertical (pitch) aiming spread. Same semantics as `spread_xy`, but for up/down aiming. Default is 0.0 (no spread).

### `range` (double, optional, default 0.0)

Maximum distance in map units the beam travels before vanishing. Set to 0 to use the engine default of 8192 map units. Default is 0.0 (uses 8192).

### `duration` (int, optional, default 0)

Lifetime of rail particles in tics (1/35 second each). Set to 0 to use the engine default of 35 tics (1 second). Default is 0 (uses 35 tics).

### `sparsity` (double, optional, default 1.0)

Distance between individual trail particles as a multiplier. Values < 1.0 pack particles closer together (denser trail); > 1.0 space them farther apart (sparser trail). A multiplier of 0 defaults to 1.0. Default is 1.0 (normal spacing).

### `driftspeed` (double, optional, default 1.0)

Speed at which particles drift away from their spawn point along the beam path, as a multiplier. Higher values make the trail dissipate/widen more quickly. Default is 1.0 (normal drift).

### `spawnclass` (class<Actor>, optional, default "none")

If non-null (not `"none"`), spawn this actor class along the beam trail instead of using particle effects. Actors spawn at intervals determined by `sparsity` (units apart along the beam). Each spawned actor inherits the shooter's pitch and is linked as an owned actor (preventing self-damage from the trail). **Warning:** Spawning many actors per tic (especially additive-renderstyle actors) causes severe performance loss. Using particle effects or limiting spawn frequency is strongly recommended. Default is `"none"` (use particle effects).

### `spawnofs_z` (double, optional, default 0.0)

Vertical offset in map units (from the actor's center) where the beam originates. Positive values shift the beam origin upward, negative downward. Offset is applied from the actor's center by default, or from half the actor's height if `RGF_CENTERZ` is set. Default is 0.0 (no offset).

## Behavior notes

### Early returns

The function silently returns (no-op) in these cases:
- When `aim` is 1 or 2 and the actor has no target (checked before any damage is dealt).
- In network client mode, unless unlagged client-side rail drawing is enabled (see "Network behavior" below).

### Stealth monster handling

If the actor has the `MF_STEALTH` flag set, the function sets `visdir = 1`, making the actor briefly visible to players (detected during attack).

The actor's `MF_AMBUSH` flag is unconditionally cleared when the function fires (regardless of success/failure).

### Velocity leading in aim modes

When `aim` is 1 or 2, the engine calculates a predicted intercept point by subtracting `target.velx * 3` and `target.vely * 3` from the target's position. This 3-multiplier (`veleffect` in upstream ZDoom) is **hardcoded in Zandronum** and cannot be configured; the wiki's `veleffect` parameter does not exist here.

### Spread calculation

Spread is applied *per call* (when the state executes the action), not per particle:
- Without `RGF_EXPLICITANGLE`: actual angle offset is computed as `random(±spread_xy * 255/255) = random(±spread_xy)` degrees (random in integer range, then scaled to degrees).
- With `RGF_EXPLICITANGLE`: `actual_angle = aimed_angle + spread_xy` (explicit offset, no randomization).

### Particle spiral parameters

The spiral of particles always starts at a fixed angle of 270 degrees. The wiki's `spiraloffset` parameter (upstream ZDoom/GZDoom) **does not exist in Zandronum 3.2.1** — spiral starting angle cannot be configured.

Pierce limit is not configurable. The beam either pierces all targets (`RGF_NOPIERCING` unset) or stops at the first hit (`RGF_NOPIERCING` set). The wiki's `limit` parameter (upstream ZDoom/GZDoom) does not exist in Zandronum.

### Network behavior (multiplayer)

In Zandronum multiplayer:
- **Server-side authority:** The server calculates the beam path and damage; clients do not perform this calculation themselves unless unlagged drawing is enabled.
- **Unlagged client-side drawing:** If the server enables client-side unlagging via the `UNLAGGED_DrawRailClientside()` path, clients may render a rail beam locally for latency compensation, but damage application remains server-authoritative.
- **Positioning synchronization:** Actor position is reconciled before the beam fires (via `UNLAGGED_Reconcile`) and restored afterward (via `UNLAGGED_Restore`) to ensure consistent line-of-trace results.

## Differences from ZDoom/GZDoom

The ZDoom Wiki page documents upstream ZDoom/GZDoom features not present in Zandronum 3.2.1:

- **`RGF_NORANDOMPUFFZ` flag:** Does not exist in Zandronum. The puff Z-offset is always randomized (within reason).
- **`spiraloffset` parameter:** Not in Zandronum — spiral always starts at a fixed 270-degree angle.
- **`limit` parameter:** Not in Zandronum — pierce limit is not configurable (always pierces all targets unless `RGF_NOPIERCING` is set).
- **`veleffect` parameter:** Not in Zandronum — velocity leading multiplier is hardcoded to 3.0.
- **Color overrides for players:** When `color1==0` and `color2==0` on a player-pawn caller, Zandronum substitutes the player's team/individual railgun color settings, not random blue/gray shades as upstream ZDoom suggests.

When writing code intended to run on both Zandronum and GZDoom-family engines, be aware of these parameter and behavior differences.

## Related functions

- **`A_RailAttack`** — Player-weapon variant (requires player pawn; takes `useammo` parameter instead of `aim`). Defined in the same file.
- **`A_CustomMissile`** — Customizable projectile attack for monsters (not a hitscan beam).
- **`A_CustomMeleeAttack`** — Customizable melee attack for monsters.

## Examples

### Basic rail attack (straight, no aiming)

```text
actor RailDrone : Monster
{
  Default
  {
    Health 50;
    Radius 20;
    Height 56;
    Mass 200;
    Speed 12;
  }

  States
  {
  Spawn:
    BSPD A 10 A_Look;
    Loop;

  See:
    BSPD A 4 A_Chase;
    Loop;

  Missile:
    BSPD B 10 A_FaceTarget;
    BSPD C 5 bright A_CustomRailgun(20, 0, "0000FF", "FFFFFF");
    BSPD D 4 bright;
    Goto See;

  Death:
    BSPD E 5;
    BSPD F 5 A_NoBlocking;
    BSPD G 5;
    Stop;
  }
}
```

This fires a blue+white rail with 20 damage, straight ahead. No aiming or spread.

### Targeted rail with leading aim

```text
A_CustomRailgun(
  30,            // damage
  0,             // spawnofs_xy
  "FF6600",      // color1 (orange spiral)
  "FFFF00",      // color2 (yellow core)
  RGF_FULLBRIGHT | RGF_EXPLICITANGLE,  // flags
  2,             // aim (lead target's velocity)
  0.0,           // maxdiff
  "BulletPuff",  // pufftype
  0.0,           // spread_xy
  0.0,           // spread_z
  0,             // range (default 8192)
  0,             // duration (default 35 tics)
  1.0,           // sparsity
  1.0            // driftspeed
);
```

This fires a bright orange+yellow rail that leads the target's movement, pierces all enemies, and deals 30 damage.

### Dual off-center rails with spread

```text
A_CustomRailgun(
  15,            // damage
  -8,            // spawnofs_xy (left side)
  "0088FF",      // color1 (blue spiral)
  "00CCFF",      // color2 (light blue core)
  RGF_NOPIERCING,  // stops at first hit
  1,             // aim (aim at target)
  1.0,           // maxdiff (jagged beam)
  "ElectricPuff",  // pufftype
  3.0,           // spread_xy (±3 degrees horizontal)
  2.0,           // spread_z (±2 degrees vertical)
  0,             // range
  70,            // duration (2 seconds)
  0.8,           // sparsity (denser trail)
  1.5            // driftspeed
);
```

Call this twice with `spawnofs_xy = -8` and `+8` to create a dual-rail effect (e.g., in a looping Missile state sequence). Each rail is off-center, aims at the target, spreads slightly, and stops on first hit.
