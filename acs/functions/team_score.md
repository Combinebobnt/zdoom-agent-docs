# `int Team_Score(int howmuch, int nogrin)`

**Tier:** A.
**Applies to:** N/A — zt-bcc-declared, neither engine implements it
**Verified against:** none
**Provenance:** wiki page `Team_Score - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://wiki.zandronum.com/w/index.php?title=Team_Score&oldid=1341`) + source-verified against the Zandronum source (`p_lnspec.cpp:2102-2121`,
`team.cpp:858-905`, `p_interaction.cpp:2813-2830`) and `zt-bcc/lib/zcommon.bcs:1499`. The wiki's
one-parameter usage and basic "gives the activator's team points" description hold; the
undocumented second parameter (dead), the always-`false` return, the dual team+player counter
update, the strict-AND gamemode-flag gate, the on-team-player-activator requirement, the
conditional announcer sound, the `pointlimit` win-condition side effect, and the netcode
replication are this doc's source-verified additions. `LS_Team_Score` is present verbatim in
`bc562a817` ("original Skulltag 0.97c2 source from Carnevil...", 2007-02-16) — the oldest commit
in this checkout's history for this function — so it necessarily predates the 3.2.1
version-string commit (`28f736fb3`) by many years; confirmed via `git merge-base
--is-ancestor bc562a817 28f736fb3`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special (positive index).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Gives the calling player's team (and the player personally) point-score, gated on the
current gamemode's team/point flags. Action special (`LS_Team_Score`, index 152 in
`zcommon.bcs`), implementation at the Zandronum source's `src/p_lnspec.cpp:2102-2121`, dispatching
to `TEAM_SetPointCount`/`PLAYER_SetPoints` in the Zandronum source's `src/team.cpp` and
the Zandronum source's `src/p_interaction.cpp`. See also `functions/changeteamscore.md` (the
`ACSF_ChangeTeamScore` extension function, a different, newer API into the same `SCORE_*`
subsystem) — this doc doesn't restate that one's enum/announce material.

```cpp
FUNC( LS_Team_Score )
// Team_Score (int howmuch, bool nogrin)
{
	// Scoring is not client side.
	if ( NETWORK_InClientMode() )
		return ( false );

	// [AK] Nothing to do if the current gamemode doesn't support teams and give points.
	if (( GAMEMODE_GetCurrentFlags() & ( GMF_PLAYERSONTEAMS | GMF_PLAYERSEARNPOINTS )) != ( GMF_PLAYERSONTEAMS | GMF_PLAYERSEARNPOINTS ))
		return ( false );

	// Make sure a valid player is doing the scoring.
	if ( !it || !it->player || it->player->bOnTeam == false )
		return ( false );

	TEAM_SetPointCount( it->player->Team, TEAM_GetPointCount( it->player->Team ) + arg0, true );
	PLAYER_SetPoints ( it->player, it->player->lPointCount + arg0 );

	return ( false );
}
```

- **The wiki only documents 1 of the special's 2 parameters.** `zcommon.bcs:1499` declares
  `Team_Score(int,int):int`, matching the engine comment `// Team_Score (int howmuch, bool
  nogrin)`, but the wiki page's "Usage"/"Parameters" section lists only `points` (`howmuch`) and
  says nothing about a second argument at all.
- **The second parameter is completely dead.** `arg1` ("`nogrin`") is never read anywhere in the
  function body — only `arg0` and the activator (`it`) are used. Whatever value is passed for
  the second argument has zero effect on behavior; there is no "grin"/announce suppression to
  control despite the parameter's name.
