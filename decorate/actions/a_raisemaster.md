# `void A_RaiseMaster()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_RaiseMaster` (retrieved 2026-08-01, oldid=53235) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4835-4848`, `src/p_things.cpp:555-591` (P_Thing_Raise implementation), `src/p_mobj.cpp:7849-7868` (AActor::GetRaiseState), and `wadsrc/static/actors/actor.txt:245`.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:4835` (`DEFINE_ACTION_FUNCTION(AActor, A_RaiseMaster)`).

Resurrects the calling actor's master (spawner) from a corpse, provided the corpse has a `Raise` state and meets the engine's resurrection requirements. **Zandronum only: this is server-authoritative and takes no parameters, unlike the ZDoom Wiki's description of GZDoom/UZDoom versions which support optional flags.**

## Parameters

None. The function takes no arguments in Zandronum, so calls like `A_RaiseMaster(RF_TRANSFERFRIENDLINESS)` result in a parse error.

## Behavior

When called, the action:

1. **Early exit if client.** If the calling actor is executing on a network client (not the server), the function returns immediately without effect. The server is the sole authority for resurrection.
2. **Null-master guard.** If the calling actor's `master` pointer is NULL, the function returns without effect.
3. **Delegates to P_Thing_Raise.** For a non-NULL master, calls `P_Thing_Raise(self->master)` with the default `byClient=false` parameter.

### Core resurrection mechanics (P_Thing_Raise)

`P_Thing_Raise` attempts to resurrect the target actor via the following sequence:

1. **Fetch the Raise state.** Calls `target->GetRaiseState()` to find the actor's `Raise` state. If none exists, returns `true` (silently succeeds with no-op).
2. **Check resurrection requirements.** An actor is resurrectable only if:
   - It has the `MF_CORPSE` flag set (is a dead monster, not a living actor or missile).
   - Its `tics` field is `-1` (it has been lying still; any non-negative `tics` value means it is still in an animation and cannot be raised yet).
   - The current state has the `CanRaise` property set (most death/death.fall states have this; some do not).
   - It is **not** a player (`APlayerPawn` subclass) — players cannot be resurrected by this function.
   - If any of these conditions fail, the function returns `true` (treats as success, does nothing).

3. **Prepare spatial properties.** Temporarily saves the actor's current height and radius, then sets them to their defaults via the actor's default-state copy (retrieved via `GetDefault()`). This ensures the spatial check uses the "full" actor size, not any reduced size from the corpse state.

4. **Check position.** Calls `P_CheckPosition(target, target->x, target->y)` to verify the actor has room to stand. If the check fails and the caller is a server (not a client), the spatial properties are restored and the function returns `false` (silently does nothing — DECORATE has no way to detect this failure).

5. **Play sound and revive.** If the position check passes (or is bypassed for clients):
   - Plays the "vile/raise" sound at the actor's location (organ music).
   - Calls `target->Revive()`, which resets all actor flags, fields, and properties to their defaults, clears the `target` and `lastenemy` pointers, restores health, and increments the kill counter.
   - On the server, sends a `SERVERCOMMANDS_SetThingState(target, STATE_RAISE)` command to all clients (see "Network behavior" below).
   - Sets the actor to the `Raise` state.

### Network behavior

**Zandronum multiplayer:** `A_RaiseMaster` is explicitly server-authoritative. The function opens with an early exit if `NETWORK_InClientMode()` is true, ensuring only the server executes the resurrection logic.

- **Server side:** The resurrection proceeds normally, checks position, plays sounds, calls `Revive()`, and broadcasts `SERVERCOMMANDS_SetThingState` to clients to synchronize the state transition and sound.
- **Client side:** The early exit means clients never execute the resurrection logic. Clients receive the state-change via the server's `SERVERCOMMANDS_SetThingState` command, which internally calls `P_Thing_Raise(..., byClient=true)`. The `byClient=true` flag causes `P_Thing_Raise` to:
  - Skip the `GetRaiseState()` check and instead call `FindState(NAME_Raise)` directly (bypassing the `tics != -1` and `CanRaise` guards).
  - Skip the `P_CheckPosition` check entirely (since position validity was verified server-side).
  - Proceed directly to `Revive()` and state-setting.

This ensures clients' resurrected actors have the exact same state and properties as the server's without re-verifying the resurrection prerequisites.

## Failure and edge cases

