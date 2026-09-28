# Zandronum-lumps doc index

Router only. See `AGENTS.md` for scope, `../shared/AUTHORING.md` for tiers/engine-scope/licensing.

**Zandronum-only section** — none of these nine lumps is parsed by any UZDoom/GZDoom-family
engine. The exception is `TEAMINFO`, which UZDoom also parses (most keys only act on Zandronum). **Not `BOTINFO` or the compiled botscript format** — those live in
[`bots/INDEX.md`](../bots/INDEX.md), a separate, earlier section for the same wiki category.

## Concepts

- [The `ANCRINFO` lump](concepts/ancrinfo.md) — tier A. Announcer profiles: named
  event-to-sound-mapping sets with open-ended custom keys; merge/overwrite behavior for
  `Default`-named blocks; fallback cascading from the default profile; and a curated table of ~90
  standard gameplay and powerup announcer keys.
- [The `AUTHINFO` lump](concepts/authinfo.md) — tier A. Network lump-authentication directives
  (`clearlumps`/`addlump`/`removelump`/`addsprites`/`removesprites`) that both client and server
  hash at startup; cannot touch the hardcoded protected set (`AUTHINFO`/`VOTEINFO`/`MEDALDEF`
  themselves) via a name+namespace set-membership check, not a blacklist.
- [The `VOTEINFO` lump](concepts/voteinfo.md) — tier A. Custom vote types via `votetype Name { ... }`
  blocks; the fixed `CallACS("script")` shape required for `Action`/`PreflightAction`,
  `ForbidCVar`'s server-side gate, the `Arg` parameter-type set, and `Menu`'s MENUDEF submenu hookup.
- [The `SECTINFO` lump](concepts/sectinfo.md) — tier A. Per-map `[MAPNAME]` sections: sector-to-label
  lookup (`names`, live, backs the `$location` chat macro and a HUD overlay), Domination-mode
  control points (`points`, live, feeds `domination.cpp`/ACS), and two dead keys (`base0`/`base1`,
  parsed but read nowhere in the engine).
- [The `CMPGNINF` lump](concepts/cmpgninf.md) — tier A. Single-player campaign settings per map
  (limits, forced game mode/dmflags, bot roster); the full effect is gated to single-player via
  `CAMPAIGN_AllowCampaign()`, but a server still separately consults `wavelimit`/
  `possessionholdtime` and MAPINFO cross-checks `gamemode` against it at parse time. Loading is
  **not** cumulative across WADs like `ANCRINFO`: a parser bug means each newly-parsed `CMPGNINF`
  lump silently replaces the previous one's entries wholesale rather than extending them.
- [The `SKININFO` lump](concepts/skininfo.md) — tier A. Player skin declarations, sharing a parser
  with the older flat `S_SKIN` lump: the two-dialect detection flag, the legacy
  eat-everything-before-`{` quirk, per-dialect error recovery, the 11 general keys, and the two
  overlapping sound-key mechanisms (`*`-prefixed events plus nine legacy `dsXXX` aliases).
- [The `MEDALDEF` lump](concepts/medaldef.md) — tier A. Named, re-openable `MedalName { ... }`
  blocks; floaty-icon awards spawned above players' heads with text, sound, announcer entries, and
  scoreboard icons; the twelve command set (`icon`, `class`, `state`, `text`, `sound`,
  `announcerentry`, `lowermedal`, `scoreboardicon`, and four color/flag commands); the mandatory
  icon/class/state check at block close; a `sc.ScriptError` failure here aborts the engine at
  startup; the engine's own `wadsrc/static/medaldef.txt` (21 medals) is extended the same way a
  mod's own `MEDALDEF` is.
- [The `SCORINFO` lump](concepts/scorinfo.md) — tier A. The scoreboard's own layout/behavior
  language: 3 top-level blocks (`scoreboard`, `column`, `compositecolumn`), the three command
  enums that drive them (`COLUMNCMD_e`/`SCOREBOARDCMD_e`/`MARGINCMD_e`), 11+18 flags, 25 native
  column types with custom column support, and the margin grammar's real `if`/`else`/`&&`/`||`
  flow control, re-evaluated live on every refresh. Note: wiki property names don't match the
  parser's required enum suffixes — see the file's divergence section.
- [The `GAMEMODE` lump](concepts/gamemode.md) — tier A. Mod-configurable game mode definitions:
  named mode blocks with behavioral flags (`COOPERATIVE`/`DEATHMATCH`/`TEAMGAME`), earning-condition
  flags (`PLAYERSEARNKILLS`/`PLAYERSEARNFRAGS`/`PLAYERSEARNPOINTS`/`PLAYERSEARNWINS`), and ten
  other gameplay flags (seventeen in all); properties (`Name`, `ShortName`, `F1Texture`, `WelcomeSound`); gameplay
  settings via `GameSettings` and `LockedGameSettings` blocks with optional `OfflineOnly`/
  `OnlineOnly` scoping; cumulative loading across WADs to fixed `g_GameModes[]` array slots;
  mandatory `GAMETYPE_MASK`/`EARNTYPE_MASK` flag validation at startup; and global
  `DefaultGameSettings`/`DefaultLockedGameSettings` blocks.
- [The `TEAMINFO` lump](concepts/teaminfo.md) — tier B. Team definitions: cumulative loading
  against the stock lump's four teams (= `MAX_TEAMS`, so a mod must `ClearTeams` first and can't
  add a fifth), the 16 keys and their consumers, `PlayerStartThingNumber` shadowing actor editor
  numbers, uninitialized omitted color/start keys, no default network authentication, and UZDoom's
  own parser (`Game` key, 16-team limit, Skulltag keys parsed and discarded).
- [Parsing model across the nine lumps](concepts/parsing-model.md) — tier B. Cumulative-across-WADs
  loading and its one exception (`CMPGNINF`), the fixed `d_main.cpp` parse order, and the two
  independent parser-generation axes (hand-rolled vs. `FScanner`; C-mode vs. default-mode).

`VOTEDEF` is resolved: the `VOTEINFO` wiki page has no mention of the name "VOTEDEF" and is not a
redirect, and it has zero hits anywhere in the Zandronum source. `VOTEINFO` is the correct/current
lump name; `VOTEDEF` was never a real name for it. `MENUDEF`'s Zandronum-specific additions are
deferred — see `maintainer/TODO.md`.

## Inventory tables (generated)

_None yet - no extractor exists yet._

## Notes (curated)

_None yet - no extractor exists yet._
