# addban

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/sv_ban.cpp` and `docs/commands.txt` reference.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Bans a given IP address or IP range with optional comment. Syntax: `addban <IP address> <duration> [comment] [file index]`

## Time argument formats

The duration is parsed by `SERVERBAN_ParseBanLength` (`src/sv_ban.cpp`). Only `perm` is compared case-insensitively, and it must be the whole argument. Every other unit is a case-sensitive substring search, so it must be lowercase: `"5 hours"` and `5hours` parse, `5Hours` and `5h` do not. The number must come first. Everything before the unit is read with `atoi`, so `"5 hours"` works but `"for 5 hours"` reads as 0. Text after the unit is ignored. Supported units, tried in this order:

- **Permanent:** `perm`. The ban never expires.
- **Minutes:** `min`, which also covers `minute`, `minutes`. E.g., `30min`.
- **Hours:** `hour`, `hours`, `hr`, `hrs`. E.g., `2hours`.
- **Days:** `day`, `days`, `dy`, `dys`. E.g., `1day`.
- **Weeks:** `week`, `weeks`, `wk`, `wks`. E.g., `2weeks`.
- **Months:** `mon`, which also covers `month`, `months`. Adds calendar months, not a fixed day count. E.g., `6mon`.
- **Years:** `year`, `yr` (and their plurals), or `decade`, which multiplies the number by 10 (`2decades` is 20 years). Adds calendar years. E.g., `1year`.

A zero, negative or unrecognized amount fails with `Error: couldn't read that length.` and no ban is added.

Examples from wiki: `"6days"`, `"1345years"`, `"6day"`, `"45 months"`.

## IP ranges and IPv4-only restriction

The command supports IP range bans using wildcard (`*`) notation, e.g., `addban 192.168.2.* 30min "Range ban"` bans an entire subnet. A `*` must stand for a whole octet. **IPv4 addresses only**; IPv6 is not supported. Bans are enforced only while `sv_enforcebans` is on; players already connected from a matching address are then kicked at once. The entry is appended to the ban file at `[file index]` (default 0, the first file in `sv_banfile`), so `reloadbans` does not remove it. A matching address stays banned until the ban expires, the exact entry is removed with `delban`, or the address is exempted with `addbanexemption`. Re-adding an address already in that file only updates its expiration and comment.

## Other behavior

- Called from ACS `ConsoleCommand()`, `addban` silently does nothing.
- With fewer than two arguments it prints its usage line and the list of ban file indices.
- An out-of-range file index prints `Error: file index is invalid.` and adds nothing.
- A bare IP never matches a player directly, because that lookup also compares the port. Only an `IP:port` argument equal to a connected client's address stores that player's name with the comment and kicks them with the comment as the reason, even with `sv_enforcebans` off. The port is dropped from the stored ban.
- Otherwise matching players are kicked by the general sweep with `IP is now banned - <comment>`.
- A partial wildcard octet such as `2*` is accepted but never matches anyone; only an octet that starts with `*` is a wildcard.

## Related commands

- `ban`, `ban_idx` — like `addban` but identify the target by player name or player index instead of IP, and share the same time-format grammar; unlike `addban` they work only on a server and refuse bots.
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
all. Invoking it under UZDoom from the console or a config file hits the console dispatcher's
command lookup, then its cvar-name fallback, and when neither matches prints
`Unknown command "addban"` to console/log and does nothing else: a visible failure at the console,
but easy to miss if triggered from an unattended context like a server startup script or
`autoexec.cfg` line nobody is watching. Calling it through ACS's `ConsoleCommand()` never gets that
far: UZDoom's `ConsoleCommand` p-codes only print a "doesn't support execution of console commands
from scripts" error and discard their arguments, so nothing reaches the dispatcher.

As a result, UZDoom has no way to ban an IP address or range by direct address — the entire
duration-grammar/range-wildcard/file-index mechanism this file documents simply does not run.
