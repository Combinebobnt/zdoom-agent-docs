# The `TERRAIN` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `TERRAIN` (https://zdoom.org/w/index.php?title=TERRAIN&oldid=55426, retrieved 2026-09-28) + verified against the UZDoom source's `src/gamedata/p_terrain.cpp` and `p_terrain.h` (`P_InitTerrainTypes:269`, `ParseOuter`, `ParseSplash`, `ParseTerrain`, `ParseFloor:638-649`, `ParseDefault`, `ParseFriction:484-511`, `GenericParse`, `P_FindTerrain:701`), `src/gamedata/gi.cpp` (`CheckGame`), `src/p_setup.cpp` (`P_Init`), `src/playsim/p_spec.cpp` and `p_spec.h` (`P_ActorOnSpecialFlat:644`, `checkForSpecialSector`), `src/playsim/p_mobj.cpp` (`P_HitWater:7441-7443`, terrain-damage call), `src/playsim/p_map.cpp` and `p_sectors.cpp` (`P_GetFriction`, `GetFriction`), `src/maploader/udmf.cpp`, `src/playsim/p_acs.cpp`, `wadsrc/static/zscript/actors/player/player.zs:1800-1857` and `wadsrc/static/terrain.txt`, and the Zandronum source's `src/p_terrain.cpp` and `p_terrain.h` (same functions), `src/gi.h` (`CheckGame`), `src/p_setup.cpp`, `src/p_spec.cpp` (`P_PlayerOnSpecialFlat`), `src/p_user.cpp`, `src/p_mobj.cpp` (`P_HitWater`), `src/p_map.cpp:526-530` (`secfriction`, `P_GetFriction`), `src/network.cpp` (connect-time lump authentication list) and `wadsrc/static/terrain.txt`. Keyword lists cross-checked against UDB's `Build/Scripting/ZDoom_TERRAIN.cfg` and SLADE's `z_terrain` block in `dist/res/config/languages/zdoom.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

TERRAIN defines named **splashes** and named **terrains**, then assigns terrains to floor flats.
A terrain bundles what happens to an actor on that flat: the splash spawned when something lands
in it, damage over time, footclip (how far actors with `+FLOORCLIP` sink in), friction, whether it
counts as liquid, and on UZDoom footstep sounds. This page covers the lump's outer grammar, the
definition and override rules, and where the two engines differ. The per-keyword detail of splash
and terrain blocks belongs to their own pages.

## When it is read

- **Every lump named `TERRAIN` is parsed, in load order**, once at startup (`P_Init`, after
  textures and actor classes exist). The engine's own `terrain.txt` loads first, so a mod's lump
  can redefine or `modify` the stock entries.
- **Names resolve at parse time, not later.** A terrain's `splash` must name a splash defined
  earlier (in this lump or an earlier one), and `floor`/`defaultterrain` must name a terrain
  defined earlier. A forward reference is a console message, not an error, and the reference is
  simply dropped (see "Errors").
- Floor assignments are keyed by texture, not by sector: every sector whose floor shows that flat
  gets the terrain. Only UZDoom can override this per sector (see "Engine-family divergence").

## Outer grammar

The lump is a flat sequence of top-level statements. Comments are `//` and `/* */`. Keywords are
case-insensitive.

```text
splash <name> [modify] { <splash keywords> }
terrain <name> [modify] { <terrain keywords> }
floor [optional] <flat> <terrain>        // "optional" is UZDoom-only
defaultterrain <terrain>
ifdoom | ifheretic | ifhexen | ifstrife
endif
```

A minimal example that works on both engines (the classes and sound are the mod's own DECORATE
actors and SNDINFO name):

```text
splash MySlime
{
    smallclass  MySlimeDrop
    baseclass   MySlimeDrop
    chunkclass  MySlimeChunk
    sound       mymod/slimeplop
}

terrain MySlime
{
    splash          MySlime
    footclip        10
    liquid
    damageamount    5
    damagetype      Slime
    damagetimemask  31      // set it explicitly, see "Damage cadence"
}

floor MYSLIME1 MySlime
floor MYSLIME2 MySlime
```

### Blocks and `modify`

