# `bool SetActivatorToPlayer(int playernumber)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** Zandronum Wiki `SetActivatorToPlayer` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=SetActivatorToPlayer&oldid=1325) +
source-verified against Zandronum `src/p_acs.cpp:7504-7510` (`ACSF_SetActivatorToPlayer` case)
and `src/p_interaction.cpp:3006-3014` (`PLAYER_IsValidPlayer` definition).
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

`true` (`1`) if the player was valid and the activator was set; `false` (`0`) if the player
number is out of range (`>= MAXPLAYERS`), not connected/in-game (`playeringame[playernumber] == false`),
or the player's actor is unspawned.

**Important:** If the player has no spawned actor (e.g. a spectator whose `.mo` is `NULL`, or a
player still loading), the function returns `1` but the activator is set to `NULL`. The calling
script's subsequent `ActivatorTID()`, `PlayerNumber()`, or pointer-reading calls will all fail
silently or return 0, not error. Check the return value's truthfulness only; don't assume a
return of `1` means the new activator is a non-NULL actor.

## Engine-family divergence

This function is **Zandronum-only and does not exist in UZDoom.** UZDoom's ACSF function table
carries no `SetActivatorToPlayer` enumerator or dispatcher — a script compiled against
`zcommon.bcs`'s `-131` function reference and run on UZDoom silently returns `0` (the fallback
for any unknown ACSF index). Zandronum's `MAXPLAYERS` limit of 64 (confirmed `src/doomdef.h:57`)
is independent of the 8-player `AAPTR_PLAYER1`-`8` static selectors documented in [Actor pointer
selectors](../concepts/actor-pointers.md), and was the motivating addition to avoid the
pointer-selector's hardcoded 8-entry cap when many players need independent manipulation.

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
