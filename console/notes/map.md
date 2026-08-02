# map

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/g_level.cpp`.

Changes the current map without displaying an intermission screen. Syntax: `map <map-lump-name>`

## Reconnection behavior: Server vs. Client

**On server:** All clients are forced to reconnect immediately, bypassing any intermission or countdown. The map change is instant.

**On client:** Cannot be used to change maps during a networked game (client quits the network and starts a new single-player game on the specified map instead). See `Send_Password` and RCon for remote server commands if you need a client to control the server.

## Map name format

Use the *lump name* (e.g., `MAP01`, `MAP23`, `E1M2`, `DIP07`), **not** the map's title from MAPINFO (e.g., do not use `"The Entryway"`). For specialized PWADs or custom map ranges, check the included `.txt` file — not all projects use the standard `MAPx` or `ExMy` format.

## Difference from changemap

Unlike `changemap`, `map` **does not** show an intermission screen; clients reconnect directly to the new level. The intermission (showing scores, frags, etc.) is skipped entirely. Use `map` for rapid map cycling; use `changemap` to give players a moment to see end-of-level results before the next map loads.
