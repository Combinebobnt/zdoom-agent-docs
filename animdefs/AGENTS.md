# animdefs/: the ANIMDEFS lump

ANIMDEFS defines texture and flat animations, switch textures, warping textures, animated doors,
camera textures and sky offsets. **Read `../shared/AUTHORING.md` and `../shared/ARCHETYPES.md`
first.**

**Both engines parse ANIMDEFS**, so a page about the lump itself stamps
`Applies to: UZDoom=yes, Zandronum=yes` plus a `Verified against:` pair, with an
`## Engine-family divergence` heading where they differ. A page about a UZDoom-only feature
(`canvastexture`, `firetexture`, `Random`, `notrim`, the `hdr`/`translucent`/`offset` camera
texture options) stamps `UZDoom=yes, Zandronum=no`. The block parsers are close, but every
UZDoom-only keyword is a fatal error on Zandronum.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router.
- `concepts/<topic>.md`: Archetype 3.

**No `inventory/`/`notes/` here.** The lump has a handful of small, fixed keyword sets (one per
block type), which the concept pages cover directly; a generated inventory would add nothing.

## Where ANIMDEFS is implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| Load order (`ANIMATED`, then `ANIMDEFS`, then `SWITCHES`) | `src/gamedata/textures/animations.h` (`FTextureAnimator::Init`) | `src/textures/texturemanager.cpp` |
| Parser (`InitAnimDefs`, `ParseAnim`, `ParseRangeAnim`, `ParsePicAnim`, `ParseFramenum`, `ParseTime`, `ParseWarp`, `ParseCameraTexture`, `ParseAnimatedDoor`) | `src/gamedata/textures/animations.cpp` | `src/textures/animations.cpp` |
| UZDoom-only parsers (`ParseCanvasTexture`, `ParseFireTexture`) | `src/gamedata/textures/animations.cpp` | none |
| Switch parser (`ProcessSwitchDef`, `ParseSwitchDef`, `AddSwitchPair`) and the Boom `SWITCHES` lump | `src/gamedata/textures/anim_switches.cpp` | `src/textures/anim_switches.cpp` |
| Boom `ANIMATED` lump (`InitAnimated`) | `src/gamedata/textures/animations.cpp` | `src/textures/animations.cpp` |
| Per-frame update (`UpdateAnimations`) | called from `src/d_main.cpp` | called from `src/d_main.cpp` |
| Switch activation | `src/playsim/p_switch.cpp` | `src/p_switch.cpp` (sends `SetLineTexture` and `SoundPoint` to clients) |
| Animated doors (`DAnimatedDoor`) | `src/playsim/mapthinkers/a_doors.cpp` | `src/p_doors.cpp` |
| ACS `SetCameraToTexture` | `src/playsim/p_acs.cpp` | `src/p_acs.cpp` (also `SERVERCOMMANDS_SetCameraToTexture`, `src/sv_commands.cpp`) |
| Stock definitions | `wadsrc/static/animdefs.txt` | `wadsrc/static/animdefs.txt` |

UltimateDoomBuilder's `Build/Scripting/ZDoom_ANIMDEFS.cfg` and SLADE's `z_animdefs` block in
`dist/res/config/languages/zdoom.txt` are secondary tier-B backing for keyword names only. The UDB
config lacks `canvastexture`, `firetexture`, `notrim`, `hdr`, `color` and `palette`; SLADE lists
them. Neither lists `skyoffset`, `quest`, `any`, `translucent` or `offset`.
