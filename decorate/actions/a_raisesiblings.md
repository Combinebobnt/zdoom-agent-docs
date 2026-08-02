# `void A_RaiseSiblings()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_RaiseSiblings` (retrieved 2026-08-01, oldid=53236) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4875-4894`.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:4875` (`DEFINE_ACTION_FUNCTION(AActor, A_RaiseSiblings)`).

Resurrects all actors that share the calling actor's master (spawner) from corpses, excluding the calling actor itself. Zandronum version takes **no parameters** — the `flags` parameter and `RF_*` constants described in the ZDoom Wiki do not exist in this fork.

## Signature

```
void A_RaiseSiblings()
```

## Behavior

When called, this action:

1. **Early exit if client.** If the calling actor is executing on a network client (not the server), the function returns immediately without effect. The server is the sole authority for resurrection.
2. **Null-master guard.** If the calling actor's `master` pointer is NULL, the function returns without effect — there is no master to use for identifying siblings.
3. **Iterates all actors in the current map** using a global thinker iterator.
4. **Identifies siblings** by checking if `mo->master == self->master` and `mo != self` (the actor's master pointer equals the calling actor's master pointer, and the actor is not the caller itself).
5. **Attempts to resurrect each sibling** by calling `P_Thing_Raise(mo)`, which:
   - Finds the sibling's `Raise` state (the entry point for resurrection animation).
   - Restores the sibling's height and radius to their default values.
   - Checks if there is room for the resurrected actor at its current position using `P_CheckPosition`. If not enough room, the sibling remains dead and no further processing occurs for that actor.
   - Plays the "vile/raise" sound effect.
   - Calls `Revive()` to restore the actor to life.
   - Sets the actor to its `Raise` state.
6. **Continues iterating** through all remaining actors; multiple siblings can be resurrected in one call.

## Sibling relationship and scope

A sibling relationship is established when actors share the same `master` pointer. This typically happens via `A_SpawnItemEx(..., SXF_SETMASTER)` — this action sets the `master` pointer of the spawned actor to point back to the spawner. The `A_RaiseSiblings` action then uses that relationship to identify and resurrect victims: all actors whose `master` pointer matches the calling actor's `master` pointer (excluding the caller itself).

For example, if actor A spawns actors B, C, and D via `A_SpawnItemEx` with `SXF_SETMASTER`, all three of B, C, and D will have `master == A`. If B calls `A_RaiseSiblings`, it will resurrect C and D (sharing the same master, A) but not B itself.

**Important limitations:**

- **Master must be non-NULL:** If the calling actor has no master (master pointer is NULL), the function returns without effect.
- **Spawned with `A_SpawnProjectile` are not affected:** The `A_SpawnProjectile` action does not set the `master` pointer and was never designed to spawn creatures targeted by this action. Only use `A_SpawnItemEx` with the `SXF_SETMASTER` flag if you intend to later resurrect spawned actors via `A_RaiseSiblings`.

## Resurrection failure conditions

### No Raise state

If a sibling actor has no `Raise` state defined, `P_Thing_Raise` returns without effect and the sibling remains dead. This is not an error; it is a silent condition. Many actors do not define a `Raise` state and therefore cannot be resurrected.

### No room to raise

If the sibling's default height and radius would overlap another actor or solid geometry at its current position, `P_CheckPosition` fails and the resurrection is aborted. The sibling remains dead and at its current location. **This check is unconditional in Zandronum** — there is no parameter to skip it (unlike the ZDoom Wiki's `RF_NOCHECKPOSITION` flag, which does not exist in this fork).

## Network behavior

**Zandronum multiplayer:** This action is server-authoritative with an unconditional early exit for network clients. Unlike `A_KillSiblings` (which carries a special exception for `+CLIENTSIDEONLY` actors), `A_RaiseSiblings` is **always server-side only** — the comment in the source states "This is handled by the server."

- **Server side:** The iteration and resurrection calls proceed normally; affected clients receive state-change updates (resurrection animations) from the server via `SERVERCOMMANDS_SetThingState`.
- **Client side:** Clients never execute the resurrection logic, even if the actor is marked `+CLIENTSIDEONLY`. Clients receive the state-change via the server's broadcast command.

This differs from `A_KillSiblings`, which allows `+CLIENTSIDEONLY` actors to manage their own sibling relationships client-side.

## Zandronum difference from ZDoom Wiki

**The ZDoom Wiki describes a more complex version** with an optional `int flags` parameter supporting two flags:

- `RF_TRANSFERFRIENDLINESS` — described as making resurrected actors change their affiliation to match the caller's.
- `RF_NOCHECKPOSITION` — described as skipping the position-availability check.

**Neither parameter nor flag constants exist in Zandronum 3.2.1.** The Zandronum version is a no-argument action that always performs the position check and does not modify affiliations — it resurrects siblings as-is.

If you port DECORATE code from upstream ZDoom/GZDoom to Zandronum, do not attempt to pass flags to `A_RaiseSiblings`. Doing so will result in a "too many arguments" compile error, not a silent no-op.

Additionally, the wiki's claim that "the only function that sets the necessary information is `A_SpawnItemEx`" is outdated — `A_RearrangePointers` and `A_TransferPointer` can also assign the `master` pointer, establishing a sibling relationship post-spawn.

## Related functions

- **`A_RaiseMaster`** — resurrects the calling actor's own master instead of its siblings. Server-authoritative; no parameters.
- **`A_RaiseChildren`** — resurrects all actors with `master == self`. Server-authoritative; no parameters.
- **`A_SpawnItemEx`** — the typical way to spawn actors as siblings (with `SXF_SETMASTER` to establish the master relationship).
- **`A_RearrangePointers`** — reassigns the calling actor's pointers (target/master/tracer) to any actor or NULL; can establish or change a `master` relationship post-spawn.
- **`A_TransferPointer`** — transfers a pointer from one actor to another; can establish a sibling relationship between pre-existing actors.
- **`A_KillSiblings`** — destroys all sibling actors (damage = sibling health). Zandronum version takes only `damagetype` and carries a special network gate (allows `+CLIENTSIDEONLY` actors).
- **`A_DamageSiblings`** — damages all sibling actors by a fixed amount. Zandronum version takes `amount` and `damagetype`.
- **`A_RemoveSiblings`** — removes (without death animation) all sibling actors instead of resurrecting them.
