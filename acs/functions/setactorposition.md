# `bool SetActorPosition(int tid, fixed x, fixed y, fixed z, bool fog)`

Directly repositions a single actor by TID, without going through normal thing-movement checks
(no Z-clip animation, no `Thing_Move`-style pathing). Compiler builtin (`PCD_SETACTORPOSITION`,
the Zandronum source's `src/p_acs.cpp:11987-11996`), implementation in `P_MoveThing`
(the Zandronum source's `src/p_things.cpp:164-218`).

**Bucket:** compiler builtin.

- `tid` — target actor's thing ID. **`0` means "the activator"** (`SingleActorFromTID`,
  `p_acs.cpp:4445-4456`) — same zero-means-activator convention documented for
  `GetActorProperty`. If `tid` doesn't resolve to any actor, the call is a no-op and returns
  `false` — matches the wiki's implication but the wiki never states the `tid=0` special case at
  all.
- `x`, `y`, `z` — destination coordinates, fixed-point map units, matching the wiki.
- `fog` — spawns a `TeleportFog` actor at **both** the old and new position (offset upward by
  `TELEFOGHEIGHT` on Z) when true and the move succeeds. **The wiki's one-line description
  ("with or without teleport fog") doesn't mention the fog spawns at both ends**, nor that no fog
  is spawned at all if the move is rejected (see below).

## Success/failure semantics — verified against source, and stricter than the wiki implies

The wiki says only "Returns true if the actor position was changed successfully, and false
otherwise," without saying what "successfully" checks. Reading `P_MoveThing`:

1. It saves the actor's old `x`/`y`/`z`, then unconditionally calls `source->SetOrigin(x, y, z)`
   — the actor is physically moved to the new spot *before* any validity check.
2. It then calls `P_TestMobjLocation` (`p_map.cpp:1640-1657`), which temporarily clears
   `MF_PICKUP` (so the position probe can't trigger an item pickup), runs `P_CheckPosition` at the
   new XY (blocking lines/actors), and additionally rejects the position if
   `z < floorz || z + height > ceilingz` at that XY.
3. **If the check passes:** the move is kept, `PrevX/PrevY/PrevZ` are updated (so no visual
   "run" interpolation glitch), the two fog actors are spawned if `fog` was true, and — a
   Zandronum-only detail absent from the ZDoom wiki entirely — if the server is authoritative it
   sends `SERVERCOMMANDS_MoveThing` to replicate the new position/flags to clients. Returns `true`.
4. **If the check fails:** it calls `source->SetOrigin(oldx, oldy, oldz)` to put the actor back
   where it started, spawns **no** fog, sends **no** network update, and returns `false`. Net
   effect: **a failed `SetActorPosition` leaves the actor exactly where it was**, not stranded at
   the rejected destination — but for one tick's worth of internal state the actor's blockmap/
   sector links were briefly at the new position and back, which matters only if something else
   observes the actor mid-call (nothing in this engine does, since ACS runs synchronously).

So `SetActorPosition` behaves like a strict "can this actor legally occupy this spot" test-and-move
— it silently refuses to move an actor into a wall, into another blocking actor, or into a Z range
that clips the floor/ceiling at the destination, rather than clamping or partially moving. This is
the same category of check `Thing_Move`/teleporters use, just without their fog/momentum-carry
extras.

**Zandronum-only nuance: "blocking actor" can exclude other players.** `P_CheckPosition`'s
actor-vs-actor blocking test consults `P_CheckUnblock` (`p_map.cpp:72-91`) before treating another
actor as solid, which returns true (i.e. "don't block, let them overlap") when **both** actors are
`APlayerPawn` and either `zadmflags & ZADF_UNBLOCK_PLAYERS` (`sv_unblockplayers`) is set, or
`ZADF_UNBLOCK_ALLIES` (`sv_unblockallies`) is set and the two are teammates. This only ever applies
player-vs-player — a monster, item, or any other non-`APlayerPawn` solid actor still blocks the
move (and still triggers the restore-on-failure above) regardless of either cvar. A server running
`sv_unblockplayers 1` (common in co-op-oriented mods so players can't wall each other into corners)
can therefore see `SetActorPosition` on a player fail intermittently — and revert silently, with no
teleport, no fog, no network message — specifically because a *monster* (not another player)
happens to occupy the destination at that instant, which is easy to misdiagnose as a
network/prediction bug rather than a genuine blocked-destination rejection.

**Example — move an actor to the activator's XY at a fixed Z, verified against destination:**

```
if (!SetActorPosition(monsterTid, GetActorX(0), GetActorY(0), GetActorZ(0), false))
{
    // move was rejected (blocked by geometry/actor, or bad Z at destination) —
    // monsterTid is still at its original position, not at the requested one.
}
```

**Provenance:** wiki page `SetActorPosition - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=40289`) + source-verified against `p_acs.cpp:11987-11996`, `p_things.cpp:164-218`,
`p_map.cpp:1640-1657`, `p_acs.cpp:4445-4456` (`SingleActorFromTID`). No wiki/fork behavioral
divergence found beyond the wiki simply omitting detail (fog-at-both-ends, restore-on-failure,
Zandronum netcode replication) that source-reading filled in.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
