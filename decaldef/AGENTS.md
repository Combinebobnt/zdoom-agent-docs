# decaldef/: the DECALDEF lump

DECALDEF defines the wall decals the engine stamps during play (bullet chips, blood splats,
scorch marks), groups them for random choice, attaches them to actor classes, and animates them.
**Read `../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

**Both engines parse DECALDEF**, so a page about the lump itself stamps
`Applies to: UZDoom=yes, Zandronum=yes` plus a `Verified against:` pair, with an
`## Engine-family divergence` heading where they differ. A page about a UZDoom-only feature
(`translatable`, `generator optional`, `A_SprayDecal`) stamps `UZDoom=yes, Zandronum=no`. The two
parsers are close: Zandronum lacks a few UZDoom keywords, and each such keyword is a fatal error
there.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router.
- `concepts/<topic>.md`: Archetype 3.

**No `inventory/`/`notes/` here.** The lump has a handful of small, fixed keyword sets (one per
block type), which the concept pages cover directly; a generated inventory would add nothing.

## Where DECALDEF is implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| Parser (`ReadAllDecals`, `ReadDecals`, `ParseDecal`, `ParseDecalGroup`, `ParseGenerator`, `ParseFader`, `ParseStretcher`, `ParseSlider`, `ParseColorchanger`, `ParseCombiner`) | `src/gamedata/decallib.cpp`, `decallib.h` | `src/decallib.cpp`, `decallib.h` |
| Startup load | `src/d_main.cpp` | `src/d_main.cpp` |
| DECORATE `Decal` property | `src/scripting/thingdef_properties.cpp` | `src/thingdef/thingdef_properties.cpp` |
| Spawning, `lowerdecal`, map-placed `Decal` thing (9200) | `src/playsim/a_decals.cpp` | `src/g_shared/a_decals.cpp` |
| Animator thinkers (`DDecalFader`, `DDecalStretcher`, `DDecalSlider`, `DDecalColorer`) | `src/playsim/mapthinkers/a_decalfx.cpp` | `src/decallib.cpp` |
| Impact decals (hitscan, projectile, blood) | `src/playsim/p_map.cpp`, `p_mobj.cpp` | `src/p_map.cpp`, `p_mobj.cpp` |
| ACS `SpawnDecal` | `src/playsim/p_acs.cpp` | `src/p_acs.cpp` (also sends `SVC2_SHOOTDECAL`, `src/sv_commands.cpp`, handled in `src/cl_main.cpp`) |
| `A_SprayDecal` | `src/playsim/p_actionfunctions.cpp`, `wadsrc/static/zscript/actors/actor.zs` | none |
| Stock definitions | `wadsrc/static/decaldef.txt` | `wadsrc/static/decaldef.txt`, plus `wadsrc_st/static/decaldef.txt` (Skulltag class generators, in `skulltag_actors.pk3`) |

UltimateDoomBuilder has no DECALDEF config. SLADE's `z_decaldef` block in
`dist/res/config/languages/zdoom.txt` is secondary tier-B backing for keyword names only: it
lists `optional` but not `translatable` or `opaqueblood`.
