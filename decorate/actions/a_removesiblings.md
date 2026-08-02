# `A_RemoveSiblings` (remove sibling actors)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_RemoveSiblings` (retrieved 2026-08-01, oldid=46799) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4811-4828` and actor declaration (`wadsrc/static/actors/actor.txt:242`).
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RemoveSiblings)` in `src/thingdef/thingdef_codeptr.cpp` — callable from any actor's state table.

Removes actors that share the calling actor's master (siblings) from the game world, optionally filtering by health state. A companion to `A_KillSiblings` and `A_RaiseSiblings` for the master/children/siblings relationship system.

## Signature

```
void A_RemoveSiblings(bool removeall = false)
```

## Parameters

### `removeall` (bool, optional)

If `false` (the default), only removes dead siblings (those with `health <= 0`). If `true`, removes all siblings regardless of health state (both alive and dead).

## Behavior

When called, this action iterates through all actors in the thinker list and removes any actor where:
1. The actor's `master` pointer equals the calling actor's `master` pointer
2. The actor is not the calling actor itself (`mo != self`)
3. Either the actor is dead (`health <= 0`) OR `removeall` is true

Removal is performed via `P_RemoveThing`, which handles:
- Clearing actor-specific counters (kill/item/secret statistics)
- Network broadcasting to clients in multiplayer (server-side only)
- Safe hiding or destruction depending on map-reset requirements

## Zandronum-specific behavior

**Parameter count differs significantly from the ZDoom wiki.** The wiki describes an advanced version with optional `flags` (bitfield), `filter` (class name), and `species` parameters that **do not exist in Zandronum**. Attempting to pass any of these parameters will result in a **parse error** at compile time, since the DECORATE function signature declares only the `removeall` boolean.

- **No flag constants.** Constants like `RMVF_MISSILES`, `RMVF_NOMONSTERS`, `RMVF_MISC`, `RMVF_EVERYTHING`, `RMVF_EXFILTER`, `RMVF_EXSPECIES`, and `RMVF_EITHER` are not defined in Zandronum and cannot be used.
- **No type discrimination.** Unlike the wiki's description ("can target non-monsters, but only by using flags"), Zandronum's version removes any sibling with `master == self->master` regardless of type — the simple health check is the only filter. Missiles, monsters, and other actors are removed equally.
- **No class or species filtering.** All siblings matching the master/health criteria are removed; there is no way to selectively spare certain classes or species.

## Network behavior

In Zandronum multiplayer, `P_RemoveThing` broadcasts actor destruction to clients via `SERVERCOMMANDS_DestroyThing` when called on the server. The removal is **server-authoritative** — the server decides which actors to remove, and clients receive the destruction command.

**Unlike `A_KillSiblings`, which has an explicit `NETWORK_InClientMode()` guard, `A_RemoveSiblings` carries no explicit network check.** The netcode handling is implicit in `P_RemoveThing`. On clients, the action executes but has no effect since `P_RemoveThing` checks the network state internally.

This absence of an explicit gate is in contrast to the Kill/Raise/Damage sibling variants. The asymmetry appears to be intentional in Zandronum's design — removal of spawned entities may not require the same server-side-only enforcement as state-changing actions like Kill or Raise.

## Siblings and the master relationship

A sibling relationship is typically established via `A_SpawnItemEx(..., SXF_SETMASTER)` — this action sets the `master` pointer of the spawned actor to point back to the spawner. The `A_RemoveSiblings` action then uses that relationship to identify victims: all actors whose `master` pointer matches the calling actor's `master` pointer, excluding the caller itself (enforced by the `mo != self` check in the iteration loop).

**Important limitations:**
- **Master must be non-NULL:** If the calling actor has no master (master pointer is NULL), the function returns without effect.
- **Spawned with `A_SpawnProjectile` are not affected:** The `A_SpawnProjectile` action does not set the `master` pointer and was never designed to spawn creatures targeted by this action. Only use `A_SpawnItemEx` with the `SXF_SETMASTER` flag if you intend to later destroy spawned actors via `A_RemoveSiblings`.

## Health vs. death state

The health check (`health <= 0`) is a direct numeric comparison, not a death-state check. An actor at `health == 0` but still in a visible or animated state will be removed if `removeall` is false. This is distinct from checking whether an actor is in its Death/XDeath state.

## Related actions

- **`A_KillSiblings`** — Kills all siblings (forces them into the Death state) regardless of current health; often used in conjunction with `A_RemoveSiblings(false)` to remove corpses first, then kill the living siblings.
- **`A_RaiseSiblings`** — Raises all siblings (resurrects them if in a corpse state).
- **`A_RemoveChildren`** — Removes all actors that are direct children of the caller (those with `master == self`).
- **`A_RemoveMaster`** — Removes the calling actor's own master.

## Example (Zandronum DECORATE)

A common pattern: spawn multiple clones via a missile action, then remove dead ones and kill the living on death:

```
ACTOR SoldierImp : DoomImp
{
    Missile:
        TROO G 6 A_SpawnItemEx("SoldierImp", 50, 50, 60, 0, 0, 0, 0, SXF_SETMASTER)
        Goto See
    Death:
        TROO I 8 A_RemoveSiblings(false)  // Remove dead clones first
        TROO J 8 A_Scream
        TROO K 6 A_KillSiblings           // Kill the living clones
        TROO L 6 A_NoBlocking
        TROO M -1
        Stop
}
```

(Note: The wiki's example uses `A_DamageSiblings` and advanced flags, which are not shown here; the basic master/sibling relationship works the same in Zandronum as described in the wiki, just without the advanced flag/filter parameters.)
