# Autosave and quicksave/quickload triggers

**Tier:** B — reverse-engineered directly from UZDoom engine source; no ZDoom Wiki page traces the
autosave call graph at this level of detail.
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** Verified against the UZDoom source's `src/g_game.cpp`, `src/g_level.cpp`,
`src/d_net.cpp`, `src/playsim/p_lnspec.cpp`, `wadsrc/static/zscript/doombase.zs`, and
`src/menu/doommenu.cpp`.

Three distinct triggers can cause an autosave, and (separately) four UI-only triggers cause a
manual save/load. All autosave triggers converge on the exact same save-writing code path as a
manual save, so custom object-field data (see [Custom data in
savegames](savegame-custom-data.md)) is captured identically no matter which one fired — only the
save's own filename and description differ, and neither is customizable by the caller on the
autosave path.

## The three autosave triggers

1. **`Level.MakeAutoSave()`** (`wadsrc/static/zscript/doombase.zs`) — declared with **no** scope
   qualifier, unlike the explicitly-`ui` `Level.GetAutomapPosition()` declared nearby in the
   same file — meaning it's callable from ordinary **play-scope** ZScript (an `Actor`'s own
   logic, a play-scope `EventHandler` override, etc.), not gated behind the `ui`-only
   [`SavegameManager`](../classes/savegamemanager.md) the way a manual save is. Calling it sets
   `gameaction = ga_autosave` directly; the actual save happens the next time the game loop
   processes pending actions.

2. **Linedef special `Autosave`, special #15** (`LS_Autosave` in `src/playsim/p_lnspec.cpp`) — a
   map-side trigger: a switch, walkover line, or any other mechanism that executes a line special,
   including `Level.ExecuteSpecial()` from play-scope ZScript or ACS. Rather than saving
   immediately, it requests an autosave-check over the net-command stream
   (`DEM_CHECKAUTOSAVE`) — the actual decision to save (and the save itself) happens on the
   network-command-processing side, same as trigger 3 below.

3. **The automatic `DAutosaver` thinker** — requested by the engine's own level-transition path,
   `G_DoWorldDone()` (`src/g_level.cpp`), whenever a map finishes and the engine loads the next one
   in sequence. There is no per-map opt-out flag: `G_DoWorldDone()` unconditionally asks for one on
   every level transition, and the actual decision is made downstream by `G_DoLoadLevel()`'s own
   gating (the `disableautosave` cvar at 1 or higher, or the transition being a savegame restore
   rather than ordinary progress, both suppress it). No player action or script call is needed at
   all; this is what produces an autosave on ordinary level-to-level progress without any mod
   involvement.

Both trigger 2 and the `DAutosaver` thinker route through the same `DEM_CHECKAUTOSAVE` /
`DEM_DOAUTOSAVE` net-command pair (`src/d_net.cpp`), which applies the actual gating (never in a
netgame, never during demo playback, respects `disableautosave`/`autosavecount`, and requires the
local player to be alive and not playing a deathmatch game) before finally setting `gameaction =
ga_autosave` — the same flag trigger 1 sets directly.

## The unified save path

Regardless of which of the three triggers set `gameaction = ga_autosave`, the game loop then calls
`G_DoAutoSave()`, which calls `G_DoSaveGame()` — **the exact same function a manual save
(`SavegameManager.DoSave()`, `quicksave`, or the `save` console command) calls.**
`G_DoSaveGame()` calls `level.SnapshotLevel()`, which serializes linedefs/sectors, the
per-level event-handler chain, and every thinker (hence every custom field on every `Actor`/
`Thinker`/non-static `EventHandler`, via the mechanism in [Custom data in
savegames](savegame-custom-data.md)) — identically to a manual save. There is no reduced or
"lightweight" autosave payload.

## What differs: hardcoded, non-parameterized metadata

`G_DoAutoSave()` itself builds the save's description string as a fixed `"Autosave " + <local
timestamp>` and picks the filename from a rotating `auto00`..`autoNN` slot pool sized by the
`autosavecount` cvar. **None of the three triggers above take a description or filename
parameter** — unlike a manual save's `SavegameManager.DoSave(index, name)`, where the caller
supplies the title directly. A mod that wants a custom-labeled checkpoint save (e.g. "Boss room
entrance") cannot get one through any of the three autosave triggers; it would have to reach the
ui-scope `SavegameManager.DoSave()` from ui-scope code instead, which is a materially different
call path (see [`SavegameManager`](../classes/savegamemanager.md)).

## Manual save/load triggers, for contrast

These are the only paths that end up at `SavegameManager`/`G_SaveGame`/`G_LoadGame` outside the
autosave mechanism above, and — unlike the autosave triggers — none of them are reachable from
play-scope ZScript or ACS at all:

1. Main menu's Load Game / Save Game entries → `SavegameManager.LoadSavegame()`/`DoSave()`.
2. F2/F3 default keybinds → `menu_save`/`menu_load` console commands (`src/menu/doommenu.cpp`) →
   open those same menus.
3. F6 default keybind → `quicksave` console command → either `G_DoQuickSave()` (if quicksave
   rotation is enabled) or `G_SaveGame()` directly on the remembered `quickSaveSlot`.
4. F9 default keybind → `quickload` console command → `G_LoadGame()` on the remembered
   `quickSaveSlot`.
5. Direct console commands `save <file> [description]` / `load <file>` (`src/console/c_cmds.cpp`)
   → `G_SaveGame`/`G_LoadGame` directly. Both are declared `UNSAFE_CCMD`, but that gates execution
   from untrusted/scripted contexts in general (a config-file `exec` chain, a bound alias, certain
   menu-item commands — the same mechanism also covers unrelated commands like `exec`,
   `screenshot`, and `writeini`), not netgame status specifically. The netgame restriction on
   saving/loading is a separate check, and it's asymmetric between the two commands: `load`'s own
   command body refuses outright whenever a netgame is active, while `save` has no such check
   itself — it defers to `G_SaveGame()`, which only blocks players who aren't the settings
   controller, and only while the `net_limitsaves` cvar (on by default) is set, so the settings
   controller can still save mid-netgame. Console commands are (like everything console-command-
   shaped) unreachable from ACS regardless, since this engine disables ACS's console-command
   execution entirely (`PCD_CONSOLECOMMAND`/`PCD_CONSOLECOMMANDDIRECT` just print a warning and
   no-op — `src/playsim/p_acs.cpp`).
