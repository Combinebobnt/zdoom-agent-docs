# changemap

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/c_cmds.cpp`.

Changes the current map while displaying an intermission screen. Syntax: `changemap <map-lump-name> [position]`

## Server-only command

`changemap` can only be executed on the server console or via RCon. Clients cannot use this command to control map changes (use RCon with correct password if needed).

## Intermission behavior

Clients are sent through the normal intermission screen (showing scores, fraglimit counters, etc.) before the new map loads. This is distinct from the `map` command, which skips intermission and reconnects immediately. Use `changemap` when you want players to see end-of-level statistics; use `map` for rapid cycling.

## Map name format

Use the *lump name* (e.g., `MAP01`, `MAP23`, `E1M2`, `DIP07`), **not** the map's title from MAPINFO (e.g., do not use `"The Entryway"`). For specialized PWADs or custom map ranges, check the included `.txt` file — not all projects use the standard `MAPx` or `ExMy` format.

## Optional position argument

The optional `[position]` argument (Zandronum only, not in ZDoom's `changemap`) allows positioning clients at a specific spawn point in the target map (rarely used in normal gameplay).

## Difference from map

`map` forces an immediate client reconnection with no intermission; `changemap` sends clients through intermission first. Both ultimately reconnect all clients when executed on the server.
