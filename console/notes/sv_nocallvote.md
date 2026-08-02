# `sv_nocallvote`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML.

Master control for whether any votes can be called on the server. This is distinct from `SV_ForbidVoteFlags`, which disables specific vote types; `sv_nocallvote` controls voting wholesale.

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Voting is enabled. Any eligible player can call votes. |
| 1 | No votes can be called whatsoever. The voting system is disabled server-wide. |
| 2 | Only players can call votes. Spectators are not allowed to call votes (though they may still vote on called votes, depending on other settings). |

Default is 0 (voting enabled).

## Relationship to other vote cvars

- **`sv_nocallvote 1`** — disables all votes, making the other voting cvars meaningless.
- **`sv_nocallvote 0` and `SV_ForbidVoteFlags`** — when voting is enabled, you can still disable specific vote types using `SV_ForbidVoteFlags` (or its individual aliases like `sv_nomapvote`, `sv_nokickvote`). This cvar is the master on/off; the forbid-flags are per-type filtering.

## Network and storage

Marked `CVAR_SERVERINFO`, so the setting is replicated to clients. Clients need to know whether voting is allowed before attempting to call a vote.

## Related cvars

- **`SV_ForbidVoteFlags`** — bitfield master cvar controlling which vote types are disabled (Kick, Map, ChangeMap, etc.). Works only when `sv_nocallvote` is 0.
- **`sv_minvoters`** — minimum number of players needed on server before any vote can be called.
- **`sv_votecooldown`** — cooldown time in minutes between votes.
- **`SV_VoteConnectWait`** — seconds a newly connected client must wait before being allowed to call votes.
