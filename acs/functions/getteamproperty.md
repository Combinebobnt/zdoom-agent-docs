# `int GetTeamProperty(int team, int prop)`

**Tier:** A.
**Engine:** Zandronum 3.2.1 for `TPROP_NumLivePlayers` through `TPROP_LoserTheme` (function itself added in `dd6c1aba9`, confirmed ancestor of the 3.2.1 version-bump `28f736fb3`). `TPROP_WinnerThemeOrder`/`TPROP_LoserThemeOrder` are **3.3-alpha-only** (see above) — not verified/usable against the 3.2.1 target.
**Provenance:** wiki page `GetTeamProperty - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=1300`) + source-verified against `p_acs.cpp:1595-1666,5455,5468,7180-7182`, `p_acs.h:430-453`, `team.cpp` (`TEAM_CheckIfValid:731`, `TEAM_GetName:741`, `TEAM_CountLivingAndRespawnablePlayers:194`, `TEAM_CountPlayers:173`, `TEAM_GetCarrier:1082`, `TEAM_GetAssistPlayer:1304`, `TEAM_GetSpread:1434`, `TEAM_GetPlayerStartThingNum:1694`, `TEAM_GetTeamItemName:1702`, `TEAM_GetReturnTicks:1119`, `TEAM_GetIntermissionTheme:1724`, `TEAM_GetIntermissionThemeOrder:1734`, `TEAM_GetNumAvailableTeams:1345`), `zstring.cpp:326-333`, `zt-bcc/lib/zcommon.bcs:813-832,1736`. Crash bug and version-gate findings both confirmed via git ancestry (`git merge-base --is-ancestor`), not just source reading.
**Bucket:** extension function.

