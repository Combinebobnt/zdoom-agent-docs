# ban_idx

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/sv_ban.cpp`.

Bans a player by index with optional comment and duration. Syntax: `ban_idx <player index> <duration> [reason] [file index]`

The duration argument and all related semantics (time formats, permanent bans, file index selection) are identical to the `addban` command — see `addban.md` for the time-format grammar details. The only difference is that `ban_idx` identifies the target by player index (from `playerinfo`'s output) rather than IP address or player name; the command resolves the player's IP at execution time and bans that address.

Related: `ban` (by player name), `addban` (by IP address directly).
