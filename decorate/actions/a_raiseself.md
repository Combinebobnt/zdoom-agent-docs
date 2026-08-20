# `bool A_RaiseSelf(int flags)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `A_RaiseSelf` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RaiseSelf&oldid=53230) + verified against the UZDoom source's `src/playsim/p_actionfunctions.cpp:2774-2778`, `src/playsim/p_things.cpp:437-483` (P_Thing_Raise implementation), and `src/playsim/p_mobj.cpp:8525-8544` (AActor::GetRaiseState).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

1. **Fetch the Raise state.** Calls `GetRaiseState()`, which checks four conditions:
   - The actor has the `MF_CORPSE` flag (is a dead monster, not a living actor or missile).
   - Either the actor's `tics` field is `-1` (it has finished animating and is lying still), **or** its current state has the `CanRaise` state keyword set. This check only fails — blocking resurrection — when *both* are false at once: `tics != -1` (still mid-animation) *and* the current state lacks `CanRaise`. In other words, `CanRaise` is not a secondary requirement on top of "lying still"; it's an alternate path that lets a state be raised out of *without* waiting for `tics` to reach `-1`. (The engine's own comment on the underlying state flag describes it as letting a monster "be resurrected without waiting for an infinite frame.")
   - The actor is not a player (`APlayerPawn` subclass) — players cannot be resurrected.
   - A `Raise` state is defined in the actor's state table.
   
   If any condition fails, `GetRaiseState()` returns NULL, the function returns `false`, and no resurrection occurs.

2. **Prepare spatial properties.** Zeroes the actor's X/Y velocity, then temporarily saves the actor's current height, radius, and flags, and replaces the height/radius with the default values from the actor's class definition (and adds `MF_SOLID`). This ensures position checks use the full actor size, not any reduced corpse-state size. Note that the velocity is zeroed unconditionally at this point, even if resurrection subsequently fails at the position or `CanResurrect` check below.

3. **Check position.** Unless `RF_NOCHECKPOSITION` is set, calls `P_CheckPosition` to verify the actor has room to stand at its current coordinates. If the check fails, the height/radius/flags saved in step 2 are restored and the function returns `false` (silent failure — no error message, no state change beyond the velocity zeroing above).

4. **Call CanResurrect.** Invokes the raiser's virtual `CanResurrect(other, passive)` method (called here as `raiser->CanResurrect(thing, false)`; for `A_RaiseSelf` this is the same actor calling it on itself) to allow subclasses (e.g., monsters with resurrection restrictions) to veto resurrection; the default implementation always allows it. If this returns `false`, the function returns `false` — and unlike the position-check failure above, the height/radius/`MF_SOLID` changes from step 2 are **not** rolled back in this case, leaving the still-dead actor with its collision box changed to class defaults.

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
- **Animated corpse without `CanRaise`:** If the actor's `tics` field is >= 0 (the corpse is still mid-animation) **and** the current state lacks the `CanRaise` keyword, `GetRaiseState()` returns NULL and resurrection fails. If the current state *does* have `CanRaise` set, resurrection can succeed even while `tics` is still counting down — `CanRaise` is an alternate way to satisfy this check, not an additional requirement on top of `tics == -1`. Once `tics` reaches `-1`, whether the state has `CanRaise` no longer matters at all.
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
- Either the actor's `tics` field is exactly `-1` (lying still, not animating), or its current state has the `CanRaise` keyword set — the check only fails if the actor is still mid-animation (`tics != -1`) *and* the current state lacks `CanRaise`.
- The actor is not a player.
- If `RF_NOCHECKPOSITION` is not set, the actor must have enough room to stand at its current position.

Actors that don't meet these requirements will return `false` (silent failure). This is by design — allows code to attempt resurrection without error-handling overhead.

## Engine-family divergence: Zandronum absence

**The ZDoom Wiki describes this function correctly for UZDoom/GZDoom-family engines.** The signature, parameters, flags, and behavior match. However, **this function does not exist in Zandronum** — attempting to use `A_RaiseSelf` in Zandronum DECORATE will result in a compiler error ("unknown action function").

For Zandronum projects, use `A_RaiseMaster` (resurrect the calling actor's master) or `A_RaiseChildren` (resurrect all spawned children) instead. Neither of these supports flags in Zandronum, and there is no Zandronum equivalent to a self-targeted raise action.

## Related functions

- **`A_RaiseMaster`** — resurrects the calling actor's master (spawner) instead of itself. Zandronum version takes no parameters.
- **`A_RaiseChildren`** — resurrects all actors whose `master` pointer points to the calling actor. Zandronum version takes no parameters.
- **`A_RaiseSiblings`** — resurrects all actors sharing the same `master` pointer as the calling actor.
- **`A_SpawnItemEx`** — spawns an actor with an optional `master` pointer set via `SXF_SETMASTER` flag; the primary way to establish a spawner relationship for resurrection.
- **`A_RearrangePointers`** — reassigns the calling actor's pointers (target/master/tracer) post-spawn; can be used to establish resurrection relationships.
