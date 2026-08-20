# `int Team_GivePoints(int team, int howMuch, bool announce)`

**Tier:** A.
**Applies to:** N/A — zt-bcc-declared, neither engine implements it
**Verified against:** none
**Provenance:** wiki page `Team_GivePoints - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `https://wiki.zandronum.com/w/index.php?title=Team_GivePoints&oldid=1343`) + source-verified against the Zandronum source
(`p_lnspec.cpp:2123-2143`, `p_lnspec.h:49`, `team.cpp:868-891`, `announcer.cpp:217-241`,
`cl_main.cpp:6558-6587`, `wadsrc/static/teaminfo.txt`) and
`zt-bcc/lib/zcommon.bcs:1500,808-811`. The wiki's signature, parameter count, and default
0-3 team/color mapping all hold; its unqualified "displays a message to all players" claim for
`announce` does not (sound only, verified against `ANNOUNCER_PlayEntry` — no text/chat output
exists in this path), and the always-`false` return value, gamemode-flag gate, per-player side
effect, strict-increase-only announce gating, and data-driven (not hardcoded) team/color mapping
are this doc's source-verified additions. `Team_GivePoints` is present in the original imported
Skulltag 0.97c2 source (`bc562a817`) and was later fixed for broader gamemode compatibility by
`52569e7d6` ("Fixed Team_Score and Team_GivePoints not working properly on all gamemodes that
support teams and give points."); both commits confirmed via `git merge-base --is-ancestor` to
be ancestors of `28f736fb3` (the 3.2.1 version-string commit), so this long predates the 3.2.1
target and is safe to verify against it.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Adds `howMuch` to one team's point counter directly (not tied to any activator/player). Action
special (`LS_Team_GivePoints`, index 153 in `zt-bcc/lib/zcommon.bcs` and `p_lnspec.h`),
implementation at the Zandronum source's `src/p_lnspec.cpp:2123-2143`, delegating to
`TEAM_SetPointCount`/`TEAM_GetPointCount` in the Zandronum source's `src/team.cpp`. See
[ChangeTeamScore](changeteamscore.md) for the related extension-function API that can *set* (not
just add to) any of a team's four score counters — the two are separate code paths (action
special vs. `ACSF_*` extension function) that happen to overlap on "points."

```cpp
FUNC( LS_Team_GivePoints )
// Team_GivePoints( int iTeam, int iHowMuch, bool bAnnounce )
{
	// Scoring is not client side.
	if ( NETWORK_InClientMode() )
		return ( false );

	// [AK] Nothing to do if the current gamemode doesn't support teams and give points.
	if (( GAMEMODE_GetCurrentFlags() & ( GMF_PLAYERSONTEAMS | GMF_PLAYERSEARNPOINTS )) != ( GMF_PLAYERSONTEAMS | GMF_PLAYERSEARNPOINTS ))
		return ( false );

	// Make sure this is a valid team.
	if ( TEAM_CheckIfValid( arg0 ) == false )
		return ( false );

	// Give the point(s) to the team.
	TEAM_SetPointCount( arg0, TEAM_GetPointCount( arg0 ) + arg1, !!arg2 );

	if ( it && it->player && it->player->bOnTeam )
	{
		PLAYER_SetPoints ( it->player, it->player->lPointCount + arg1 );
	}

	return ( false );
}
```

- **Always returns `false`.** Despite the `:int` return type in `zcommon.bcs` (ACS specials
  return `bool`-as-int by convention), every path through `LS_Team_GivePoints` — success,
  wrong network mode, unsupported gamemode, and invalid team — returns `false`/`0`. The wiki page
  doesn't document a return value at all; there isn't a useful one to check. Don't use this
  special's return in an `if`.
