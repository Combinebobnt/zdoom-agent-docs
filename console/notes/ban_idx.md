# ban_idx

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/sv_ban.cpp` (`serverban_ExecuteBanCmd` 714-747, `SERVERBAN_BanPlayer` 498-508, `SERVERBAN_BanAddress` 512-561) and `src/c_dispatch.cpp:1017-1045` (`GetPlayerFromArg`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Bans a player by index for a required duration, with an optional reason. Syntax: `ban_idx <player index> <duration> [reason] [file index]`. With fewer than two arguments it only prints usage and the ban file indices.

The duration argument and all related semantics (time formats, permanent bans, file index selection) are identical to the `addban` command — see `addban.md` for the time-format grammar details. `ban_idx` identifies the target by player index (from `playerinfo`'s output) rather than IP address or player name; the command resolves the player's IP at execution time, bans that address through the same path as `addban`, and kicks the player with the reason as the kick message.

Differences from `addban`:

- It does nothing unless the game is running as a server. `addban` has no such check.
- A non-numeric index prints "That is not a valid player index."; a numeric index with no player in that slot does nothing, silently.
- Bots are refused ("Player <name> is a bot.").
- Like `addban`, it is silently ignored when run through ACS `ConsoleCommand()`.

Related: `ban` (by player name), `addban` (by IP address directly).

## Engine-family divergence

`ban_idx` is confirmed absent from UZDoom's source entirely — no `CCMD`/`CVAR` declaration and no
bare mention of the name anywhere in the tree. This isn't an undocumented feature; it's
dedicated-server IP-banning infrastructure that UZDoom's netcode has no equivalent surface for at
all. Invoking it under UZDoom from the console or a config file hits the console dispatcher's
command lookup, then its cvar-name fallback, and when neither matches prints
`Unknown command "ban_idx"` to console/log and does nothing else: a visible failure at the console,
but easy to miss if triggered from an unattended context like a server startup script or
`autoexec.cfg` line nobody is watching. Calling it through ACS's `ConsoleCommand()` never gets that
far: UZDoom's `ConsoleCommand` p-codes only print a "doesn't support execution of console commands
from scripts" error and discard their arguments, so nothing reaches the dispatcher.

As a result, UZDoom has no way to ban a connected player by `playerinfo` index — the index-to-IP
resolution this command performs never runs, so the only path this file documents is entirely
unavailable.
