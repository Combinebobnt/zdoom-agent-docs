# `MapMarker`

**Tier:** A
**Engine:** Zandronum 3.2.1 (primary; verified `src/g_shared/a_sharedglobal.h`, `src/g_shared/a_mapmarker.cpp`, `src/am_map.cpp`); `args[2]` divergence cross-checked against UZDoom 4.15pre
**Provenance:** ZDoom Wiki Classes:MapMarker (retrieved 2026-08-01, oldid=52573) + verified against Zandronum source
**Bucket:** `src/g_shared/a_sharedglobal.h:185–192` (native C++ class `AMapMarker : public AActor`, implementation in `src/g_shared/a_mapmarker.cpp`); default DECORATE definition in `wadsrc/static/actors/shared/mapmarker.txt`.
**Source excerpt:** This file quotes Zandronum engine source verbatim (the `MapMarker` DECORATE definition, `wadsrc/static/actors/shared/mapmarker.txt`); reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

A built-in actor class representing an automap-only marker. MapMarker actors do not appear in the 3D view — they appear only on the automap with their sprite rendered at a specified location. Typical use is to mark points of interest, secret areas, or tracked actors for the player.

**Critical:** A MapMarker must have `BeginPlay()` called without interruption. The implementation calls `ChangeStatNum(STAT_MAPMARKER)` to register the marker with the automap renderer. If a subclass overrides `BeginPlay()` without chaining to the parent, the marker is silently never rendered — no error occurs, but the actor will be invisible on the automap.

## Placement and visibility control

MapMarker is **not** a pickup and should not be inherited from `Inventory`. It is placed in the world as a standalone actor, similar to `MapSpot`. After spawning, a MapMarker's visibility can be toggled:

- **`Activate(activator)`** — sets the `MF2_DORMANT` flag, which **hides** the marker from the automap (the automap render loop checks this flag and skips rendering if set).
- **`Deactivate(activator)`** — clears the `MF2_DORMANT` flag, which **shows** the marker on the automap.

In multiplayer, the server propagates these activation/deactivation calls to all clients via `SERVERCOMMANDS_ThingActivate`, so visibility is synchronized consistently. In ACS/BCS, use `Thing_Activate` / `Thing_Deactivate` to toggle visibility; in ZScript (UZDoom only), call the methods directly.

Note: The engine source at `a_mapmarker.cpp:47–48` contains a misleading comment ("To enable display of the sprite, activate it") that contradicts the code — the comment is reversed. The actual behavior (verified in the automap renderer at `am_map.cpp:2852–2855`) is that `Activate` hides and `Deactivate` shows the marker.

## Arguments and behavior

The actor's special arguments control marker behavior:

| Argument | Value | Behavior |
|----------|-------|----------|
| `args[0]` | 0 | Display the marker sprite at the MapMarker actor's own location. |
| `args[0]` | N (nonzero) | Display the marker sprite at the location of any actor with TID matching N. If multiple actors share that TID, the marker is drawn at each one's location. |
| `args[1]` | 0 (default) | Display the marker always, regardless of visibility state. |
| `args[1]` | 1 | Display the marker only after its (or the followed actor's, if `args[0]` is set) sector has been drawn on the automap — i.e., after the player has explored that area. For `args[0] != 0` (TID follow mode), this check is applied per-followed-actor. On Zandronum maps without GL nodes, this uses whole-sector `SECF_DRAWN`; with GL nodes, it uses per-subsector `SSECF_DRAWN` for finer granularity. |
| `args[2]` | (any) | **Zandronum only:** Ignored. Zandronum always draws the marker at constant scale. |

## Engine divergence: args[2] scaling

The ZDoom wiki mentions a third argument for automap-zoom scaling — "If the third argument is 1, the map marker scales relative to the automap zoom, rather than keep a constant scale." This feature exists in UZDoom/GZDoom but **does not exist in Zandronum** (version 3.2.1). Zandronum's automap renderer has no code path for `args[2]` and always draws markers at constant scale. A MapMarker subclass that sets `args[2] = 1` will compile and run on Zandronum without error, but the argument will be silently ignored.

## DECORATE definition

```
ACTOR MapMarker 9040 native
{
	+NOBLOCKMAP
	+NOGRAVITY
	+DONTSPLASH
	+INVISIBLE
	Scale 0.5
	States
	{
	Spawn:
		AMRK A -1
		Stop
	}
}
```

The doomednum `9040` allows placement in a map editor. The default scale is `0.5` (half-size). The actor carries no collision flags (`+NOBLOCKMAP`, `+NOGRAVITY`, `+DONTSPLASH`) and is invisible in the 3D view (`+INVISIBLE`); the only visual output is the automap sprite in frame A of the `AMRK` sprite, held indefinitely.

## Inheritance and customization

To create a custom map marker, inherit from `MapMarker`:

```
ACTOR MyMarker : MapMarker
{
	Scale 1.0
	// Customize the scale, sprite, or other properties
}
```

A subclass can override the sprite (default `AMRK`), the scale factor, or the render color/translation through actor properties, and inherit the automap-rendering and activation/deactivation behavior from the parent. Be sure to set all properties before `BeginPlay()` is called, or chain to the parent's `BeginPlay()` if overriding it. Attempting to change `args[0]`, `args[1]`, or `args[2]` at runtime will not re-register the marker — argument values are read only during the initial render pass, not queried dynamically per frame.
