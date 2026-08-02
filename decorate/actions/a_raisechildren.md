# `void A_RaiseChildren()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_RaiseChildren` (retrieved 2026-08-01, oldid=53237) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4852-4868` and `src/p_things.cpp:527-566`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_RaiseChildren)` in `src/thingdef/thingdef_codeptr.cpp`.

Resurrects all actors whose master pointer is set to the calling actor, typically creatures spawned by the calling actor. Zandronum version takes **no parameters** — the `flags` parameter and `RF_*` constants described in the ZDoom Wiki do not exist in this fork.

## Signature

```
void A_RaiseChildren()
```

## Behavior

When called, this action:

1. **Iterates all actors in the current map** using a global thinker iterator.
2. **Identifies children** by checking if `mo->master == self` (the actor's master pointer equals the calling actor).
3. **Attempts to resurrect each child** by calling `P_Thing_Raise(mo)`, which:
   - Finds the child's `Raise` state (the entry point for resurrection animation).
   - Restores the child's height and radius to their default values.
   - **Checks if there is room** for the resurrected actor at its current position using `P_CheckPosition`. If not enough room, the child remains dead and no further processing occurs for that actor.
   - Plays the "vile/raise" sound effect.
   - Calls `Revive()` to restore the actor to life.
   - Sets the actor to its `Raise` state.
4. **Continues iterating** through all remaining actors; multiple children can be resurrected in one call.

## Child relationship and scope

A child's master relationship is typically established via `A_SpawnItemEx(..., SXF_SETMASTER)` — this action sets the `master` pointer of the spawned actor to point back to the spawner. The `A_RaiseChildren` action then uses that relationship to identify and resurrect victims.

**Important limitation:** Actors spawned with `A_SpawnProjectile` are **not affected** by `A_RaiseChildren`. The `A_SpawnProjectile` action does not set the `master` pointer and was never designed to spawn creatures targeted by this action. Only use `A_SpawnItemEx` with the `SXF_SETMASTER` flag if you intend to later resurrect spawned actors via `A_RaiseChildren`.

## Resurrection failure conditions

### No Raise state

If a child actor has no `Raise` state defined, `P_Thing_Raise` returns without effect and the child remains dead. This is not an error; it is a silent condition. Many actors do not define a `Raise` state and therefore cannot be resurrected.

### No room to raise

If the child's default height and radius would overlap another actor or solid geometry at its current position, `P_CheckPosition` fails and the resurrection is aborted. The child remains dead and at its current location. **This check is unconditional in Zandronum** — there is no parameter to skip it (unlike the ZDoom Wiki's `RF_NOCHECKPOSITION` flag, which does not exist in this fork).

## Zandronum difference from ZDoom Wiki

**The ZDoom Wiki describes a more complex version** of `A_RaiseChildren` with an optional `int flags` parameter supporting two flags:

- `RF_TRANSFERFRIENDLINESS` — described as making resurrected actors change their affiliation to match the caller's.
- `RF_NOCHECKPOSITION` — described as skipping the position-availability check.

**Neither parameter nor flag constants exist in Zandronum 3.2.1.** The Zandronum version is a no-argument action that always performs the position check and does not modify affiliations — it resurrects the child as-is.

If you port DECORATE code from upstream ZDoom/GZDoom to Zandronum, do not attempt to pass flags to `A_RaiseChildren`. Doing so will result in a "too many arguments" compile error, not a silent no-op.

## Monster-only resurrection

The ZDoom Wiki states: "Raise and damage functions only work with monsters." This claim has not been fully verified for Zandronum. The `P_Thing_Raise` function gates resurrection on the presence of a `Raise` state, not on a monster-specific flag check. It is possible for non-monster actors to be resurrected if they have a `Raise` state, though this is an uncommon configuration.

## Network behavior

**Zandronum multiplayer:** This action is handled by the server. The iteration and resurrection calls are resolved server-side; affected clients receive state-change updates (resurrection animations) from the server via `SERVERCOMMANDS_SetThingState`.

## Related actions

- **`A_RaiseMaster`** — resurrects the calling actor's own master instead of its children.
- **`A_RaiseSiblings`** — resurrects all other actors that share the same master.
- **`A_SpawnItemEx`** — the typical way to spawn actors as children (with `SXF_SETMASTER` to establish the master relationship).
- **`A_KillChildren`** — destroys all children instead of resurrecting them.
- **`A_DamageChildren`** — damages all children by a fixed amount.
- **`A_RemoveChildren`** — removes (without death animation) all children instead of damaging them.
