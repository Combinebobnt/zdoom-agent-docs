# callvote

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/callvote.cpp` (vote type enums); corrections to vote types, flag syntax, thresholds and permissions verified against `src/callvote.cpp` (`CALLVOTE_TallyVotes` L1037, `callvote_CheckForFlooding` L1121, `callvote_CheckValidity` L1197, `callvote_GetVoteType` L1453, `callvote_IsFlagValid` L1524, cvar block L1560-1592, `CCMD( callvote )` L1594), `src/callvote.h` (vote enum L87-101, `VOTE_COUNTDOWN_TIME` L60) and `src/sv_main.cpp` (`server_CallVote` L7219).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Initiates a server vote. Syntax: `callvote <vote-type> [parameter] [reason]`

The vote type determines what is being voted on and which parameter (if any) is required. The reason is one console argument (quote it if it contains spaces) and is cut to 25 characters. For every vote type except `kick`/`forcespec`, the parameter may not contain a space or `;`. Each built-in type can be disabled by the server through `sv_forbidvoteflags` or its per-type `sv_no<type>vote` alias (see [sv_forbidvoteflags](sv_forbidvoteflags.md)); voting as a whole is controlled by [sv_nocallvote](sv_nocallvote.md). `listvotetypes` prints every type, including VOTEINFO-defined custom ones, and marks the forbidden ones.

## Vote types

| Vote Type | Parameter | Effect |
|---|---|---|
| `kick` | Player name | Vote to kick a player. On a pass the server runs `addban <ip> 10min`, a 10-minute ban. |
| `forcespec` | Player name | Vote to force a player to spectate. Rejected if the target is already a true spectator. |
| `map` | Map lump name | Vote to change to a specific map *without intermission screen*. The map must exist and, when the server's map rotation has any entries, must be in it. |
| `changemap` | Map lump name | Vote to change to a specific map *with intermission screen*. Same existence and rotation checks as `map`. |
| `nextmap` | (none) | Vote to advance to the next map (the rotation's next entry, or the current map's MAPINFO `nextmap`). Rejected if there is no next map. |
| `nextsecret` | (none) | Vote to jump to the current map's MAPINFO `nextsecret` map if it has one; otherwise behaves like `nextmap`. |
| `resetmap` | (none) | Vote to reset the current map to its initial state. Only allowed in game modes that support map resets. |
| `fraglimit` | Integer 0-255 | Vote to change the frag limit. |
| `timelimit` | Integer 0-65535 | Vote to change the time limit. |
| `winlimit` | Integer 0-255 | Vote to change the win limit. |
| `duellimit` | Integer 0-255 | Vote to change the duel limit. |
| `pointlimit` | Integer 0-65535 | Vote to change the point limit. |
| *DMFlag cvar name* | `true`/`false` or `1`/`0` | Vote to set a DMFlag to the given value. There is no `flag` keyword: the flag cvar's own name goes in the vote-type slot, e.g. `callvote sv_nomonsters true`. The value is explicit, not a toggle, and the vote is rejected if the flag already has that value. The cvar must be a flag of `dmflags`, `dmflags2` or `zadmflags`; compatibility flags and flags locked by the current game mode are rejected. Flag votes are forbidden by default (`sv_forbidvoteflags` defaults to the flag-vote bit). |

Vote-type names are matched case-insensitively.

## Voting as a client

Only a connected network client can call a vote (not the server console, not single player), and only while in a level (not during intermission). The server additionally refuses the call when `sv_nocallvote` is 1 (nobody may vote), when it is 2 and the caller is spectating, when fewer than `sv_minvoters` eligible voters are present (default 1), when that vote type is forbidden, or when another vote is already underway.

Once called, all clients are prompted to vote with `vote_yes`/`vote_no`, for up to 15 seconds. Eligible voters are all connected human clients, minus spectators when `sv_nocallvote` is 2; one vote counts per IP address. The vote ends early as soon as either side has more than half of the eligible voters. Otherwise, when the countdown runs out, it passes only if it has at least one yes vote and more yes than no votes. There is no configurable percentage threshold. The caller can cancel their own vote by voting no (or with `cancelvote`), and the vote is also cancelled if the caller disconnects.

## Permission model

The server checks every call (see above). `kick` and `forcespec` votes cannot target the caller themself, a player on the server's admin list, or a player logged into RCON: those players are protected from being voted out.

Flooding protection is `sv_votecooldown` (minutes, default 5; 0 disables it, as does `sv_limitcommands` being off): a caller must wait that long between any two votes and twice that long before calling the same vote type again, and a specific failed vote (same type and parameter, or the same kick target) can't be re-called by anyone for twice the cooldown. A kick vote that passed doesn't count against its caller's same-type wait. `sv_voteconnectwait` (seconds, default 0) makes newly connected clients wait before they can call a vote; it is skipped whenever the cooldown itself is disabled. See [sv_votecooldown](sv_votecooldown.md).

## Engine-family divergence

`callvote` is confirmed absent from UZDoom's source entirely — no `CCMD`/`CVAR` declaration and no
bare mention of the name anywhere in the tree. This isn't a documentation gap; UZDoom's netcode has
no client-side voting surface at all for a command like this to drive. Invoking it under UZDoom
from the console or a config file hits the console dispatcher's command lookup, then its cvar-name
fallback, and when neither matches prints `Unknown command "callvote"` to console/log and does
nothing else: a visible failure at the console, but easy to miss if triggered from an unattended
context like a server startup script or `autoexec.cfg` line nobody is watching. Calling it through
ACS's `ConsoleCommand()` never gets that far: UZDoom's `ConsoleCommand` p-codes only print a
"doesn't support execution of console commands from scripts" error and discard their arguments, so
nothing reaches the dispatcher.

As a result, UZDoom clients have no console-driven way to initiate any of the vote types this file
documents — kicking or force-spectating a player, changing or resetting the map, adjusting
frag/time/win/duel/point limits, or setting a DMFlag by vote — the entire vote-type table and
permission/threshold mechanism simply does not run.
