# Teleport

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** `Teleport - ZDoom Wiki` (oldid=52693), verified 2026-07-29 against the Zandronum source (`p_lnspec.cpp` LS_Teleport, `p_teleport.cpp` EV_Teleport/SelectTeleDest/P_Teleport)
**Bucket:** Action special, index 70

## Signature

```c
Teleport(int tid, int tag, int nosourcefog)
```

## Parameters

- `tid` — Thing ID of a `TeleportDest` destination actor. If non-zero, a destination with this TID is selected at random from all matching destinations. If zero, `tag` must be non-zero (see below).
- `tag` — Sector tag. If `tid` is non-zero, limits the random selection to destinations in sectors with this tag. If `tid` is zero and `tag` is non-zero, uses the first `TeleportDest` found in the first sector with that tag (Doom legacy behavior). If both are zero, the function fails.
- `nosourcefog` — If non-zero, suppresses the fog effect at the **source** location only; the **destination** fog always spawns. The `nosourcefog` parameter is inverted: `nosourcefog=1` disables source fog, `nosourcefog=0` (or omitted) enables it.

## Return Value

`true` if the activator was successfully teleported; `false` if the teleport failed (no valid destination, destination blocked, activator missing, etc.). **All failure reasons collapse into a single `false` return** — there is no way to distinguish a missing destination from a blocked one.

## Behavior

The activator is moved to a destination `TeleportDest` actor selected as follows (per `SelectTeleDest` in the engine):

1. If `tid != 0`: randomly pick from all `TeleportDest` actors with that TID, optionally filtered by `tag` if non-zero.
2. If `tid == 0` and `tag != 0`: use the **first** `TeleportDest` found in the **first** sector matching `tag`.
3. If both `tid` and `tag` are zero: **fails and returns `false`**.

### Destination Z Coordinate

**The destination actor's Z coordinate is ignored for normal Teleport calls.** Instead, the activator is placed at the **floor level** of the destination sector (`ONFLOORZ`), except:

- If the destination is a `TeleportDest2` actor (not a plain `TeleportDest`), the destination's own Z coordinate is used.
- Missiles and floating players (with `MF_NOGRAVITY`) may adjust relative to their height above the destination floor to avoid crushing, but the base reference is still the destination's floor, not the spot's Z.

This is a **significant fork divergence from intuition**: mapping a `TeleportDest` at height 256 does not mean activators teleport to Z=256; they teleport to the floor of the sector the spot is in. Use a `TeleportDest2` if you need to preserve height.

### Angle and Velocity

- The activator's angle is set to match the destination's angle.
- The activator's velocity is **halted** (zeroed). Players are frozen for approximately 0.5 seconds (reaction time set to 18 tics).
- Missiles are exempt: their velocity is reoriented to the new angle, preserving speed.

### Fog Effects

- **Destination fog** always spawns (the classic "teleport flash"). Its position is offset slightly from the destination based on the destination angle.
- **Source fog** spawns at the original location unless `nosourcefog=1` (or equivalently, the parameter can be omitted to default to 0, spawning source fog).
- **Exception:** Spectators (in Zandronum) never spawn teleport fog, even if the parameters would otherwise call for it.

The fog is always an `ATeleportFog` actor, positioned at the terrain's height plus an offset (`TELEFOGHEIGHT` for actors, 0 for missiles).

### Failure Conditions

The function returns `false` without moving the activator if any of the following occur:

- **No activator:** called from an `OPEN` script or other context with no activator (`thing == NULL`). **This is indistinguishable from other failures to the caller.**
- **`MF2_NOTELEPORT` flag:** the activator has the `MF2_NOTELEPORT` flag set, preventing teleportation (not mentioned in the ZDoom wiki). This is a per-actor property set in DECORATE.
- **No matching destination:** no `TeleportDest`/`TeleportDest2` actor matches the requested TID and tag combination. Fallback logic checks `MapSpot` actors and then any non-solid actor, but if none exist, returns `false`.
- **Destination blocked:** the destination's position is solid geometry (walls, closed doors, etc.) and the teleport would overlap the activator. The `P_TeleportMove` placement check fails, returning `false`. **This is also indistinguishable from a missing destination.**

## Zandronum Netcode (Server-Side)

If called server-side, the teleport is replicated to all clients via `SERVERCOMMANDS_TeleportThing`, passing the fog and halt-velocity flags. The server also adjusts the client-side reaction-time (frozen-frame effect) to compensate for network latency. This is a **Zandronum addition not covered by the ZDoom wiki.**

## Known Divergence from ZDoom Wiki

The ZDoom wiki mentions a ZScript alias `TeleportSpecial`, added upstream to resolve a name conflict with a ZScript actor function. **This fork has no ZScript, so `TeleportSpecial` does not exist** — call `Teleport` only. The alias is a ZDoom-only feature.

## See Also

- [Teleport_NoFog](teleport_nofog.md) — variant that suppresses destination fog.
- [TeleportOther](teleportother.md) — teleports a third-party actor instead of the activator.
- [TeleportGroup](teleportgroup.md) — teleports all actors with a given TID.
- [Teleport_NoStop](teleport_nostop.md) — variant with different velocity handling.
- `TeleportDest` / `TeleportDest2` — DECORATE classes that mark valid teleport destinations (required).
