# `A_RemoveChildren` (remove spawned children)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_RemoveChildren` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RemoveChildren&oldid=46803) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4790-4804` and actor declaration (`wadsrc/static/actors/actor.txt:240`), with `P_RemoveThing` at `src/p_things.cpp:504-519` and `AActor::HideOrDestroyIfSafe` at `src/p_mobj.cpp:619-647` for the network behavior.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RemoveChildren)` in `src/thingdef/thingdef_codeptr.cpp` — callable from any actor's state table.

Removes actors spawned by the calling actor (those with `master` pointer set to the caller) from the game world, optionally filtering by health state. A companion to `A_KillChildren` and `A_RaiseChildren` for the master/children relationship system.

## Signature

```text
void A_RemoveChildren(bool removeall = false)
```

## Parameters

### `removeall` (bool, optional)

If `false` (the default), only removes dead children (those with `health <= 0`). If `true`, removes all children regardless of health state (both alive and dead).

## Behavior

When called, this action iterates through all actors in the thinker list and removes any actor where:
1. The actor's `master` pointer equals the calling actor
2. Either the actor is dead (`health <= 0`) OR `removeall` is true

Removal is performed via `P_RemoveThing`, which handles:
- Clearing actor-specific counters (kill/item/secret statistics)
- Network broadcasting to clients in multiplayer (server-side only)
- Safe hiding or destruction depending on map-reset requirements

## Zandronum-specific behavior

**Parameter count differs significantly from the ZDoom wiki.** The wiki describes an advanced version with optional `flags` (bitfield), `filter` (class name), and `species` parameters that **do not exist in Zandronum**. Attempting to pass any of these parameters will result in a **parse error** at compile time, since the DECORATE function signature declares only the `removeall` boolean.

- **No flag constants.** Constants like `RMVF_MISSILES`, `RMVF_NOMONSTERS`, `RMVF_MISC`, `RMVF_EVERYTHING`, `RMVF_EXFILTER`, `RMVF_EXSPECIES`, and `RMVF_EITHER` are not defined in Zandronum and cannot be used.
- **No type discrimination.** Unlike the wiki's description ("can target non-monsters, but only by using flags"), Zandronum's version removes any actor with `master == self` regardless of type — the simple health check is the only filter. Missiles, monsters, and other actors are removed equally.
- **No class or species filtering.** All children matching the master/health criteria are removed; there is no way to selectively spare certain classes or species.

## Network behavior

In Zandronum multiplayer, `P_RemoveThing` broadcasts actor destruction to clients via `SERVERCOMMANDS_DestroyThing` when called on the server. Clients that receive that command destroy the actor too (`src/cl_main.cpp:5449-5468`).

Unlike `A_RaiseChildren`, which has an explicit `NETWORK_InClientMode()` guard, `A_RemoveChildren` has no client-mode check, and neither does `P_RemoveThing` (`src/p_things.cpp:504-519`). Its only network check gates the server-side broadcast. If this action runs on a client, the client still clears counters and removes the matching children locally, just without broadcasting. On a client the removal is always a plain `Destroy()`: the map-reset hide path in `HideOrDestroyIfSafe` requires not being in client mode (`src/p_mobj.cpp:619-647`). In practice this only reaches actors the client spawned itself: the protocol never sends `master`, so a server-spawned child's `master` is NULL on the client and matches nothing.

## Health vs. death state

The health check (`health <= 0`) is a direct numeric comparison, not a death-state check. An actor at `health == 0` but still in a visible or animated state will be removed if `removeall` is false. This is distinct from checking whether an actor is in its Death/XDeath state.

## Engine-family divergence: full wiki parameter set, type-gated removal, and no client/server split

UZDoom's `A_RemoveChildren` is **not** the stripped-down single-parameter version described above — it implements the full wiki-documented signature (`src/playsim/p_actionfunctions.cpp:4403-4422`, ZScript-side native declaration in `wadsrc/static/zscript/actors/actor.zs`):

```text
void A_RemoveChildren(bool removeall = false, int flags = 0, class<Actor> filter = null, name species = "None")
```

