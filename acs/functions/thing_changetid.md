# `int Thing_ChangeTid(int oldtid, int newtid)`

Changes the TID of one or more actors. Action special (positive index 176 in `zcommon.bcs`'s
`special` table), semantics in the Zandronum source's `src/p_lnspec.cpp`, `FUNC(LS_Thing_ChangeTID)`
(line 1081).

**Bucket:** action special.

- `oldtid` — `0` means "the activator" (`it`, the actor that triggered the script/special);
  non-zero means "every actor currently holding this TID" (via `FActorIterator`, so more than one
  actor can be retagged by a single call if `oldtid` is shared).
- `newtid` — the TID to assign. `0` is valid and means "no TID" (matches the rest of the engine's
  TID-zero convention, e.g. `ActivatorTID()`/`IsTidUsed`).
- **Always returns `true`/`1`, regardless of whether anything was actually changed** — both the
  `oldtid == 0` branch (even if `it == NULL`, i.e. no activator) and the `oldtid != 0` branch (even
  if `FActorIterator` finds zero matching actors) fall through to an unconditional `return true;`
  at the end of the function (`p_lnspec.cpp:1120`). The wiki doesn't mention a return value at
  all; don't rely on this special's return to detect "did anything match `oldtid`" — check
  `IsTidUsed(newtid)` afterward instead if that matters.
- **Skips actors already marked for destruction.** Both branches guard on
  `!(actor->ObjectFlags & OF_EuthanizeMe)` (`p_lnspec.cpp:1086`, `:1108`) — an actor mid-destruction
  in the same tic (`OF_EuthanizeMe`, "Object wants to die", `dobject.h:214`) is silently skipped
  and keeps its old TID. Narrow edge case, but relevant if this is ever called from a `DEATH`
  script racing against the actor's own destruction.
- **Zandronum-specific netcode addition not in the ZDoom wiki source:** on a network server
  (`NETWORK_GetState() == NETSTATE_SERVER`), every successful retag calls
  `SERVERCOMMANDS_SetThingTID(actor)` (`p_lnspec.cpp:1093-1094`, `:1114-1116`) to push the new TID
  to clients (`sv_commands.cpp:2044-2053`). This is automatic — callers don't need to do anything
  extra for the TID change to be visible clientside — except that
  `SERVERCOMMANDS_SetThingTID` silently no-ops if the actor doesn't have a net ID yet
  (`EnsureActorHasNetID` fails, `sv_commands.cpp:2046-2047`), a case that shouldn't arise for a
  normal, already-spawned actor.

**Example — tag the activating player with a TID derived from player number (the wiki's
canonical use case):**

```
script "Tag_Player" ENTER
{
    Thing_ChangeTID(0, 1337 + PlayerNumber());
}
```

For multiplayer, the wiki stresses resetting a player's TID to `0` in `DEATH`/`RESPAWN` before
re-tagging on the next `RESPAWN`/`ENTER` — otherwise a corpse and its respawned player can end up
sharing the same TID, since `Thing_ChangeTID` never checks for a collision before assigning
`newtid`.

**Returns:** `int` per the declared signature, but see above — this special always returns `1`
in practice; it is not a reliable success/failure signal.

**Provenance:** wiki page `Thing_ChangeTID - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=43784`) + source-verified against the Zandronum source (`p_lnspec.cpp:1081-1121`,
`sv_commands.cpp:2044-2053`, `dobject.h:214`) and `zt-bcc/lib/zcommon.bcs:1515`. The wiki's
`oldtid`/`newtid` semantics and multiplayer TID-collision warning both hold exactly against this
fork's source; the always-`true` return value, the `OF_EuthanizeMe` skip, and the
`SERVERCOMMANDS_SetThingTID` client-sync call are this doc's source-verified additions, not
mentioned on the ZDoom wiki page (unsurprising for the netcode sync, since that's a
Zandronum-only addition — see `[BB]` comment at `p_lnspec.cpp:1092` — that doesn't exist in
upstream ZDoom at all).
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
