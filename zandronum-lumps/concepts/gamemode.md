# The `GAMEMODE` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `GAMEMODE` (https://wiki.zandronum.com/w/index.php?title=GAMEMODE&oldid=2438, retrieved 2026-09-09); verified against the Zandronum source's `src/gamemode.cpp` (GAMEMODE_ParseGameModeInfo, GAMEMODE_ParseGameModeBlock, GAMEMODE_ParseGameSettingBlock; lines 188-416, 420-489) and `src/gamemode_enums.h`; locked-setting enforcement in `src/c_cvars.cpp` (`FBaseCVar::SetGenericRep`, lines 263, 283).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
(NonCommercial) — see [LICENSE](../../LICENSE) §2.

`GAMEMODE` declares or modifies game mode definitions: named sets of behavioral flags, game-setting cvars, and display names that control round progression, scoring, and player mechanics in multiplayer modes. Custom or modified modes take effect at startup. It is a plain text lump of named mode blocks and optional default blocks, parsed at startup by `GAMEMODE_ParseGameModeInfo` (called from `src/d_main.cpp` at line 2905, between `CMPGNINF` and `VOTEINFO` in the fixed startup parse order).

## Grammar and scope

```text
ModeName
{
    RemoveFlag FLAGNAME1
    AddFlag FLAGNAME2
    Name "Human-readable name"
    ShortName "ShortName"
    F1Texture "LumpName"
    WelcomeSound "SoundName"

    GameSettings
    {
        cvar1 = value
        cvar2 = value
        OfflineOnly { cvar3 = value }
        OnlineOnly { cvar4 = value }
    }

    LockedGameSettings
    {
        cvar5 = value
    }
}
```

Every `GAMEMODE` block is named: the bare token before `{` is the mode's identifying name (case-insensitive when looked up). The block's closing `}` returns control to the top level; another mode name begins the next block, or the lump ends. The parser is `FScanner`-based and reports errors through `sc.ScriptError`, which routes to `I_Error`: a bad `GAMEMODE` lump does not just fail to load, it aborts the engine at startup with that message on screen (same as `MEDALDEF`, `VOTEINFO`, `SCORINFO`, `AUTHINFO`).

Game mode names must be one of the sixteen predefined `GAMEMODE_e` enum values: `Cooperative`, `Survival`, `Invasion`, `Deathmatch`, `Teamplay`, `Duel`, `Terminator`, `LastManStanding`, `TeamLMS`, `Possession`, `TeamPossession`, `TeamGame`, `CTF`, `OneFlagCTF`, `Skulltag`, `Domination`. Each is a fixed slot in the engine's `g_GameModes[]` array, so multiple blocks for the same mode name (in this lump or across several lumps) do not create duplicate entries — they modify the existing mode's attributes in place.

## Flags and their categories

The parser accepts named flags via `AddFlag` and `RemoveFlag` commands, both suffixed with the bare enum name (not the `GMF_` prefix). Flags are looked up via `sc.MustGetEnumName("flag", "GMF_", GetValueGMF)`, so `AddFlag COOPERATIVE` (case-insensitive) is what a `GAMEMODE` file writes, not `AddFlag GMF_COOPERATIVE` or `AddFlag = "COOPERATIVE"`. All seventeen available flags are listed below. The engine validates two flags-per-mode at startup (lines 461-485, `src/gamemode.cpp`):

- **Exactly one `GAMETYPE_MASK` bit must be set**: `COOPERATIVE`, `DEATHMATCH`, or `TEAMGAME`. If a mode has none or more than one, the engine aborts at startup.
- **Exactly one `EARNTYPE_MASK` bit must be set**: `PLAYERSEARNKILLS`, `PLAYERSEARNFRAGS`, `PLAYERSEARNPOINTS`, or `PLAYERSEARNWINS`. If a mode has none or more than one, the engine aborts at startup.

The engine's own `wadsrc/static/gamemode.txt` ships sixteen modes with these flags already configured; a mod modifying an existing mode must be careful not to strip a `GAMETYPE_MASK` or `EARNTYPE_MASK` bit without adding a different one from the same category.

