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
- [Map block definitions and inheritance](concepts/map-block-and-inheritance.md) — tier A. The
  `map`, `defaultmap`, `adddefaultmap`, and `gamedefaults` blocks form a hierarchical inheritance
  system. Describes block forms, file-scoping rules (`defaultmap` is file-local; `gamedefaults` is
  game-wide), and reset-vs-accumulate semantics. Includes an engine-family divergence survey
  checked against both parsers: Zandronum lacks ~20 GZDoom-family properties (renderer features
  like `EnableShadowmap`, cutscene blocks `Intro`/`Outro` (fatal there), ZScript `EventHandlers`,
  metadata keys `Author`/`Label`, and others); GZDoom-family lacks Zandronum-specific
  multiplayer/campaign properties. Also covers the `monsterfallingdamage`/
  `nomonsterfallingdamage` keys' HexenHack retraction gap — a numeric-header (`map 1 "..."`) map
  declaration re-applies `LEVEL2_MONSTERFALLINGDAMAGE` after the `defaultmap`/`gamedefaults`
  baseline copy, defeating an inherited `nomonsterfallingdamage`, including on every IWAD hexen.wad
  map declaration.
- [Cluster block definition](concepts/cluster-block.md) — tier A. Defines cluster-scope MAPINFO
  block for intermission messages, hub state retention, and cutscene blocks; comprehensive
  engine-family divergence survey (GZDoom-family `AllowIntermission`, `Intro`, `Outro`, `GameOver`
  blocks absent in Zandronum, where a cutscene block is fatal but a bare unknown flag isn't).
- [Episode block definition](concepts/episode-block.md) — tier B. Defines selectable episodes in
  the episode menu; documents common properties (name, picname, key, noskillmenu, optional,
  extended, remove) with engine-family divergences: intro block (UZDoom/GZDoom-only), bot episode
  properties (Zandronum-only), and lookup property unsupported in both.
- [Skill block definition](concepts/skill-block.md) — tier A. Defines difficulty levels with
  monster/damage scaling, respawn rules, actor replacement, and menu properties. Zandronum and
  GZDoom/UZDoom families diverge significantly: nine properties are UZDoom-only, DefaultSkill
  behavior differs (Zandronum errors on any second one, so a PWAD's `DefaultSkill` is fatal unless
  `clearskills` came first; UZDoom uses last), and Zandronum's fixed-point
  storage quantizes very small factors.
- [Zandronum map-definition extensions](concepts/zandronum-map-extensions.md) — tier A.
  Zandronum-specific `map` block properties, sourced from the Zandronum wiki (not the ZDoom wiki
  the other files here cite, so kept as its own file per the licensing split): multiplayer/campaign
  features (`islobby`, `nobotnodes`) and intermission customization (`gamemode`, `winnerpic`,
  `loserpic`, `winnermusic`, `losermusic`); includes version-availability breakdown (some
  properties pre-3.2.1, others 3.3-alpha and above only).

- [Automap block definition](concepts/automap-block.md) — tier A. `automap`/`automap_overlay`
  colorsets (`base`, `showlocks`, 22 shared color keys). `SectorFillAlpha`, `PortalColor`,
  `SectorFillColor` and `UnexploredSecretColor` are UZDoom-only and a fatal "Unknown key" on
  Zandronum; each block restarts from white rather than layering.
- [Intermission block definition](concepts/intermission-block.md) — tier A. Named intermission
  sequences (Image, Scroller, Fader, Wiper, TextScreen, Cast, GotoTitle, UZDoom-only Cutscene) and
  their keys. Every step's default `Time` is 0 (wait for a key); the wiki has seconds/tics
  reversed for `InitialDelay`/`ScrollTime`/`TextDelay`; a `Multiplayer` DrawConditional never
  draws in either engine.
- [DamageType block](concepts/damagetype-block.md) — tier A. MAPINFO `DamageType` (Factor,
  ReplaceFactor, NoArmor, Obituary) and the factor-resolution order. UZDoom-only as a MAPINFO
  block; the DECORATE `damagetype` form works on both engines but has no `Obituary` and takes
  `Factor` without `=`.
- [DoomEdNums block](concepts/doomednums-block.md) — tier A. Editor number to class mapping with
  optional `noskillflags`, special and args (`+` partial-args form). UZDoom-only; a DECORATE
  header number always wins; ZScript classes can only get a number this way. Duplicate and
  bad-special errors are non-fatal (unreachable error check).
- [SpawnNums block](concepts/spawnnums-block.md) — tier A. Spawn number to class mapping for
  `Thing_Spawn` and friends; separate namespace from editor numbers. UZDoom-only; an actor's
  DECORATE `SpawnID` overrides it and `N = None` only clears MAPINFO-sourced numbers (including
  the engine's own base table).
- [ConversationIDs block](concepts/conversationids-block.md) — tier A. Strife conversation ID to
  class mapping. UZDoom-only; actor `ConversationID` overrides it; the built-in Strife IDs come
  from the engine's bundled MAPINFO, so `N = None` clears them. DECORATE `ConversationID` teaser
  arguments only matter on Zandronum.

## Inventory tables (generated)

_None yet — no extractor exists for MAPINFO keys yet (unlike DECORATE flags/properties or console
cvars/ccmds, MAPINFO keys aren't declared via a single repeating C macro; they're read ad hoc
inside `FMapInfoParser::ParseMapInfo`'s block-parsing switch, so an extractor would need a
different approach — likely scanning for the parser's own string-literal key comparisons rather
than a macro table. Left as a documented gap rather than a guessed-at generator)._

## Notes (curated, per key)

_None yet._
