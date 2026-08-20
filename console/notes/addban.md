# addban

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/sv_ban.cpp` and `docs/commands.txt` reference.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

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

## Engine-family divergence

`addban` is confirmed absent from UZDoom's source entirely — no `CCMD`/`CVAR` declaration and no
bare mention of the name anywhere in the tree. This isn't an undocumented feature; it's
dedicated-server IP-banning infrastructure that UZDoom's netcode has no equivalent surface for at
all. Invoking it under UZDoom — from the console, a config file, or ACS's `ConsoleCommand()` — hits
the console dispatcher's command lookup, then its cvar-name fallback, and when neither matches
prints `Unknown command "addban"` to console/log and does nothing else: a visible failure at the
console, but easy to miss if triggered from an unattended context like a server startup script or
`autoexec.cfg` line nobody is watching.

As a result, UZDoom has no way to ban an IP address or range by direct address — the entire
duration-grammar/range-wildcard/file-index mechanism this file documents simply does not run.