### Type-categorizing flags

- **`COOPERATIVE`** — designates this mode as a cooperative-family mode (one of the three `GAMETYPE_MASK` options). Modes with this flag spawn players at co-op starts, not deathmatch or team starts.
- **`DEATHMATCH`** — designates this mode as a deathmatch/fragfest-family mode (one of the three `GAMETYPE_MASK` options). Modes with this flag spawn players at deathmatch starts.
- **`TEAMGAME`** — designates this mode as a team-game-family mode (one of the three `GAMETYPE_MASK` options). Modes with this flag spawn players at team starts.

### Earning-condition flags

- **`PLAYERSEARNKILLS`** — players earn the round by accumulating kills against monsters, not other players. Used by co-op-family modes (Cooperative, Survival, Invasion).
- **`PLAYERSEARNFRAGS`** — players or teams win the game by killing enemy players (one of the four `EARNTYPE_MASK` options). Used by deathmatch-family modes.
- **`PLAYERSEARNPOINTS`** — players or teams win the game by earning points rather than frags — used by point-based modes like Possession and CTF (one of the four `EARNTYPE_MASK` options).
- **`PLAYERSEARNWINS`** — players or teams win the game by winning rounds rather than by a single-round metric (one of the four `EARNTYPE_MASK` options). Used by Last Man Standing and similar round-based modes.
- **`PLAYERSEARNMEDALS`** — controls which game modes players can earn medals through competitive games.

### Gameplay-enabling flags

- **`USEFLAGASTEAMITEM`** — forces a game mode to use a team's flag item or icon instead of their skull (used in CTF variants).
- **`PLAYERSONTEAMS`** — players are organized into teams; displays the team selection menu when pressing spacebar to join.
- **`USETEAMITEM`** — enables support for a team's flag or skull item in CTF and Skulltag, or the white flag in 1-flag CTF.
- **`USEMAXLIVES`** — players have a limited number of lives, controlled by the `sv_maxlives` cvar.
- **`DEADSPECTATORS`** — enables support for dead spectators (players that are dead and cannot rejoin until the round ends).

### Gameplay-restricting flags

- **`DONTSPAWNMAPTHINGS`** — items and weapons are not spawned; only monsters spawn (used by survival/elimination modes).
- **`MAPRESETS`** — the map can be reset to its original state. The `ResetMap` ACS function and `ResetMap` console command require this flag to be set to work.
- **`MAPRESET_RESETS_MAPTIME`** — resetting the map also resets the level time. Also prevents the time limit from being active while the game is not in progress.
- **`DONTPRINTPLAYERSLEFT`** — prevents the "x allies/opponents left" message from being drawn on the screen.

## Properties: Name, ShortName, F1Texture, WelcomeSound

- **`Name "..."` (required)** — the mode's display name as it appears on the scoreboard, countdown screen, and server console. The value is the next string token, with no `=` (the shipped `gamemode.txt` quotes it). Every mode must have a non-empty `Name` once every `GAMEMODE` lump has been parsed, or the engine aborts at startup (lines 467-468).
- **`ShortName "..."`** (required, auto-truncated) — a shorter, abbreviated version of the mode's name; used in the built-in server browser. Same string-token value, no `=`. Automatically truncated to 8 characters by the parser (`ShortName.Truncate(8)`), so longer strings are silently shortened. Every mode must have a non-empty `ShortName` once every `GAMEMODE` lump has been parsed, or the engine aborts at startup (lines 469-470).
- **`F1Texture "..."`** (optional, auto-truncated) — the graphics lump name drawn in the "Read This!" menu in non-single-player games if no other help page is defined. Same string-token value, no `=`. Automatically truncated to 8 characters (`F1Texture.Truncate(8)`). No validation of the lump's existence happens at parse time; an invalid name is silently stored.
- **`WelcomeSound "..."`** (optional) — the announcer sound played at the start of a new game (e.g., "welcome to capture the flag" or "welcome to Skulltag"). Same string-token value, no `=`.

The scanner treats `=` as a token of its own, so writing `Name = "Foo"` stores `=` as the name and then aborts on `"Foo"` as an unknown option. Only CVar assignments inside the settings blocks below take an `=`.

