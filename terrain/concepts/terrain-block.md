# TERRAIN `terrain` blocks

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/p_terrain.cpp` and `p_terrain.h` (`TerrainKeywords`, `TerrainParser`, `MakeDefaultTerrain`, `ParseTerrain`, `ParseDamage`, `ParseFriction`, `GenericParse`), `src/common/engine/sc_man.cpp` (`ScriptError`, `GetNumber`, `GetFloat`, `MustMatchString`), `src/playsim/p_spec.cpp` and `p_spec.h` (`P_ActorOnSpecialFlat`, `checkForSpecialSector`, `P_SetSectorFriction`, `FrictionToMoveFactor`), `src/playsim/p_mobj.cpp` (`AActor::Tick`'s terrain call, `P_HitWater`, `P_HitFloor`, `AdjustFloorClip`, `P_ZMovement`, `FloorBounceMissile`), `src/playsim/p_3dfloors.cpp` (`P_ActorOnSpecial3DFloor`), `src/playsim/p_map.cpp` (`P_GetFriction`, `P_GetMoveFactor`), `src/playsim/p_sectors.cpp` (`GetFriction`), `src/playsim/p_trace.cpp` (`isLiquid`), `src/playsim/p_enemy.cpp`, `src/g_game.cpp`, `src/playsim/p_user.cpp` (`snd_footstepvolume`), `wadsrc/static/zscript/actors/player/player.zs` (`MakeFootsteps`, `DoFootstep`, the player movement thrust), `wadsrc/static/zscript/actors/actor.zs`, `wadsrc/static/zscript/actors/shared/ice.zs` (`A_IceSetTics`), `wadsrc/static/zscript/doombase.zs` (`TerrainDef`) and `wadsrc/static/terrain.txt`, and the Zandronum source's `src/p_terrain.cpp` and `p_terrain.h` (same parser functions), `src/sc_man.cpp`, `src/p_spec.cpp` (`P_PlayerOnSpecialFlat`, `P_SetSectorFriction`), `src/p_user.cpp` (`P_PlayerThink`'s terrain call, `P_MovePlayer`), `src/p_3dfloors.cpp` (`P_PlayerOnSpecial3DFloor`), `src/p_mobj.cpp` (`P_HitWater`, `P_HitFloor`, `AdjustFloorClip`, `P_XYMovement`, `PlayerLandedOnThing`, `FloorBounceMissile`), `src/p_map.cpp` (`secfriction`, `secmovefac`, `P_GetFriction`, `P_GetMoveFactor`), `src/p_enemy.cpp`, `src/g_shared/a_action.cpp` (`A_IceSetTics`) and `wadsrc/static/terrain.txt`. Keyword lists cross-checked against UDB's `Build/Scripting/ZDoom_TERRAIN.cfg` and SLADE's `z_terrain` block in `dist/res/config/languages/zdoom.txt`.

A `terrain` block defines what a floor flat does to the actors on it. This page is the
per-keyword reference: every keyword each engine's parser accepts, its value, default and units,
and what the engine actually does with it at runtime. The outer grammar, `modify`, redefinition,
load order and the lump-wide error table are on the section's lump page,
[The TERRAIN lump](terrain-lump.md); which flat gets which terrain is on
[Floor assignment](floor-assignment.md); the splash a terrain names is on
[`splash` blocks](splash-block.md).

## Keywords

Keywords are case-insensitive. Flags take no value (a value after one is read as the next
keyword, which is fatal). "Fatal" below means the engine aborts at startup with a script error.

| Keyword | Value | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|
| `splash` | splash name | Splash spawned when something lands in or on this flat | yes | yes |
| `damageamount` | integer | Damage per damage tic; `0` disables damage | yes | yes |
| `damagetype` | name | Damage type of that damage; `lava` is stored as `Fire` | yes | yes |
| `damagetimemask` | integer | Damage cadence | yes, interval: every `mask+1` tics | yes, bitmask: tics where `time & mask` is 0 |
| `allowprotection` | flag | A radiation suit (`PowerIronFeet`) blocks the damage | yes | yes |
| `footclip` | number, map units | How far `+FLOORCLIP` actors sink in | yes | yes |
| `liquid` | flag | Floor counts as liquid (see "Liquid") | yes | yes |
| `friction` | number | Floor friction; see "Friction" for the scale | yes | yes (see the `1.0` trap) |
| `stepvolume` | number | Footstep volume multiplier | yes | parsed, never read |
| `leftstepsounds`, `rightstepsounds` | sound name | Alternating footstep sounds (plural spelling on both engines) | yes | parsed, never read |
| `walksteptics`, `runsteptics` | integer tics | Footstep interval walking / running | yes | fatal unknown keyword |
| `walkingsteptime`, `runningsteptime` | seconds, fractions allowed | Zandronum's spelling of the step interval | fatal unknown keyword | parsed (stored as seconds x 35, truncated), never read |
| `stepsounds` | sound name | One footstep sound for both feet; beats the left/right pair | yes | fatal unknown keyword |
| `stepdistance` | number, map units | Distance-based footsteps: one step per this many units moved | yes | fatal unknown keyword |
| `stepdistanceminvel` | number, map units per tic | Minimum horizontal speed for distance-based steps | yes | fatal unknown keyword |
| `damageonland` | flag | Also damage a player when it lands on the flat (see "Damage on landing") | yes | fatal unknown keyword |

There is nothing else: the terrain block ends at `}` and any other word is a fatal unknown
keyword on both engines. (Tables: UZDoom `p_terrain.cpp:162-221`, Zandronum
`p_terrain.cpp:173-227`.) The editors lag the engines: UDB's `ZDoom_TERRAIN.cfg` lists only
`footclip`, `liquid`, `friction`, `damagetype`, `damageamount`, `damagetimemask` and
`allowprotection` as terrain properties (`splash` appears only as a top-level word), with no
footstep keyword, `damageonland` or `modify`. SLADE's
`z_terrain` list matches UZDoom exactly and has no entry for `walkingsteptime`/`runningsteptime`.

A short example, loadable on both engines (the flats are the mod's own; `Sludge` is a stock
splash on both):

```text
terrain MyAcid
{
    splash          Sludge
    footclip        6
    liquid
    damageamount    4
    damagetype      Slime
    damagetimemask  15      // every 16 tics on both engines
    allowprotection
}

