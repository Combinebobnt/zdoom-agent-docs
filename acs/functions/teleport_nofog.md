# Teleport_NoFog

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki (Teleport_NoFog, rev 44998), verified against Zandronum source (p_teleport.cpp, p_lnspec.cpp)

## Signature

```
Teleport_NoFog(int tid, int useangle, int tag, int keepheight)
```

## Parameters

- `tid` — Thing ID of a TeleportDest or other valid destination actor. The teleport will pick a random destination from all actors with this TID, optionally restricted to a specific sector tag.

- `useangle` — Controls how the destination actor's angle is applied to the teleported thing. **This parameter is a boolean in practice; see "Fork divergence" below.**
  - **0** (Hexen-compatible): Do not change the thing's angle or velocity.
  - **Non-zero** (Strife-compatible): Use the destination actor's angle, and zero the thing's velocity. Modes 2 and 3 (described in wiki sources as "Boom-compatible" variants) **are not distinguished in this fork** — they silently behave identically to mode 1.

- `tag` — Destination sector tag. If non-zero, teleport destinations are limited to TeleportDest actors in sectors with this tag. If `tid` is 0 and `tag` is non-zero, uses the first TeleportDest found in the first matching sector (old Doom behavior).

- `keepheight` — If set (non-zero), the teleported thing maintains its height relative to the floor of the destination sector. If 0, the thing lands on the floor (or maintains its z-offset if it's a missile or has `MF_NOGRAVITY`).

## Return

Returns `true` if teleport succeeds, `false` if:
- No destination actor with the matching `tid` (and optional sector `tag`) exists
- The destination actor exists but is NULL or invalid
- The thing being teleported has the `MF2_NOTELEPORT` flag set
- The teleport was triggered from the back side of a line (only relevant for linedef activation, not ACS calls)
- The destination position is blocked by geometry

## Behavior

Teleports the activating thing to a TeleportDest actor's location **without fog at either the source or destination** (the main difference from the fog-generating `Teleport` action special).

The thing's height in the destination is determined by:
- If `keepheight` is set: same height above the floor as at the origin
- If `keepheight` is 0 and the thing is a player: lands on the floor
- If `keepheight` is 0 and the thing is a missile: lands at the same height relative to floor as before

Velocity handling (when `useangle` is non-zero): both linear and bobbing velocity are zeroed. This differs from some wiki descriptions that suggest velocity preservation.

## Fork divergence: ZDoom → Zandronum

The ZDoom wiki describes four distinct angle-handling modes for the `useangle` parameter (0=Hexen, 1=Strife, 2=Boom-with-bug, 3=Boom-fixed). **In Zandronum 3.2.1, only a binary distinction exists:** `useangle=0` preserves the thing's angle and velocity; any non-zero `useangle` applies the destination's angle and zeros velocity. Modes 2 and 3 are not supported as separate behaviors — a map author using `useangle=2` or `useangle=3` gets Strife behavior (mode 1), silently.

This affects map conversions: Boom linedef types 207–210 (Teleport Preserve Direction) are documented as converting to `Teleport_NoFog(0, 2, tag, 1)`, which in Zandronum behaves as `Teleport_NoFog(0, 1, tag, 1)` — the relative-angle adjustment is lost.

## See also

- `Teleport` (action special 70) — identical except fog is generated at both source and destination
- `TeleportOther`, `TeleportGroup` (extension functions) — teleport other actors or groups
