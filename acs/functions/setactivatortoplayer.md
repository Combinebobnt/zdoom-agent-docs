# `bool SetActivatorToPlayer(int playernumber)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki `SetActivatorToPlayer` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=SetActivatorToPlayer&oldid=1325) +
source-verified against Zandronum `src/p_acs.cpp:7504-7510` (`ACSF_SetActivatorToPlayer` case)
and `src/p_interaction.cpp:3006-3014` (`PLAYER_IsValidPlayer` definition); `src/p_interaction.cpp:3018-3022`
(`PLAYER_IsValidPlayerWithMo` tests `mo` and spectator status separately), `src/p_mobj.cpp:5601-5610`
(spectator spawn path), `src/p_acs.cpp:12380-12384` (`PlayerNumber()` on a NULL activator) and
`docs/zandronum-history.txt:537` (stated purpose).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -131 in zt-bcc's `lib/zcommon.bcs:1764`), dispatched as
`ACSF_SetActivatorToPlayer`.

Sets the calling script's activator to a specific player by player number, for the remainder of
the script's execution. Extension function (`ACSF_SetActivatorToPlayer`, index `-131` in the
zt-bcc source's `lib/zcommon.bcs:1764`), implementation in the Zandronum source's
`src/p_acs.cpp:7504-7510`.

## Parameters

**`playernumber`** — the player number to set as the activator. Zero-indexed (player 1 in the
console is `playernumber=0`). Must be a valid, currently-connected player (passed to
`PLAYER_IsValidPlayer`, which checks bounds against `MAXPLAYERS` and `playeringame[]`).

## Return value

`true` (`1`) if the player number passed `PLAYER_IsValidPlayer` and the activator was set;
`false` (`0`) if the player number is out of range (`>= MAXPLAYERS`; a negative number is also out
of range, since the check takes it as unsigned) or that slot is not in the game
(`playeringame[playernumber] == false`). On failure the activator is left unchanged.

**Important:** The check never looks at the player's actor. The activator is set to
`players[playernumber].mo` as-is, so if that slot is in the game but its `mo` is `NULL`, the
function still returns `1` and the activator becomes `NULL`. After that, `ActivatorTID()` returns
`0` and `PlayerNumber()` returns `-1`, with no error. A return of `1` does not guarantee a
non-NULL activator. Spectators are not rejected either: a Zandronum spectator has a body, so the
activator becomes that spectator's body.

## Engine-family divergence

This function is **Zandronum-only and does not exist in UZDoom.** UZDoom's ACSF function table
carries no `SetActivatorToPlayer` enumerator or dispatcher. A script compiled against
`zcommon.bcs`'s `-131` function reference and run on UZDoom silently returns `0` (the fallback
for any unknown ACSF index) and leaves the activator unchanged. Zandronum's `MAXPLAYERS` limit of
64 (`src/doomdef.h:57`) means this function can reach every player slot, unlike the 8-player
`AAPTR_PLAYER1`-`8` static selectors documented in [Actor pointer
selectors](../concepts/actor-pointers.md). Zandronum's changelog (`docs/zandronum-history.txt:537`)
names it as the replacement for `AAPTR_PLAYERx` that works with all 64 players.

## Scope of the change

Identical to `SetActivator` and `SetActivatorToTarget`: the reassignment affects only the running
script instance's own `activator` variable, persists for the rest of that script's execution,
and has no Zandronum server→client replication (activator state is per-script, per-instance,
not globally replicated).

## See also

- `SetActivator(int tid [, int pointer_selector])` (`p_acs.cpp:5952-5961`, index `-12`) — sets
  the activator directly to an actor found by TID, optionally through an `AAPTR_*` pointer selector.
- `SetActivatorToTarget(int tid)` (`p_acs.cpp:5963-5982`, index `-13`) — sets the activator to the
  target of the actor found by TID.
- [Actor pointer selectors](../concepts/actor-pointers.md) (`AAPTR_*` constants and their resolution
  order).
