# `int ChangeTeamScore(int team, int type, int value, bool announce = true)`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `ChangeTeamScore - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `https://wiki.zandronum.com/w/index.php?title=ChangeTeamScore&oldid=2242`) + source-verified against the Zandronum source
(`p_acs.cpp:8071-8125`, `team.cpp:868-891,1155-1240`, `team.h:115,143,146,149`) and
`zt-bcc/lib/zcommon.bcs:1228-1238,1784`. The wiki's parameter list, enum values 0-3, and return
convention all hold, but its first-parameter name (`player`), the frags-only negative-value
carve-out, the no-op-returns-0 ambiguity, the per-type announce gating, and the wider 9-member
shared `SCORE_*` enum are this doc's source-verified additions. `ChangeTeamScore` was added in
commit `65f04f8c2` ("Added ACS function: 'ChangeTeamScore'.", 2022-04-22), confirmed via
`git merge-base --is-ancestor` to be a direct ancestor of `28f736fb3` (the 3.2.1 version-string
commit) — it predates the 3.2.1 target and is safe to verify against it.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Sets one of a team's four score counters. Extension function (`ACSF_ChangeTeamScore`, index -154
in `zcommon.bcs`), implementation at the Zandronum source's `src/p_acs.cpp:8071-8125`, dispatching to
`TEAM_SetFragCount`/`TEAM_SetPointCount`/`TEAM_SetWinCount`/`TEAM_SetDeathCount` in
the Zandronum source's `src/team.cpp`.

```cpp
case ACSF_ChangeTeamScore:
{
	const ULONG ulTeam = static_cast<ULONG>( args[0] );
	const bool bAnnounce = argCount > 3 ? !!args[3] : true;

	// [AK] With the exception of frags, the new score must not be a negative value.
	const LONG lScore = ( args[1] == SCORE_FRAGS || args[2] >= 0 ) ? args[2] : 0;

	if ( TEAM_CheckIfValid( ulTeam ) )
	{
		switch ( args[1] )
		{
			case SCORE_FRAGS:
				if ( teams[ulTeam].lFragCount == lScore ) return 0;
				TEAM_SetFragCount( ulTeam, lScore, bAnnounce );
				return 1;
			case SCORE_POINTS:
				if ( teams[ulTeam].lPointCount == lScore ) return 0;
				TEAM_SetPointCount( ulTeam, lScore, bAnnounce );
				return 1;
			case SCORE_WINS:
				if ( teams[ulTeam].lWinCount == lScore ) return 0;
				TEAM_SetWinCount( ulTeam, lScore, bAnnounce );
				return 1;
			case SCORE_DEATHS:
				if ( teams[ulTeam].lDeathCount == lScore ) return 0;
				TEAM_SetDeathCount( ulTeam, lScore );
				return 1;
		}
	}
	return 0;
}
```

- **Wiki's first parameter name is wrong.** The wiki prose calls parameter 1 `player` ("The
  number of the team whose score to change") but it's a team index, matching the actual signature
  `int team`. Confirmed against `TEAM_CheckIfValid(ulTeam)` — this is a team-index API, not a
  player-index one.
- **`type` shares its enum with player-score functions, but only 4 of 9 values are handled here.**
  `zt-bcc/lib/zcommon.bcs`'s anonymous `SCORE_*` enum actually has nine members: `SCORE_FRAGS=0`,
  `SCORE_POINTS=1`, `SCORE_WINS=2`, `SCORE_DEATHS=3`, then `SCORE_KILLS`, `SCORE_ITEMS`,
  `SCORE_SECRETS`, `SCORE_SPREAD`, `SCORE_RANK` (used by `GetPlayerScore`/`SetPlayerScore`,
  `zcommon.bcs:1771-1772`). `ChangeTeamScore`'s `switch` only has cases for the first four — passing
  any of the other five (or any out-of-range int) matches no `case`, falls out of the `switch` with
  no side effect, and the function silently returns `0`. This is a real footgun since the wiki
  lists only the 4 values with no hint that the enum is shared and larger.
