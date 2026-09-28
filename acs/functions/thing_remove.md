# `int Thing_Remove(int tid)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `Thing_Remove - ZDoom Wiki.html` (`zdoom.org`, retrieved 2026-07-29, https://zdoom.org/w/index.php?title=Thing_Remove&oldid=35880) is essentially content-free — one parameter line, one sentence of behavior, one example — so this doc is almost entirely source-verified. The wiki's description "Removes the specified thing from the map" is vague and doesn't distinguish removal from hiding; the tid semantics and unconditional-return behavior are source-derived, not wiki-confirmed. Zandronum's `HideOrDestroyIfSafe()` is a `[BB]`-tagged fork addition not in upstream ZDoom — the hide behavior doesn't exist in base ACS. The network server sync and CLIENTSIDE-callability are also source-verified additions.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special.

Removes or hides one or more actors from the level. Action special (positive index 132 in `zcommon.bcs`'s `special` table), semantics in the Zandronum source's `src/p_lnspec.cpp`, `FUNC(LS_Thing_Remove)` (line 1310), implementation in the Zandronum source's `src/p_things.cpp`, `P_RemoveThing()` (line 504), dispatch entry `p_lnspec.cpp:3732`.

## Behavior

- `tid` — thing ID. `0` means "the activator" (`it`, the actor that triggered the script/special); non-zero means "every actor currently holding this TID" (via `FActorIterator`, so more than one actor can be removed by a single call if `tid` is shared).
- Iterates through matching actors and calls `P_RemoveThing()` on each. The iterator uses `temp = iterator.Next()` *before* calling `P_RemoveThing()` on the actor, ensuring all actors with the matching TID are removed even if the iteration is invalidated by removal mid-loop.
- **Zandronum-specific hide-vs-destroy fork divergence:** `P_RemoveThing()` doesn't always destroy. It calls `HideOrDestroyIfSafe()` (`src/p_mobj.cpp:619-648`) which checks: if the current game mode has the `GMF_MAPRESETS` flag enabled (map rotations with resets) **and** the actor is level-spawned (`STFL_LEVELSPAWNED`) **and** not running in client mode (`!NETWORK_InClientMode()`), the actor is instead hidden:
  - Unlinks it from the world, sets `MF2_DORMANT` (spawners stop working), `MF_NOSECTOR`, `MF_NOBLOCKMAP` flags and clears `MF_SOLID`
  - Sets state to `"HideIndefinitely"`
  - Marks with `STFL_HIDDEN_INSTEAD_OF_DESTROYED`
  - **Critical difference:** a hidden actor keeps its TID and remains in the engine's `TIDHash`, so subsequent `FActorIterator` lookups (e.g., another `Thing_Remove(tid)`, `IsTidUsed(tid)`, `SetActivator(tid)`) still find it. `ThingCount` is the exception: it skips actors carrying `STFL_HIDDEN_INSTEAD_OF_DESTROYED` (`src/p_acs.cpp:3931-3932`, `3957-3958`).
  - By default only Survival, Invasion, Duel, LastManStanding and TeamLMS set `MAPRESETS` (`wadsrc/static/gamemode.txt`); in the other modes the actor is always destroyed. A mod's own `GAMEMODE` lump can add or remove the flag (`src/gamemode.cpp:196-200`).
- **No death state runs.** Removal is not a kill: the actor never enters `Death`/`XDeath`, so any
  cleanup an actor does in its own death states never happens. The common casualty is a child
  spawned with `A_SpawnItemEx(..., SXF_SETMASTER)` that relies on its master's `A_KillChildren`:
  after the master is removed the child lives on with a null `master` (a DECORATE `AAPTR_MASTER`
  check on it finds nothing). Either `Thing_Destroy` the master instead, or have the child check
  `AAPTR_MASTER` itself and die when it's gone. Same on both engines (live-confirmed on Zandronum
  3.2.1, 2026-09-24). Two Zandronum caveats: `SXF_SETMASTER` only sets `master` there when spawner
  and child are both monsters (`src/thingdef/thingdef_codeptr.cpp:2439-2454`). In a map-reset mode
  (above) a level-spawned master is only hidden, so the child's `master` still points at it and an
  `AAPTR_MASTER` check still finds it.
