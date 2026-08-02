# TeleportGroup

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki (verified against Zandronum fork implementation)

## Signature

```
int TeleportGroup(int group_tid, int source_tid, int dest_tid, int movesource, int fog)
```

Action special with index 77.

## Parameters

- **`group_tid`** — The TID of actor(s) to teleport. If `0`, teleports the activator only.
- **`source_tid`** — TID of the source anchor point (the center of the group before teleport). Must be a `TeleportDest` or similar anchor actor.
- **`dest_tid`** — TID of the destination anchor point (where the group center moves to). Must also be a `TeleportDest` or similar anchor actor.
- **`movesource`** — If nonzero, the source anchor actor itself also teleports to the destination anchor location. If `0`, only the group teleports.
- **`fog`** — If nonzero, teleport fog is spawned at source and destination. If `0`, no fog.

## Return Value

Returns `1` (true) if at least one actor was successfully teleported, or `0` (false) otherwise.

## Behavior

Teleports a group of actors while preserving their relative positions. Each actor in the group (`group_tid`) is offset from the source anchor by its current position, then placed at the same offset from the destination anchor.

**If source anchor does not exist:** The function falls back to behavior equivalent to `TeleportOther(group_tid, dest_tid, fog)` — each group member teleports directly to `dest_tid` without offset calculation.

**If destination anchor does not exist:** Returns `0` (false) and no teleportation occurs.

**If the destination anchor is a `TeleportDest2` actor:** The destination floor height determines the z-coordinate. Otherwise, `ONFLOORZ` is used.

**Velocity is preserved:** Velocities are not adjusted; actors retain their original velocity vectors after teleportation.

## Notes

- Both source and destination anchors should be placed using dedicated teleport destination actors (`TeleportDest`, `TeleportDest2`).
- The relative-position preservation is useful for teleporting groups while maintaining formation.
- When `movesource` is nonzero, the source anchor's angle is also synchronized to match the destination anchor's angle.
