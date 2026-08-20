# `int GameType()`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `GameType - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://wiki.zandronum.com/w/index.php?title=GameType&oldid=1282`) + source-verified (`p_acs.h:658,977`, `p_acs.cpp:11159-11169`, `team.cpp:1748-1875`,
`deathmatch.cpp:118-289`, `wadsrc/static/gamemode.txt`). The wiki's four base values and its
team-game inclusion/exclusion list both check out; the cascading-cvar-callback mechanism behind
the team-game list, the zcommon.bcs gap for `GAME_NET_TEAMGAME`, and the
Cooperative/Survival/Invasion collapse are this doc's source-verified additions.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Reads the server's current game-mode selection back as one of five `GAME_*` enum values.
Compiler builtin (`PCD_GAMETYPE`, the Zandronum source's `src/p_acs.h:658`), implemented inline in
`case PCD_GAMETYPE:` (the Zandronum source's `src/p_acs.cpp:11159-11169`) — no separate helper
function, unlike `PlayerCount`/`CountPlayers`.

```cpp
case PCD_GAMETYPE:
	if (gamestate == GS_TITLELEVEL)
		PushToStack (GAME_TITLE_MAP);
	else if (deathmatch)
		PushToStack (GAME_NET_DEATHMATCH);
	else if ( teamgame )
		PushToStack( GAME_NET_TEAMGAME );
	else if ( NETWORK_GetState( ) != NETSTATE_SINGLE )
		PushToStack (GAME_NET_COOPERATIVE);
	else
		PushToStack (GAME_SINGLE_PLAYER);
	break;
```

- Checks are an **if/else-if chain in this exact priority order**: title map, then the
  `deathmatch` cvar, then the `teamgame` cvar, then "is this a networked game at all," then
  single-player as the fallback. Only the first match wins — a state that satisfies two branches
  (see below) always reports the earlier one.
- **`GAME_SINGLE_PLAYER = 0` / `GAME_NET_COOPERATIVE = 1` / `GAME_NET_DEATHMATCH = 2` /
  `GAME_TITLE_MAP = 3`** match the wiki and are declared in this toolchain's
  the zt-bcc source's `lib/zcommon.bcs:48-53`.
- **`GAME_NET_TEAMGAME = 4` is real in the engine (the Zandronum source's `src/p_acs.h:977`) but is
  NOT declared anywhere in the zt-bcc source's `lib/zcommon.bcs`, `builtin.c`, or any other zt-bcc
  header** — confirmed by grep, nothing partial. A script in this toolchain that wants to detect
  it must compare against the raw literal `4`; `GAME_NET_TEAMGAME` will not compile as an
  identifier. Same "exists in the engine, unnamed in this toolchain's BCS constants" gap already
  documented for `GAMEEVENT_PLAYERJOINS` (`../concepts/event-scripts.md`) and the ACSF 93-99 gap
  (`families/spawning.md`, `families/inventory.md`).
- **The wiki's team-game inclusion list is correct, and the reason is worth recording because it
  isn't obvious from the `if(teamgame)` line alone.** `teamgame` and `deathmatch` are independent
  server cvars (the Zandronum source's `src/team.h:201`, `deathmatch.h`), but each game-mode-selector
  cvar's own `CUSTOM_CVAR` callback force-sets one or the other as a side effect when turned on
  (the Zandronum source's `src/team.cpp:1748-1875`, `deathmatch.cpp:118-133,222-238,274-289`):
  - `ctf`, `oneflagctf`, `skulltag`, `domination` → their callbacks force `teamgame = true`.
    Setting `teamgame` directly (the literal "Team Game" mode) obviously also sets it. All four
    read back as `GAME_NET_TEAMGAME`.
  - `teamplay` (Team Deathmatch), `teamlms` (Team LMS), `teampossession` (Team Possession) →
    their callbacks force `deathmatch = true` instead. Because the `deathmatch` branch is checked
    **before** the `teamgame` branch in the if/else chain, all three read back as
    `GAME_NET_DEATHMATCH`, never reaching the teamgame check — matching the wiki's explicit
    exclusion list exactly.
  - the Zandronum source's `wadsrc/static/gamemode.txt` corroborates this at the flag level: `CTF`,
    `OneFlagCTF`, `Skulltag`, `Domination`, `TeamGame` all `AddFlag TEAMGAME`, while `Teamplay`
    (Team DM), `TeamLMS`, `TeamPossession` all `AddFlag DEATHMATCH` instead, despite all seven
    modes putting players on teams.
- **`GAME_NET_COOPERATIVE` does not distinguish plain Cooperative from Survival or Invasion.**
  Those three modes set neither `deathmatch` nor `teamgame`, so any networked
  (`NETWORK_GetState() != NETSTATE_SINGLE`) game in one of them falls through to the same
  `GAME_NET_COOPERATIVE` branch — a distinction the wiki page doesn't mention. A common
  workaround also checks `GetCVar("invasion")`/`GetCVar("survival")` alongside
  `GameType() == GAME_NET_COOPERATIVE`, confirming the collapse is real and a known gotcha.
- **Single-player note:** `GAME_SINGLE_PLAYER` requires *both* not-title-map, not-deathmatch,
  not-teamgame, *and* `NETWORK_GetState() == NETSTATE_SINGLE` — i.e. truly offline, not just
  "coop with one player." A dedicated/listen server with one connected player reports
  `GAME_NET_COOPERATIVE`, not `GAME_SINGLE_PLAYER`.

**Returns:** `int` — one of the five `GAME_*` values above. No failure mode; always returns one
of them.

**Version note:** `PCD_GAMETYPE` and all five `GAME_*` constants (including the
zcommon.bcs-unexposed `GAME_NET_TEAMGAME`) trace back to `bc562a817` ("original Skulltag 0.97c2
source"), confirmed via `git merge-base --is-ancestor` to predate the `28f736fb3` 3.2.1
version-bump commit by the entire project history — this is original Skulltag-era functionality,
not a recent addition, so the 3.2.1 engine stamp below is solid.

## Engine-family divergence: no team-game branch, no `GAME_NET_TEAMGAME` value at all

UZDoom implements the same opcode (`PCD_GAMETYPE`, `src/playsim/p_acs.cpp:8927-8936`) with a
shorter if/else-if chain that drops the team-game branch entirely: title map, then `deathmatch`,
then `multiplayer`, else single-player. There is no `teamgame` check — confirmed by grep, the
`teamgame` cvar/global that drives Zandronum's third branch does not exist anywhere in UZDoom's
`p_acs.cpp`. Consequently `GAME_NET_TEAMGAME` is not just unexposed to BCS here the way it is in
zt-bcc's `zcommon.bcs` — the enum member itself does not exist in UZDoom's source at all (the local
`enum` at `p_acs.cpp:483-486` declares only the four values `GAME_SINGLE_PLAYER`,
`GAME_NET_COOPERATIVE`, `GAME_NET_DEATHMATCH`, `GAME_TITLE_MAP`; confirmed by grep across
`~/source/UZDoom/src`). None of this doc's Zandronum-specific team-game notes above (the
`ctf`/`domination`/`skulltag` vs. `teamplay`/`teamlms`/`teampossession` cvar-cascade split, and
the reason `GAME_NET_TEAMGAME` is reachable at all) have any UZDoom counterpart — GZDoom-family
has no engine-level team-mode cvar system feeding this opcode.

The coop branch's networked-game test also differs mechanically: UZDoom checks the single global
`bool multiplayer` (set by session setup/demo playback, reset at level load/demo teardown) instead
of Zandronum's live `NETWORK_GetState() != NETSTATE_SINGLE` computation — functionally the same
"is this a networked session" question, just a cached flag rather than a live state check (see
`ismultiplayer.md`'s divergence section for the same `netgame`-flag-vs-live-state pattern on a
different opcode).

This doc's Cooperative/Survival/Invasion-collapse note also doesn't carry over: UZDoom's source has
no `invasion` or `survival` cvar/mode at all (confirmed by grep), so there is no analogous
sub-mode distinction for `GAME_NET_COOPERATIVE` to collapse in the first place — UZDoom's
`multiplayer` branch simply means "any non-deathmatch networked game."