- **Always returns `false`, even on success.** Every code path — the two early-out gamemode/
  activator checks *and* the successful scoring path at the end — returns `false`. Because
  `zcommon.bcs` declares this with an `:int` result, `bcc` will compile `Team_Score(n)` used in
  an expression context (e.g. `if (Team_Score(10))`) to the result-producing line-special opcode
  (`PCD_LSPEC5RESULT`), which will push `0` onto the stack unconditionally — the return value
  cannot be used to detect success. (Called as a bare statement, the result is discarded anyway
  via the plain `PCD_LSPECn` opcodes, which is the overwhelmingly more common usage pattern in
  the Zandronum source's `src/p_acs.cpp`.)
- **Server-only.** The very first check bails out with no effect at all if
  `NETWORK_InClientMode()` — this special is a pure no-op on clients, not just "less reliable"
  as Zandronum netcode caveats elsewhere in this tree tend to phrase it.
- **Gamemode gate requires *both* flags simultaneously, not "any team gamemode."** The check is
  `(flags & (GMF_PLAYERSONTEAMS | GMF_PLAYERSEARNPOINTS)) != (GMF_PLAYERSONTEAMS |
  GMF_PLAYERSEARNPOINTS)` — a team-based gamemode that doesn't also earn *points* specifically
  (e.g. a frags-based or wins-based team mode) silently no-ops here, same as a non-team mode.
- **Requires a real, in-game, on-team player activator.** `it && it->player &&
  it->player->bOnTeam` all have to hold. A `NULL` activator (e.g. an `OPEN` script, or any
  context with no player activator) or a spectator activator makes this silently do nothing —
  same silent-`false` return as the gamemode-flag failure, indistinguishable from the outside.
- **Updates two separate counters, not one.** On success it calls both
  `TEAM_SetPointCount(team, oldTeamPoints + howmuch, true)` (the team's shared point pool) *and*
  `PLAYER_SetPoints(player, oldPlayerPoints + howmuch)` (that specific player's personal point
  stat) — a "team score" special that also mutates individual player state, which the wiki's
  one-line description doesn't hint at.
- **Announcement is hardcoded on, but conditional on the count actually rising.**
  `TEAM_SetPointCount`'s `doAnnouncement` is passed as the literal `true` here (no way to
  suppress it via this special's arguments, confirming the dead-`nogrin`-param finding above),
  but the "`<Team>Scores`" announcer sound still only plays if the new point count is strictly
  greater than the old one (`team.cpp:876`) — a `howmuch <= 0` call updates the counters silently.
- **Can end the game.** `TEAM_SetPointCount` checks the `pointlimit` cvar after every update
  (`team.cpp:898-905`; skipped entirely in client mode, which is moot here since this special
  never runs client-side anyway) and, if the team's new point count reaches it, prints the
  "has won the game!" server message and runs the win sequence — a real, non-obvious side effect
  of calling this special that the wiki page doesn't mention at all.
- **Server-authoritative replication on both counters.** `TEAM_SetPointCount` calls
  `SERVERCOMMANDS_SetTeamScore(team, TEAMSCORE_POINTS, doAnnouncement)` +
  `SERVERCONSOLE_UpdateScoreboard()`, and `PLAYER_SetPoints` separately calls
  `SERVERCOMMANDS_SetPlayerPoints(...)` + `SERVERCONSOLE_UpdatePlayerInfo(..., UDF_FRAGS)` +
  `SERVERCONSOLE_UpdateScoreboard()`, when `NETWORK_GetState() == NETSTATE_SERVER` — Zandronum
  netcode with no ZDoom-wiki equivalent (this is a Zandronum-only special to begin with).

**Returns:** `int`, but always `0`/`false` regardless of outcome (see above) — do not rely on the
return value to detect success or failure; check gamemode flags and activator state yourself if
that matters.

**Possible family:** This function, `ChangeTeamScore` (`functions/changeteamscore.md`), and
`Team_GivePoints` (index 153, processed concurrently by a sibling agent in this batch) are all
different entry points into the same team-scoring subsystem and may be worth consolidating into
a `families/team-scoring.md` at some point. Per this batch's instructions, this file was kept
standalone rather than folding into a family file — flagging the overlap here for the
coordinating session to consider.
