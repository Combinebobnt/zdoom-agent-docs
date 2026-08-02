# `int GetPlayerScore(int player, int type)`

Reads one of a player's score counters. Extension function (`ACSF_GetPlayerScore`, index -139 in
`zcommon.bcs`), implementation at the Zandronum source's `src/p_acs.cpp:7792-7822`. Getter half of the
`GetPlayerScore`/`SetPlayerScore` pair (both added in the same commit); see
`functions/changeteamscore.md` for the analogous team-level `SCORE_*` API and a more detailed
writeup of the shared enum.

**Bucket:** extension function.

```cpp
case ACSF_GetPlayerScore:
{
	const ULONG ulPlayer = static_cast<ULONG> ( args[0] );

	if ( PLAYER_IsValidPlayer( ulPlayer ) )
	{
		switch ( args[1] )
		{
			case SCORE_FRAGS:   return players[ulPlayer].fragcount;
			case SCORE_POINTS:  return players[ulPlayer].lPointCount;
			case SCORE_WINS:    return players[ulPlayer].ulWins;
			case SCORE_DEATHS:  return players[ulPlayer].ulDeathCount;
			case SCORE_KILLS:   return players[ulPlayer].killcount;
			case SCORE_ITEMS:   return players[ulPlayer].itemcount;
			case SCORE_SECRETS: return players[ulPlayer].secretcount;
			case SCORE_SPREAD:  return PLAYER_CalcSpread( ulPlayer );
			case SCORE_RANK:    return PLAYER_CalcRank( ulPlayer );
		}
	}

	return 0;
}
```

- **`type` is the full 9-member `SCORE_*` enum, and this function handles all nine** —
  `SCORE_FRAGS=0`, `SCORE_POINTS=1`, `SCORE_WINS=2`, `SCORE_DEATHS=3`, `SCORE_KILLS=4`,
  `SCORE_ITEMS=5`, `SCORE_SECRETS=6`, `SCORE_SPREAD=7`, `SCORE_RANK=8`
  (`zt-bcc/lib/zcommon.bcs:1229-1239`). Unlike `ChangeTeamScore` (which only implements 4 of the 9
  shared values), `GetPlayerScore` has a `case` for every member — no silent-fallthrough footgun
  here. An out-of-range `type` still falls out of the `switch` with no case matched and returns
  `0` from the outer function, same as an invalid player.
- **`SCORE_SPREAD` and `SCORE_RANK` are computed, not stored fields**, and both depend on the
  active gamemode's scoring flags (`GAMEMODE_GetCurrentFlags()`), not always frags:
  - `PLAYER_CalcSpread` (`p_interaction.cpp:3658-3700`) picks whichever of
    `GMF_PLAYERSEARNWINS`/`GMF_PLAYERSEARNPOINTS`/`GMF_PLAYERSEARNFRAGS` is set (checked in that
    priority order — wins beats points beats frags if a gamemode somehow sets more than one),
    finds the highest score among all *other* players in-game who aren't true spectators, and
    returns `player's score - that highest score`. A negative result means trailing the leader by
    that amount; a positive result (possible only for the current leader) is the lead over the
    runner-up. If no other counted player exists (or none of the three flags is set), it returns
    `0` rather than erroring.
  - `PLAYER_CalcRank` (`p_interaction.cpp:3704-3723`) counts how many other non-spectator
    in-game players strictly exceed the target player's score on whichever single metric the
    gamemode flags select (same wins/points/frags priority as above). The result is **0-based**
    (rank `0` = first place, not `1`), and ties do not increment rank — two players tied for the
    lead both report rank `0`.
  - Both functions silently return `0` for a gamemode with none of the three `GMF_PLAYERSEARN*`
    flags set (e.g. a mode that doesn't track any of wins/points/frags) — indistinguishable from
    "tied for the lead" / "no spread from the leader". The wiki doesn't mention this
    gamemode-dependence at all, describing `SCORE_SPREAD`/`SCORE_RANK` only as generic "spread
    from the leading player" / "current rank".
- **Invalid player and "score is actually 0" are indistinguishable.** `PLAYER_IsValidPlayer(
  ulPlayer)` failing returns `0` from the outer function, the same value a legitimately
  zero-valued counter (or an out-of-range `type`) would produce. The wiki's "Returns the score of
  the player indicated by the player parameter" doesn't mention any failure case at all — there is
  no sentinel to detect an invalid call.
- **No side effects** — this is a pure read, unlike the `Set*`/`Change*` half of the pair (no
  netcode replication, no announcer sounds).

**Returns:** `int` — the requested counter's current value, or `0` if `player` is not a valid
in-game player index or `type` is outside the 9 recognized `SCORE_*` values.

**Provenance:** wiki page `GetPlayerScore - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=1350`) + source-verified against the Zandronum source
(`p_acs.cpp:7792-7822`, `p_interaction.cpp:3658-3723`) and `zt-bcc/lib/zcommon.bcs:1229-1239,1772`.
The wiki's parameter list, all 9 enum values, and basic return semantics hold as documented. This
doc's source-verified additions: the gamemode-flag dependence and priority order of
`SCORE_SPREAD`/`SCORE_RANK`, the 0-based/tie-insensitive rank convention, and the
invalid-player/zero-score return-value ambiguity — none of which the wiki mentions.
`GetPlayerScore` (with `SCORE_FRAGS` through `SCORE_SECRETS`) was added in commit `b9f6e508c`
(2020-11-29); `SCORE_SPREAD`/`SCORE_RANK` were added later in commit `a48b8b1aa` (2021-11-20, "Added
SCORE_SPREAD and SCORE_RANK to GetPlayerScore."). Both commits confirmed via
`git merge-base --is-ancestor` to be direct ancestors of `28f736fb3` (the 3.2.1 version-string
commit) — the full 9-value function predates the 3.2.1 target and is safe to verify against it.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
