# `A_CustomRailgun` (customizable rail attack for monsters)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_CustomRailgun` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CustomRailgun&oldid=53914) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1998` and `wadsrc/static/actors/constants.txt`; color parsing `src/thingdef/thingdef_parse.cpp:100`, trace/puffs `src/p_map.cpp:4835`, trail/spawnclass `src/p_effect.cpp:704`, unlagged gating `src/unlagged.cpp:368`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CustomRailgun)` in `src/thingdef/thingdef_codeptr.cpp`.

Fires a customizable rail beam attack (hitscan, piercing beam with particle trail) for monsters or any non-weapon actor. Supports optional target aiming, with the aim trailing a moving target's velocity. The beam pierces all targets along its path by default (can be limited with `RGF_NOPIERCING`).

## Engine-family divergence

UZDoom's `A_CustomRailgun` (`src/playsim/p_actionfunctions.cpp`, `DEFINE_ACTION_FUNCTION(AActor, A_CustomRailgun)`) differs from the Zandronum-specific behavior described throughout this file in several ways:

- **The full 19-parameter signature is real.** UZDoom's native declaration (`wadsrc/static/zscript/actors/actor.zs`) matches the ZDoom Wiki's 19-parameter form exactly, adding `spiraloffset` (int, default `270`), `limit` (int, default `0`), and `veleffect` (double, default `3`) beyond the 16 parameters Zandronum accepts. The "Zandronum limitation" callout under Signature does not apply to UZDoom.
- **`spiraloffset` is genuinely configurable**, unlike Zandronum where the spiral always starts at a fixed 270-degree angle. The value is passed straight through to the particle-trail routine.
- **`veleffect` is genuinely configurable**, unlike Zandronum where the velocity-trailing multiplier used in `aim` modes 1/2 is hardcoded to `3`.
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

Color of the spiral particle trail surrounding the beam. The DECORATE parser stores the empty string `""` as 0, which draws the spiral in random shades of blue (picked separately for each particle). `"none"` is stored as -1 and makes the spiral invisible. Any other string (RRGGBB hex or a named color from the `X11R6RGB` lump) is marked internally so that even black never collides with 0. Default is `""` (random blue).

### `color2` (color, optional, default "")

Color of the core/center beam. `""` (stored as 0) draws the core in random shades of gray, picked per particle; `"none"` makes it invisible. Same color formats as `color1`. Default is `""` (random gray).

**Player-pawn note:** When called from a player pawn with both colors left at `""` (0), Zandronum overrides them with the player's railgun color settings. In team game modes, for a player on a team, the spiral takes the team's railgun color and the core the player's own railgun color. Otherwise the spiral takes the player's railgun color and the core is white. This differs from the upstream ZDoom/GZDoom behavior of using random blue/gray shades.

### `flags` (int, optional, default 0)

Bitfield controlling rail behavior. Flags are combined with `|`. Zandronum defines five flags:

#### Zandronum flags (Zandronum 3.2.1)

- `RGF_SILENT` (1) — Suppresses the weapon/actor attack sound. Without this flag, the attack fires with the actor's `AttackSound` property (non-player callers), or the ready weapon's `AttackSound` (player callers), falling back to `weapons/railgf` when that is unset.

- `RGF_NOPIERCING` (2) — Stops the beam at the first actor hit (not only enemies), rather than passing through all targets. Useful for single-target railguns; by default the beam pierces all actors in its path.

- `RGF_EXPLICITANGLE` (4) — Treats `spread_xy` and `spread_z` as explicit firing angles (in degrees, added directly to aim direction) rather than maximum random deviation. Without this flag, spreads are applied as random offsets (angles chosen randomly from ±0 to ±spread value).

- `RGF_FULLBRIGHT` (8) — Rail particles render at full brightness, ignoring sector lighting. Without this flag, particles fade with the map's light levels.

- `RGF_CENTERZ` (16) — The beam originates at half the actor's height plus `spawnofs_z`. Without this flag, the attack Z-offset is added on top of that (8 map units for non-players, `AttackZOffset` scaled by crouch for players).

