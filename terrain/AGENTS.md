# terrain/: the TERRAIN lump

TERRAIN gives floor flats gameplay properties: splashes when something lands in or falls onto
them, damage while standing on them, footclip (sinking into liquid), friction, and on UZDoom
footstep sounds. **Read `../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

**Both engines parse TERRAIN**, so a page about the lump itself stamps
`Applies to: UZDoom=yes, Zandronum=yes` plus a `Verified against:` pair, with an
`## Engine-family divergence` heading where they differ. A page about a UZDoom-only feature
(footsteps, `damageonland`, per-sector terrain overrides) stamps `UZDoom=yes, Zandronum=no`. The
two parsers share one ancestor but have drifted: the footstep timing keywords have different
names on each engine (each engine's name is a fatal error on the other), and `damagetimemask`
means an interval on UZDoom but a bitmask on Zandronum.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router.
- `concepts/<topic>.md`: Archetype 3.

**No `inventory/`/`notes/` here.** The lump has three small, fixed keyword sets (outer, splash,
terrain), which the concept pages cover directly; a generated inventory would add nothing.

## Where TERRAIN is implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| Parser (`P_InitTerrainTypes`, `ParseOuter`, `ParseSplash`, `ParseTerrain`, `ParseFloor`, `ParseDefault`) | `src/gamedata/p_terrain.cpp`, `p_terrain.h` | `src/p_terrain.cpp`, `p_terrain.h` |
| Startup load (`P_Init`) | `src/p_setup.cpp` | `src/p_setup.cpp` |
| `ifdoom`/`ifheretic`/... game test (`CheckGame`) | `src/gamedata/gi.cpp` | `src/gi.h` |
| Terrain damage | `src/playsim/p_spec.cpp` (`P_ActorOnSpecialFlat`), called from `src/playsim/p_mobj.cpp` and `p_3dfloors.cpp` | `src/p_spec.cpp` (`P_PlayerOnSpecialFlat`), called from `src/p_user.cpp` |
| Splashes (`P_HitWater`) | `src/playsim/p_mobj.cpp` | `src/p_mobj.cpp` |
| Friction (`P_GetFriction`) | `src/playsim/p_map.cpp`, `src/playsim/p_sectors.cpp` (`GetFriction`) | `src/p_map.cpp` (`secfriction`, `secmovefac`) |
| Footclip (`AdjustFloorClip`) | `src/playsim/p_mobj.cpp` | `src/p_mobj.cpp` |
| Footsteps | `wadsrc/static/zscript/actors/player/player.zs` (`MakeFootsteps`, `DoFootstep`) | none (keywords parsed, never read) |
| Per-sector overrides (UDMF and ExtraData `floorterrain`/`ceilingterrain`, ACS `SetSectorTerrain`, `GetActorFloorTerrain`) | `src/maploader/udmf.cpp`, `src/maploader/edata.cpp`, `src/playsim/p_acs.cpp` | none |
| Stock definitions | `wadsrc/static/terrain.txt` | `wadsrc/static/terrain.txt` |

UltimateDoomBuilder's `Build/Scripting/ZDoom_TERRAIN.cfg` and SLADE's `z_terrain` block in
`dist/res/config/languages/zdoom.txt` are secondary tier-B backing for keyword names only. UDB's
list lacks `modify`, every footstep keyword and `damageonland`. SLADE lists UZDoom's keyword
names only, so it has no entry for Zandronum's `walkingsteptime`/`runningsteptime`.
