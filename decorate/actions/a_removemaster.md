# `A_RemoveMaster` (remove spawned master)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_RemoveMaster` (retrieved 2026-08-01, oldid=46797) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4777-4783` and actor declaration (`wadsrc/static/actors/actor.txt:239`).
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_RemoveMaster)` in `src/thingdef/thingdef_codeptr.cpp` — callable from any actor's state table.

Removes the calling actor's master (the actor that spawned it) from the game world. A companion to `A_RemoveChildren`, `A_RemoveSiblings`, and `A_KillMaster` for the master/children relationship system.

## Signature

```
void A_RemoveMaster()
```

## Behavior

When called, this action:
1. Checks if the calling actor has a non-NULL `master` pointer
2. If true, removes the master actor by calling `P_RemoveThing`

Removal is performed via `P_RemoveThing`, which handles:
- Clearing actor-specific counters (kill/item/secret statistics)
- Network broadcasting to clients in multiplayer (server-side only)
- Safe hiding or destruction depending on map-reset requirements

## Zandronum-specific behavior

**No parameters exist.** The ZDoom wiki describes an advanced version with optional `flags` (bitfield), `filter` (class name), and `species` parameters that **do not exist in Zandronum**. The Zandronum implementation is a simple no-argument function that unconditionally removes the master actor if it exists.

- **No flag constants.** Constants like `RMVF_MISSILES`, `RMVF_NOMONSTERS`, `RMVF_MISC`, `RMVF_EVERYTHING`, `RMVF_EXFILTER`, `RMVF_EXSPECIES`, and `RMVF_EITHER` are not defined in Zandronum and cannot be used.
- **No type discrimination.** Unlike the wiki's description, Zandronum's version removes the master actor unconditionally, regardless of type — missiles, monsters, and other actors are removed equally. There is no filter mechanism.
- **No class or species filtering.** The master actor is always removed if it exists; there is no way to selectively spare certain classes or species.

## Network behavior

In Zandronum multiplayer, `P_RemoveThing` broadcasts actor destruction to clients via `SERVERCOMMANDS_DestroyThing` when called on the server. The removal is **server-authoritative** — the server decides which master actors to remove, and clients receive the destruction command.

On clients, the action executes but has no effect since `P_RemoveThing` checks the network state internally.

## NULL master check

The function safely checks whether `master != NULL` before attempting removal. Calling `A_RemoveMaster` on an actor with no master (common case) is harmless and has no effect.

## Related actions

- **`A_KillMaster`** — Kills the calling actor's master (forces it into the Death state) without removing it from the game world.
- **`A_DamageMaster`** — Damages the calling actor's master by a specified amount.
- **`A_RemoveChildren`** — Removes actors spawned by the calling actor (its children).
- **`A_RemoveSiblings`** — Removes all actors that share the calling actor's master (siblings, not including the caller itself).

## Example (Zandronum DECORATE)

A spawned imp that removes its spawner when killed:

```
ACTOR SpawnedImp : DoomImp
{
    Death:
        TROO I 8 A_RemoveMaster    // Remove the spawner
        TROO J 8 A_Scream
        TROO K 6 A_NoBlocking
        TROO L 6
        TROO M -1
        Stop
}

ACTOR SpawnerDemon : BaronOfHell
{
    Missile:
        BOSS G 6 A_SpawnItemEx("SpawnedImp", 50, 50, 60, 0, 0, 0, 0, SXF_SETMASTER)
        Goto See
}
```

In this example, if a `SpawnedImp` dies, its Death state removes the `SpawnerDemon` that created it.