- **Gated on gamemode flags the wiki doesn't mention.** The special no-ops entirely (silently,
  still returning `false`) unless the current gamemode has both `GMF_PLAYERSONTEAMS` and
  `GMF_PLAYERSEARNPOINTS` set (`gamemode.h`'s `EARNTYPE_MASK` family). In a gamemode that doesn't
  award points (e.g. plain Deathmatch/frags-only modes), calling this does nothing at all, not
  even an error.
- **Server-only; a no-op on clients.** `NETWORK_InClientMode()` short-circuits the whole function
  before the team-validity check even runs. Calling it from clientside ACS is a guaranteed no-op.
- **`team` (`arg0`) is a raw team index, not a name.** `TEAM_CheckIfValid` just bounds-checks
  against however many teams are currently loaded (`teams.Size()`); an out-of-range index (or a
  negative one, since `arg0` is treated as `ULONG` via cast) fails validation and no-ops.
- **Team index-to-color mapping is data-driven, not hardcoded — the wiki's "0=Blue, 1=Red,
  2=Green, 3=Gold" is the *default* `TEAMINFO` order, not a guarantee.** Confirmed in
  the Zandronum source's `wadsrc/static/teaminfo.txt` (the engine's own default team defs: `Blue`,
  `Red`, `Green`, `Gold`, in that declaration order, giving indices 0-3) — the wiki is correct
  for an unmodified install, but any WAD/mod that ships its own `TEAMINFO` lump (`ClearTeams` +
  its own `Team "..."` blocks) redefines both how many teams exist and what index maps to which
  color/name. Also note `zt-bcc/lib/zcommon.bcs` only exposes named constants for the first two
  (`TEAM_BLUE = 0`, `TEAM_RED = 1`, plus a sentinel `NO_TEAM = 2`) — indices 2 (Green) and 3
  (Gold) have no named BCS constant in this toolchain and must be passed as raw integers.
- **`announce` only ever triggers an announcer *sound*, never any on-screen or chat text — the
  wiki's "displays a message to all players" is not accurate for this engine.** Traced
  `TEAM_SetPointCount` (`team.cpp:868-891`) → when `doAnnouncement` is true *and* the new point
  count is strictly greater than the old one, it calls `ANNOUNCER_PlayEntry(cl_announcer,
  "<TeamName>Scores")` (`announcer.cpp:217-241`), which does nothing but look up and `S_Sound()`
  an announcer sound entry — no `Printf`/HUD message/chat line is ever produced by this path, on
  either the server or the client-side re-application of the score update. If the announcer
  profile has no matching sound entry for that team, `announce=true` produces no player-visible
  effect at all.
- **`announce` is not honored when raising points via a non-positive or non-increasing delta.**
  Because `TEAM_SetPointCount` only announces on a strict increase, `Team_GivePoints(team, 0,
  true)` and any call with a negative `howMuch` announce nothing even though the special "ran
  successfully" (validity/gamemode checks passed).
- **Also updates the activator's personal point total, independently of the team-wide change.**
  If the activator (`it`) is a player currently on a team, `PLAYER_SetPoints` bumps that specific
  player's own `lPointCount` by the same `howMuch` — this happens unconditionally (not gated on
  `it->player->Team == arg0`), so an activator on a *different* team than the one being credited
  still gets their personal point total incremented by `howMuch`. The wiki page doesn't mention
  this per-player side effect at all; it only describes the team-level change.
- **Server-authoritative replication, same pattern as `ChangeTeamScore`.** `TEAM_SetPointCount`
  calls `SERVERCOMMANDS_SetTeamScore(...)` and `SERVERCONSOLE_UpdateScoreboard()` when running as
  a server, and the client-side handler (`cl_main.cpp:6558`, `client_SetTeamScore`) re-invokes
  `TEAM_SetPointCount` locally with the same `bAnnounce` flag it received — except it forces
  `bAnnounce = false` while still receiving a level snapshot (`g_ConnectionState != CTS_ACTIVE`),
  so a just-joined client doesn't hear a burst of announcer sounds for scores that changed before
  they connected.
- **Sibling special `Team_Score` (152, same file, `p_lnspec.cpp:2102-2119`) is a different,
  activator-only API** — it takes `(int howmuch, bool nogrin)` with no team argument, always
  credits the *activator's own* team, and always returns `false` too. Don't confuse the two: this
  page is specifically `Team_GivePoints` (153), which takes an explicit team index and can credit
  points to a team the activator isn't even on.

**Returns:** `int`/bool-like — always `0`/`false` on every path (success and every failure case
alike); not usable to detect whether the point change actually happened.
