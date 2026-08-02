# `bool A_RaiseSelf(int flags)`

**Tier:** A
**Engine:** UZDoom 4.15pre / GZDoom-family — does not exist in Zandronum
**Provenance:** ZDoom Wiki `A_RaiseSelf` (retrieved 2026-08-01, oldid=53230) + verified against the UZDoom source's `src/playsim/p_actionfunctions.cpp:2774-2778`, `src/playsim/p_things.cpp:437-483` (P_Thing_Raise implementation), and `src/playsim/p_mobj.cpp:8525-8544` (AActor::GetRaiseState).
**Bucket:** `src/playsim/p_actionfunctions.cpp:2774` (`DEFINE_ACTION_FUNCTION(AActor, A_RaiseSelf)`).

Resurrects the calling actor from a corpse state, provided the corpse has a `Raise` state and meets the engine's resurrection requirements. **UZDoom/GZDoom-family only — does not exist in Zandronum.** The optional `flags` parameter supports spatial checks and friendliness transfer, though the latter is meaningless when raiser and target are the same actor.

## Parameters

`flags` (optional, default 0): An integer combining any of the following flag constants via bitwise OR:

| Flag | Value | Behavior |
|---|---|---|
| `RF_NOCHECKPOSITION` | 2 | Skip the position-availability check. Allows resurrection even if there is no room for the actor to stand at its current location. |
| `RF_TRANSFERFRIENDLINESS` | 1 | Copy the friendly/hostile alignment of the raiser to the resurrected actor. **When raiser and target are the same (as in `A_RaiseSelf`), this flag has no effect** — the actor cannot change its own allegiance relative to itself. |

## Return value

Returns `true` if the actor is resurrected successfully, `false` if resurrection fails for any reason (no Raise state, no room, failed resurrection check, etc.).

## Behavior

When called, the action attempts to resurrect the calling actor via the following sequence:

1. **Fetch the Raise state.** Calls `GetRaiseState()`, which checks five conditions:
   - The actor has the `MF_CORPSE` flag (is a dead monster, not a living actor or missile).
   - The actor's `tics` field is `-1` (it has been lying still; any non-negative `tics` value means it is still animating and cannot be raised yet).
   - The current state has the `CanRaise` keyword set (most death states have this; confirm in the actor definition).
   - The actor is not a player (`APlayerPawn` subclass) — players cannot be resurrected.
   - A `Raise` state is defined in the actor's state table.
   
   If any condition fails, `GetRaiseState()` returns NULL, the function returns `false`, and no resurrection occurs.

2. **Prepare spatial properties.** Temporarily saves the actor's current height and radius, then replaces them with the default values from the actor's class definition. This ensures position checks use the full actor size, not any reduced corpse-state size.

3. **Check position.** Unless `RF_NOCHECKPOSITION` is set, calls `P_CheckPosition` to verify the actor has room to stand at its current coordinates. If the check fails, spatial properties are restored and the function returns `false` (silent failure — no error message, no state change).

4. **Call CanResurrect.** Invokes the virtual `CanResurrect(raiser, thing)` method to allow subclasses (e.g., monsters with resurrection restrictions) to veto resurrection. If this returns `false`, the function returns `false`.

5. **Play sound and revive.** If all checks pass:
   - Plays the "vile/raise" sound at the actor's location (characteristic organ music).
   - Calls `Revive()`, which resets all actor flags, fields, and health to their defaults, clears the `target` and `lastenemy` pointers, and increments the kill counter.
   - If `RF_TRANSFERFRIENDLINESS` is set and the raiser is not NULL, copies the raiser's friendly/hostile alignment to the revived actor via `CopyFriendliness(raiser, false)`. **For `A_RaiseSelf`, raiser and target are the same, so this is a no-op.**
   - Sets the actor to the `Raise` state.
   - Returns `true`.

## Failure and edge cases

