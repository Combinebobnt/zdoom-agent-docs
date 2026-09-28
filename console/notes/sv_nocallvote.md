# `sv_nocallvote`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML; corrections to spectator voting, flags, replication and related cvars verified against `src/callvote.cpp` (declaration L1571, `CALLVOTE_VoteYes` L717, `CALLVOTE_VoteNo` spectator check L832, `CALLVOTE_CountNumEligibleVoters` L900, `CCMD ( listvotetypes )` L1734), `src/sv_main.cpp` (`SERVER_SettingChanged` L4751, `server_CallVote` L7219), `src/sv_commands.cpp` (`SERVERCOMMANDS_SetGameModeLimits` L2534) and `src/cl_main.cpp` (`client_SetGameModeLimits` L6189).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Master control for whether any votes can be called on the server. This is distinct from `SV_ForbidVoteFlags`, which disables specific vote types; `sv_nocallvote` controls voting wholesale.

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Voting is enabled. Any eligible player can call votes. |
| 1 | No votes can be called whatsoever. The server refuses every vote call with a "disabled voting" message. |
| 2 | Only players can call votes. Spectators can neither call a vote nor vote on one in progress (`vote_yes`/`vote_no` are refused with a message telling them to join the game), and they are not counted as eligible voters for `sv_minvoters` or the early-majority check that ends a vote. |

Default is 0 (voting enabled).

## Relationship to other vote cvars

- **`sv_nocallvote 1`** — disables all votes, making the other voting cvars meaningless.
- **`sv_nocallvote 0` or `2`, and `SV_ForbidVoteFlags`** — when voting is enabled (for everyone, or for players only), you can still disable specific vote types using `SV_ForbidVoteFlags` (or its individual aliases like `sv_nomapvote`, `sv_nokickvote`). This cvar is the master on/off; the forbid-flags are per-type filtering.

## Network and storage

Declared `CVAR_ARCHIVE | CVAR_SERVERINFO`. When it changes on a server, the server announces the new value and resends its game-mode limits packet, which carries `sv_nocallvote` and which clients force-set locally. Clients use the value for `listvotetypes`, which marks every vote type forbidden when it is 1, or when it is 2 and the client is spectating. The actual refusal of a vote call is done server-side.

## Related cvars

- **`SV_ForbidVoteFlags`** — bitfield master cvar controlling which vote types are disabled (Kick, Map, ChangeMap, etc.). Has no effect when `sv_nocallvote` is 1.
- **`sv_minvoters`** — minimum number of eligible voters (connected human clients, minus spectators when `sv_nocallvote` is 2) needed before a vote can be called. Default 1.
- **`sv_votecooldown`** — per-caller cooldown in minutes between votes (default 5). See [callvote](callvote.md) for the full flood rules.
- **`SV_VoteConnectWait`** — seconds a newly connected client must wait before being allowed to call votes.

## Engine-family divergence

`sv_nocallvote` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. Attempting to set it under UZDoom via the console or a config file prints `Unknown command "sv_nocallvote"` to console/log and the write silently fails to apply: a visible failure if someone is watching the console at the time, but easy to miss in an unattended context such as a server startup script or an `autoexec.cfg` line. ACS's `ConsoleCommand()` never reaches the console dispatcher on UZDoom; it only prints "UZDoom doesn't support execution of console commands from scripts" (`src/playsim/p_acs.cpp`) and does nothing else.

UZDoom's networking model has no server-side voting system at all, so the master on/off (and players-only) gate this cvar provides over vote-calling has nothing to control on that engine — the entire feature it governs is simply absent, not merely unconfigurable.
