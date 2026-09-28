# Zandronum weapon still-bob, sway and pitch offset

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/p_pspr.cpp:85-128`
(client cvars) and `:531-772` (`P_BobWeapon`), `src/p_pspr.h:58-71` (style enums),
`src/g_shared/a_pickups.h:285-292` (`AWeapon` fields), `src/thingdef/thingdef_properties.cpp:2851-2933`
(property parsing), `src/dobjtype.cpp:408-419` (zero-filled class defaults), `src/p_user.cpp:3039`
and `:4037` (`AngleDelta`/`PitchDelta`), `wadsrc/static/menudef.za:661-693` (Weapon Setup menu);
`cl_bobrangex`/`cl_bobrangey` added after 3.2.1 in `9cc8abac6`.
UZDoom absence checked by grepping its `src/` and `wadsrc/` for all eight names (zero hits). All
`p_pspr.cpp` lines are from the `bdd0f7beb` checkout; the 3.2.1 tag's copy sits about 40-50 lines
earlier.

Zandronum adds eight `Weapon` properties that move the weapon sprite on top of the ordinary
`Weapon.BobStyle`/`BobSpeed`/`BobRangeX`/`BobRangeY` bob: a bob while standing still, three kinds
of sway, and an offset driven by the player's pitch. They are pure HUD presentation, computed
client-side in the renderer, and change nothing about gameplay, hitscan origin or netcode. None of
them exist on UZDoom, where an unknown property is a parse error, so a mod that must load on both
engines cannot use them in shared DECORATE.

| Property | Type | Group | Note |
|---|---|---|---|
| `Weapon.StillBobRange` | float | still bob | [stillbobrange](../notes/stillbobrange.md) |
| `Weapon.StillBobSpeed` | float | still bob | [stillbobspeed](../notes/stillbobspeed.md) |
| `Weapon.ViewSwaySpeed` | float | sway | [viewswayspeed](../notes/viewswayspeed.md) |
| `Weapon.MotionSwaySpeed` | float | sway | [motionswayspeed](../notes/motionswayspeed.md) |
| `Weapon.JumpSwaySpeed` | float | sway | [jumpswayspeed](../notes/jumpswayspeed.md) |
| `Weapon.SwayStyle` | name | sway | [swaystyle](../notes/swaystyle.md) |
| `Weapon.ViewPitchStyle` | name | pitch | [viewpitchstyle](../notes/viewpitchstyle.md) |
| `Weapon.ViewPitchOffset` | float | pitch | [viewpitchoffset](../notes/viewpitchoffset.md) |

## Where they are applied

All eight are read in one function, `P_BobWeapon` (`p_pspr.cpp:531`), which the software renderer
(`src/r_things.cpp:1300`) and the GL renderer (`src/gl/scene/gl_weapon.cpp:204`) call when drawing
the `ps_weapon` layer. It builds an `(x, y)` offset in four stages, each adding to the last:

1. **Regular bob** (`BobStyle`/`BobSpeed`/`BobRangeX/Y`, shared with UZDoom). Skipped entirely,
   along with everything below, when the weapon has `+Weapon.DontBob` or the player is spectating.
2. **Still bob** (`p_pspr.cpp:642-652`), vertical only.
3. **Sway** (`p_pspr.cpp:654-737`), horizontal from turning, vertical from pitch changes, jumping,
   stair steps and crouching, then filtered by `SwayStyle`.
4. **Pitch offset** (`p_pspr.cpp:739-771`), vertical only.

Positive `y` is further down the screen, the same direction the regular bob's downswing uses.
All six numeric properties are parsed with `PROP_FIXED_PARM`, so they are 16.16 fixed-point and
accept fractions. The two style properties match their names case-insensitively (`MatchString`
uses `stricmp`); an unknown name is a fatal `I_Error` at load, not a warning.

## Defaults

None of the eight is set by `AWeapon` or by the `Weapon` DECORATE actor in `wadsrc`, and class
defaults are zero-filled beyond whatever the parent copied (`dobjtype.cpp:408-419`). So every
weapon starts with range, speeds and offset at `0` (feature off) and both styles at index `0`
(`Normal` and `Full`). Subclasses inherit a parent weapon's values like any other property.

## Client overrides

Each group has a client-side switch that replaces the weapon's values for that group wholesale,
not per property (`p_pspr.cpp:85-128`, exposed in Zandronum's Weapon Setup menu):

| Switch | Replaces | With |
|---|---|---|
| `cl_usecustombob` | `StillBobRange`, `StillBobSpeed` (and the regular `BobStyle`/`BobSpeed`/`BobRangeX`/`BobRangeY`) | `cl_stillbobrange`, `cl_stillbobspeed`, `cl_bobstyle`, `cl_bobspeed`, `cl_bobrangex`, `cl_bobrangey` |
| `cl_usecustomsway` | `ViewSwaySpeed`, `MotionSwaySpeed`, `JumpSwaySpeed`, `SwayStyle` | `cl_viewswayspeed`, `cl_motionswayspeed`, `cl_jumpswayspeed`, `cl_swaystyle` |
| `cl_usecustompitch` | `ViewPitchOffset`, `ViewPitchStyle` | `cl_viewpitchoffset`, `cl_viewpitchstyle` |

The replacement cvars default to `0` except `cl_bobspeed`, `cl_bobrangex` and `cl_bobrangey`
(`1.0`), so turning a switch on without setting its values disables still bob, sway or pitch
offset for every weapon (the regular bob falls back to `Normal` at speed and range `1.0`).
`cl_bobrangex`/`cl_bobrangey` were added after 3.2.1 (`9cc8abac6`). A 3.2.1 client has neither
cvar, and `cl_usecustombob` there keeps the weapon's own `BobRangeX`/`BobRangeY`. A mod therefore cannot force these effects: any player can
override or zero them. `cl_alwaysbob` separately lets bobbing (regular and still) continue while
firing. The `cl_swaystyle` and `cl_viewpitchstyle` integers follow the same enum order as the
property names, which differ between the two: see [swaystyle](../notes/swaystyle.md). Per-switch notes:
[cl_usecustombob](../../console/notes/cl_usecustombob.md),
[cl_usecustomsway](../../console/notes/cl_usecustomsway.md),
[cl_usecustompitch](../../console/notes/cl_usecustompitch.md). Rows for all of these are in
[`console/inventory/cvars.md`](../../console/inventory/cvars.md).

## Shared state

`P_BobWeapon` keeps its smoothing state in function-local statics: `curbob` for the regular bob,
and `swaypos[2]` plus `lastSwayTime` for sway. None of it belongs to the weapon or the player. It
is never reset on weapon switch or level change and is not saved, so a new weapon starts from
wherever the previous one's sway had drifted and eases from there.

Sway is recomputed at most once per `level.time` tic (the renderers may call in more often) and
not while the game is paused, the ticker is paused, or the client considers the server lagging
(`CLIENT_GetServerLagging`). During those frames the last `swaypos` is still applied, so the
weapon holds its position rather than snapping back. Each recompute moves each axis toward its
new target by `max(256, distance / 10)` in fixed-point units: a tenth of the gap, but never less
than 1/256 pixel. A gap of 1/256 pixel or less snaps straight to the target. This is what gives
the sway its lag and ease-out.

## Not the same thing

- **The `stillbob` userinfo cvar** (`src/d_netinfo.cpp:89`, ACS `PLAYERINFO_STILLBOB`) bobs the *view*
  while standing, not the weapon. Unrelated to `Weapon.StillBob*`.
- **`A_WeaponReady(WRF_NOBOB)`** and the bob-while-ready rules in
  [Creating weapons](creating-weapons.md) decide *when* `player->WeaponState` allows bobbing.
  Still bob obeys that same gate; sway and pitch offset do not.

## Engine-family divergence

UZDoom has no equivalent properties: each of the eight is a fatal `is an unknown actor
property` error (`src/scripting/decorate/thingdef_parse.cpp:977` at @98b16b78fc), and none of
the `cl_*` override cvars exist either. The same effects are built in ZScript by overriding
`PlayerPawn.BobWeapon`/`BobWeapon3D` (`wadsrc/static/zscript/actors/player/player.zs`) or
`Weapon.ModifyBobLayer` (`wadsrc/static/zscript/actors/inventory/weapons.zs`) and adding the
extra offset there. See the [ZScript section](../../zscript/INDEX.md).
