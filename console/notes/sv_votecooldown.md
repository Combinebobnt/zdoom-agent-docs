# `sv_votecooldown`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02) for the previous-name note; Zandronum source `src/callvote.cpp` (CVAR declaration and vote-cooldown enforcement), verified against vote-call throttling logic; corrections to the cooldown rules, declaration, replication, precision, rename version and related cvars verified against `src/callvote.cpp` (`CALLVOTE_BeginVote` flood check L597 and vote record L641-654, `bPassed` set L394, cancelled-vote type reset L376/L822/L1013, `callvote_CheckForFlooding` L1121-1192, cvar block L1560-1590 with `sv_votecooldown` at L1589), `src/sv_main.h` (`MINUTE` L103), `src/sv_main.cpp` (`server_CallVote` `sv_minvoters` check L7261), `src/c_cvars.cpp` (`FBaseCVar::SetGenericRep` L187, SERVERINFO handling L291-350, `FBaseCVar::ToInt` L382) and `docs/zandronum-history.txt` (3.0 rename entry L631).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Vote flood protection, in minutes (default 5). It throttles how often each caller can call votes, and how soon a failed vote can be called again. It is not a single server-wide wait between votes.

## Cooldown behavior

The server records each vote at the moment it is called (not when it completes), keyed by the caller's IP address (port ignored). When a new vote is called, the server checks it against the records still younger than twice the cooldown and rejects it if any of these hold:

- The same caller called any vote less than `sv_votecooldown` minutes ago.
- The same caller called a vote of the same type less than twice `sv_votecooldown` minutes ago. A kick vote that passed does not count toward this rule.
- A vote of the same type with the same parameter (for `kick`/`forcespec`, the same target player) was called by anyone less than twice `sv_votecooldown` minutes ago and failed.

A rejected caller is told how many minutes remain, rounded up to a whole minute. A vote the caller cancelled (by voting no), or abandoned by disconnecting, or that was cancelled because its flag already had the voted value or its target player left, has its type cleared from the record. It still counts toward the caller's plain per-vote wait, but not toward the same-type or failed-vote rules.

If `sv_votecooldown` is 0, or `sv_limitcommands` is off, none of these checks run. The `sv_voteconnectwait` check is skipped too in that case, because it sits after the same early exit. The checks only run on a server.

Example:
- `sv_votecooldown 5`: a player who called a vote must wait 5 minutes before calling another, and 10 minutes before calling the same vote type again. A failed `map map30` vote can't be re-called by anyone for 10 minutes.
- `sv_votecooldown 0`: no flood checks, so votes can be called back to back (one at a time, since only one vote can run at once).

## Precision

It is an `Int` cvar, so the cooldown is whole minutes. A fractional value typed at the console is truncated when parsed (`2.5` becomes 2). There is no range clamp. A negative value makes every time comparison fail, so it also lets votes through, but unlike 0 it does not skip the `sv_voteconnectwait` check.

## Wiki note: Previous name

The Zandronum Wiki notes that this cvar was "Previously known as: SV_LimitNumVotes". Zandronum 3.0 renamed `sv_limitnumvotes` (a boolean on/off switch) to `sv_votecooldown` and made it an integer time. The old name **no longer exists as an alias**, in released Zandronum 3.2.1 or in the 3.3-alpha checkout read. Configuration files and scripts must use the current name `sv_votecooldown`.

## Network and storage

Declared with a plain `CVAR( Int, sv_votecooldown, 5, CVAR_ARCHIVE | CVAR_SERVERINFO )`, so the value persists to the config file. In Zandronum `CVAR_SERVERINFO` alone does not broadcast the value to ordinary clients (only `CVAR_MOD` server-info cvars are sent that way), and no packet carries it; clients never need it, since the checks are server-side. A change on the server is synced to RCON-connected admins, an RCON admin's client-side set is forwarded to the server, and a plain connected client cannot set it locally.

## Related cvars and vote control

- **`sv_minvoters`**: minimum number of eligible voters (connected human clients, minus spectators when `sv_nocallvote` is 2) needed before a vote can be called. Default 1.
- **`sv_nocallvote`**: enables/disables voting entirely (0 = allowed, 1 = all disabled, 2 = players only).
- **`sv_limitcommands`**: when off, disables this flood protection along with the other command rate limits.
- **`SV_VoteConnectWait`**: number of seconds a newly-connected client must wait before being allowed to call votes (default 0). Skipped when the cooldown is disabled.
- **`SV_ForbidVoteFlags`**: bitfield master cvar controlling which vote types are disabled (e.g., `sv_nokickvote`, `sv_nomapvote`).

See [callvote](callvote.md) for the vote flow as a whole.

## Engine-family divergence

`sv_votecooldown` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. Attempting to set it under UZDoom via the console or a config file prints `Unknown command "sv_votecooldown"` to console/log and the write silently fails to apply: a visible failure if someone is watching the console at the time, but easy to miss in an unattended context such as a server startup script or an `autoexec.cfg` line. ACS's `ConsoleCommand()` never reaches the console dispatcher on UZDoom; it only prints "UZDoom doesn't support execution of console commands from scripts" (`src/playsim/p_acs.cpp`) and does nothing else.

UZDoom has no server-side voting system to throttle in the first place, so the minutes-between-votes spam guard this cvar provides has no equivalent — there is nothing on that engine for it to rate-limit.
