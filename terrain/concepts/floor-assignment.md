# How a floor gets its terrain

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/p_terrain.cpp` and `p_terrain.h` (`ParseFloor`, `ParseDefault`, `P_FindTerrain`, `FTerrainTypeArray`), `src/common/textures/texturemanager.cpp` (`CheckForTexture`, the TEXTURES top-level type mapping, `SetTranslation`), `src/gamedata/textures/animations.cpp` (`UpdateAnimations`), `src/maploader/maploader.cpp` (sector flat lookup), `src/maploader/udmf.cpp` (sector keys), `src/maploader/edata.cpp` (ExtraData sector records), `src/playsim/p_sectors.cpp` (`GetTerrain`, `GetFriction`), `src/playsim/p_map.cpp` (`P_GetFloorCeilingZ`, `P_FindFloorCeiling`, `P_CheckPosition`, `P_TryMove`, `P_TeleportMove`, `P_AdjustFloorCeil`, `P_GetFriction`), `src/playsim/p_maputl.cpp` (`P_LineOpening`), `src/playsim/p_3dfloors.cpp` (`P_Add3DFloor`, `P_ActorOnSpecial3DFloor`, 3D line openings), `src/playsim/p_3dmidtex.cpp`, `src/playsim/p_mobj.cpp` (`P_GetThingFloorType`, `P_HitWater`, `P_HitFloor`, `AdjustFloorClip`, `AActor::Tick`, spawn), `src/playsim/p_spec.cpp`, `src/playsim/p_trace.cpp` (`isLiquid`), `src/playsim/p_acs.cpp` (`ACSF_SetSectorTerrain`, `ACSF_GetActorFloorTerrain`), `src/playsim/p_tags.cpp` (`FSectorTagIterator::Next`), `src/serializer_doom.cpp` (`SerializeTerrain`), `src/scripting/vmthunks.cpp`, `wadsrc/static/zscript/mapdata.zs`, `wadsrc/static/terrain.txt` and `wadsrc/static/filter/game-heretic/animated.lmp`, and the Zandronum source's `src/p_terrain.cpp` and `p_terrain.h` (same functions), `src/textures/texturemanager.cpp` (`CheckForTexture`, TEXTURES type mapping), `src/textures/animations.cpp`, `src/p_setup.cpp` (sector flat lookup), `src/p_map.cpp` (`P_GetFloorCeilingZ`, `P_CheckPosition`, `secfriction`, `P_GetFriction`), `src/p_3dfloors.cpp` (`P_Add3DFloor`, `P_PlayerOnSpecial3DFloor`), `src/p_3dmidtex.cpp`, `src/p_mobj.cpp` (`P_GetThingFloorType`, `P_HitWater`, `P_HitFloor`, `AdjustFloorClip`), `src/p_spec.cpp` (`P_PlayerOnSpecialFlat`), `src/p_user.cpp` and `src/p_acs.cpp` (ACSF enum, `CallFunction`). Keyword names cross-checked against UDB's `Build/Scripting/ZDoom_TERRAIN.cfg` and `Build/Configurations/Includes/ZDoom_misc.cfg`, and SLADE's `z_terrain` block in `dist/res/config/languages/zdoom.txt`.

This page is the detail behind the lump page's `floor` and `defaultterrain` summary: which texture a
`floor` line actually keys, what the default covers and when it is read, how animation and
runtime texture changes interact with it, which plane decides the terrain an actor is standing on
(3D floors, deep water, 3D middle textures), what reads ceiling terrain, and UZDoom's per-sector
overrides. The outer grammar, load order, `ifdoom`..`endif` and redefinition rules are in
[The TERRAIN lump](terrain-lump.md). What a terrain's keywords do is on
[terrain-block.md](terrain-block.md); splashes are on [splash-block.md](splash-block.md).

## The model: one terrain per texture, resolved at lookup

Both engines keep one table with a slot per texture index. A `floor` line writes a terrain index
into its texture's slot; every other slot holds an "unassigned" marker. When something asks for a
plane's terrain, the engine takes the texture index the plane shows and reads the slot, and an
unassigned slot returns **whatever `defaultterrain` currently is** (UZDoom `p_terrain.h:40-51`,
Zandronum `p_terrain.h:50-59`). Two consequences:

- **Assignment is by texture, not by sector or map.** Every plane showing that texture, anywhere,
  gets the terrain. Only UZDoom can override it per sector (see "Engine-family divergence").
- **A plane whose texture changes at runtime changes terrain with it.** Floor texture changes by
  ACS (`ChangeFloor`), line specials or donut-style movers all take effect on the next lookup,
  because the lookup reads the plane's current texture (UZDoom `p_sectors.cpp:968-971`).

## `floor`

```text
floor <texture> <terrain>
floor optional <texture> <terrain>     // UZDoom only
floor <texture> None                   // UZDoom only; Null is a synonym
```

| Form | UZDoom | Zandronum |
|---|---|---|
| `floor <texture> <terrain>` | yes | yes |
| `optional` before the texture | yes: an unknown texture is skipped with no console message | no: fatal in practice (see the lump page's "`floor` forms") |
| `None` / `Null` as the terrain | yes: puts the slot back to unassigned, so the texture follows `defaultterrain` | no: an unknown terrain name, assigns `Solid` |
| A texture name containing `/` (a full lump path) | yes: the texture is created on first reference, the same way a map naming it would create it | no path lookup: reported as unknown |

### Which texture a name matches

The `floor` name goes through **exactly the same lookup the map loader uses for a sector's floor
texture**: "look for a flat, accept a TEXTURES `texture` override, and fall back to any texture
type" (UZDoom `p_terrain.cpp:625-626` and `maploader.cpp:189-190`; Zandronum `p_terrain.cpp:634-635`
and `p_setup.cpp:665-666`). So a `floor` line keys the same texture that a sector showing that name
displays, including when several definitions share the name. The precedence rules (TEXTURES
`texture` entries are use type Override and win flat lookups; `flat` entries are Flat; `walltexture`
entries are found only by the any-type fallback) are on
[`../../textures/concepts/textures-lump.md`](../../textures/concepts/textures-lump.md)'s "Which
definition wins". Both engines map the TEXTURES keywords the same way (UZDoom
`texturemanager.cpp:821-836`, Zandronum `texturemanager.cpp:714-732`).

A wall texture's slot matters in two places:

- **3D middle textures.** An actor standing on a 3D midtex takes the terrain of the **line's middle
  texture**, looked up in the same table (UZDoom `p_3dmidtex.cpp:303`; Zandronum
  `p_3dmidtex.cpp:290` sets the actor's floor texture, which `P_GetThingFloorType` then looks up).
  A `floor` line naming a wall texture is how a walkable bridge gets a terrain.
- **A sector floor showing a wall texture.** The fallback lookup lets a map put a wall texture on a
  floor, and the terrain follows that texture's slot.

### Animated flats: each frame needs its own line

Terrain does **not** follow an animation. ANIMDEFS and ANIMATED animate by redirecting the
*drawn* texture (`SetTranslation`: UZDoom `animations.cpp:1176-1182`, Zandronum
`animations.cpp:928-934`); a sector's stored texture never changes. The terrain lookup reads the
stored texture, so:

- A sector placed on the base frame always has the base frame's terrain, whatever frame is showing.
- A sector placed directly on a **later frame of a `range` animation** (a map editor lets the mapper
  pick any frame) has that frame's own terrain, which is the default unless that frame has its own
  `floor` line.

The stock lump shows both styles. Heretic's `FLTWAWA1` animates as a range through `FLTWAWA3`
(the stock Heretic ANIMATED lump), but the stock `terrain.txt` assigns only `FLTWAWA1`, so a Heretic
sector placed on `FLTWAWA2` has no water terrain. Strife's section lists every water frame
separately. **For a mod, write a `floor` line for every frame a mapper might place.**

### Redefinition and order

- A later `floor` line for the same texture overwrites the slot (both engines).
- `floor` stores the terrain's slot, and redefining a terrain keeps its slot (see the lump page), so a
  `floor` line written before a later `terrain <name> { ... }` redefinition picks up the new
  properties.
- The terrain name must already be defined when the `floor` line is parsed (in this lump or an
  earlier one). A forward reference is the "unknown terrain" case below.

### Bad input

| Input | UZDoom | Zandronum |
|---|---|---|
| Unknown texture | Console `Unknown flat <name>`; the line (both names) is skipped. Silent with `optional` | Same message; line skipped |
| Unknown terrain, including a forward reference | Console `Unknown terrain <name>`; the slot is set to **unassigned**, so it follows the final `defaultterrain` | Same message; the slot is set to **`Solid`**, fixed, whatever `defaultterrain` later says |
| `None` / `Null` | Silent; slot unassigned | Unknown terrain: message, `Solid` |

None of these is a script error; the lump page's error table covers the fatal cases (UZDoom
`p_terrain.cpp:628-648`, Zandronum `p_terrain.cpp:636-649`).

## `defaultterrain`

```text
defaultterrain <terrain>
```

- **Scope: every unassigned texture slot, of every texture type, in every map.** It covers flats,
  wall textures used as 3D midtex floors, and sectors showing a texture no `floor` line names. It
  is a global, not per game, unless you wrap it in an `ifdoom`-style conditional.
- **It is read at lookup time, not copied at parse time.** Its position relative to the `floor`
  lines doesn't matter, and **the last `defaultterrain` in load order wins** for the whole game.
  A later mod's `defaultterrain` replaces an earlier one's.
- An unknown name prints `Unknown terrain <name>` and sets the default to `Solid` (index 0) on both
  engines (UZDoom `p_terrain.cpp:657-669`, Zandronum `p_terrain.cpp:658-670`). `None` is not
  special here: it is just an unknown name.
- Before any `defaultterrain`, the default is the built-in `Solid`.

## Which terrain an actor is standing on

Two kinds of consumer read terrain differently:

- **Cached per actor.** Terrain damage (via `P_GetThingFloorType`), ACS `GetActorFloorTerrain` and
  ZScript `Actor.GetFloorTerrain` use a value stored on the actor. UZDoom caches the terrain index
  (`floorterrain`); Zandronum caches the floor texture (`floorpic`) and looks its terrain up on use.
  UZDoom refreshes `floorterrain` when the actor spawns (`p_mobj.cpp:5512`, `5524`), moves through
  `P_TryMove` (`p_map.cpp:2687`), teleports (`p_map.cpp:551`), is re-fitted by
  `P_FindFloorCeiling` (`p_map.cpp:373`, `407`) or has a touching sector change height
  (`P_AdjustFloorCeil`, `p_map.cpp:6466`), not every tic: an actor with no horizontal movement
  returns from `P_XYMovement` before `P_TryMove` (`p_mobj.cpp:2483-2501`). A per-sector override or
  texture change therefore reaches an actor through its next refresh.
- **Looked up live.** Landing and water-entry splashes (`P_HitWater`), friction and footclip read
  the sector's terrain when they run.

The cached value is chosen in the position check: the highest floor under the actor, which is the
sector floor, the top of a solid 3D floor, or a 3D midtex (UZDoom `p_map.cpp:320-340`,
`1790-1840`; Zandronum `p_map.cpp:238-245`).

| Situation | Terrain used |
|---|---|
| Plain sector floor | That sector's floor terrain |
| On top of a solid 3D floor | The **control sector's top plane**, which is its **ceiling** for a normal 3D floor and its floor for a Vavoom-style inverted one (UZDoom `p_3dfloors.cpp:124-154`, Zandronum `p_3dfloors.cpp:147-163`) |
| On a 3D midtex | The line's middle texture (see above) |
| Straddling several sectors (footclip) | The shallowest footclip among touching sectors whose floor is at the actor's feet |
| UZDoom: stepping up onto a line portal | Index 0, the built-in `Solid`, not the default terrain (`p_map.cpp:877`, `945`) |
| Swimming (`waterlevel` above 0) | Terrain damage still applies on both engines, using the floor under the actor, even when not touching it (UZDoom `p_mobj.cpp:5097-5099`, Zandronum `p_spec.cpp:847-852`) |

### Splashes: which plane `P_HitWater` picks

Both engines check, in order (UZDoom `p_mobj.cpp:7400-7428`, Zandronum `p_mobj.cpp:6858-6884`):

1. **A 3D floor whose top is within half a unit of the splash point**: its control sector's top
   plane terrain. UZDoom accepts solid, swimmable, or any rover with nonzero alpha; Zandronum only
   solid or swimmable. A 3D floor whose bottom is below the point but not below the actor's floor
   height suppresses the splash.
2. **A `Transfer_Heights` sector whose control sector has the "clip fake planes" flag** (arg 1
   bit 4): the **control sector's** floor terrain.
3. Otherwise the sector's own floor terrain.

A landing (`P_HitFloor`) never splashes in a sector with a `Transfer_Heights` control sector; entry
into such deep water splashes through the water-level check instead (UZDoom `p_mobj.cpp:5352-5360`).
UZDoom's sector damage flag that asks for terrain effects on damage ticks (UDMF
`damageterraineffect`, ExtraData `TERRAINHIT`) splashes with the sector's own floor terrain,
skipping the 3D floor and `Transfer_Heights` checks (`p_spec.cpp:477`).

## Ceiling terrain

There is no gameplay on a sector's own ceiling: **nothing reads an ordinary sector's ceiling
terrain as "the ceiling"**. Ceiling terrain matters in one way on both engines:

- **A 3D floor's walkable top is its control sector's ceiling**, so the control sector's ceiling
  texture (or, on UZDoom, its `ceilingterrain` override) is the terrain actors stand on, splash
  in, and on UZDoom take damage and friction from. A `floor` line for the texture on the control
  sector's ceiling is what gives a 3D pool its water terrain. On UZDoom, UDMF `ceilingterrain`
  on the control sector does the same for one pool without touching the texture's global slot.

UZDoom also exposes it directly: ZScript `Sector.GetTerrain(pos)` and `Sector.GetFloorTerrain(pos)`
take a plane argument, 1 for the ceiling (`mapdata.zs:530-531`, `vmthunks.cpp:464-475`), and the
hitscan trace's liquid test for 3D floors reads the control sector's ceiling terrain, or its floor
for an inverted-planes floor (`p_trace.cpp:128-133`).

## Example

```text
terrain MyAcid
{
    splash          Sludge      // a stock splash, defined for every game
    liquid
    damageamount    4
    damagetimemask  31
}