#### Flags in ZDoom wiki not present in Zandronum

- `RGF_NORANDOMPUFFZ` — Listed in upstream ZDoom/GZDoom docs but **not exported in Zandronum 3.2.1**. Treating it as a raw integer will have no effect.

### `aim` (int, optional, default 0)

Determines the attack direction:

- `0` — Shoot in the direction the actor is facing (default). Does not require a target. Pitch is still auto-aimed at whatever lies in the aim cone.

- `1` — Aim at the actor's current target, with the aim trailing behind it: the engine subtracts `target.velx * 3` and `target.vely * 3` from the target's position, so the shot goes where the target was, not where it is heading. The beam is fired from the `spawnofs_xy`-offset origin parallel to that aim line. Returns silently without firing if the target is NULL.

- `2` — Same as `1`, but the shooter's position is first shifted by `spawnofs_xy` (which is then zeroed) and the angle is recomputed from there, so the beam converges on the aim point instead of running parallel to it. Returns silently without firing if the target is NULL. In Zandronum's source this shift indexes the fine sine/cosine tables with the raw, unshifted actor angle rather than a fine-angle index, so the shift is not computed from a valid table entry.

With `aim` 1 or 2, a target with `MF_SHADOW` adds a random yaw error. Zandronum's `actor.txt` declares `aim` as `bool aim = false`, but DECORATE parses `bool` parameters as integers, so `2` reaches the code intact.

### `maxdiff` (double, optional, default 0.0)

Jagged/lightning-like distortion of the drawn beam. Higher values increase warping; 0 produces a perfectly straight beam. It jitters only the core trail particles (and `spawnclass` actors) within ±`maxdiff`; the hit trace itself stays straight. Default is 0.0 (straight).

### `pufftype` (class<Actor>, optional, default "BulletPuff")

Actor class spawned where the beam hits (impact effect). On an actor hit, the puff appears only if the victim has `NOBLOOD` or is `DORMANT` or `INVULNERABLE`, unless the puff actor has the `ALWAYSPUFF` flag. Where the beam ends on a wall, a puff spawns only with `ALWAYSPUFF`. Floor and ceiling puffs with `ALWAYSPUFF` were added after Zandronum 3.2.1 (commit `f26a7bcbc`); a 3.2.1 build spawns none there. Regardless of visibility, the puff's `DamageType` property is still applied to targets, enabling custom damage type handling. Default is `BulletPuff`.

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

Lifetime of rail particles in tics (1/35 second each). Set to 0 to use the engine default of 35 tics (1 second) for the spiral and 33 tics for the core. Default is 0.

### `sparsity` (double, optional, default 1.0)

Distance between individual trail particles as a multiplier. Values < 1.0 pack particles closer together (denser trail); > 1.0 space them farther apart (sparser trail). A multiplier of 0 defaults to 1.0. Default is 1.0 (normal spacing).

### `driftspeed` (double, optional, default 1.0)

Speed at which particles drift away from their spawn point, outward from the beam, as a multiplier. Higher values make the trail dissipate/widen more quickly. Default is 1.0 (normal drift).

### `spawnclass` (class<Actor>, optional, default "none")

If non-null (not `"none"`), spawn this actor class along the beam trail instead of using particle effects. Actors spawn at intervals determined by `sparsity` (map units apart along the beam; in Zandronum a `sparsity` below 1 means 32 units). In Zandronum each spawned actor only gets the beam's yaw; its pitch and `target` are left unset. UZDoom also sets its pitch to the beam's and its `target` to the shooter. In Zandronum multiplayer the server skips trail drawing entirely, so these actors exist only on clients. **Warning:** Spawning many actors per tic (especially additive-renderstyle actors) causes severe performance loss. Using particle effects or limiting spawn frequency is strongly recommended. Default is `"none"` (use particle effects).

### `spawnofs_z` (double, optional, default 0.0)

