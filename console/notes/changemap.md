# changemap

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/c_cmds.cpp`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

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

## Engine-family divergence: permission model

UZDoom has no separate server console/RCon concept for `changemap`. Instead, whenever `netgame` is true, it checks a per-player "settings controller" flag — held by the game's arbitrator/host by default, but transferable to another player during the session — and refuses with a "only setting controllers can change the map" message if the invoking player doesn't hold it. Any player who does hold it can run `changemap` from their own client console; there's no restriction to a distinct server process the way Zandronum's client/server check enforces. Outside of a netgame entirely (a genuine single-player session), UZDoom drops the permission check altogether and the local player can use it freely. This replaces this doc's "Server-only command" section for UZDoom: rather than "only the server console or RCon," it's "only the current settings controller, and only when networked."

Contrary to this doc's "Optional position argument (Zandronum only, not in ZDoom's changemap)" claim, UZDoom's `changemap` *does* accept the same optional `[position]` argument, applied with equivalent effect (positions the client at the given spot in the target map).

UZDoom's `changemap` also accepts map-name shortcuts not present in the Zandronum implementation described above: `*` re-targets the current map, `+` targets the map defined as the current map's next map (MAPINFO `nextmap`), and `+$` targets its secret map (MAPINFO `nextsecret`), each in place of a literal map lump name.
