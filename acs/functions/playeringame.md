# `bool PlayerInGame(int player)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `PlayerInGame - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`https://zdoom.org/w/index.php?title=PlayerInGame&oldid=55335`) + source-verified (`p_acs.cpp:12391-12401,4015-4024`, `doomdef.h:57`). The wiki's
basic "true/false, tied to `PlayerCount`" description holds; the `[0..7]` range and the
spectator-exclusion behavior are this doc's source-verified corrections/additions — the wiki
(written for stock ZDoom) has neither, since stock ZDoom has no spectator concept.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Checks whether a player slot is occupied by a connected, non-spectating player. Compiler builtin
(`PCD_PLAYERINGAME` in `zt-bcc/src/builtin.c:128,276`), implementation at
the Zandronum source's `src/p_acs.cpp:12391-12401`.

```cpp
case PCD_PLAYERINGAME:
    if (STACK(1) < 0 || STACK(1) >= MAXPLAYERS)
    {
        STACK(1) = false;
    }
    else
    {
        // [BB] Skulltag doesn't count spectators as players.
        STACK(1) = playeringame[STACK(1)] && ( players[STACK(1)].bSpectating == false );
    }
    break;
```

The ZDoom wiki page describes this as "Returns true if the player [0..7] is in the game." Two
things differ in the Zandronum engine fork:

- **Range is `[0..63]`, not `[0..7]`.** `MAXPLAYERS` is `64` in Zandronum
  (the Zandronum source's `src/doomdef.h:57`), not the classic 8-player ZDoom/vanilla limit the wiki's
  range comment describes. Any `player` outside `[0, MAXPLAYERS)` (including negative values)
  silently returns `false` — no error, no crash.
- **Spectators read back as `false`, not just "not in game."** The `bSpectating == false` check
  (tagged `[BB] Skulltag doesn't count spectators as players` — a Skulltag-inherited,
  Zandronum-specific addition, not stock ZDoom behavior) means a player who is fully connected
  and `playeringame[p] == true` but currently spectating still returns `false` here. Callers
  cannot distinguish "slot empty" from "player connected but spectating" from this return value
  alone — use `PlayerIsSpectator()` (see `functions/playerisspectator.md`) if that distinction
  matters.

The wiki's cross-reference claim — "that player is not counted by `PlayerCount`" — does hold in
the Zandronum engine fork: `PlayerCount`'s backing `DLevelScript::CountPlayers()` (`p_acs.cpp:4015-4024`) uses the
identical `playeringame[i] && !players[i].bSpectating` condition, tagged with the same Skulltag
comment, so the two functions agree on who counts as "in game."

**Returns:** `bool` — `true` only for a valid slot index that is both connected
(`playeringame[player]`) and not spectating; `false` for an out-of-range index, an empty slot, or
a spectating player.

## Engine-family divergence: no spectator exclusion in UZDoom

UZDoom has no spectator concept at all — there is no `bSpectating` field anywhere in its player
state, and its `PCD_PLAYERINGAME` handler (`src/playsim/p_acs.cpp`) delegates to a level method
that reduces to a bare `playeringame[pnum]` lookup, with no second condition to exclude anything.
The out-of-range bounds check is identical to Zandronum's (any index outside `[0, MAXPLAYERS)`,
including negative values, silently yields `false`, and `MAXPLAYERS` is likewise `64`), so the
range behavior this doc describes carries over unchanged. What doesn't carry over is the
spectator-exclusion behavior itself: on UZDoom, a connected player returns `true` regardless of
any spectating state, because the engine has no such state to check. `PlayerCount`'s backing
`CountPlayers()` is implemented purely in terms of `PlayerInGame()` on UZDoom, so the two
functions still agree with each other on who counts as "in game" — they just agree on a simpler,
spectator-blind definition than Zandronum's Skulltag-inherited one.
