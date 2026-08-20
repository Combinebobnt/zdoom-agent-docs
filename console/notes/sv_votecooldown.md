# `sv_votecooldown`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02) for the previous-name note; Zandronum source `src/callvote.cpp` (CUSTOM_CVAR declaration and vote-cooldown enforcement), verified against vote-call throttling logic.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Cooldown time (in minutes) enforced between consecutive votes on the server. Prevents vote spam by forcing players to wait a minimum time interval between calling new votes.

## Cooldown behavior

When a vote completes (succeeds or fails):
- All players must wait at least `sv_votecooldown` minutes before any player can call another vote.
- If a player attempts to call a vote before the cooldown expires, the server rejects the vote and informs the player how many more minutes they must wait.
- If `sv_votecooldown` is 0, the cooldown is disabled and votes can be called consecutively with no delay.

Example:
- `sv_votecooldown 5` — after any vote completes, no player can call another vote for 5 minutes.
- `sv_votecooldown 0` — votes can be called immediately one after another.

## Precision

The cooldown is measured in whole minutes (integer values). Fractional minute values are accepted but are truncated/rounded by the cvar parser.

## Wiki note: Previous name

The Zandronum Wiki notes that this cvar was "Previously known as: SV_LimitNumVotes". This old name **no longer exists as an alias** in released Zandronum 3.2.1; it was renamed to `sv_votecooldown` at some point in development. Configuration files and scripts must use the current name `sv_votecooldown`.

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_SERVERINFO`, so the value persists to the config file and is replicated to clients.

## Related cvars and vote control

- **`sv_minvoters`** — minimum number of players required on the server before any vote can be called.
- **`sv_nocallvote`** — enables/disables voting entirely (0 = allowed, 1 = all disabled, 2 = players only).
- **`SV_VoteConnectWait`** — number of seconds a newly-connected client must wait before being allowed to call votes.
- **`SV_ForbidVoteFlags`** — bitfield master cvar controlling which vote types are disabled (e.g., `sv_nokickvote`, `sv_nomapvote`).

## Engine-family divergence

`sv_votecooldown` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. Attempting to set it under UZDoom (via the console, a config file, or ACS's `ConsoleCommand()`) prints `Unknown command "sv_votecooldown"` to console/log and the write silently fails to apply — a visible failure if someone is watching the console at the time, but easy to miss in an unattended context such as a server startup script or an `autoexec.cfg` line.

UZDoom has no server-side voting system to throttle in the first place, so the minutes-between-votes spam guard this cvar provides has no equivalent — there is nothing on that engine for it to rate-limit.
