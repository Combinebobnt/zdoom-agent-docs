# `int Thing_Remove(int tid)`

Removes or hides one or more actors from the level. Action special (positive index 132 in `zcommon.bcs`'s `special` table), semantics in the Zandronum source's `src/p_lnspec.cpp`, `FUNC(LS_Thing_Remove)` (line 1310), implementation in the Zandronum source's `src/p_things.cpp`, `P_RemoveThing()` (line 504), dispatch entry `p_lnspec.cpp:3732`.

**Bucket:** action special.

## Behavior

- `tid` — thing ID. `0` means "the activator" (`it`, the actor that triggered the script/special); non-zero means "every actor currently holding this TID" (via `FActorIterator`, so more than one actor can be removed by a single call if `tid` is shared).
- Iterates through matching actors and calls `P_RemoveThing()` on each. The iterator uses `temp = iterator.Next()` *before* calling `P_RemoveThing()` on the actor, ensuring all actors with the matching TID are removed even if the iteration is invalidated by removal mid-loop.
- **Zandronum-specific hide-vs-destroy fork divergence:** `P_RemoveThing()` doesn't always destroy. It calls `HideOrDestroyIfSafe()` which checks: if the current game mode has the `GMF_MAPRESETS` flag enabled (map rotations with resets) **and** the actor is level-spawned (`STFL_LEVELSPAWNED`) **and** not running in client mode (`!NETWORK_InClientMode()`), the actor is instead hidden:
  - Sets `MF2_DORMANT` (spawners stop working), `MF_NOSECTOR`, `MF_NOBLOCKMAP` flags
  - Sets state to `"HideIndefinitely"`
  - Marks with `STFL_HIDDEN_INSTEAD_OF_DESTROYED`
  - **Critical difference:** a hidden actor keeps its TID and remains in the engine's `TIDHash`, so subsequent `FActorIterator` lookups (e.g., another `Thing_Remove(tid)`, `IsTidUsed(tid)`, `SetActivator(tid)`) still find it.
- **Can't remove live players.** `P_RemoveThing()` guards on `!(actor->player == NULL || actor != actor->player->mo)` — an actor with a `player` pointer that *is* that player's current body (`actor->player->mo`) is not removed. An actor with a `player` pointer that *isn't* the current body (a corpse or voodoo doll) *will* be removed; the guard only protects live player bodies.
- **Always returns `true`/`1`, regardless of whether anything was actually changed** — both the `tid == 0` branch (even if `it == NULL`, i.e., no activator to remove) and the `tid != 0` branch (even if `FActorIterator` finds zero matching actors, or all matches are live player bodies that `P_RemoveThing()` skips) fall through to an unconditional `return true;` at the end of the function (`p_lnspec.cpp:1332`). The wiki doesn't mention a return value; don't rely on this special's return to detect "did anything get removed" — check `IsTidUsed(tid)` afterward if that matters (but note that a hidden actor still counts as "used").
- **Network server sync:** on a network server (`NETWORK_GetState() == NETSTATE_SERVER`), `P_RemoveThing()` calls `SERVERCOMMANDS_DestroyThing(actor)` (`p_lnspec.cpp:1311`) to push the destruction to clients. This call silently no-ops if the actor doesn't have a net ID yet (`EnsureActorHasNetID`, `sv_commands.cpp:1732-1733`), a case that shouldn't arise for a normal, already-spawned actor.
- **No explicit CLIENTSIDE guard.** `LS_Thing_Remove` doesn't check `NETWORK_InClientMode()`, so it can be called from a `CLIENTSIDE` script — but such a call won't be networked back, and the client sees only its own local removal.

**Example — tag and remove all enemies matching a specific tag:**

```
script "Clear_Tagged_Enemies" (int tag)
{
    Thing_Remove(tag);
    print(s:"\cgCleared tagged enemies");
}
```

**Provenance:** wiki page `Thing_Remove - ZDoom Wiki.html` (`zdoom.org`, retrieved 2026-07-29, oldid=35880) is essentially content-free — one parameter line, one sentence of behavior, one example — so this doc is almost entirely source-verified. The wiki's description "Removes the specified thing from the map" is vague and doesn't distinguish removal from hiding; the tid semantics and unconditional-return behavior are source-derived, not wiki-confirmed. Zandronum's `HideOrDestroyIfSafe()` is a `[BB]` (Blzut3) fork addition not in upstream ZDoom — the hide behavior doesn't exist in base ACS. The network server sync and CLIENTSIDE-callability are also source-verified additions.

**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD, with `HideOrDestroyIfSafe()` behavior cross-checked in `p_mobj.cpp:619-648` and `p_things.cpp:504-519`). **Tier:** A.
