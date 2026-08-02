# callvote

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/callvote.cpp` (vote type enums).

Initiates a server vote. Syntax: `callvote <vote-type> [parameter] [reason]`

The vote type determines what is being voted on and which parameter (if any) is required. All vote types must have voting enabled on the server; see `sv_callvoteminimumvotes` and related cvars for permission/threshold settings.

## Vote types

| Vote Type | Parameter | Effect |
|---|---|---|
| Kick | Player name | Vote to kick a player from the server. |
| ForceSpec | Player name | Vote to force a player to spectate. |
| Map | Map lump name | Vote to change to a specific map *without intermission screen*; only maps in the server's rotation are available. |
| ChangeMap | Map lump name | Vote to change to a specific map *with intermission screen*; only maps in the server's rotation are available. |
| NextMap | (none) | Vote to advance to the next map in rotation (or to the map specified in current map's MAPINFO `nextmap`). |
| NextSecret | (none) | Vote to jump to the secret map if the current map has `nextsecret` defined in MAPINFO; otherwise behaves like `NextMap`. |
| ResetMap | (none) | Vote to reset the current map to its initial state. |
| FragLimit | Integer | Vote to change the frag limit to the given integer value. |
| TimeLimit | Integer | Vote to change the time limit to the given integer value. |
| WinLimit | Integer | Vote to change the win limit to the given integer value. |
| DuelLimit | Integer | Vote to change the duel limit to the given integer value. |
| PointLimit | Integer | Vote to change the point limit to the given integer value. |
| Flag | DMFlag cvar name | Vote to toggle a DMFlag on or off; the parameter is the exact name of the DMFlag cvar (e.g., `sv_nomonsters`), not a display name. The flag is toggled (current value is inverted). |

## Voting as a client

Only clients in an active level (not during intermission, pre-match, etc.) can call votes. The server must have voting enabled (`sv_callvote` = true, default). If a vote is called successfully, all clients are prompted to vote Yes or No; the result is determined by server-configured thresholds (`sv_callvoteminimumvotes`, `sv_callvoteminimumpercentage`, etc.).

## Permission model

Calling a vote is subject to server-side permission checking. RCon-authenticated clients may have additional permissions. Flooding protection exists to prevent rapid successive vote calls by the same client.