Reads a single property off a team by team index. Extension function (`ACSF_GetTeamProperty`,
index `-103`, `zt-bcc/lib/zcommon.bcs:1736`), implementation in the static helper
`GetTeamProperty` (the Zandronum source's `src/p_acs.cpp:1600-1666`), dispatched at
`p_acs.cpp:7180-7182`.

- `team` — team index, `unsigned int` at the engine level (no negative-team guard — a negative
  `int` argument becomes a huge unsigned value, which then simply fails every getter's own bounds
  check the same as any other out-of-range index; see the crash caveat below for the one case
  where "fails safe" isn't true).
- `prop` — one of the `TPROP_*` constants already named in `zt-bcc/lib/zcommon.bcs:813-832`. The
  enum order there (`NAME, SCORE, ISVALID, NUMPLAYERS, NUMLIVEPLAYERS, TEXTCOLOR,
  PLAYERSTARTNUM, SPREAD, CARRIER, ASSISTER, FRAGCOUNT, DEATHCOUNT, WINCOUNT, POINTCOUNT,
  RETURNTICS, TEAMITEM, WINNERTHEME, LOSERTHEME`) matches the engine's own `ETeamProperty` enum
  (`p_acs.h:433-450`) value-for-value, so the named constants resolve correctly.

## Wiki text is accurate for all 18 named properties, verified against the switch

Every `TPROP_*` the wiki describes matches the engine switch in `p_acs.cpp:1600-1663`:
`TPROP_NumLivePlayers`/`NumPlayers` exclude spectators and (for `NumLivePlayers`) dead players
that can't respawn (`TEAM_CountLivingAndRespawnablePlayers`/`TEAM_CountPlayers`, `team.cpp:173,
194`); `TPROP_Score` dispatches to frags/wins/points depending on `GMF_PLAYERSEARNFRAGS`/
`GMF_PLAYERSEARNWINS` gamemode flags (`GetTeamScore`, `p_acs.cpp:1580-1589`), matching the wiki's
"frags in TDM, wins in TLMS, flags/points otherwise"; `TPROP_Assister`/`TPROP_Carrier` both
convert the engine's internal "nobody"/`NULL` sentinel to `-1` for ACS (documented in-line at
`p_acs.cpp:1614-1627` as a deliberate consistency choice with `PlayerNumber()`); `TPROP_IsValid`
is `team < min(teams.Size(), sv_maxteams)` (`TEAM_CheckIfValid`, `team.cpp:731-735` +
`TEAM_GetNumAvailableTeams`, `team.cpp:1345-1348`) — a team defined in TEAMINFO but disabled via
`sv_maxteams` reads back as invalid, not just a nonexistent team slot.

## Real crash: `TPROP_TeamItem`/`TPROP_WinnerTheme`/`TPROP_LoserTheme` with an invalid `team` — not on the wiki, not fail-safe

The four string-returning properties (`TPROP_TeamItem`, `TPROP_WinnerTheme`, `TPROP_LoserTheme`,
`TPROP_Name`) share one code path (`p_acs.cpp:1644-1666`) that builds an `FString` and appends the
underlying getter's `const char*` result to it via `operator+=`. The four getters do **not**
agree on what they return for an invalid `team`:

- `TEAM_GetName` (`team.cpp:741-746`) returns `""` for an invalid team — safe.
- `TEAM_GetTeamItemName` (`team.cpp:1702-1709`) and `TEAM_GetIntermissionTheme`
  (`team.cpp:1724-1730`, backs `WinnerTheme`/`LoserTheme`) both explicitly `return NULL;` for an
  invalid team.

`FString::operator+=(const char *tail)` (`zstring.cpp:326-333`) calls `strlen(tail)` with no null
check before appending. Passing it a `NULL` C string is undefined behavior and segfaults in
practice on this codebase's target platforms. **Net effect: `GetTeamProperty(<invalid team>,
TPROP_TeamItem | TPROP_WinnerTheme | TPROP_LoserTheme)` crashes the caller (server or client,
whichever runs the script) instead of returning an empty string like `TPROP_Name` and every other
property do.** This is a real, verified fork bug, not a documentation gap — the wiki doesn't
mention it because the wiki does not document invalid-`team` behavior for these properties at
all. Always validate `team` against `GetTeamProperty(team, TPROP_IsValid)` (or a known team-count
bound) before reading any of these three properties with an untrusted index.

## `TPROP_WinnerThemeOrder`/`TPROP_LoserThemeOrder` exist in the engine switch but postdate the 3.2.1 target

The engine enum (`p_acs.h:452-453`) and switch (`p_acs.cpp:1640-1643`) also implement
`TPROP_WinnerThemeOrder`/`TPROP_LoserThemeOrder` (intermission music ordering), added in commit
`95735f243`. That commit is **not** an ancestor of the 3.2.1 version-bump commit `28f736fb3`
(`git merge-base --is-ancestor 95735f243 28f736fb3` fails) — it postdates the 3.2.1 tag, landing
only in the `3.3-alpha` snapshot this checkout is on. Consistent with that, `zt-bcc`'s
`zcommon.bcs` (`lines 813-832`) does **not** define named constants for either value — they'd
have to be called as raw integers (`18`/`19`) to be reached at all, and neither is usable via a
named constant in `zt-bcc` regardless of target engine version. Treat both as **not part of
the 3.2.1 surface**.

## Clientside caveat — from the original commit message, not independently re-traced

The commit that introduced this function (`dd6c1aba9`, an ancestor of the 3.2.1 tag) states in
its own message: *"Note: TPROP_ReturnTics and TPROP_Assister do not work in client-side scripts
yet."* No later commit before (or after) the 3.2.1 tag touches `g_ulAssistPlayer` or the
return-ticks path in a way that looks like a fix for this. This doc is recording that note as a
plausible still-live caveat rather than a freshly-derived one — full client/server state-sync
tracing for these two fields wasn't done here; treat `TPROP_ReturnTics`/`TPROP_Assister` as
suspect on a `CLIENTSIDE` script until checked against actual client behavior.
