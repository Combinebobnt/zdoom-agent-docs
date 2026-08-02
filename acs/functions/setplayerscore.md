# `int SetPlayerScore(int player, int type, int value)`

Sets one of a player's seven score counters. Extension function (`ACSF_SetPlayerScore`, index
-138 in `zcommon.bcs`), implementation at the Zandronum source's `src/p_acs.cpp:7707-7790`,
dispatching to `PLAYER_SetFragcount`/`PLAYER_SetPoints`/`PLAYER_SetWins`/`PLAYER_SetDeaths`/
`PLAYER_SetKills`/direct field writes in the Zandronum source's `src/p_interaction.cpp`.

**Bucket:** extension function.

```cpp
case ACSF_SetPlayerScore:
{
	const ULONG ulPlayer = static_cast<ULONG> ( args[0] );
	// [AK] With the exception of frags, the new score must not be a negative value.
	const LONG lScore = ( args[1] == SCORE_FRAGS || args[2] >= 0 ) ? args[2] : 0;

	if ( PLAYER_IsValidPlayer( ulPlayer ) )
	{
		switch ( args[1] )
		{
			case SCORE_FRAGS:
				if ( players[ulPlayer].fragcount == lScore ) return 0;
				PLAYER_SetFragcount( &players[ulPlayer], lScore, true, true );
				return 1;
			case SCORE_POINTS:
				if ( players[ulPlayer].lPointCount == lScore ) return 0;
				PLAYER_SetPoints( &players[ulPlayer], lScore );
				return 1;
			case SCORE_WINS:
				if ( players[ulPlayer].ulWins == static_cast<ULONG>( lScore ) ) return 0;
				PLAYER_SetWins( &players[ulPlayer], lScore );
				return 1;
			case SCORE_DEATHS:
				if ( players[ulPlayer].ulDeathCount == static_cast<ULONG>( lScore ) ) return 0;
				PLAYER_SetDeaths( &players[ulPlayer], lScore );
				return 1;
			case SCORE_KILLS:
				if ( players[ulPlayer].killcount == lScore ) return 0;
				PLAYER_SetKills( &players[ulPlayer], lScore );
				return 1;
			case SCORE_ITEMS:
				if ( players[ulPlayer].itemcount == lScore ) return 0;
				players[ulPlayer].itemcount = lScore;
				return 1;
			case SCORE_SECRETS:
				if ( players[ulPlayer].secretcount == lScore ) return 0;
				players[ulPlayer].secretcount = lScore;
				return 1;
		}
	}
	return 0;
}
```

- **Unlike [`ChangeTeamScore`](changeteamscore.md), the wiki's enum coverage here is complete.**
  The shared anonymous `SCORE_*` enum (`zt-bcc/lib/zcommon.bcs:1229-1238`) has nine members, but
  the two not handled by this `switch` — `SCORE_SPREAD` and `SCORE_RANK` — are both
  *computed* read-only values (`PLAYER_CalcSpread`/`PLAYER_CalcRank`, only reachable through
  `GetPlayerScore`, `p_acs.cpp:7814-7817`), not settable counters. The wiki's 7-value list for
  `SetPlayerScore` (`SCORE_FRAGS`..`SCORE_SECRETS`) is exactly the 7 cases this `switch` handles —
  no gap, no footgun, unlike the team version. Passing `SCORE_SPREAD`/`SCORE_RANK`/anything
  out-of-range still falls out of the `switch` with no effect and returns `0`, for the same
  structural reason as `ChangeTeamScore`.
- **Value is clamped to non-negative except for `SCORE_FRAGS`** — identical asymmetry to
  `ChangeTeamScore`: `lScore` is `args[2] >= 0 ? args[2] : 0` for every type except `SCORE_FRAGS`,
  which passes `args[2]` through unmodified (frags is the only counter driveable negative). The
  wiki page doesn't mention this at all.
- **A no-op write (new value == current value) returns `0`, indistinguishable from failure.**
  Every `case` compares the requested value against the current field *before* writing and
  returns `0` without writing if they're equal — same return value as an invalid player or
  unhandled `type`. The wiki's "Returns 1 if success, 0 on failure (player doesn't exist or
  invalid type)" framing doesn't mention this third, silent case.