All of `RMVF_MISSILES`, `RMVF_NOMONSTERS`, `RMVF_MISC`, `RMVF_EVERYTHING`, `RMVF_EXFILTER`, `RMVF_EXSPECIES`, and `RMVF_EITHER` exist and behave as the wiki describes (defined alongside a shared `DoRemove` helper also used by `A_RemoveTarget`, `A_RemoveTracer`, and `A_RemoveMaster`). `filter` restricts removal to a specific actor class and `species` to a specific species name; `RMVF_EXFILTER`/`RMVF_EXSPECIES` invert those two checks individually, and `RMVF_EITHER` changes the two checks from AND to OR. Neither `removeall` nor the health check changes: a candidate still has to satisfy `mo->master == self && (mo->health <= 0 || removeall)` before `DoRemove` is even called.

**Removal is type-gated, and the default `flags = 0` only matches monsters.** Passing no flags at all is not "remove anything that matches the master/health check," as it is on Zandronum — `DoRemove` requires one of four type conditions to independently pass before it calls `P_RemoveThing`:

- `RMVF_EVERYTHING` set → always removes (subject to filter/species).
- `RMVF_MISC` set → removes anything that isn't a monster-flagged missile.
- Actor has `MF3_ISMONSTER` set **and** `RMVF_NOMONSTERS` is *not* set → removes it. This condition is active by default, since `flags = 0` never sets `RMVF_NOMONSTERS`.
- Actor has `MF_MISSILE` set **and** `RMVF_MISSILES` is set → removes it.

So `A_RemoveChildren(true)` called with every other parameter left at its default only removes children flagged as monsters; a non-monster, non-missile child (e.g. a plain decoration or pickup spawned with `SXF_SETMASTER`) survives unless the caller explicitly passes `RMVF_MISC` or `RMVF_EVERYTHING`. This is the opposite of the existing Zandronum-specific section's claim that "Zandronum's version removes any actor with `master == self` regardless of type" — that statement is Zandronum-only; it does not hold for UZDoom's default-flags call.

**No client/server split exists anywhere in UZDoom's source tree** — there is no `NETWORK_InClientMode()`-equivalent guard and no `SERVERCOMMANDS_DestroyThing`-equivalent broadcast. UZDoom's `P_RemoveThing` (`src/playsim/p_things.cpp:422-435`) just refuses to remove a live player's own body or a non-map actor (owned inventory), clears kill/item/secret counters, and calls `Destroy()` directly — no network role check, no server-authoritative/client-prediction distinction. The existing "Network behavior" section above describes a real Zandronum-only mechanism (the server-only `SERVERCOMMANDS_DestroyThing` broadcast inside `P_RemoveThing`) that has no UZDoom counterpart at all, not a differently-implemented version of the same mechanism.

## Related actions

- **`A_KillChildren`** — Kills all children (forces them into the Death state) regardless of current health, without removing them from the game world; often called after `A_RemoveChildren(false)` to kill the remaining living children.
- **`A_RaiseChildren`** — Raises all children (resurrects them if in a corpse state).
- **`A_RemoveMaster`** — Removes the calling actor's own master.
- **`A_RemoveSiblings`** — Removes all actors that share the calling actor's master (siblings, not including the caller itself).

## Example (Zandronum DECORATE)

A classic pattern: spawn children via a missile action, then remove dead spawns and kill living ones on death:

```text
ACTOR VoodooLeaderImp : DoomImp
{
    States
    {
    Missile:
        TROO G 6 A_SpawnItemEx("ChildImp", 50, 50, 60, 0, 0, 0, 0, SXF_SETMASTER)
        Goto See
    Death:
        TROO I 8 A_RemoveChildren(false)  // Remove corpses first
        TROO J 8 A_Scream
        TROO K 6 A_KillChildren            // Kill the living spawns
        TROO L 6 A_NoBlocking
        TROO M -1
        Stop
    }
}
```

(Note: The wiki's example uses `A_RaiseChildren` in a Pain state, which is not shown here; the children/master system works the same in Zandronum as in the wiki's example, just without the advanced flag/filter parameters.)
