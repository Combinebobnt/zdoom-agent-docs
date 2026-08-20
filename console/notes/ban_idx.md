# ban_idx

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/sv_ban.cpp`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Bans a player by index with optional comment and duration. Syntax: `ban_idx <player index> <duration> [reason] [file index]`

The duration argument and all related semantics (time formats, permanent bans, file index selection) are identical to the `addban` command — see `addban.md` for the time-format grammar details. The only difference is that `ban_idx` identifies the target by player index (from `playerinfo`'s output) rather than IP address or player name; the command resolves the player's IP at execution time and bans that address.

Related: `ban` (by player name), `addban` (by IP address directly).

## Engine-family divergence

`ban_idx` is confirmed absent from UZDoom's source entirely — no `CCMD`/`CVAR` declaration and no
bare mention of the name anywhere in the tree. This isn't an undocumented feature; it's
dedicated-server IP-banning infrastructure that UZDoom's netcode has no equivalent surface for at
all. Invoking it under UZDoom — from the console, a config file, or ACS's `ConsoleCommand()` — hits
the console dispatcher's command lookup, then its cvar-name fallback, and when neither matches
prints `Unknown command "ban_idx"` to console/log and does nothing else: a visible failure at the
console, but easy to miss if triggered from an unattended context like a server startup script or
`autoexec.cfg` line nobody is watching.

As a result, UZDoom has no way to ban a connected player by `playerinfo` index — the index-to-IP
resolution this command performs never runs, so the only path this file documents is entirely
unavailable.
