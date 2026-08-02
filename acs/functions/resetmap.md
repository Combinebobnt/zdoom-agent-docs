# ResetMap

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki; verified against Zandronum engine source (`p_acs.cpp` case `ACSF_ResetMap:`, `g_game.cpp:GAME_RequestMapReset`, and `g_game.cpp:GAME_ResetMap` function, present in the ancestry of version tag `ZA_3.2.1`).

```
bool ResetMap(void)
```

## Description

Requests a map reset — restores the map to its initial state. The reset flag is queued immediately (the function returns at once), but the actual reset executes at a specific point during the end-of-tic update loop after all script execution and damage calculations complete. Any commands placed immediately after this function call execute before the map actually resets.

The reset clears all decals, unloads and restarts all ACS scripts (including the calling script itself), resets all actors and objects to their map-spawned state, restores all sector/line specials and textures, resets all polyobject state, and respawns all players. On the client side (non-server, non-clientmode), all HUD messages are cleared via `StatusBar->DetachAllMessages()`.

## Requirements

The map reset only succeeds if the current gamemode has the `MAPRESETS` flag enabled. The wiki states this flag is set by default in Survival, (T)LMS, Invasion, and Duel gamemodes, but this cannot be verified from the engine source alone — the flags are configured in external gamemode definition files rather than hardcoded. For custom gamemodes, the flag can be explicitly enabled via the `GAMEMODE` lump:

```
Cooperative 
{
    addflag MAPRESETS
    addflag MAPRESET_RESETS_MAPTIME // Optional
}
```

The optional `MAPRESET_RESETS_MAPTIME` flag causes the reset to additionally reset the level time (retrieved via `Timer()`) to 0. Without this flag, the level time persists across the reset.

## Return value

Returns `true` (1) if the map reset was successfully requested. Returns `false` (0) if the current gamemode does not have the `MAPRESETS` flag enabled. On failure, a message is printed to the console (not specifically restricted to the server console): `"ResetMap can only be used in game modes that support map resets."`

## Calling script termination

Because `GAME_ResetMap` unloads all ACS modules and destroys all running scripts, **the script that calls `ResetMap()` is terminated by the reset itself**. Commands written after the call are executed first (since the reset is deferred to the end-of-tic), and the script instance does not resume afterward.

## Compatibility flags

This function interacts with the `compat_resetglobalvarsonmapreset` compatibility flag. When enabled, all world-scope and global-scope ACS variables and arrays are reset to their initial values when the map resets (via `P_ClearACSVars(true)` inside `GAME_ResetScripts`). Without this flag, ACS variables persist across the reset.

## Examples

```
script 5 DEATH
{
    PrintBold(s: "You've died! Restarting map.");
    Delay(90);
    ResetMap();
    // This line and all subsequent lines in this script are unreachable
    // because ResetMap() destroys all scripts during the reset.
}
```

## See also

- `Timer` — retrieve the current level time (reset if `MAPRESET_RESETS_MAPTIME` flag is set)
- `GAMEMODE` lump documentation for flag syntax
