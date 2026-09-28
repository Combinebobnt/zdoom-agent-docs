# TeleportGroup

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `TeleportGroup` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=TeleportGroup&oldid=42518) + verified against the Zandronum source's `src/p_lnspec.cpp` and `src/p_teleport.cpp` (`EV_TeleportGroup`, `DoGroupForOne`, `P_Teleport`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special (index 77; dispatched as `LS_TeleportGroup`).

## Signature

```text
int TeleportGroup(int group_tid, int source_tid, int dest_tid, int movesource, int fog)
```

Action special with index 77.

## Parameters

- **`group_tid`** — The TID of actor(s) to teleport. If `0`, teleports the activator only.
- **`source_tid`** — TID of the source anchor point (the center of the group before teleport). Any actor with this TID is accepted as the source anchor; unlike `dest_tid`, the engine does not require it to be a `TeleportDest`-family actor, though placing a dedicated anchor there is the intended usage.
- **`dest_tid`** — TID of the destination anchor point (where the group center moves to). Must also be a `TeleportDest` or similar anchor actor.
- **`movesource`** — If nonzero, the source anchor actor itself also teleports to the destination anchor location. If `0`, only the group teleports.
- **`fog`** — If nonzero, teleport fog is spawned at source and destination. If `0`, no fog.

## Return Value

Returns `1` (true) if at least one actor was successfully teleported, or `0` (false) otherwise.

## Behavior

Teleports a group of actors while preserving their positions and facing angles relative to the anchors. For each actor in the group (`group_tid`), the offset from the source anchor is rotated by the angle difference between the destination anchor and the source anchor, then applied as an offset from the destination anchor. The group's formation is thus rotated to match the destination anchor's facing, not just translated. Each actor's own facing angle is rotated by that same difference.

**If source anchor does not exist:** The function falls back to behavior equivalent to `TeleportOther(group_tid, dest_tid, fog)` — each group member teleports directly to `dest_tid` without offset calculation.

**If destination anchor does not exist:** Returns `0` (false) and no teleportation occurs.

**If the destination anchor is a `TeleportDest2` actor:** each actor's z-coordinate is computed as an offset, preserving its height above (or below) the source anchor and adding that to the destination anchor's own z-coordinate. **Otherwise (a plain `TeleportDest` anchor):** `ONFLOORZ` is used instead, so each actor lands on the destination sector's floor rather than keeping its relative height.

**Velocity is preserved:** velocities are not adjusted; an actor retains its original velocity vector after teleportation.

## Engine-family divergence: velocity when `fog` is nonzero

On Zandronum, a teleport with `fog` nonzero also halts each non-missile actor's velocity (and, for a player, the player's own momentum); a missile instead keeps its speed but has its direction redirected, regardless of `fog`. `DoGroupForOne` passes `keepOrientation = !fog` into `P_Teleport`, whose default `haltVelocity` argument zeroes velocity when `keepOrientation` is false. UZDoom's `DoGroupForOne` always passes `TELF_KEEPORIENTATION` regardless of `fog`, so velocity is never halted there. The "Velocity is preserved" claim above holds unconditionally only on UZDoom; on Zandronum it holds only when `fog` is `0`.

## Notes

- The destination anchor must be a `TeleportDest`-family actor (or a subclass, e.g. `TeleportDest2`); the source anchor can be any actor with the matching TID, but is conventionally also a dedicated teleport destination actor.
- The relative-position preservation is useful for teleporting groups while maintaining formation, including the group's orientation relative to the anchors.
- When `movesource` is nonzero, the source anchor's angle is also synchronized to match the destination anchor's angle, and this move never spawns fog regardless of the `fog` argument.
