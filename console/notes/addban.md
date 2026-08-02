# addban

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/sv_ban.cpp` and `docs/commands.txt` reference.

Bans a given IP address or IP range with optional comment. Syntax: `addban <IP address> <duration> [comment] [file index]`

## Time argument formats

The duration argument accepts a wide variety of time formats. All matching is case-insensitive and can appear anywhere in the duration string (e.g., `"5 hours"`, `5hours`, `5h`, all parse correctly). Supported units:

- **Permanent:** `perm` — sets ban to never expire.
- **Minutes:** `min`, `minute`, `minutes` — e.g., `30min`.
- **Hours:** `hour`, `hours`, `hr`, `hrs` — e.g., `2hours`.
- **Days:** `day`, `days`, `dy`, `dys` — e.g., `1day`.
- **Weeks:** `week`, `weeks`, `wk`, `wks` — e.g., `2weeks`.
- **Months:** `mon` — e.g., `6mon`.
- **Years:** `year`, `yr`, `decade` (humorously, with no special handling) — e.g., `1year`.

Examples from wiki: `"6days"`, `"1345years"`, `"6day"`, `"45 months"`.

## IP ranges and IPv4-only restriction

The command supports IP range bans using wildcard (`*`) notation, e.g., `addban 192.168.2.* 30min "Range ban"` bans an entire subnet. **IPv4 addresses only** — IPv6 is not supported. Any client or clients in a range ban cannot communicate with the server until whitelisted via `addbanexemption` or removed via `delban`/`reloadbans`.

## Related commands

- `ban`, `ban_idx` — equivalent to `addban` but identify target by player name or player index instead of IP; share the same time-format grammar.
- `delban` — remove a ban by IP address.
- `addbanexemption` — whitelist an IP to exempt it from a range ban.
- `viewbanlist` — list all active bans.
- `reloadbans` — reload ban lists from disk if modified externally.
- `sv_banfile` (cvar) — file(s) to load bans from; default `"banlist.txt"`.
- `sv_enforcebans` (cvar) — whether to enforce the ban list at all; default `true`.