terrain MyIce
{
    friction        1.7     // slippery; never write exactly 1.0, see "Friction"
}

floor MYACID1 MyAcid
floor MYICE1 MyIce
```

A UZDoom-only block (`stepsounds` and the `*steptics` keywords are fatal on Zandronum, and
TERRAIN has no engine conditional, since `ifdoom` and friends test the game, not the engine):

```text
terrain MyGravel
{
    stepsounds      mymod/step/gravel
    stepvolume      0.8     // default is 0: silent
    walksteptics    12
    runsteptics     8
}
```

## Defaults and units

A new terrain, or a redefinition without `modify`, starts zeroed: no splash, no damage, damage
type none, footclip 0, friction unset, not liquid, no protection, no footsteps, `stepvolume` 0.
The only nonzero default is `damagetimemask`: **31 on UZDoom, 0 on Zandronum** (UZDoom
`p_terrain.cpp:428-445`, Zandronum `p_terrain.cpp:436-451`). The built-in `Solid` terrain has the
same defaults (UZDoom `p_terrain.cpp:263-271`, Zandronum `:269-277`).

- **Integer keywords** (`damageamount`, `damagetimemask`, UZDoom's `walksteptics`/`runsteptics`)
  accept decimal or `0x` hex; a fractional value such as `3.5` is a fatal
  `Bad numeric constant`.
- **Number keywords** (`footclip`, `friction`, `stepvolume`, `stepdistance`,
  `stepdistanceminvel`, Zandronum's `walkingsteptime`/`runningsteptime`) accept any decimal.
  Zandronum stores `footclip` as fixed point; UZDoom stores a double.
- **Time:** UZDoom's step keywords are tics (35 per second). Zandronum's are seconds, multiplied
  by 35 and truncated to whole tics, then never used.
- **Sound keywords** take a SNDINFO logical name. An unknown name is silently no sound, on both
  engines (the warning is commented out in both `GenericParse`s).
- **`splash`** must name a splash defined earlier; otherwise a console message and no splash (see
  the lump page's "Errors").

## Bad input

Both engines' script errors go to `I_Error`, so they really are fatal: UZDoom's `ScriptError`
only downgrades to a console message when the scanner's `NoFatalErrors` is set, which the TERRAIN
parser never does (`sc_man.cpp:1079-1087`); Zandronum's has no such branch
(`sc_man.cpp:888-906`). The message differs: UZDoom reports `Unknown keyword '<word>'`,
Zandronum's `MustMatchString` passes no text and reports `Bad syntax.`.

| Input | UZDoom | Zandronum |
|---|---|---|
| Unknown or other-engine keyword | Fatal, `Unknown keyword` | Fatal, `Bad syntax.` |
| Non-integer for an integer keyword | Fatal, `Bad numeric constant` | same |
| Non-number for a number keyword | Fatal, `Bad numeric constant` | same (with a Linux locale hint appended) |
| Missing `}` (end of lump inside the block) | Fatal, `Missing string (unexpected end of file).` | same |
| Unknown sound name | Silent, no sound | same |
| `damagetimemask -1` with nonzero `damageamount` | Integer division by zero (`time % 0`) on the first damage check. Observed live on x86-64: SIGFPE crash in `P_ActorOnSpecialFlat` (`p_spec.cpp:644`) as soon as the player stood on the flat | Mask of all bits: damages only on level tic 0. Observed live: no damage and no crash over 175 tics on the flat, where `damagetimemask 31` dealt 6 hits |
| `friction` at or below about `-8.67` | Clamps to 0, which both engines treat as "unset": normal friction | same |

## Terrain damage

`damageamount`, `damagetype`, `damagetimemask` and `allowprotection` work together. Who takes
terrain damage and the cadence formulas are divergences covered on the lump page
([Who takes terrain damage](terrain-lump.md#who-takes-terrain-damage),
[Damage cadence](terrain-lump.md#damage-cadence-damagetimemask)); the detail here:

- **The check runs every tic** for each eligible actor touching the floor (its feet at or below
  the sector's floor height) or with any `waterlevel` (UZDoom `p_mobj.cpp:5092-5100`, Zandronum
  `p_spec.cpp:845-851`). Damage is dealt only on tics the cadence selects.
- **The clock is level time**, shared by every actor, not a per-actor timer. An actor that steps
  onto the flat can be hurt on its first tic there or wait up to a full interval.
- **Damage goes through the normal damage path** with no inflictor and no source (UZDoom
  `p_spec.cpp:660-661`, Zandronum `p_spec.cpp:870-871`), so armor, the victim's
  [`DamageFactor`](../../decorate/notes/damagefactor.md) for the type, god mode and
  invulnerability all apply. See
  [custom damage types](../../decorate/concepts/custom-damage-types.md) and the MAPINFO
  [`DamageType` block](../../mapinfo/concepts/damagetype-block.md) for how a type name is
  interpreted.
- **`damagetype lava`** (any case) is stored as `Fire` (UZDoom `p_terrain.cpp:468-476`,
  Zandronum `p_terrain.cpp:474-482`). The type is also read by frozen corpses on both engines:
  `A_IceSetTics` quarters the shatter delay on a `Fire` terrain and doubles it on an `Ice` one.
  That is the only reason the stock Hexen `Ice` terrain sets `damagetype ice` with no
  `damageamount` (UZDoom `ice.zs:42-53`, Zandronum `a_action.cpp:247-260`).
- **`allowprotection`**: when set, an actor carrying a `PowerIronFeet` (or a subclass) takes no
  terrain damage at all. That is the only powerup the check looks for; any other protection
  applies only through the normal damage path. Without `allowprotection` a radiation suit does
  nothing against terrain damage.
- **The splash `sound`** of the terrain's splash plays on the damage tic: on UZDoom only when
  damage was actually dealt, on Zandronum every damage tic regardless.
- **3D floors.** UZDoom also applies the terrain of the 3D floor an actor stands on (solid) or is
  inside (non-solid), taken from the control sector's top-plane flat (`p_3dfloors.cpp:191-222`),
  in the same tic as the normal floor check. Zandronum's 3D-floor pass applies only sector
  specials, not terrain (`p_3dfloors.cpp:320-348`), and its floor-touch test uses the real
  sector floor, so a player standing on a solid 3D floor above it takes no terrain damage there.

### Damage on landing (`damageonland`, UZDoom only)

`damageonland` is checked inside `P_HitWater`, not in the per-tic damage code
(`p_mobj.cpp:7435-7443`), so it follows different rules:

- It applies to any actor with a player attached, and needs a nonzero `damageamount` **and a
  `splash`**: a terrain without a splash returns before the check.
- It fires when the level time ANDed with `damagetimemask` is **nonzero**, the opposite of the
  interval test. With the default 31 that is 31 tics out of 32; with `damagetimemask 0` it
  never fires.
- It **ignores `allowprotection`**: a radiation suit does not block it.
- `P_HitWater` runs whenever the player lands on the floor with downward speed (including small
  drops such as stepping down a ledge) and, with footsteps enabled, on **every footstep**
  (`DoFootstep` calls it, `player.zs:1797`). A player walking on such a terrain with
  `MakeFootsteps` on takes the landing damage per step as well as the timed damage.
- It runs before the `+DONTSPLASH` test, and UZDoom's `P_HitFloor` doesn't test that flag, so
  it doesn't prevent it. The landing path does skip `Transfer_Heights` deep-water sectors
  (`P_HitFloor`, `p_mobj.cpp:7543-7617`).

The stock Hexen `Lava` terrain has `damageonland` on UZDoom and not on Zandronum; otherwise the
two stock `terrain.txt` files define the same terrains.

## Footclip

`footclip` sets how many map units an actor with [`+FLOORCLIP`](../../decorate/INDEX.md) (see
the [actor flags inventory](../../decorate/inventory/actor-flags.md)) sinks into the flat.
Actors without the flag, and actors with `+SPECIALFLOORCLIP` (which manage their own clip), are
unaffected.

- **What it changes:** the sprite is drawn that much lower, a player's view height drops by the
  same amount, and attack and missile spawn heights are lowered to match. The actor's position
  and collision box are unchanged.
- **When it is recomputed:** when the actor spawns, moves, or the floor under it moves or
  changes flat. It is not a per-tic check.
- **Straddling sectors:** of the sectors the actor touches whose floor is exactly at its feet,
  the **shallowest** footclip wins; if none qualify the clip is 0.
- **Deep water:** a sector with a `Transfer_Heights` effect never contributes, so the fake
  water does its own clipping (both engines).
- **3D floors:** UZDoom uses the terrain of a solid 3D floor the actor stands on
  (`p_mobj.cpp:6006-6020`). Zandronum ignores 3D floors and zeroes the clip whenever the actor is
  above the real floor of a sector that has any (`p_mobj.cpp:5342`).

## Friction

`friction` gives the flat a Boom-style friction, on the same scale as the friction line special
and `Sector_SetFriction` (amount = friction x 100). Unset (0) means no terrain friction.

**What the value means.** The engine derives two numbers from it (UZDoom `p_terrain.cpp:484-507`,
Zandronum `p_terrain.cpp:490-513`):

- A **per-tic horizontal velocity multiplier** of about `0.8125 + 0.09375 x friction`, clamped
  to 0..1. Higher is slipperier.

  | `friction` | Multiplier | Feel |
  |---|---|---|
  | `0` | 0.8125 | heavy mud |
  | `1.0` | 0.9063 | normal ground (UZDoom; see the trap below) |
  | `1.70824` | 0.9727 | stock Hexen ice (the engines' own ice value) |
  | `2.0` and above | 1.0 | no friction: an actor slides until it hits something |

- A **movement factor** that scales how hard a player's input pushes. Above normal friction it
  falls as the value rises (about 30% of normal at `2.0`), so ice is slow to get going as well
  as slow to stop. Below normal it starts low and is multiplied by 2, 4 or 8 as the actor's
  horizontal speed passes about 0.23, 0.46 and 0.92 map units per tic
  (`P_GetMoveFactor`), so mud is sluggish from a standstill and eases once moving.

**Who it affects.** The velocity multiplier applies to every actor on the ground or in water
except missiles and charging skulls (UZDoom also exempts `+NOFRICTION`); the on-ground terrain
lookup skips `+NOGRAVITY` and noclipping actors, which keep normal friction. The movement factor
applies to player walking;
monsters are only slowed by mud under the MBF monster-movement compatibility flag
(UZDoom `p_enemy.cpp:526`, Zandronum `p_enemy.cpp:481`).

**Resolution rules** (UZDoom `p_map.cpp:635-742`, Zandronum `p_map.cpp:548-620`):

- **Straddling:** among the sectors the actor touches whose floor it is standing at, only those
  with a sector friction effect or a terrain `friction` count, and the **lowest** multiplier
  (muddiest) wins. Normal-floor sectors are skipped, so ice next to plain floor is still ice.
- **Sector vs terrain:** the engines disagree on which wins in one sector; see the lump page's
  [Friction precedence](terrain-lump.md#friction-precedence).
- **Underwater** (`waterlevel` above 1, or 1 while more than 6 units above the floor): the
  actor's own sector decides, with the same precedence, and the movement factor is halved.
- **`var_friction`** (a server-info CVAR, default true, on both engines): when false, the
  on-ground friction lookup is skipped entirely, terrain included. The underwater case still
  reads it.
- **UZDoom only:** swimmable 3D floors count as well as solid ones (Zandronum checks solid 3D
  floors only), and in water the same friction value also damps vertical velocity
  (`p_mobj.cpp:3007-3027`).

**The `friction 1.0` trap on Zandronum.** Zandronum computes the terrain value in integer
arithmetic, and `1.0` lands exactly on the engine's normal-friction constant. The terrain parser
then takes the mud branch (it tests "greater than normal", where the sector-friction code tests
"greater than or equal", `p_spec.cpp:2407`), giving a movement factor about 1/8 of normal. And
because the friction is not below normal, the mud speed-up never applies. A player on a
`friction 1.0` flat on Zandronum therefore accelerates to only about 1/8 of normal speed. UZDoom
computes in floating point, lands just above the constant and gets normal movement. Values in
roughly `0.99988`..`1.00004` hit this on Zandronum; for normal friction, omit `friction`
entirely. Derived from source arithmetic and observed live (2026-09-29, local test builds, probe
UDMF map): 20 tics of walking forward then coasting covered 38.8 units on a `friction 1.0` flat
on Zandronum against 313.7 on a normal floor (0.12). UZDoom covered 165.3 against 166.5. (The
two engines ran with different run settings, so compare within an engine only.)

## Liquid

`liquid` does not make anything swim (water level comes from sectors and 3D floors, not
terrain) and does not affect damage, footclip or friction. It is read by:

- **`P_HitWater`'s result**, returned whenever an actor hits the floor, even when the terrain has
  no splash. A bouncing actor (`+BOUNCEONFLOORS` and similar) that lands on a liquid floor is
  removed, or explodes with `+EXPLODEONWATER`, unless it has `+CANBOUNCEWATER` (UZDoom
  `p_mobj.cpp:2145-2160`, Zandronum `p_mobj.cpp:1760-1775`). That path goes through
  `P_HitFloor`, which on both engines returns "not liquid" for a sector with a
  `Transfer_Heights` deep-water effect and for an actor not exactly on a floor plane.
- **Player landing sounds:** the `*land` sound is skipped when a player lands on a liquid floor
  (UZDoom `PlayerLandedMakeGruntSound` in `actor.zs`, Zandronum `PlayerLandedOnThing`).
- **Hexen's serpent head** checks it to decide between splashing away and dying.
- **UZDoom hitscan traces:** a non-swimmable 3D floor counts as water for bullet splashes when
  its terrain is `liquid` and has a `splash` (`p_trace.cpp:128-133`). Zandronum's traces only
  treat swimmable 3D floors as water.

On Zandronum, both `P_HitFloor` and `P_HitWater` return "not liquid" for a `+DONTSPLASH` actor
before looking at the terrain (`p_mobj.cpp:7009`, `6810`), and `P_HitWater` does the same for
any non-client-side actor on a client (`p_mobj.cpp:6818`), so a `+DONTSPLASH` bouncer bounces off
liquid there. UZDoom's `P_HitFloor` has no such test and its `P_HitWater` tests `+DONTSPLASH`
only around the splash spawn (`p_mobj.cpp:7461`), after the liquid result is known.

## Footsteps (UZDoom only)

Footsteps are implemented in ZScript on `PlayerPawn` (`player.zs:1766-1856`), so only player
pawns make them, and only when the class sets the `MakeFootsteps` player flag. No stock player
class sets it. `MakeFootsteps` is a virtual, so a class can replace the whole behaviour.

Each tic the player's think calls it when the flag is set. What it does, in order:

- Nothing while the player is above the floor. It reads the terrain under the player's feet
  (including UZDoom's per-sector terrain override, see [Floor assignment](floor-assignment.md)).
- Steps happen only while the player is **pressing a movement key** (forward/back or strafe).
  Sliding on ice without input makes no steps; letting go resets the counters.
- "Running" means the run state of the input (the run key XOR `cl_run`), not actual speed.
  Toggling it resets the counters.
- **Distance mode** (`stepdistance` above 0, which takes priority): each tic the player's
  horizontal speed is added to a distance counter while it exceeds `stepdistanceminvel`, and one
  step plays each time the counter passes `stepdistance`. Below the minimum speed the counter is
  reset so the next step plays immediately. `walksteptics`/`runsteptics` are ignored.
- **Interval mode** (otherwise): one step on the first tic of movement, then every
  `runsteptics` tics while running or `walksteptics` while walking. An interval of 0 (the
  default) makes no steps.
- **The sound:** `stepsounds` if set; otherwise `leftstepsounds` and `rightstepsounds` in
  alternation, left first. It plays at `stepvolume` x the `snd_footstepvolume` CVAR (default 1).
  **`stepvolume` defaults to 0**, so a terrain that sets sounds but not `stepvolume` is silent.
- **Every step also calls `HitWater`**, whether or not a sound played: a small splash (or a
  normal one for a player with Mass 200 or more) when the terrain has a splash and the player
  isn't already standing in water, plus `damageonland` damage if the terrain has it.

Zandronum parses `stepvolume`, `leftstepsounds`, `rightstepsounds`, `walkingsteptime` and
`runningsteptime` into its terrain table and never reads them; it has no footstep code.

## Engine-family divergence

Beyond the keyword spellings in the table and the three divergences the lump page already covers
(damage cadence, who takes damage, friction precedence):

- **Default `damagetimemask`:** UZDoom 31, Zandronum 0. `damagetimemask -1` divides by zero on
  UZDoom; on Zandronum it means "only on tic 0".
- **`friction 1.0`:** normal on UZDoom, about 1/8 movement speed on Zandronum (see "Friction").
- **Damage splash sound:** UZDoom only when damage was dealt; Zandronum every damage tic.
- **3D floors:** UZDoom applies their terrain for damage (solid and non-solid), footclip (solid
  only) and friction (solid and swimmable); Zandronum ignores 3D-floor terrain for damage and
  footclip and checks only solid 3D floors for friction.
- **Vertical water friction:** UZDoom only.
- **`liquid` and `+DONTSPLASH`:** on Zandronum a `+DONTSPLASH` actor never gets a liquid result
  from `P_HitFloor`/`P_HitWater`; on UZDoom it does.
- **Hitscan liquid on 3D floors:** UZDoom honours `liquid` plus `splash`; Zandronum needs a
  swimmable 3D floor.
- **UZDoom only:** `damageonland`, footsteps, per-sector terrain overrides, ACS
  `GetActorFloorTerrain` (absent from Zandronum's source), and ZScript access through the
  `TerrainDef` struct (`doombase.zs:712-734`), whose fields map one-to-one onto the keywords
  (`DamageMOD` is `damagetype`, `IsLiquid` is `liquid`, `StepSound` is `stepsounds`,
  `WalkStepTics`/`RunStepTics` the step intervals).
- **Error text:** `Unknown keyword '<word>'` on UZDoom, `Bad syntax.` on Zandronum.

## Zandronum-specific: which machine's copy is used

TERRAIN isn't checksummed at connect (see the lump page's
[section](terrain-lump.md#zandronum-specific-which-machines-copy-is-used)), so a mismatch between
server and client copies is silent. Per keyword:

- **`damageamount`, `damagetype`, `damagetimemask`, `allowprotection`:** the server's. The
  damage check doesn't run during client prediction (`p_user.cpp:4126`), and a client in client
  mode skips the damage call and waits for the server (`p_spec.cpp:866-872`). The damage-tic
  splash sound still plays from the client's own copy.
- **`friction`:** both. `P_MovePlayer` calls `P_GetMoveFactor` (`p_user.cpp:3073`) and
  `P_XYMovement` applies the multiplier (`p_mobj.cpp:2611`) on the server and in the client's own
  prediction, so a client whose copy differs predicts its movement wrongly and is repeatedly
  corrected.
- **`footclip`:** effectively each machine's own. The server sends a floorclip value only for a
  small splash it spawned (`p_mobj.cpp:6928`); otherwise `AdjustFloorClip` runs locally wherever
  an actor is moved or spawned, so a differing copy shows actors, and a client's own view height,
  at a different depth.
- **`liquid`:** the server's for everything decided in `P_HitWater`, which clients skip for
  server-side actors. The `*land` sound test reads the local copy.
- **Footstep keywords:** unused on Zandronum.

## See also

- [The TERRAIN lump](terrain-lump.md): outer grammar, `modify`, load order, errors, the
  overview divergences.
- [`splash` blocks](splash-block.md): the splash a terrain's `splash` names.
- [Floor assignment](floor-assignment.md): `floor`, `defaultterrain` and which terrain an actor
  actually stands on.
- [Custom damage types](../../decorate/concepts/custom-damage-types.md) and
  [`DamageFactor`](../../decorate/notes/damagefactor.md) for `damagetype`.
- [`Sector_SetFriction`](../../acs/functions/sector_setfriction.md) for sector friction.
