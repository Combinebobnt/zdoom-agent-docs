# `bool PlayerInGame(int player)`

Checks whether a player slot is occupied by a connected, non-spectating player. Compiler builtin
(`PCD_PLAYERINGAME` in `zt-bcc/src/builtin.c:128,276`), implementation at
the Zandronum source's `src/p_acs.cpp:12391-12401`.

**Bucket:** compiler builtin.

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
things differ in this fork:

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
this fork: `PlayerCount`'s backing `DLevelScript::CountPlayers()` (`p_acs.cpp:4015-4024`) uses the
identical `playeringame[i] && !players[i].bSpectating` condition, tagged with the same Skulltag
comment, so the two functions agree on who counts as "in game."

**Returns:** `bool` — `true` only for a valid slot index that is both connected
(`playeringame[player]`) and not spectating; `false` for an out-of-range index, an empty slot, or
a spectating player.

**Provenance:** wiki page `PlayerInGame - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`oldid=55335`) + source-verified (`p_acs.cpp:12391-12401,4015-4024`, `doomdef.h:57`). The wiki's
basic "true/false, tied to `PlayerCount`" description holds; the `[0..7]` range and the
spectator-exclusion behavior are this doc's source-verified corrections/additions — the wiki
(written for stock ZDoom) has neither, since stock ZDoom has no spectator concept.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
