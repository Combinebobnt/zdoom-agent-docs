# `int PlayerCount()`

Returns how many players are currently connected and **not spectating**. Compiler builtin
(`PCD_PLAYERCOUNT`, the Zandronum source's `src/p_acs.h:657`), implementation in
`DLevelScript::CountPlayers` (the Zandronum source's `src/p_acs.cpp:4015-4025`), invoked from
`case PCD_PLAYERCOUNT:` (`p_acs.cpp:11156-11158`).

**Bucket:** compiler builtin.

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
values lower than expected when players quit or (per this fork specifically) spectate.

**Provenance:** wiki page `PlayerCount - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`oldid=36033`) + source-verified (`p_acs.h:657`, `p_acs.cpp:4015-4025,11156-11158`). The wiki's
basic description holds, but it documents vanilla ZDoom behavior; the spectator exclusion is this
doc's source-verified addition and the reason this earns a tier-A file instead of staying
signature-only. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
