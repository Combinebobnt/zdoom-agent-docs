# `A_RemoveSiblings` (remove sibling actors)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_RemoveSiblings` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RemoveSiblings&oldid=46799) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4811-4828` and actor declaration (`wadsrc/static/actors/actor.txt:241`); network and removal behavior from `src/p_things.cpp:504-519` and `src/p_mobj.cpp:619-647`; `SXF_SETMASTER` rules from `src/thingdef/thingdef_codeptr.cpp:2415-2456`.
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

Zandronum performs removal via `P_RemoveThing` (UZDoom's version is covered further down), which:
- Skips any actor that is a player's current body (`player->mo`); voodoo dolls are not spared
- Broadcasts the removal to clients (server only)
- Clears kill/item/secret counters
- Hides rather than destroys the actor only when all of these hold: the game mode resets the map, the actor was spawned with the level, and this is not a client. Anything else, including actors spawned at runtime by `A_SpawnItemEx`, is destroyed outright

## Zandronum-specific behavior

**Parameter count differs significantly from the ZDoom wiki.** The wiki describes an advanced version with optional `flags` (bitfield), `filter` (class name), and `species` parameters that **do not exist in Zandronum**. Passing a second argument is a fatal DECORATE **parse error** at load time: after the single `removeall` argument the state parser requires a closing `)` (`src/thingdef/thingdef_states.cpp:430`).

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

In Zandronum multiplayer, when `P_RemoveThing` runs on the server it broadcasts each removal to clients via `SERVERCOMMANDS_DestroyThing`, so clients receive the server's removals.

**Unlike `A_KillSiblings`, which returns early on clients (unless the caller is a client-side-only actor), `A_RemoveSiblings` has no network check.** `P_RemoveThing` has none either beyond making the broadcast server-only. A client that runs this state therefore removes the matching siblings locally as well: it skips the broadcast but still clears their counters and destroys them (on a client the map-reset hiding path never applies). In practice this only reaches actors the client spawned itself: the protocol never sends `master`, so on a client a server-spawned actor's `master` is NULL and the action returns at its `master != NULL` check. `A_DamageSiblings` is likewise ungated; `A_KillSiblings` and `A_RaiseSiblings` are the gated ones.

## Zandronum-specific: implicit network handling has no UZDoom equivalent

UZDoom's `A_RemoveSiblings` and the `DoRemove`/`P_RemoveThing` chain it calls (`src/playsim/p_actionfunctions.cpp:4426-4449`, `src/playsim/p_things.cpp:422-431`) carry no client/server authority check anywhere — no `NETWORK_InClientMode()` call, no `SERVERCOMMANDS_*` broadcast, and no such mechanism exists anywhere in the UZDoom source tree at all. `P_RemoveThing` only guards against removing a live player-controlled actor (`actor->player == NULL || actor != actor->player->mo`) and against removing a non-map actor (`!actor->IsMapActor()`), then clears kill/item/secret counters and calls `Destroy()` unconditionally. There is no equivalent to Zandronum's server-decides/clients-receive destruction broadcast, because UZDoom (a GZDoom-family fork) has no separate server/client process architecture at all — the server-broadcast framing this doc uses for Zandronum's `P_RemoveThing` doesn't apply on UZDoom; the same code path runs regardless of network state.

## Siblings and the master relationship

A sibling relationship is typically established via `A_SpawnItemEx(..., SXF_SETMASTER)`, which points the spawned actor's `master` back at the spawner. On UZDoom that flag applies to any spawned actor. On Zandronum it only takes effect when the spawned actor is a monster and the spawner (after walking up from a missile to its shooter) is also a monster; a spawned missile, decoration or pickup, or a monster spawned by a player, gets no master from it. `SXF_TRANSFERPOINTERS` instead copies the spawner's own `master` to the spawned actor, making it a sibling of the spawner, and works for non-monsters on both engines. The `A_RemoveSiblings` action then uses that relationship to identify victims: all actors whose `master` pointer matches the calling actor's `master` pointer, excluding the caller itself (enforced by the `mo != self` check in the iteration loop).

**Important limitations:**
- **Master must be non-NULL:** If the calling actor has no master (master pointer is NULL), the function returns without effect.
- **Spawned with `A_SpawnProjectile` (Zandronum: `A_CustomMissile`) are not affected:** that action does not set the `master` pointer and was never designed to spawn creatures targeted by this action. Only use `A_SpawnItemEx` with the `SXF_SETMASTER` flag if you intend to later destroy spawned actors via `A_RemoveSiblings`.

## Health vs. death state

The health check (`health <= 0`) is a direct numeric comparison, not a death-state check. An actor at `health == 0` but still in a visible or animated state will be removed if `removeall` is false. This is distinct from checking whether an actor is in its Death/XDeath state.

## Related actions

- **`A_KillSiblings`** — Kills all siblings by damaging each for its current health; often used in conjunction with `A_RemoveSiblings(false)` to remove corpses first, then kill the living siblings.
- **`A_RaiseSiblings`** — Raises all siblings (resurrects them if in a corpse state).
- **`A_RemoveChildren`** — Removes the caller's direct children (those with `master == self`), with the same dead-only filter unless `removeall` is true.
- **`A_RemoveMaster`** — Removes the calling actor's own master.

## Example (Zandronum DECORATE)

A common pattern: a summoner spawns minions with `SXF_SETMASTER`, and a dying minion clears its fellow minions' corpses and then kills the living ones. The call has to sit on the minion: the summoner itself has no master, so `A_RemoveSiblings` on it would do nothing. Both actors are monsters, which Zandronum requires for `SXF_SETMASTER` to set the master.

```text
ACTOR SummonerImp : DoomImp
{
    States
    {
    Missile:
        TROO EF 8 A_FaceTarget
        TROO G 6 A_SpawnItemEx("ImpMinion", 50, 50, 0, 0, 0, 0, 0, SXF_SETMASTER)
        Goto See
    }
}

ACTOR ImpMinion : DoomImp
{
    States
    {
    Death:
        TROO I 8 A_RemoveSiblings(false)  // Remove dead fellow minions first
        TROO J 8 A_Scream
        TROO K 6 A_KillSiblings           // Kill the living ones
        TROO L 6 A_NoBlocking
        TROO M -1
        Stop
    }
}
```

(Note: The wiki's example uses `A_DamageSiblings` and advanced flags, which are not shown here; the basic master/sibling relationship works the same in Zandronum as described in the wiki, just without the advanced flag/filter parameters.)
