# `A_RemoveSiblings` (remove sibling actors)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_RemoveSiblings` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RemoveSiblings&oldid=46799) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4811-4828` and actor declaration (`wadsrc/static/actors/actor.txt:242`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RemoveSiblings)` in `src/thingdef/thingdef_codeptr.cpp` — callable from any actor's state table.

Removes actors that share the calling actor's master (siblings) from the game world, optionally filtering by health state. A companion to `A_KillSiblings` and `A_RaiseSiblings` for the master/children/siblings relationship system.

## Signature

```text
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

## Zandronum-specific: full wiki parameter set exists on UZDoom

**The ZDoom Wiki describes the GZDoom/UZDoom version**, and UZDoom's actual signature matches it exactly: `A_RemoveSiblings(bool removeall = false, int flags = 0, class<Actor> filter = null, name species = "None")` (native declaration at `wadsrc/static/zscript/actors/actor.zs:1409`, implementation at `src/playsim/p_actionfunctions.cpp:4426-4449`). All of the constructs the existing "Zandronum-specific behavior" section above says are missing are present and functional on UZDoom:

- **Flag constants work.** `RMVF_MISSILES`, `RMVF_NOMONSTERS`, `RMVF_MISC`, `RMVF_EVERYTHING`, `RMVF_EXFILTER`, `RMVF_EXSPECIES`, and `RMVF_EITHER` are all defined (`src/playsim/p_actionfunctions.cpp:4303-4312`) and consumed by the shared `DoRemove` helper.
- **Type discrimination works.** `DoRemove` checks `RMVF_EVERYTHING` (unconditional removal once the filter passes), `RMVF_MISC` (non-monster, non-missile actors), the monster case (removed unless `RMVF_NOMONSTERS` is set), and the missile case (`RMVF_MISSILES`) as separate conditions, so monsters, missiles, and misc actors can be selectively spared.
- **Class and species filtering work.** `filter` and `species` are resolved via the shared `DoCheckClass`/`DoCheckSpecies` helpers (`src/playsim/p_actionfunctions.cpp:3626-3638`); `RMVF_EXFILTER`/`RMVF_EXSPECIES` invert a match, and `RMVF_EITHER` ORs the two checks together instead of ANDing them.

`A_RemoveSiblings` shares this `DoRemove` helper with `A_RemoveMaster`, `A_RemoveChildren`, `A_RemoveTarget`, and `A_RemoveTracer` — the same shared-helper pattern earlier waves found for `DoKill` (the Kill family) and `P_Thing_Raise` (the Raise family) carries over to the Remove family too. Wiki example code using `flags`/`filter`/`species` parameters, which fails to compile under Zandronum (see above), compiles and behaves as documented under UZDoom.

## Network behavior

In Zandronum multiplayer, `P_RemoveThing` broadcasts actor destruction to clients via `SERVERCOMMANDS_DestroyThing` when called on the server. The removal is **server-authoritative** — the server decides which actors to remove, and clients receive the destruction command.

**Unlike `A_KillSiblings`, which has an explicit `NETWORK_InClientMode()` guard, `A_RemoveSiblings` carries no explicit network check.** The netcode handling is implicit in `P_RemoveThing`. On clients, the action executes but has no effect since `P_RemoveThing` checks the network state internally.

This absence of an explicit gate is in contrast to the Kill/Raise/Damage sibling variants. The asymmetry appears to be intentional in Zandronum's design — removal of spawned entities may not require the same server-side-only enforcement as state-changing actions like Kill or Raise.

## Zandronum-specific: implicit network handling has no UZDoom equivalent

UZDoom's `A_RemoveSiblings` and the `DoRemove`/`P_RemoveThing` chain it calls (`src/playsim/p_actionfunctions.cpp:4426-4449`, `src/playsim/p_things.cpp:422-431`) carry no client/server authority check anywhere — no `NETWORK_InClientMode()` call, no `SERVERCOMMANDS_*` broadcast, and no such mechanism exists anywhere in the UZDoom source tree at all. `P_RemoveThing` only guards against removing a live player-controlled actor (`actor->player == NULL || actor != actor->player->mo`) and against removing a non-map actor (`!actor->IsMapActor()`), then clears kill/item/secret counters and calls `Destroy()` unconditionally. There is no equivalent to Zandronum's server-decides/clients-receive destruction broadcast, because UZDoom (a GZDoom-family fork) has no separate server/client process architecture at all — the "server-authoritative" framing this doc uses for Zandronum's `P_RemoveThing` doesn't apply on UZDoom; the same code path runs regardless of network state.

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

```text
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