Vertical offset in map units where the beam originates. Positive values shift the beam origin upward, negative downward. In Zandronum the base is half the actor's height plus the attack Z-offset (8 units for non-players, `AttackZOffset` for players) by default, or just half the actor's height if `RGF_CENTERZ` is set. Default is 0.0 (no offset).

## Behavior notes

### Early returns

The function silently returns (no-op) in these cases:
- When `aim` is 1 or 2 and the actor has no target (checked before any damage is dealt).
- In network client mode, unless unlagged client-side rail drawing is enabled (see "Network behavior" below).

### Stealth monster handling

If the actor has the `MF_STEALTH` flag set, the function sets `visdir = 1`, making the actor briefly visible to players (detected during attack).

The actor's `MF_AMBUSH` flag is cleared once the no-target check has passed, even on a client that then skips the attack. It is not cleared when `aim` is 1 or 2 and there is no target.

### Velocity trailing in aim modes

When `aim` is 1 or 2, the engine aims at a point behind the target by subtracting `target.velx * 3` and `target.vely * 3` from the target's position. This makes the shot lag a moving target rather than lead it. This 3-multiplier (`veleffect` in upstream ZDoom) is **hardcoded in Zandronum** and cannot be configured; the wiki's `veleffect` parameter does not exist here.

### Spread calculation

Spread is applied *per call* (when the state executes the action), not per particle:
- Without `RGF_EXPLICITANGLE`: actual angle offset is computed as `random(±spread_xy * 255/255) = random(±spread_xy)` degrees (random in integer range, then scaled to degrees).
- With `RGF_EXPLICITANGLE`: `actual_angle = aimed_angle + spread_xy` (explicit offset, no randomization).

### Particle spiral parameters

The spiral of particles always starts at a fixed angle of 270 degrees. The wiki's `spiraloffset` parameter (upstream ZDoom/GZDoom) **does not exist in Zandronum 3.2.1** — spiral starting angle cannot be configured.

Pierce limit is not configurable. The beam either pierces all targets (`RGF_NOPIERCING` unset) or stops at the first hit (`RGF_NOPIERCING` set). The wiki's `limit` parameter (upstream ZDoom/GZDoom) does not exist in Zandronum.

### Network behavior (multiplayer)

In Zandronum multiplayer:
- **Server-side authority:** The server calculates the beam path and damage; clients skip the attack (unless the actor is client-handled) and draw the trail when the server tells them to.
- **Unlagged client-side drawing:** `UNLAGGED_DrawRailClientside()` only applies when the shooter is a player, unlagged is not disabled by `ZADF_NOUNLAGGED`, and that player has unlagged turned on. A client then runs the rail locally for its own player only, but damage application remains server-authoritative. Monster callers never qualify.
- **Positioning synchronization:** For such a player shooter (not a bot), the server rewinds the other players and sector planes to where that player saw them (via `UNLAGGED_Reconcile`) for the trace and restores them afterward (via `UNLAGGED_Restore`). The shooter itself is not rewound, and monster shots are never reconciled.

## Differences from ZDoom/GZDoom

The ZDoom Wiki page documents upstream ZDoom/GZDoom features not present in Zandronum 3.2.1:

- **`RGF_NORANDOMPUFFZ` flag:** Does not exist in Zandronum. The puff Z-offset is always randomized (within reason).
- **`spiraloffset` parameter:** Not in Zandronum — spiral always starts at a fixed 270-degree angle.
- **`limit` parameter:** Not in Zandronum — pierce limit is not configurable (always pierces all targets unless `RGF_NOPIERCING` is set).
- **`veleffect` parameter:** Not in Zandronum — velocity-trailing multiplier is hardcoded to 3.0.
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

### Targeted rail with target aim

```text
A_CustomRailgun(
  30,            // damage
  0,             // spawnofs_xy
  "FF6600",      // color1 (orange spiral)
  "FFFF00",      // color2 (yellow core)
  RGF_FULLBRIGHT | RGF_EXPLICITANGLE,  // flags
  2,             // aim (at target, trailing its velocity)
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

This fires a bright orange+yellow rail aimed at the target (trailing slightly behind a moving target), pierces all enemies, and deals 30 damage.

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