// every frame a mapper might place, not just the animation's base
floor MYACID1 MyAcid
floor MYACID2 MyAcid
floor MYACID3 MyAcid

// a wall texture used as a 3D midtex bridge
floor MYGRATE Solid

defaultterrain Solid
```

## Engine-family divergence

### Unassigned vs `Solid` on a bad `floor` line

On UZDoom a `floor` line with an unknown terrain name leaves the texture unassigned, so it follows
`defaultterrain`, even one set later (`p_terrain.cpp:643-648` stores the -1 lookup result, which
the table reads back as unassigned). On Zandronum the same line assigns `Solid` permanently
(`p_terrain.cpp:643-649`). UZDoom's explicit `None`/`Null` form has no Zandronum equivalent.

### 3D floors

| What | UZDoom | Zandronum |
|---|---|---|
| Terrain damage on a solid 3D floor top | yes: `P_ActorOnSpecial3DFloor` applies the control sector's top-plane terrain (first matching 3D floor only) to an actor standing on it (`p_3dfloors.cpp:192-223`); `P_ActorOnSpecialFlat` itself does no floor-contact check (`p_spec.cpp:639`) | not from either path read: `P_PlayerOnSpecial3DFloor` applies sector specials only (`p_3dfloors.cpp:320-347`), and `P_PlayerOnSpecialFlat` skips a player above the sector's real floor unless `waterlevel` is nonzero (`p_spec.cpp:847-852`) |
| Terrain damage inside a swimmable 3D floor | yes, the control sector's top-plane terrain | not from the 3D floor; the texture under the player applies instead, because swimmable 3D floors raise `waterlevel` (`p_mobj.cpp:4703-4712`) |
| Friction from a 3D floor | the control sector's **top plane** (normally ceiling) terrain, solid tops and swimmable volumes (`p_map.cpp:670`, `709`) | the control sector's **floor** texture terrain, solid tops only (`p_map.cpp:589` via `secfriction`, which reads the floor texture at `p_map.cpp:528`) |
| Footclip on a 3D floor top | the top plane's terrain (`p_mobj.cpp:6010-6020`) | none: footclip is zeroed above the real floor (`p_mobj.cpp:5342`) |
| Splash on a 3D floor | top-plane terrain; solid, swimmable or alpha above 0 | top texture's terrain; solid or swimmable only |

On Zandronum a solid 3D floor's splash and friction can therefore come from **different** textures
of the control sector (ceiling for splash, floor for friction). Keep both assigned to the same
terrain if friction matters.

### Per-sector terrain (UZDoom only)

UZDoom stores an optional terrain per sector plane. When set, it replaces the texture's terrain for
that plane of that sector only (`p_sectors.cpp:968-971`), survives texture changes, and is saved
in savegames by name (`serializer_doom.cpp:137-150`). **Zandronum has none of these**: no UDMF key,
no ExtraData, and neither ACS function.

| Source | Reads / writes | Details |
|---|---|---|
| UDMF sector `floorterrain` / `ceilingterrain` (string) | Writes the override at map load | Honoured only in the `ZDoom`, `ZDoomTranslated` and `Vavoom` namespaces (`udmf.cpp:1740`, `1996-2002`). An unknown name, `None` or empty leaves no override, silently |
| ExtraData sector record `floorterrain` / `ceilingterrain` | Writes the override at map load | Same name resolution (`edata.cpp:277-305`, applied at `603-604`) |
| ACS `SetSectorTerrain(int tag, int plane, str terrain)` (extension function -95) | Writes the override on every sector with `tag` | `plane` is `0` floor, `1` ceiling; any other value does nothing. **Tag 0 means every untagged sector** (`p_tags.cpp:404-430`). An unknown name, `""` or `"None"` clears the override back to the texture's terrain (`p_acs.cpp:6560-6573`). No return value, no message |
| ACS `str GetActorFloorTerrain(int tid)` (extension function -205) | Reads the actor's **cached** terrain | Returns the terrain name (the built-in is `"Solid"`); `""` when no actor matches; tid 0 is the activator (`p_acs.cpp:6754-6765`). Reflects 3D floors and midtex, and lags a change until the actor's next refresh (see above) |
| ZScript `Actor.GetFloorTerrain()`, `Sector.GetTerrain(plane)`, `Sector.GetFloorTerrain(plane)` | Read | The sector calls apply the override first, then the texture |

The terrain name in all of these resolves when the map loads or the call runs, against the
terrains TERRAIN defined at startup. On Zandronum, ACS indices -95 and -205 are unassigned (its
extension enum jumps from 92 to 204 and then runs 100 to 186, `p_acs.cpp:5447-5557`), so a compiled call reaches `CallFunction`'s default case and returns 0
with no effect and no message (`p_acs.cpp:9059`).

### Editors

UDB's TERRAIN highlighting lists `optional` but not `None`/`Null`; SLADE lists all three. UDB's
ZDoom UDMF configuration (`ZDoom_misc.cfg`) carries `floorterrain` and `ceilingterrain` as sector
string fields.

## See also

- [The TERRAIN lump](terrain-lump.md): outer grammar, load order, conditionals, errors, and which
  Zandronum machine's copy decides damage, splashes and friction.
- [terrain-block.md](terrain-block.md): what `footclip`, `friction`, damage and the other terrain
  keywords do.
- [splash-block.md](splash-block.md): what a splash spawns and plays.
- [`../../animdefs/concepts/texture-flat-animations.md`](../../animdefs/concepts/texture-flat-animations.md)
  and [`../../animdefs/concepts/animdefs-lump.md`](../../animdefs/concepts/animdefs-lump.md) for
  how animation frames are chosen.
- [`../../textures/concepts/textures-lump.md`](../../textures/concepts/textures-lump.md) for which
  same-named texture a lookup finds.
- [`../../acs/families/sector-terrain.md`](../../acs/families/sector-terrain.md) for
  `SetSectorTerrain` and `GetActorFloorTerrain` as ACS calls.
