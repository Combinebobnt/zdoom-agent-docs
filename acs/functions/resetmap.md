# ResetMap

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-07)
**Provenance:** Zandronum Wiki `ResetMap` (retrieved 2026-08-07, https://wiki.zandronum.com/w/index.php?title=ResetMap&oldid=2479); verified against Zandronum engine source's `src/p_acs.cpp:7136-7146` (extension function `ACSF_ResetMap`), `src/g_game.cpp:4299-4302` (`GAME_RequestMapReset`), and `src/g_game.cpp:3346-4247` (`GAME_ResetMap` and actor-reset logic). Introducing commit `20fa4539f` (2012-04-04) confirmed as ancestor of the 3.2.1 version-bump commit (`28f736fb3`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

```text
bool ResetMap(void)
```

## Description

Requests a map reset — restores the map to its initial state. The reset flag is queued immediately (the function returns at once), but the actual reset executes at a specific point during the end-of-tic update loop. Any commands placed immediately after this function call execute before the map actually resets.

The reset clears all decals, unloads and restarts all ACS scripts (including the calling script itself), respawns all actors and world objects to their map-spawned state, restores all sector/line specials and textures, resets all polyobject state, and resets player inventory/state. On single-player and non-multiplayer instances (before entering client mode), all HUD messages are explicitly cleared before the reset proceeds via `StatusBar->DetachAllMessages()`. The actual player respawning (position, health, inventory) is not part of `GAME_ResetMap` itself but handled by a separate call to `GAMEMODE_RespawnAllPlayers` immediately afterward.

## Requirements

The map reset only succeeds if the current gamemode has the `MAPRESETS` flag enabled. The wiki states this flag is set by default in Survival, (T)LMS, Invasion, and Duel gamemodes, but this cannot be verified from the engine source alone — the flags are configured in external gamemode definition files rather than hardcoded. For custom gamemodes, the flag can be explicitly enabled via the `GAMEMODE` lump:

```text
Cooperative 
{
    addflag MAPRESETS
    addflag MAPRESET_RESETS_MAPTIME // Optional
}
```

The optional `MAPRESET_RESETS_MAPTIME` flag causes the reset to additionally reset the level time (retrieved via `Timer()`) to 0. Without this flag, the level time persists across the reset.

## Return value

Returns `true` (1) if the map reset was successfully requested. Returns `false` (0) if the current gamemode does not have the `MAPRESETS` flag enabled. On failure, a message is printed via `Printf()` (plain console output, not specifically restricted to server console on multiplayer): `"ResetMap can only be used in game modes that support map resets."`

**Wiki vs. source divergence:** The Zandronum Wiki states "prints a message to the server console", but the actual engine calls plain `Printf()`, which reaches all visible consoles, not only server-side.

## Calling script termination

Because `GAME_ResetScripts` unloads all ACS modules and destroys all running scripts during the reset process, **the script that calls `ResetMap()` is terminated by the reset itself**. Commands written after the call are executed first (since the reset is deferred to the end-of-tic), and the script instance does not resume afterward.

## Inventory handling

Player inventory is handled in two ways during reset:

- **Map-spawned items in player inventory:** Respawned at their original map locations but remain in the player's inventory. The item instance is destroyed and a fresh spawn is created, then added back to the same player's inventory slot.
- **Non-map-spawned items:** Destroyed without replacement (any items added via ACS/gameplay are lost).

Player actors themselves are **not** respawned or repositioned by `GAME_ResetMap` — they remain in place. Full player state restoration (health, armor, weapons, position) is handled by the separate `GAMEMODE_RespawnAllPlayers` call that follows the reset.

## Client-side behavior

On a client that is not connected to a server (single-player, non-client mode), `ResetMap()` executes locally on the client's own instance. There is no explicit guard preventing a `CLIENTSIDE` script from calling `ResetMap()`, which could theoretically cause the client to reset its own map independently of server state — a potential desync scenario in networked play. In typical multiplayer, the server calls `SERVERCOMMANDS_ResetMap()` to synchronize the reset across all clients.

## Compatibility flags

This function interacts with the `compat_resetglobalvarsonmapreset` compatibility flag. When enabled, all world-scope and global-scope ACS variables and arrays are reset to their initial values when the map resets (via `P_ClearACSVars(true)` inside `GAME_ResetScripts`). Without this flag, ACS variables persist across the reset.

## Examples

```text
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

## Engine-family divergence

`ResetMap` is bound as ACSF (CALLFUNC) index 100 — inside the 100–199 range UZDoom's own ACSF enum reserves for Zandronum's extensions and implements none of. A Zandronum-compiled object calling `ResetMap()` under UZDoom hits UZDoom's `default: break;` case in its `CallFunction` dispatcher and gets `0` back, silently — no error, no log line, and critically none of the `Printf()` failure message the Return value section above documents for the real (Zandronum) failure path.

The practical effect is that every side effect this file documents simply doesn't happen: no decal clear, no ACS module unload/script restart, no actor/polyobject/sector-special reset, no inventory handling, and no follow-up `GAMEMODE_RespawnAllPlayers`. Because the calling script isn't terminated either (per "Calling script termination" above — there's no real reset to destroy it), execution falls through to whatever comes after the call instead of stopping there, so code written assuming it's unreachable (as in the Examples section) actually runs. A script that checks the return value for success/failure reads this identically to the documented "gamemode lacks `MAPRESETS`" failure case, but with no console message at all — there is no way, from ACS alone, to distinguish "this build doesn't support `ResetMap`" from "this gamemode doesn't support map resets" under UZDoom.

See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general reserved-ACSF-range mechanism this is an instance of.
