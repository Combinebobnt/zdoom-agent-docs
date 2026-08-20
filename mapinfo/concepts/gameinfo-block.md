# GameInfo block structure

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `MAPINFO/GameInfo_definition` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=MAPINFO%2FGameInfo_definition&oldid=54708) + verified against Zandronum source (`src/gi.cpp:202-406`) and UZDoom source (`src/gamedata/gi.cpp:272-481`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

The `GameInfo` definition block in MAPINFO is distinct from the separate `GAMEINFO` lump — this page describes the former. It sets global game-wide settings and defaults used throughout a session, including UI/menu configuration, default music and graphics, weapon slots, and engine-side client state (skill-level respawn timing, hit-point-to-gib thresholds, teleport fog height, etc.).

## Block structure and parsing

The `gameinfo { ... }` block contains a series of whitespace-separated key-value pairs. Most keys accept a single value or a type-specific set of values (strings, integers, floats, music references, color values); some keys are repeatable (weapon slots, credit pages, precached assets), and some are block-valued (the `Intro` block on GZDoom/UZDoom).

All of the documented keys use a macro-driven parsing system in both engines: the parser in Zandronum's `src/gi.cpp` and UZDoom's `src/gamedata/gi.cpp` both dispatch through a series of `GAMEINFOKEY_*` macros (differentiating type: string, integer, floating-point, color, music, font, array) mapping each key's string name to its corresponding engine-side `gameinfo_t` struct field. Unknown keys are handled differently per engine (see divergence section below).

## Engine-family divergence

### Unknown key handling

Unknown keys (keys not recognized by either parser) are handled differently per engine:

- **Zandronum:** silently ignored during parsing.
- **UZDoom:** logged as `DPrintf(DMSG_ERROR, ...)` but parsing continues (the error is printed to the debug log, not treated as a fatal parse error). Zandronum projects including UZDoom-only keys will have those keys silently ignored.

### Key availability

**The wiki page describes upstream ZDoom/GZDoom-family features.** Zandronum implements a subset of the keys listed below; all keys in this section that **do not appear in the table below** exist only in UZDoom/GZDoom-family engines (the primary target). Zandronum projects may include them in a MAPINFO source file but they are silently ignored at runtime.

### Zandronum 3.2.1 (verified, exhaustive)

**Common to both engines:**
`advisor`, `backpacktype`, `border`, `borderflat`, `chatSound`, `creditPage` / `addCreditPage`, `cursorPic`, `defKickback`, `defaultBloodColor`, `defaultBloodParticleColor`, `defaultEndSequence`, `defaultRespawnTime`, `definventoryMaxAmount`, `defaultDropStyle`, `dimColor`, `dimAmount`, `drawReadThis`, `endoom`, `finaleFlat`, `finaleMusic`, `finalePage`, `gibFactor`, `infoPage` / `addInfoPage`, `intermissionCounter`, `intermissionMusic`, `nightmareFast`, `noLoopFinaleMusic`, `noRandomPlayerClass`, `pauseSign`, `pickupColor`, `playerClasses` / `addPlayerClasses`, `quitMessages` / `addQuitMessages`, `quitSound`, `skyFlatName`, `statusbar`, `swapMenu`, `telefogHeight`, `textScreenX`, `textScreenY`, `titleMusic`, `titlePage`, `titleTime`, `translator`, `weaponSlot`.

**Menu font colors:** `menuFontColor_Title`, `menuFontColor_Label`, `menuFontColor_Value`, `menuFontColor_Action`, `menuFontColor_Header`, `menuFontColor_Highlight`, `menuFontColor_Selection`, `menuBackButton`.

**Statscreen fonts:** `statScreen_MapNameFont`, `statScreen_FinishedFont`, `statScreen_EnteringFont` are available in both engines. Zandronum additionally accepts `statScreen_FinishedPatch` and `statScreen_EnteringPatch` as patch-name alternatives to the `_Font` variants. UZDoom adds `statScreen_ContentFont` and `statScreen_AuthorFont`.

**Zandronum-only or Zandronum-early keys:**
- `addCustomData` / `removeCustomData` — custom player data columns (Zandronum ACS/modding extension).
- `allowDominationContestScripts` — enable `GAMEEVENT_DOMINATION_CONTEST` ACS script trigger (Zandronum multiplayer mode extension).
- `forceSpawnEventScripts`, `forceDamageEventScripts` — force script triggers on spawn/damage events.
- `player5start` — support for a 5th player start position in multiplayer maps.
- `statscreen_finishedpatch`, `statscreen_enteringpatch` — Zandronum accepts patch-name alternatives to the `_Font` variants for finished/entering statscreen graphics.

### GZDoom/UZDoom-only (verified absent from Zandronum)

**ZScript class references:**
- `basicArmorClass`, `hexenArmorClass` — custom armor class names (requires ZScript).
- `statusBarClass` — custom status bar class (requires ZScript; distinct from `statusbar` which references an SBARINFO file).
- `messageBoxClass` — custom message-box menu class (requires ZScript).
- `helpMenuClass`, `menuDelegateClass` — custom menu classes (require ZScript).
- `altHudClass` — alternate HUD class (requires ZScript).
- `defaultConversationMenuClass` — conversation/Strife dialog menu class (requires ZScript).

**Event handlers and precaching (GZDoom/UZDoom extension):**
- `eventHandlers` / `addEventHandlers` — global event handler class names (requires ZScript).
- `precacheSounds`, `precacheTextures`, `precacheClasses` — preload assets at level load (map-level precaching keys exist separately; these are global defaults).

**Intro cutscene block (GZDoom/UZDoom extension):**
- `intro { ... }` — a block containing `video`/`function`, `sound`/`soundID`, `fps`, and `delete`/`clear` commands for a startup cutscene. Requires ZScript for the `function` path.

**Additional UZDoom/GZDoom-family keys:**
- `blurAmount` — fullscreen menu blur intensity (0–1.0).
- `cheatKey`, `easyKey` — automap arrow graphics for cheated keys (distinct from `mapArrow`).
- `correctPrintBold` — fix for legacy `PrintBold` behavior (compatibility flag).
- `dontCrunchCorpses` — prevent corpse-to-gib crushing behavior.
- `forceTextInMenus` — replace menu graphics with BIGFONT text (language-support feature).
- `forceNoGFXSubstitution` — disable sprite substitution (no description in source).
- `fullscreenAutoaspect` — fullscreen image aspect-ratio handling mode (0–3; see UZDoom source for mode meanings).
- `menuSliderColor`, `menuSliderBackColor` — menu slider styling (UZDoom adds these styling keys beyond the title/label/value/etc. font colors).
- `nomergepickupmsg` — disable message merging for simultaneous pickups.
- `normForwardMove`, `normSideMove` — base player movement speeds (separate from skill-level modifiers).
- `usePauseString` — flag to control pause-string behavior.
- `bloodSplatDecalDistance` — decal rendering distance.
- `statusScreen_Single`, `statusScreen_Coop`, `statusScreen_DM` — custom intermission/tally screen classes per game mode (requires ZScript).

## Properties with type/format notes

- **Music references** (`titleMusic`, `finaleMusic`, `intermissionMusic`): accept SNDINFO logical music names or `$<constant>` references to language strings.
- **Lump names** (`titlePage`, `finaleFlat`, `borderFlat`, etc.): accept up-to-8-character lump identifiers, or (for some keys) long-form names.
- **Color values**: accept strings like `"255 0 0"` (RGB decimal), or named constants like `"RED"` (see TEXTCOLO lump).
- **String arrays** (`creditPage`, `infoPage`, `playerClasses`, `quitMessages`, `precacheSounds`, `precacheTextures`): `addXxx` variant appends; non-prefixed variant replaces the list.
- **Weapon slots** (`weaponSlot = <slot>, "<weapon1>", "<weapon2>", ...`): slot indices 0–9; repeatable per slot.

## Known gaps

The extractor used to clean the source wiki page produced empty descriptions for `ForceNoGFXSubstitution`, `StatScreen_ContentFont`, and `StatScreen_AuthorFont` — these likely have descriptions in the live wiki but were not captured here. The first key is UZDoom-only; the latter two are UZDoom-only additions (Zandronum does implement `statScreen_MapNameFont`, `statScreen_FinishedFont`, and `statScreen_EnteringFont`).