- **`splash <name> { ... }`** and **`terrain <name> { ... }`** define an entry. The block is a
  list of keywords, some followed by one value, and ends at `}`. Keywords that are flags (`liquid`,
  `allowprotection`, `noalert`, UZDoom's `damageonland`) take **no value**; writing `liquid true`
  makes the parser read `true` as the next keyword, which is a fatal error.
- **Redefining an existing name without `modify` resets it** to defaults before applying the new
  block. The entry keeps its slot, so earlier `floor` lines pointing at that terrain still point
  at it, now with the new properties.
- **`modify`** (`terrain Water modify { ... }`) keeps the existing values and changes only the
  keywords listed. On a name that doesn't exist yet it behaves like a plain definition.
- **The built-in terrain `Solid`** exists before any lump is read, has no properties, and is the
  initial default. It is an ordinary named entry, so `terrain Solid modify { ... }` works.

### `floor` and `defaultterrain`

- **`floor <flat> <terrain>`** assigns a terrain to a flat. The name is looked up as a flat first,
  but any texture type is accepted. A later `floor` line for the same flat replaces the earlier one.
- **`defaultterrain <terrain>`** sets the terrain every unassigned flat uses (initially `Solid`).
  An unknown name falls back to `Solid` on both engines.
- The stock `terrain.txt` assigns flats only for Heretic, Hexen and Strife. **Doom's stock flats
  have no terrain**, so Doom water and nukage don't splash unless a mod maps them.

### Game conditionals

`ifdoom`, `ifheretic`, `ifhexen` and `ifstrife` skip everything up to the next `endif` unless the
running game matches. **Chex Quest counts as Doom** here. There is no `ifchex`, no `else`, and no
nesting: the first `endif` ends the skipped region, and a condition inside a region that isn't
being skipped simply starts a new one. While skipping, the parser only counts braces (so a `}`
too many is a fatal `Too many left braces` error); it doesn't check keywords. An `endif` with no
matching condition is ignored.

## Block keywords at a glance

Both engines share the splash keywords: `smallclass`, `smallclip`, `smallsound`, `baseclass`,
`chunkclass`, `chunkxvelshift`, `chunkyvelshift`, `chunkzvelshift`, `chunkbasezvel`, `sound`,
`noalert`. An actor class of `None` leaves that slot empty.

Terrain keywords:

| Keyword | Value | UZDoom | Zandronum |
|---|---|---|---|
| `splash` | splash name | yes | yes |
| `damageamount` | integer | yes | yes |
| `damagetype` | damage type name (`lava` is read as `Fire`) | yes | yes |
| `damagetimemask` | integer | yes, an interval (see "Damage cadence") | yes, a bitmask |
| `allowprotection` | flag | yes | yes |
| `footclip` | number | yes | yes |
| `liquid` | flag | yes | yes |
| `friction` | number, higher = slipperier; `1.0` is normal on UZDoom but about 1/8 movement speed on Zandronum, so omit it for normal friction | yes | yes |
| `stepvolume`, `leftstepsounds`, `rightstepsounds` | number / sound / sound | yes | parsed, never used |
| `walksteptics`, `runsteptics` | integer tics | yes | **fatal unknown keyword** |
| `walkingsteptime`, `runningsteptime` | seconds (fractions allowed) | **fatal unknown keyword** | parsed, never used |
| `stepsounds`, `stepdistance`, `stepdistanceminvel` | sound / number / number | yes | fatal unknown keyword |
| `damageonland` | flag | yes | fatal unknown keyword |

`damagetype lava` is stored as `Fire`; see
[`../../decorate/concepts/custom-damage-types.md`](../../decorate/concepts/custom-damage-types.md)
for how damage type names work.

## Errors

| Condition | Both engines |
|---|---|
| Unknown top-level keyword, or unknown keyword inside a block | Fatal script error (UZDoom `Unknown keyword '...'`, Zandronum `Bad syntax.`). This is how the other engine's footstep keywords fail. |
| Missing `{` after the name (or after `modify`) | Fatal: `Expected {` |
| Non-integer value for an integer keyword (`walksteptics 3.5`) | Fatal: `Bad numeric constant` |
| `splash` in a terrain names an undefined splash | Console message (`... is not defined yet`); the terrain has no splash. |
| Unknown actor class in a splash | Console message; that slot is empty. UZDoom says `Unknown actor ...`, Zandronum `... is not an Actor ...`. |
| `floor` names an unknown flat | Console message; the line is skipped. UZDoom's `optional` silences the message. |
| `floor` names an unknown terrain | Console message. **UZDoom** leaves the flat unassigned, so it follows the last `defaultterrain` (even a later one); **Zandronum** gives it `Solid`. |

## Engine-family divergence

The two parsers share one ancestor. Beyond the keyword table above:

### Damage cadence (`damagetimemask`)

- **UZDoom** damages when the level time is a multiple of `damagetimemask + 1`, so the value is an
  interval minus one. **The default is 31**: every 32 tics. For a desired two-second interval (2
  seconds × 35 tics/second = 70 tics), use mask 69 (70 - 1 = 69).
- **Zandronum** damages when the level time ANDed with `damagetimemask` is zero, so the value is a
  bitmask. **The default is 0: every tic.** A terrain with `damageamount` and no
  `damagetimemask` hurts 32 times as often on Zandronum as on UZDoom.
- For the two to agree, **always set `damagetimemask` explicitly to one less than a power of two**
  (`1`, `3`, `7`, `15`, `31`, `63`, ...). Other values give a regular interval on UZDoom but an
  irregular pattern on Zandronum (for example `20` damages in bursts of 4 consecutive tics, 8 tics
  out of every 32). The stock terrains set `31`.

### Who takes terrain damage

- **UZDoom:** any actor touching the floor (or in water) that passes the sector-damage test:
  players always, and other actors when the sector has the UDMF `hurtmonsters` flag or the actor has
  `+FORCESECTORDAMAGE`. `+NOSECTORDAMAGE` exempts an actor. 3D floors apply their own terrain too.
  The terrain's splash `sound` plays only if damage was actually dealt.
- **Zandronum:** **players only**, touching the floor or in water. The splash `sound` plays on every
  damage tick, even when `allowprotection` and a radiation suit block the damage.
- Both: `allowprotection` lets a `PowerIronFeet` powerup block the timed damage. It doesn't
  block UZDoom's `damageonland`.

### Friction precedence

- **UZDoom:** a sector friction effect (the friction line special or `Sector_SetFriction`) beats
  the terrain's `friction`. Terrain friction applies only where the sector has none.
- **Zandronum:** the terrain's `friction`, when set, beats the sector's own. See
  [`../../acs/functions/sector_setfriction.md`](../../acs/functions/sector_setfriction.md).

### `floor` forms

- **`floor optional <flat> <terrain>`** is UZDoom-only. On Zandronum `optional` is read as the
  flat name. That flat is unknown, so the line is skipped after consuming one more token (the real
  flat name), and the terrain name is then read as a top-level keyword: a fatal error in practice.
- **`floor <flat> None`** (or `Null`) on UZDoom returns the flat to unassigned, so it follows
  `defaultterrain`. Zandronum
  has no such form: it reports an unknown terrain and assigns `Solid`.

### UZDoom-only features

- **Footsteps.** A player class with the `MakeFootsteps` player flag plays the terrain's
  `stepsounds` (or alternating `leftstepsounds`/`rightstepsounds`) at `walksteptics`/`runsteptics`
  intervals, or every `stepdistance` units moved when that is set, scaled by `stepvolume` and the
  `snd_footstepvolume` cvar. On Zandronum the step keywords it accepts are parsed and never read.
  The matching ZScript `TerrainDef` fields drop the plural: `StepSound`, `LeftStepSound`,
  `RightStepSound`.
- **`damageonland`**: a player landing on a damaging terrain that also has a splash can take the
  damage on landing too, but only when the level time ANDed with `damagetimemask` is nonzero (for
  a power-of-two-minus-one mask, any tic that isn't a regular damage tic; never with mask 0). It
  ignores `allowprotection`, and with footsteps on it fires on every step. See
  [terrain blocks](terrain-block.md#damage-on-landing-damageonland-uzdoom-only).
- **Per-sector terrain.** UDMF sector keys `floorterrain`/`ceilingterrain` and ACS
  `SetSectorTerrain` override the flat's terrain for one sector; ACS `GetActorFloorTerrain`
  returns the name under an actor. None of these exist on Zandronum.
- **ZScript access** to a terrain's fields: `GetFloorTerrain` returns a `TerrainDef` struct with
  all terrain fields exposed. The `FSplashDef` struct for splash data is not exposed to ZScript.

## Zandronum-specific: which machine's copy is used

TERRAIN is not among the lumps Zandronum checksums when a client connects (`src/network.cpp`'s
authentication list), so a client and server can run different TERRAIN contents with no connect
error. What each side's copy decides:

- **Damage:** the server's (or the single-player game's). Clients run the same check but skip the
  damage itself and wait for the server. They still play the splash sound from their own copy.
- **Splashes:** the server's. Clients skip `P_HitWater` entirely (except for client-side-only
  actors) and spawn what the server tells them to. Spectators never splash.
- **Friction:** both. Movement code runs on the server and in the client's own prediction, so a
  client whose copy differs predicts its movement wrongly and keeps getting corrected by the
  server.

Ship identical TERRAIN contents to server and clients.

## See also

- [`splash` blocks](splash-block.md) for every splash keyword, units and defaults, and when
  `P_HitWater` spawns a small or large splash.
- [`terrain` blocks](terrain-block.md) for per-keyword defaults, units and runtime behaviour.
- [Floor assignment](floor-assignment.md) for `floor`, `defaultterrain` and which terrain an actor
  actually stands on.
- [`../../decorate/concepts/custom-damage-types.md`](../../decorate/concepts/custom-damage-types.md)
  for `damagetype` names.
- [`../../acs/functions/sector_setfriction.md`](../../acs/functions/sector_setfriction.md) for
  sector friction on Zandronum.