## GameSettings and LockedGameSettings blocks

Both `GameSettings` and `LockedGameSettings` blocks hold CVar assignments: a CVar name, an `=` token, and a value. CVars must have the `CVAR_GAMEPLAYSETTING` flag or, if a flag CVar, must belong to one of the approved flagsets (`DMFlags`, `DMFlags2`, `ZaDMFlags`, `CompatFlags`, `CompatFlags2`, `ZaCompatFlags`, `LMSAllowedWeapons`, `LMSSpectatorSettings`). Attempting to set a CVar without this flag is a fatal parse error.

The difference between the two blocks is mutability at runtime:

- **`GameSettings`** — the CVar values can still be changed during gameplay by the server operator or clients (depending on the CVar's own `CVAR_SERVERINFO` flag). Useful for mods that want to change certain values by default but still allow the host to customize them.
- **`LockedGameSettings`** — the CVar values can never be changed after the mode is selected. Attempting to change a locked CVar prints an error message and blocks the change. Useful for mods that need certain settings enabled/disabled and do not want the host to mess with them.

Locked settings are enforced by `GAMEMODE_IsGameplaySettingLocked` (line 1661), which checks whether the current mode has the CVar in its locked list, respecting scope rules (see below). The wiki's claim that "attempting to do so will print an error message" is accurate. Both the block and the message ("... cannot be changed in this game mode.") live in the CVar setter `FBaseCVar::SetGenericRep` (`src/c_cvars.cpp:283`), not in the `GAMEMODE` parsing code. For a flagset CVar such as `dmflags`, the setter reverts only the locked bits and prints the message per bit (`src/c_cvars.cpp:263`).

## OfflineOnly and OnlineOnly sub-blocks

By default, all GameSettings/LockedGameSettings CVars apply to both offline (single-player or multiplayer emulation) and online games. However, `OfflineOnly` and `OnlineOnly` sub-blocks allow different values for each context:

```text
GameSettings
{
    sv_respawntime = 30
    OfflineOnly { sv_respawntime = 10 }
    OnlineOnly { sv_respawntime = 20 }
}
```

Sub-blocks are **not** nestable: attempting to open an `OnlineOnly` block while already inside an `OfflineOnly` block is a fatal parse error. The scope applies to every CVar declared until the sub-block closes with `}` (the same brace that closes the sub-block), and scope then returns to `GAMESCOPE_OFFLINEANDONLINE` (both contexts) until another sub-block opens. "Offline" is defined exactly as `NETWORK_GetState() != NETSTATE_SERVER` (line 155, `src/gamemode.cpp`); online play is exactly `NETWORK_GetState() == NETSTATE_SERVER`.

The same CVar **can** appear in both `OfflineOnly` and `OnlineOnly` blocks within the same parent block, and will take different values in each context (line 383). If a CVar appears in the parent block (unscoped) and also in a sub-block, precedence depends on the existing entry's scope and lock state and on the new one's:

- **Same scope:** the later entry replaces the earlier one. The exception is an unlocked entry arriving over a locked one: the new entry is discarded (line 395).
- **New entry unscoped, existing entry scoped:** the new entry replaces the old one. The exception is again unlocked over locked: the new entry is narrowed to the scope opposite the locked one, and both are kept (lines 392-393).
- **New entry scoped, existing entry unscoped:** the existing entry is narrowed to the scope opposite the new one, and both are kept (lines 404-406). Lock state does not matter here.
- **Opposite scopes (`OfflineOnly` vs `OnlineOnly`):** both are kept.

These rules are implemented in lines 376-413 and exist to handle the interaction between a Default block (which applies to all modes) and per-mode overrides in the same lump, plus cross-lump interactions. For hand-written `GAMEMODE` lumps, the simplest rule is: if you need different values for offline vs. online, put them in separate sub-blocks and don't also put the same CVar in the parent block.

## DefaultGameSettings and DefaultLockedGameSettings

A `GAMEMODE` lump can include top-level `DefaultGameSettings` and/or `DefaultLockedGameSettings` blocks, which apply their CVar assignments to **all** 16 game modes at once, rather than to a single named mode:

```text
DefaultGameSettings
{
    sv_respawntime = 30
}

Cooperative { ... }
Deathmatch { ... }
```

Only one of each Default block is allowed per lump (lines 435, 444); a second one causes a fatal `sc.ScriptError`. The first Default block of either kind parsed in a lump clears every mode's entire `GameplaySettings` list (lines 269-273), wiping out any settings that were set by earlier-loaded lumps. The "already parsed" tracking is per lump (lines 427-428), so this happens again in every later lump that has a Default block. Only the second Default block within the same lump (a `DefaultLockedGameSettings` after a `DefaultGameSettings`, or the reverse) skips the clearing. This means the order of blocks in a single lump is significant: a lump's first Default block, placed after a named mode block, wipes the settings that block just added, along with every setting from earlier-loaded lumps.

The wiki's phrase "will reset all the flags and their attributes back to zero" is imprecise: only the `GameplaySettings` list (CVars) is cleared, not `ulFlags` (the game mode flags like `COOPERATIVE`, `DEATHMATCH`, etc.), `Name`, `ShortName`, or other properties. Flags must be set separately via `AddFlag`/`RemoveFlag`.

## RemoveGameSetting

A `RemoveGameSetting` command within a mode block removes a prior CVar setting from that mode's list:

```text
Cooperative
{
    RemoveGameSetting sv_respawntime
}
```

If the CVar appears in the mode's `GameplaySettings` list, the first matching entry is deleted and the search stops (line 247-249). If the same CVar is present multiple times (e.g., once as `OfflineOnly` and once as `OnlineOnly`), only the first match is removed.

## Loading is cumulative, but modes are fixed slots

Every loaded archive is scanned for a `GAMEMODE` lump and each is parsed in turn (`Wads.FindLump` loop at line 424). A mode block for `Cooperative` in mod A and another `Cooperative` block in mod B do not create two separate modes — they both modify the same `g_GameModes[GAMEMODE_COOPERATIVE]` slot in place (array indexing at line 371). This is cumulative loading (multiple lumps extend a single mode), but different from `ANCRINFO`'s named-merge behavior or `MEDALDEF`'s name-lookup merge: mode names are not arbitrary identifiers, they are fixed enum slots.

## Type coercion for CVar values

The parser accepts string representations of numeric values and converts them per the CVar's own type (lines 333-362):

- **`CVAR_Bool` / `CVAR_Dummy`**: accepts literal `true`/`false` (case-insensitive) or a numeric string (zero is false, nonzero is true).
- **`CVAR_Float`**: parses the string via `atof()`.
- **`CVAR_Int` / anything else**: parses the string via `atoi()`.

## Wiki/engine divergence

Three differences between wiki and source implementation:

1. **Scope of DefaultGameSettings clearing.** Wiki: "loading another DefaultGameSettings or DefaultLockedGameSettings block in a subsequent GAMEMODE lump will reset all the flags and their attributes back to zero." Source: only `GameplaySettings` (CVars) are cleared; `ulFlags` (flags), `Name`, `ShortName`, `F1Texture`, and `WelcomeSound` are not touched. The wiki is right that a Default block in a later lump resets things again: the clearing runs at the first Default block of every lump, not once globally.

2. **Block position matters.** Wiki text emphasizes "at the beginning of the file" as a convention, but the source (lines 269, 269-273, and 438) makes position consequential: a `DefaultGameSettings` or `DefaultLockedGameSettings` block anywhere in a single lump will clear every mode's whole settings list if it's the first Default block in that file. A Default block after a named mode block in the same lump wipes that mode's settings parsed earlier in the same lump.

3. **Truncation is silent.** Wiki does not mention that `ShortName` and `F1Texture` are automatically truncated to 8 characters (lines 215, 223). A `ShortName "VeryLongName"` is silently shortened to `"VeryLong"` and stored; the parser does not warn or error.

## Engine-family divergence

UZDoom/GZDoom-family engines do not parse `GAMEMODE` and have no game mode attribute system of this shape to port it to.
