# MAPINFO doc index

Router only. See `AGENTS.md` for where MAPINFO parsing lives in engine source,
`../shared/AUTHORING.md` for tiers/engine-scope/licensing.

## Concepts

- [MAPINFO format](concepts/mapinfo-format.md) — tier A. Overview of the MAPINFO/ZMAPINFO lump
  format, including old (Hexen) vs. new format distinction, the per-WAD ZMAPINFO override
  behavior, supported block types, and engine-family divergences (four block types —
  doomednums, damagetype, spawnnums, conversationids — exclusive to GZDoom-family engines and
  absent from Zandronum).
- [GameInfo block definition](concepts/gameinfo-block.md) — tier B. Defines global game settings
  (UI, defaults, precaching); Zandronum and GZDoom/UZDoom families diverge significantly — all
  ZScript class keys, event handlers, Intro block, and several asset/ui keys are GZDoom/UZDoom-only.
- [Map block definitions and inheritance](concepts/map-block-and-inheritance.md) — tier B. The
  `map`, `defaultmap`, `adddefaultmap`, and `gamedefaults` blocks form a hierarchical inheritance
  system. Describes block forms, file-scoping rules (`defaultmap` is file-local; `gamedefaults` is
  game-wide), and reset-vs-accumulate semantics. Includes comprehensive engine-family divergence
  survey: Zandronum lacks ~13 GZDoom-family properties (renderer features like `EnableShadowmap`,
  cutscene blocks `Intro`/`Outro`, ZScript `EventHandlers`, metadata keys `Author`/`Label`, and
  others); GZDoom-family lacks Zandronum-specific multiplayer/campaign properties. Spot-checked
  against both engines; see file for full list. Also covers the `monsterfallingdamage`/
  `nomonsterfallingdamage` keys' HexenHack retraction gap — a numeric-header (`map 1 "..."`) map
  declaration re-applies `LEVEL2_MONSTERFALLINGDAMAGE` after the `defaultmap`/`gamedefaults`
  baseline copy, defeating an inherited `nomonsterfallingdamage`, including on every IWAD hexen.wad
  map declaration.
- [Cluster block definition](concepts/cluster-block.md) — tier A. Defines cluster-scope MAPINFO
  block for intermission messages, hub state retention, and cutscene blocks; comprehensive
  engine-family divergence survey (GZDoom-family `AllowIntermission`, `Intro`, `Outro`, `GameOver`
  blocks absent in Zandronum).
- [Episode block definition](concepts/episode-block.md) — tier B. Defines selectable episodes in
  the episode menu; documents common properties (name, picname, key, noskillmenu, optional,
  extended, remove) with engine-family divergences: intro block (UZDoom/GZDoom-only), bot episode
  properties (Zandronum-only), and lookup property unsupported in both.
- [Skill block definition](concepts/skill-block.md) — tier A. Defines difficulty levels with
  monster/damage scaling, respawn rules, actor replacement, and menu properties. Zandronum and
  GZDoom/UZDoom families diverge significantly: nine properties are UZDoom-only, DefaultSkill
  behavior differs (Zandronum errors on duplicates, UZDoom uses last), and Zandronum's fixed-point
  storage quantizes very small factors.

## Inventory tables (generated)

_None yet — no extractor exists for MAPINFO keys yet (unlike DECORATE flags/properties or console
cvars/ccmds, MAPINFO keys aren't declared via a single repeating C macro; they're read ad hoc
inside `FMapInfoParser::ParseMapInfo`'s block-parsing switch, so an extractor would need a
different approach — likely scanning for the parser's own string-literal key comparisons rather
than a macro table. Left as a documented gap rather than a guessed-at generator)._

## Notes (curated, per key)

_None yet._
