# zdoom-agent-docs — top-level map

The full section map. Read `AGENTS.md` first if you haven't — it routes by knowledge area and
gets you to the right section index in one hop, without loading this file. Read this file only
when the router table doesn't resolve your question, or you want the overall coverage picture.

## Major sections

- **[acs/](acs/INDEX.md)** — ACS/BCS function semantics for UZDoom/GZDoom-family (primary target)
  and Zandronum + `zt-bcc`/BCS superset where they diverge. The
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
- **[menudef/](menudef/INDEX.md)** — MENUDEF block/menu-item grammar, shared by both engines
  (item-keyword dispatch is closed on Zandronum, open on UZDoom), plus Zandronum's own
  option-menu-item additions.
- **[zandronum-lumps/](zandronum-lumps/INDEX.md)** — nine other Zandronum/Skulltag-native lump
  formats (`ANCRINFO`, `AUTHINFO`, `CMPGNINF`, `GAMEMODE`, `MEDALDEF`, `SCORINFO`, `SECTINFO`,
  `SKININFO`, `VOTEINFO`), each unrelated to the others beyond sharing that lineage.
  **Zandronum-only** — none exists on UZDoom/GZDoom-family engines. Also `TEAMINFO`, the one
  exception: UZDoom parses it too, though most of its keys only act on Zandronum. `BOTINFO` and the compiled
  botscript format are a
  related but separate lump pair covered by `bots/`, not here.

## Runtime & assets

- **[console/](console/INDEX.md)** — console cvars and CCMDs. Generated inventories cover every
  cvar and ccmd tree-wide, cross-referenced against UZDoom; see `zandronum/docs/commands.txt` for
  the first-party prose reference `notes/` entries should draw from. A growing subset of cvars/
  ccmds have curated `notes/` prose — see the section's own `INDEX.md` for what's covered.
- **[sprites/](sprites/INDEX.md)** — sprite naming/rotation conventions.
- **[bots/](bots/INDEX.md)** — the `BOTINFO` declaration lump and the compiled botscript bytecode
  its `script =` key names. **Zandronum-only** — UZDoom/GZDoom-family engines parse neither. Two
  tier-B concept pages cover both lumps; the 114-entry bot command table is not yet inventoried.

## Networking

- **[netcode/](netcode/INDEX.md)** — the out-of-band UDP protocols a Zandronum server speaks to
  external tools: launcher queries, master-server registration and ban-list push, and RCON.
  **Zandronum-only** — UZDoom/GZDoom-family engines have no dedicated server. The game protocol
  and hosting how-tos are out of scope; outbound-traffic measurement lives in `console/`.

## Shared concepts

- **[shared/concepts/](shared/concepts/)** — knowledge that genuinely spans sections (engine
  divergence patterns, lump load order across formats). See `shared/ARCHETYPES.md`'s Archetype 3
  for when something belongs here instead of in one section's own `concepts/`.
  - [Constants across ACS/BCS and DECORATE](shared/concepts/constants.md) — tier A. Why "a named
    constant" is two unrelated mechanisms depending which language you're in (ACS/BCS's is a
    preprocessor artifact; DECORATE's is a real engine-parsed keyword with no preprocessor at
    all) — routes to `acs/concepts/constants.md` and `decorate/concepts/constants.md` for each
    side's own detail.
  - [PK3 lump names drop the extension](shared/concepts/pk3-lump-naming.md) — tier A. A PK3
    entry is named by its basename cut at the last dot and capped at 8 chars, so
    `TEXTURES.tex`/`TEXTURES.hud`/`TEXTURES.cmap` are all one lump name `TEXTURES` — legal and
    supported for formats the engine enumerates in a `FindLump` loop, silently lossy for ones
    it looks up once. Searching an archive for an exact lump name gives false negatives.
  - [Persistent storage: Zandronum's ACS database has no UZDoom/GZDoom-family
    equivalent](shared/concepts/persistent-storage-engine-divergence.md) — tier B. Zandronum's
    SQLite-backed ACS database family has no counterpart at all on UZDoom/GZDoom-family engines
    (not even the dead `PCD_WRITETOINI`/`GETFROMINI` opcodes work) — closest analogue is
    CVARINFO-declared archived cvars, meaningfully weaker on every axis (no dynamic keys, no
    ranked queries, ZScript-only).
  - [Damage retaliation: what writes a monster's `target` during
    gameplay](shared/concepts/monster-target-retaliation.md) — tier B. Getting hit flips who a
    monster is chasing, gated by a twelve-check `OkayToSwitchTarget` decision (Zandronum's gate
    set; UZDoom's native default adds three more and is `native virtual`, fully overridable from
    ZScript) — and `AActor::Die` unconditionally overwrites `target` with the killer regardless of
    that gate.

## Not yet covered

These lump formats have local tier-B backing (UltimateDoomBuilder's `Build/Scripting/*.cfg` files
and/or SLADE's `dist/res/config/languages/*.txt`) but no section exists yet — listed here so an
agent can tell "not covered" from "doesn't exist", rather than silently getting nothing back for a
name search. A directory gets created the same session its first doc does; see `shared/AUTHORING.md`
for what earns an entry.

| Format | Backing source (once someone documents it) |
|---|---|
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
