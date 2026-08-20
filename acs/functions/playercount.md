# `int PlayerCount()`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `PlayerCount - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`https://zdoom.org/w/index.php?title=PlayerCount&oldid=36033`) + source-verified (`p_acs.h:657`, `p_acs.cpp:4015-4025,11156-11158`). The wiki's
basic description holds, but it documents vanilla ZDoom behavior; the spectator exclusion is this
doc's source-verified addition and the reason this earns a tier-A file instead of staying
signature-only.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Returns how many players are currently connected and **not spectating**. Compiler builtin
(`PCD_PLAYERCOUNT`, the Zandronum source's `src/p_acs.h:657`), implementation in
`DLevelScript::CountPlayers` (the Zandronum source's `src/p_acs.cpp:4015-4025`), invoked from
`case PCD_PLAYERCOUNT:` (`p_acs.cpp:11156-11158`).

```cpp
int DLevelScript::CountPlayers ()
{
	int count = 0, i;

	// [BB] Skulltag doesn't count spectators as players.
	for (i = 0; i < MAXPLAYERS; i++)
		if (( playeringame[i] ) && ( players[i].bSpectating == false ))
			count++;

	return count;
}
```

- Iterates every player slot (`0..MAXPLAYERS-1`), counting a slot only if `playeringame[i]` is set
  (the slot is occupied by a connected client) **and** `players[i].bSpectating` is false.
- **Fork-specific divergence from the ZDoom wiki page:** the wiki page for this function (written
  for vanilla ZDoom/Hexen) describes it purely as "the number of players currently in the game,"
  with no mention of spectators — vanilla `PlayerCount` counts every `playeringame` slot
  unconditionally. The `bSpectating` exclusion is called out in the fork's own source as a
  Skulltag-era deviation (`// [BB] Skulltag doesn't count spectators as players.`), inherited
  unchanged by Zandronum. Practical effect: on a Zandronum server with active spectators, this
  fork's `PlayerCount()` returns a strictly smaller number than a vanilla-ZDoom reading of "players
  in the game" would suggest — spectators are connected and `playeringame`, but excluded from the
  count.
- Does **not** distinguish a "true" spectator from a dead-and-waiting-to-respawn player in
  LMS/survival modes (`bDeadSpectator`, see `functions/playerisspectator.md`) — both set
  `bSpectating = true` and both get excluded here.
- Single-player: always `1` while the local player is in-game and not spectating.

**Returns:** `int` — count of connected, non-spectating player slots. `0` is possible (e.g. every
player has become a spectator), matching the wiki's own caveat that multiplayer counts can drop to
values lower than expected when players quit or (per the Zandronum engine fork specifically, not
UZDoom — see "Engine-family divergence" below) spectate.

## Engine-family divergence

UZDoom's `DLevelScript::CountPlayers()` (`src/playsim/p_acs.cpp:3738-3747`) drops the Skulltag/Zandronum
spectator exclusion entirely: it loops `0..MAXPLAYERS-1` and counts a slot whenever
`Level->PlayerInGame(i)` is true, with no second condition. `PlayerInGame()`
(`src/g_levellocals.h:612-615`) is a thin wrapper that just returns `playeringame[pnum]` — there is
no `bSpectating`-equivalent field anywhere in the UZDoom source tree to even check. This matches
the plain vanilla-ZDoom reading the wiki page describes ("the number of players currently in the
game"), not the Skulltag-derived exclusion this file documents as Zandronum's addition.

Practical effect: on a build where the same map/script runs under both forks, `PlayerCount()` can
return a strictly larger number under UZDoom than under Zandronum whenever spectators are present,
because UZDoom counts every connected slot unconditionally while Zandronum excludes spectating
slots. Since UZDoom is coop/single-player-focused and has no spectator mechanic wired into
`playeringame` at all, this divergence is mostly moot in practice (no spectators to exclude) rather
than an active behavioral trap — but a script porting Zandronum-authored assumptions about
"non-spectating count" should not assume that filtering still happens.

`MAXPLAYERS` itself is not a factor here: both forks currently define it as `64`
(`src/common/engine/i_net.h:33` in UZDoom, `src/doomdef.h:57` in Zandronum), so the iteration bound
doesn't change the comparison above.