- **Value is clamped to non-negative except for `SCORE_FRAGS`.** `lScore` is computed as
  `args[2] >= 0 ? args[2] : 0` for every type *except* `SCORE_FRAGS`, which passes `args[2]`
  through unmodified — frags is the only counter this function will let you drive negative. The
  wiki page doesn't mention this asymmetry at all.
- **A no-op write (new value == current value) returns `0`, indistinguishable from failure.** Each
  `case` checks the relevant `teams[ulTeam].l*Count == lScore` *before* calling the `TEAM_Set*`
  helper and, if equal, returns `0` without calling it — same return value as an invalid team or
  unhandled `type`. The wiki's "Returns 1 if the team's score was successfully changed, 0 on
  failure" framing conflates "failed" with "already had that value"; you cannot distinguish the
  two from the return value alone.
- **`announce` is silently ignored for `SCORE_DEATHS`.** `TEAM_SetDeathCount(ULONG, LONG)`
  (`team.h:146`) takes no announce parameter at all — the 4th arg has no effect when
  `type == SCORE_DEATHS`, contradicting the wiki's blanket "whether to announce the change in
  frags, points, or wins" phrasing (which, read literally, already excludes deaths — but the
  wiki doesn't say the argument is simply dropped for that case).
- **Even when `announce` is honored, it doesn't unconditionally announce.** For `SCORE_POINTS`
  and `SCORE_WINS`, `TEAM_SetPointCount`/`TEAM_SetWinCount` only play the "`<Team>Scores`"
  announcer sound if the *new* count is strictly greater than the old one — passing
  `announce=true` while lowering a team's points/wins plays nothing. For `SCORE_FRAGS`,
  `TEAM_SetFragCount` gates its announcer sounds on `GAMEMODE_GetCurrentFlags() &
  GMF_PLAYERSEARNFRAGS` in addition to `bAnnounce` — in a non-frag gamemode the sound never plays
  regardless of the flag. None of this conditionality is documented on the wiki.
- **Server-authoritative side effects beyond the return value.** All four `TEAM_Set*` helpers also
  call `SERVERCOMMANDS_SetTeamScore(...)` and `SERVERCONSOLE_UpdateScoreboard()` when
  `NETWORK_GetState() == NETSTATE_SERVER`, replicating the change to clients and refreshing the
  server console scoreboard — real Zandronum netcode behavior with no ZDoom-wiki equivalent (the
  wiki doesn't mention networking at all, consistent with this being a Zandronum-only feature).

**Returns:** `int`/bool-like — `1` if the target counter was changed, `0` if `team` is invalid,
`type` isn't one of `SCORE_FRAGS`/`SCORE_POINTS`/`SCORE_WINS`/`SCORE_DEATHS`, or the requested
value already equals the current one.

## Engine-family divergence

`ChangeTeamScore` is bound as ACSF index 154 (`-154` in `zcommon.bcs`), squarely inside the
100–199 range UZDoom reserves for Zandronum's own extensions and implements none of — see
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md). Under UZDoom,
`CallFunction`'s dispatch switch has no `case` for this index, falls to `default: break;`, and
returns `0` with no error or log line; the interpreter rebalances the stack as if the call had
succeeded, so the script's execution simply continues.

Because this function is a mutator rather than a query, the practical effect is worse than a wrong
read: none of `TEAM_SetFragCount`/`TEAM_SetPointCount`/`TEAM_SetWinCount`/`TEAM_SetDeathCount` ever
runs under UZDoom, so the target team's counter is left completely untouched — no scoreboard
update, no server replication, no announcer sound. A script expecting the change to show up on the
scoreboard or feed a win-count check instead gets the same `0` this doc's body already documents
for a genuine no-op write (new value equals current value) or an invalid `team`/`type` on
Zandronum itself — so on UZDoom the call is indistinguishable, by return value alone, from either
of those legitimate Zandronum failure paths. A script that doesn't check the return value at all
will silently never see the score change take effect.