- **NULL or missing Raise state:** If the master actor has no `Raise` state defined, `P_Thing_Raise` returns `true` without effect — the master remains dead and is not resurrected. Zandronum does not emit any error or warning; the silent no-op is by design (allows monsters without a raise state to be "raised" without breaking the caller's sequence).
- **No room to stand:** If the position check fails, the actor is not resurrected and remains in its current death state. There is no return value or detectable event for the action; the failure is silent.
- **Non-corpses:** Calling `A_RaiseMaster` on an actor whose master is still alive (not a corpse, no `MF_CORPSE` flag) results in a silent no-op — `GetRaiseState` returns NULL, and nothing happens.
- **Player masters:** If the master is a player (e.g., a player-spawned summoned monster resurrecting its player spawner), `GetRaiseState` returns NULL and the player is not resurrected (players are never valid resurrection targets in Zandronum).

## Revived actor properties

When `Revive()` completes:

- **Flags:** All actor flags (`MF_*`, `MF2_*`, ..., `MF7_*`) are reset to the actor's default-class values, including `MF_CORPSE` (which is cleared, transitioning the actor back to "alive").
- **Health:** Restored to `SpawnHealth()` (the actor's full health at spawn).
- **Pointers:** The `target` and `lastenemy` pointers are cleared (set to NULL). The `master` pointer, if any, is preserved (the resurrected actor keeps its master relationship). **Wiki note:** The wiki states "the resurrected actors will change their affiliation to match that of the calling actor" if the `RF_TRANSFERFRIENDLINESS` flag is used. **This flag does not exist in Zandronum** and cannot be used. There is no other mechanism to change the resurrected actor's allegiance.
- **Level-spawned flag:** The `STFL_LEVELSPAWNED` flag is preserved from the corpse state (so level-spawned actors revived during gameplay retain this flag, which affects map-reset cleanup).
- **Position:** The actor is revived at its current `x`/`y` coordinates (height/radius are set to defaults as part of `Revive()`).

## Resurrectable actors (requirements)

An actor cannot be resurrected by `A_RaiseMaster` unless all of the following are true:

- The actor is a monster with the `MF_CORPSE` flag (set by death state transitions or explicit flag changes).
- The actor's `Raise` state is defined in its state table.
- The actor's current state has `CanRaise` set (most doom monster death/death.fall states do; confirm in the actor definition).
- The actor's `tics` field is exactly `-1` (it is lying still; tics >= 0 means it is still animating and cannot be raised yet).
- The actor is not a player.

Monsters that don't meet these requirements will simply be skipped (function returns `true`, no-op). **Exceptions:** The wiki states "Raise and damage functions only work with monsters. Kill functions can be used on monsters and missiles." For this fork, the parenthetical is accurate — `A_RaiseMaster` only works on corpses with a `Raise` state and only resurrects, never kills.

## Zandronum-specific: no-parameter vs. wiki flags

**The ZDoom Wiki page describes the GZDoom/UZDoom version,** which accepts an optional `flags` parameter supporting:

- `RF_TRANSFERFRIENDLINESS` — changes the resurrected actor's friendly/hostile status to match the calling actor's.
- `RF_NOCHECKPOSITION` — skips the position check, allowing resurrection even if there's no room.

**Neither flag exists in Zandronum.** The function signature is:

```
action native A_RaiseMaster();
```

If you attempt to call `A_RaiseMaster(RF_NOCHECKPOSITION)` or `A_RaiseMaster(RF_TRANSFERFRIENDLINESS)` in Zandronum DECORATE, the compiler will emit a parse error ("too many arguments to function"). There is no way to disable the position check or override the resurrected actor's allegiance in Zandronum.

Additionally, the wiki's claim that "the only function that sets the necessary information is `A_SpawnItemEx`" is outdated — `A_RearrangePointers` and `A_TransferPointer` can also assign the `master` pointer, establishing a spawner relationship post-spawn.

## Related functions

- **`A_RaiseChildren`** — resurrects all actors with `master == self` (all spawned children). Server-authoritative; no parameters.
- **`A_RaiseSiblings`** — resurrects all actors sharing the same `master` as the calling actor. Server-authoritative; no parameters.
- **`A_SpawnItemEx`** — spawns a new actor with an optional `master` pointer set via `SXF_SETMASTER` flag; the primary way to establish the spawner relationship for resurrection.
- **`A_RearrangePointers`** — reassigns the calling actor's pointers (target/master/tracer) to any actor or NULL; can establish or change a `master` relationship post-spawn.
- **`A_TransferPointer`** — transfers a pointer from one actor to another; can establish a `master` relationship between pre-existing actors.