- **No `announce` parameter — unlike `ChangeTeamScore`, frags are always announced and always
  update team frags, with no way to suppress either from ACS.** The 3-arg signature here (matching
  the wiki) has no analog to `ChangeTeamScore`'s optional 4th `announce` bool. `SCORE_FRAGS` always
  calls `PLAYER_SetFragcount( &players[ulPlayer], lScore, /*bAnnounce=*/true, /*bUpdateTeamFrags=*/true )`
  hardcoded — meaning every `SetPlayerScore(p, SCORE_FRAGS, v)` call also attempts to update the
  player's team's frag total (`TEAM_SetFragCount` with the frag delta, `p_interaction.cpp:2194-2199`)
  if the player is on a team in a team-based frags gamemode. `PLAYER_SetFragcount`'s own internal
  gating (`GMF_PLAYERSEARNFRAGS`, non-teamplay, warm-up countdown skip) still applies — see that
  function's body at `p_interaction.cpp:2175-2216` — but there is no ACS-level knob to opt out of
  the announce sound or the team-frags side effect the way `ChangeTeamScore`'s 4th argument allows.
- **The other five setters (`POINTS`/`WINS`/`DEATHS`/`KILLS`, plus the two direct field writes for
  `ITEMS`/`SECRETS`) never play an announcer sound and take no `announce`-equivalent input at
  all** — `PLAYER_SetPoints`/`PLAYER_SetWins`/`PLAYER_SetKills`/`PLAYER_SetDeaths`
  (`p_interaction.cpp:2813-2887`) only set the field, call `HUD_ShouldRefreshBeforeRendering()`,
  and — server-side — call the matching `SERVERCOMMANDS_SetPlayer*` replication command plus
  `SERVERCONSOLE_UpdatePlayerInfo`/`UpdateScoreboard`. `SCORE_ITEMS`/`SCORE_SECRETS` skip even
  that: they write `players[ulPlayer].itemcount`/`secretcount` directly inline in `p_acs.cpp`
  with no wrapper function, so they get the HUD refresh and server replication for free (via the
  same `case` block) but bypass whatever a future `PLAYER_SetItemCount`-style helper might add.
- **Server-authoritative replication beyond the return value**, same pattern as
  `ChangeTeamScore`: every branch that succeeds also updates the server console scoreboard and
  pushes a `SERVERCOMMANDS_SetPlayer*` packet to clients when `NETWORK_GetState() == NETSTATE_SERVER`
  — real Zandronum netcode with no ZDoom-wiki equivalent (this is a Zandronum-only function to
  begin with, so the wiki doesn't discuss networking at all).

**Returns:** `int`/bool-like — `1` if the target counter was changed, `0` if `player` is not a
valid in-game player index, `type` isn't one of the seven settable `SCORE_*` values, or the
requested value already equals the current one.

**Provenance:** wiki page `SetPlayerScore - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=1337`) + source-verified against the Zandronum source
(`p_acs.cpp:7707-7822`, `p_interaction.cpp:2175-2216,2813-2887,3006-3014`) and
`zt-bcc/lib/zcommon.bcs:1229-1238,1771-1772`. The wiki's parameter list, all 7 enum values, and
the basic return convention hold as-is; the frags-only negative-value carve-out, the no-op-
returns-0 ambiguity, the hardcoded (non-optional) announce/team-frags behavior for
`SCORE_FRAGS`, and the per-type replication side effects are this doc's source-verified
additions, cross-referenced against the already-documented [`ChangeTeamScore`](changeteamscore.md)
(same `SCORE_*` enum, same no-op/negative-value patterns, different announce-parameter shape).
`SetPlayerScore` was added in commit `b9f6e508c` ("Added ACS functions: SetPlayerScore... and
GetPlayerScore...", 2020-11-29), confirmed via `git merge-base --is-ancestor` to be a direct
ancestor of `28f736fb3` (the 3.2.1 version-string commit, 2025-08-04) — it predates the 3.2.1
target and is safe to verify against it. **Engine:** Zandronum 3.2.1 (verified against
the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.

**Note:** `GetPlayerScore` is documented separately (processed concurrently in this same intake
batch) — see `functions/getplayerscore.md` if present. Both functions share the `SCORE_*` enum
and the `PLAYER_IsValidPlayer` gate; this file does not duplicate `GetPlayerScore`'s own
`SCORE_SPREAD`/`SCORE_RANK` read-only behavior beyond noting why they're absent here.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