- **Can't remove live players.** `P_RemoveThing()` guards on `!(actor->player == NULL || actor != actor->player->mo)` — an actor with a `player` pointer that *is* that player's current body (`actor->player->mo`) is not removed. An actor with a `player` pointer that *isn't* the current body (a corpse or voodoo doll) *will* be removed; the guard only protects live player bodies.
- **Always returns `true`/`1`, regardless of whether anything was actually changed** — both the `tid == 0` branch (even if `it == NULL`, i.e., no activator to remove) and the `tid != 0` branch (even if `FActorIterator` finds zero matching actors, or all matches are live player bodies that `P_RemoveThing()` skips) fall through to an unconditional `return true;` at the end of the function (`p_lnspec.cpp:1332`). The wiki doesn't mention a return value; don't rely on this special's return to detect "did anything get removed" — check `IsTidUsed(tid)` afterward if that matters (but note that a hidden actor still counts as "used").
- **Network server sync:** on a network server (`NETWORK_GetState() == NETSTATE_SERVER`), `P_RemoveThing()` calls `SERVERCOMMANDS_DestroyThing(actor)` (`p_things.cpp:510-511`) to push the destruction to clients. It sends this even when the server only hides the actor, and clients always `Destroy()` their copy (`cl_main.cpp:5449-5468`). Nothing is sent for an actor with no net ID (`EnsureActorHasNetID`, `sv_commands.cpp:1732-1733`); `NETFL_NONETID`/`NETFL_SERVERSIDEONLY` actors never get one. With `sv_showwarnings` on, that skip prints a warning unless the actor is `NETFL_SERVERSIDEONLY` (`sv_commands.cpp:99-112`).
- **No explicit CLIENTSIDE guard.** `LS_Thing_Remove` doesn't check `NETWORK_InClientMode()`, so it can be called from a `CLIENTSIDE` script — but such a call won't be networked back, and the client sees only its own local removal.

## Engine-family divergence

UZDoom's `LS_Thing_Remove` (`src/playsim/p_lnspec.cpp:1481`) and `P_RemoveThing()` (`src/playsim/p_things.cpp:422`) differ from Zandronum in three ways:

- **No hide-vs-destroy fork.** UZDoom's `P_RemoveThing()` has no `HideOrDestroyIfSafe()` equivalent — the map-reset hide path described above (`STFL_HIDDEN_INSTEAD_OF_DESTROYED`, `MF2_DORMANT`, etc.) doesn't exist in UZDoom at all. A removed actor is unconditionally `Destroy()`ed (subject to the live-player and owned-inventory guards below); it never keeps its TID or stays findable by a later `FActorIterator`/tid lookup the way a Zandronum hidden actor does.
- **Owned inventory items are protected from removal.** UZDoom's `P_RemoveThing()` additionally checks `actor->IsMapActor()` (`src/playsim/p_mobj.cpp:814`, comment `// [SP] Don't remove owned inventory objects`) — an inventory-kind actor with a non-null `Owner` is skipped entirely (silently; the special still returns `true`). Zandronum's `P_RemoveThing()` has no such check, so `Thing_Remove(tid)` targeting an inventory item some actor is currently holding destroys it on Zandronum but leaves it alone on UZDoom.
- **No explicit network sync call.** UZDoom's netcode has no `NETSTATE_SERVER`/`SERVERCOMMANDS_*` concept in this source tree at all (it isn't a client-server split the way Zandronum's is), so there's nothing analogous to Zandronum's `SERVERCOMMANDS_DestroyThing()` push — removal is just each peer's own simulation doing the same thing.

The live-player guard (`actor->player == NULL || actor != actor->player->mo`), the tid==0-means-activator / non-zero-means-iterate-every-matching-TID semantics, the "grab `temp` before removing" safe-iteration pattern, and the unconditional `return true;` regardless of whether anything was actually removed are all identical between the two engines.

**Example — tag and remove all enemies matching a specific tag:**

```text
script "Clear_Tagged_Enemies" (int tag)
{
    Thing_Remove(tag);
    print(s:"\cgCleared tagged enemies");
}
```