- **No Raise state:** If the actor has no `Raise` state defined, `GetRaiseState()` returns NULL and the function returns `false`. The actor remains dead. This is silent (no warning).
- **No room to stand:** If the position check fails (and `RF_NOCHECKPOSITION` is not set), the actor is not resurrected and remains at its current location. The function returns `false`.
- **Non-corpses:** Calling `A_RaiseSelf` on a living actor (no `MF_CORPSE` flag) results in `GetRaiseState()` returning NULL; the function returns `false` and does nothing.
- **Animated corpse:** If the actor's `tics` field is >= 0 (the corpse is still animating), `GetRaiseState()` returns NULL. The actor must finish its animation and reach `tics == -1` before `A_RaiseSelf` can resurrect it.
- **CanRaise state keyword missing:** If the current state lacks the `CanRaise` keyword and `tics != -1`, `GetRaiseState()` returns NULL. Most monster death states have `CanRaise` set; check the actor definition if resurrection fails unexpectedly.
- **Player actors:** Calling `A_RaiseSelf` on a player or any `APlayerPawn` subclass always fails — `GetRaiseState()` explicitly rejects players.

## Revived actor properties

When `Revive()` completes:

- **Flags:** All actor flags (`MF_*`, `MF2_*`, ..., `MF8_*`) are reset to the actor's class defaults (including `MF_CORPSE`, which is cleared, transitioning the actor back to "alive" status).
- **Health:** Restored to `SpawnHealth()` (the actor's full health at spawn).
- **Pointers:** The `target` and `lastenemy` pointers are cleared (set to nullptr). The `master` pointer is preserved (the resurrected actor keeps its spawner relationship, if any). If `RF_TRANSFERFRIENDLINESS` is set, the friendly/hostile alignment is copied from the raiser (no-op for `A_RaiseSelf`).
- **Damage immunities:** `PoisonDamageReceived`, `PoisonPeriodReceived`, and associated poison state are cleared.
- **Position:** The actor is revived at its current X/Y coordinates. Height and radius are set to class defaults as part of `Revive()`.

## Resurrectable actors (requirements)

An actor can only be resurrected via `A_RaiseSelf` if **all** of the following are true:

- The actor is a monster with the `MF_CORPSE` flag (not a living actor or missile).
- The actor's `Raise` state is defined in its state table.
- The actor's current state has the `CanRaise` keyword set (most doom monster death/death.fall states do; check the actor definition).
- The actor's `tics` field is exactly `-1` (it is lying still, not animating).
- The actor is not a player.
- If `RF_NOCHECKPOSITION` is not set, the actor must have enough room to stand at its current position.

Actors that don't meet these requirements will return `false` (silent failure). This is by design — allows code to attempt resurrection without error-handling overhead.

## Wiki-to-UZDoom note

**The ZDoom Wiki describes this function correctly for UZDoom/GZDoom-family engines.** The signature, parameters, flags, and behavior match. However, **this function does not exist in Zandronum** — attempting to use `A_RaiseSelf` in Zandronum DECORATE will result in a compiler error ("unknown action function").

For Zandronum projects, use `A_RaiseMaster` (resurrect the calling actor's master) or `A_RaiseChildren` (resurrect all spawned children) instead. Neither of these supports flags in Zandronum, and there is no Zandronum equivalent to a self-targeted raise action.

## Related functions

- **`A_RaiseMaster`** — resurrects the calling actor's master (spawner) instead of itself. Zandronum version takes no parameters.
- **`A_RaiseChildren`** — resurrects all actors whose `master` pointer points to the calling actor. Zandronum version takes no parameters.
- **`A_RaiseSiblings`** — resurrects all actors sharing the same `master` pointer as the calling actor.
- **`A_SpawnItemEx`** — spawns an actor with an optional `master` pointer set via `SXF_SETMASTER` flag; the primary way to establish a spawner relationship for resurrection.
- **`A_RearrangePointers`** — reassigns the calling actor's pointers (target/master/tracer) post-spawn; can be used to establish resurrection relationships.
