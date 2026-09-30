# GameInfo block structure

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `MAPINFO/GameInfo_definition` (retrieved 2026-09-28, https://zdoom.org/w/index.php?title=MAPINFO%2FGameInfo_definition&oldid=54708) + verified against Zandronum source (`src/gi.cpp:202-430`, unknown-key skipping `src/g_mapinfo.cpp:583-593`, color parsing `src/v_video.cpp:442-532`, `player5start` use `src/p_mobj.cpp:5973-5977`) and UZDoom source (`src/gamedata/gi.cpp:261-470`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

The `GameInfo` definition block in MAPINFO is distinct from the separate `GAMEINFO` lump ([gameinfo-lump/concepts/gameinfo-lump.md](../../gameinfo-lump/concepts/gameinfo-lump.md)) — this page describes the former. It sets global game-wide settings and defaults used throughout a session, including UI/menu configuration, default music and graphics, weapon slots, and gameplay defaults (the fallback monster respawn time for skills that set none, the spawn-health multiplier for default gib health, teleport fog height, etc.).

## Block structure and parsing

The `gameinfo { ... }` block contains a series of `key = value` entries; a key taking several values separates them with commas. Most keys accept a single value or a type-specific set of values (strings, integers, floats, music references, color values); some keys are repeatable (weapon slots, credit pages, precached assets), and some are block-valued (the `Intro` block on GZDoom/UZDoom).

Most keys use a macro-driven parsing system in both engines: the parser in Zandronum's `src/gi.cpp` and UZDoom's `src/gamedata/gi.cpp` both dispatch through a series of `GAMEINFOKEY_*` macros (differentiating type: string, integer, floating-point, boolean, color, music, font, array, among others) mapping each key's string name to its corresponding engine-side `gameinfo_t` struct field. A few keys are parsed by hand instead: `weaponSlot`, `border`, `armorIcons` and `mapArrow` in both engines, plus Zandronum's `addCustomData`/`removeCustomData` and UZDoom's `dialogue` and `intro`. Unknown keys are handled differently per engine (see divergence section below).

## Engine-family divergence

### Unknown key handling

Unknown keys (keys not recognized by either parser) are handled differently per engine:

- **Zandronum:** silently skipped at parse time. The parser still requires `key =`, then skips a comma-separated value list. A UZDoom `intro { ... }` block has no `=`, so on Zandronum it is a fatal MAPINFO parse error, not an ignored key.
- **UZDoom:** logged as `DPrintf(DMSG_ERROR, ...)` but parsing continues (the error is printed to the debug log, not treated as a fatal parse error). Zandronum projects including UZDoom-only `key = value` entries will have those keys silently skipped.

### Key availability

**The wiki page describes upstream ZDoom/GZDoom-family features.** Zandronum implements a subset of the keys listed below; all keys in this section that **do not appear in the table below** exist only in UZDoom/GZDoom-family engines (the primary target). Zandronum projects may include them in a MAPINFO source file and Zandronum's parser silently skips them. The exception is the `intro` block, which is a fatal parse error on Zandronum (see above).

### Zandronum 3.3-alpha (verified)

**Common to both engines:**
`advisoryTime`, `armorIcons`, `backpacktype`, `border`, `borderflat`, `chatSound`, `creditPage` / `addCreditPage`, `cursorPic`, `defKickback`, `defaultBloodColor`, `defaultBloodParticleColor`, `defaultEndSequence`, `defaultRespawnTime`, `definventoryMaxAmount`, `defaultDropStyle`, `dimColor`, `dimAmount`, `drawReadThis`, `endoom`, `finaleFlat`, `finaleMusic`, `finalePage`, `forceKillScripts`, `gibFactor`, `infoPage` / `addInfoPage`, `intermissionCounter`, `intermissionMusic`, `mapArrow`, `nightmareFast`, `noLoopFinaleMusic`, `noRandomPlayerClass`, `pageTime`, `pauseSign`, `pickupColor`, `playerClasses` / `addPlayerClasses`, `quitMessages` / `addQuitMessages`, `quitSound`, `skyFlatName`, `statusbar`, `swapMenu`, `telefogHeight`, `textScreenX`, `textScreenY`, `titleMusic`, `titlePage`, `titleTime`, `translator`, `weaponSlot`.

**Menu font colors:** `menuFontColor_Title`, `menuFontColor_Label`, `menuFontColor_Value`, `menuFontColor_Action`, `menuFontColor_Header`, `menuFontColor_Highlight`, `menuFontColor_Selection`, `menuBackButton`.

**Statscreen fonts:** `statScreen_MapNameFont`, `statScreen_FinishedFont`, `statScreen_EnteringFont` are available in both engines. Zandronum additionally accepts `statScreen_FinishedPatch` and `statScreen_EnteringPatch` as patch-name alternatives to the `_Font` variants. UZDoom adds `statScreen_ContentFont` and `statScreen_AuthorFont`.

**Zandronum-only or Zandronum-early keys:**
- `addCustomData` / `removeCustomData` — custom player data columns (Zandronum ACS/modding extension).
- `allowDominationContestScripts` — enable `GAMEEVENT_DOMINATION_CONTEST` ACS script trigger (Zandronum multiplayer mode extension).
- `forceSpawnEventScripts`, `forceDamageEventScripts` — force script triggers on spawn/damage events.
- `player5start`: the editor number (DoomEdNum) of the player 5 start. Players 6 and up take the following consecutive numbers, up to `MAXPLAYERS` (8 on Strife). The base MAPINFOs set 4001 for Doom, Heretic and Chex, 9100 for Hexen and 5 for Strife.
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
- `statscreen_single`, `statscreen_coop`, `statscreen_dm` — custom intermission/tally screen classes per game mode (requires ZScript).

## Properties with type/format notes

- **Music references** (`titleMusic`, `finaleMusic`, `intermissionMusic`): accept SNDINFO logical music names or `$<constant>` references to language strings (the string's text gets a `D_` prefix, the DeHackEd convention). An optional `:<n>` suffix selects the subsong.
- **Lump names**: on Zandronum, `titlePage`, `finaleFlat`, `borderFlat`, `pauseSign`, `skyFlatName`, `endoom` and `menuBackButton`, plus each `creditPage`/`infoPage`/`finalePage` entry, are capped at 8 characters. A longer value is a fatal script error. UZDoom accepts long names for those single-value keys and keeps the 8-character cap only on the three page arrays.
- **Color values** (`pickupColor`, `defaultBloodColor`, `defaultBloodParticleColor`, `dimColor`): accept `"#RRGGBB"`, `"#RGB"`, `"RRGGBB"`, a space-separated `"RR GG BB"` where each component is hexadecimal (only its first two characters count), or a color name from the `X11R6RGB` lump such as `"red"`. `"255 0 0"` is therefore not red: it reads as hex `25 00 00`.
- **String arrays** (`creditPage`, `infoPage`, `playerClasses`, `quitMessages`): the `addXxx` variant appends; the non-prefixed variant replaces the list. `finalePage` has only the replacing form. UZDoom's `precacheSounds`, `precacheTextures` and `precacheClasses` have no `add` form and always append.
- **Weapon slots** (`weaponSlot = <slot>, "<weapon1>", "<weapon2>", ...`): slot indices 0-9; an index outside that range is a fatal script error. Each `weaponSlot` line clears that slot first, so a later line for the same slot replaces its list rather than adding to it.

## Wiki/source divergence

The wiki example in the source page contains `mapinfo = "mapinfo/doom2.txt"`, which is not recognized by either Zandronum or UZDoom parsers. Neither engine implements it: Zandronum skips it silently (per unknown-key handling above), and UZDoom skips it with an "Unknown GAMEINFO key" message that only prints when the `developer` cvar is on (`src/gamedata/gi.cpp:460-465`).

## Known gaps

The extractor used to clean the source wiki page produced empty descriptions for `ForceNoGFXSubstitution`, `StatScreen_ContentFont`, and `StatScreen_AuthorFont` — these likely have descriptions in the live wiki but were not captured here. The first key is UZDoom-only; the latter two are UZDoom-only additions (Zandronum does implement `statScreen_MapNameFont`, `statScreen_FinishedFont`, and `statScreen_EnteringFont`).
