# zdoom-agent-docs — top-level map

The full section map. Read `CLAUDE.md` first if you haven't — it routes by knowledge area and
gets you to the right section index in one hop, without loading this file. Read this file only
when the router table doesn't resolve your question, or you want the overall coverage picture.

## Major sections

- **[acs/](acs/INDEX.md)** — ACS/BCS function semantics (Zandronum + `zt-bcc`/BCS superset). The
  most mature section — functions, families, and concepts are well-populated with tier-A/B prose,
  with a long tail of compiler/engine names still signature-only (tier C) until someone writes
  them up. See it for what a fully-populated section looks like. See the section's own `INDEX.md`
  for current counts.
- **[decorate/](decorate/INDEX.md)** — DECORATE action functions, actor flags, actor properties.
  Generated inventories cover every action function, actor flag, and actor property tree-wide
  (class-scoped, so some names repeat per class), cross-referenced against UZDoom — every row
  starts tier C until a `notes/`/`actions/` file promotes it; a substantial and growing subset of
  actions already have full tier-A/B prose. See the section's own `INDEX.md` for current counts.
- **[zscript/](zscript/INDEX.md)** — ZScript classes, methods, VM/scope semantics.
  **UZDoom/GZDoom-family only — ZScript does not exist in Zandronum.** Coverage is still early —
  see the section's own `INDEX.md` for what's documented so far.

## Lump formats

- **[mapinfo/](mapinfo/INDEX.md)** — MAPINFO keys and block structure.
- **[gldefs/](gldefs/INDEX.md)** — GLDEFS keys (dynamic lights, glows, etc).
- **[sbarinfo/](sbarinfo/INDEX.md)** — SBARINFO keys and commands.
- **[cvarinfo/](cvarinfo/INDEX.md)** — CVARINFO declaration syntax and semantics.

## Runtime & assets

- **[console/](console/INDEX.md)** — console cvars and CCMDs. Generated inventories cover every
  cvar and ccmd tree-wide, cross-referenced against UZDoom; see `zandronum/docs/commands.txt` for
  the first-party prose reference `notes/` entries should draw from. A growing subset of cvars/
  ccmds have curated `notes/` prose — see the section's own `INDEX.md` for what's covered.
- **[sprites/](sprites/INDEX.md)** — sprite naming/rotation conventions.

## Shared concepts

- **[shared/concepts/](shared/concepts/)** — knowledge that genuinely spans sections (engine
  divergence patterns, lump load order across formats). See `shared/ARCHETYPES.md`'s Archetype 3
  for when something belongs here instead of in one section's own `concepts/`.
  - [Constants across ACS/BCS and DECORATE](shared/concepts/constants.md) — tier A. Why "a named
    constant" is two unrelated mechanisms depending which language you're in (ACS/BCS's is a
    preprocessor artifact; DECORATE's is a real engine-parsed keyword with no preprocessor at
    all) — routes to `acs/concepts/constants.md` and `decorate/concepts/constants.md` for each
    side's own detail.

## Not yet covered

These lump formats have local tier-B backing (UltimateDoomBuilder's `Build/Scripting/*.cfg` files
and/or SLADE's `dist/res/config/languages/*.txt`) but no section exists yet — listed here so an
agent can tell "not covered" from "doesn't exist", rather than silently getting nothing back for a
name search. A directory gets created the same session its first doc does; see `shared/AUTHORING.md`
for what earns an entry.

| Format | Backing source (once someone documents it) |
|---|---|
| MENUDEF | `UDB/Build/Scripting/ZDoom_MENUDEF.cfg` |
| KEYCONF | `UDB/Build/Scripting/ZDoom_KEYCONF.cfg` |
| GAMEINFO | `UDB/Build/Scripting/ZDoom_GAMEINFO.cfg` |
| TEXTURES | `UDB/Build/Scripting/ZDoom_TEXTURES.cfg` |
| SNDINFO | `UDB/Build/Scripting/ZDoom_SNDINFO.cfg` |
| ANIMDEFS | `UDB/Build/Scripting/ZDoom_ANIMDEFS.cfg` |
| LOCKDEFS | `UDB/Build/Scripting/ZDoom_LOCKDEFS.cfg` |
| TERRAIN | `UDB/Build/Scripting/ZDoom_TERRAIN.cfg` |
| REVERBS | `UDB/Build/Scripting/ZDoom_REVERBS.cfg` |
| FONTDEFS | `UDB/Build/Scripting/ZDoom_FONTDEFS.cfg` |
| MODELDEF | `UDB/Build/Scripting/ZDoom_MODELDEF.cfg` |
| VOXELDEF | `UDB/Build/Scripting/ZDoom_VOXELDEF.cfg` |
| DEHACKED | `UDB/Build/Scripting/Dehacked.cfg` |

`UDB` above is the `udb` key in `sources.local.md`/`sources.example.md`.
