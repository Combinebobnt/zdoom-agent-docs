# map

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/g_level.cpp`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Changes the current map without displaying an intermission screen. Syntax: `map <map-lump-name>`

## Reconnection behavior: Server vs. Client

**On server:** All clients are forced to reconnect immediately, bypassing any intermission or countdown. The map change is instant.

**On client:** Cannot be used to change maps during a networked game (client quits the network and starts a new single-player game on the specified map instead). See `Send_Password` and RCon for remote server commands if you need a client to control the server.

## Map name format

Use the *lump name* (e.g., `MAP01`, `MAP23`, `E1M2`, `DIP07`), **not** the map's title from MAPINFO (e.g., do not use `"The Entryway"`). For specialized PWADs or custom map ranges, check the included `.txt` file — not all projects use the standard `MAPx` or `ExMy` format.

## Difference from changemap

Unlike `changemap`, `map` **does not** show an intermission screen; clients reconnect directly to the new level. The intermission (showing scores, frags, etc.) is skipped entirely. Use `map` for rapid map cycling; use `changemap` to give players a moment to see end-of-level results before the next map loads.

## Engine-family divergence: netgame handling

On UZDoom, `map` is gated on the same `netgame` flag that is true for both the hosting server and joined clients (false only in a genuine single-player session). Whenever `netgame` is set, the command refuses outright — it prints a message telling the user to use `changemap` instead and performs no map change at all, for host or client alike. This replaces the Zandronum behavior described above (server forces an instant reconnect for all clients; client quits the network session and starts a local single-player game): UZDoom's `map` is effectively single-player-only and cannot be used to change maps in any multiplayer session, on either side of the connection.

Outside of a netgame, UZDoom's `map` also accepts an optional second argument, `coop` or `dm`, which sets the deathmatch flag and marks the next game as multiplayer before loading — a syntax form not present in the format described above. A bare `*` as the map name reloads the current map. An invalid or missing map lump is reported with a "No map <name>" console message rather than starting the level.
