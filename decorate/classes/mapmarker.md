# `MapMarker`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes — the `args[2]` scaling sub-feature is UZDoom-only, see
"Engine-family divergence: args[2] scaling" below; the class itself exists on both
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki Classes:MapMarker (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3AMapMarker&oldid=52573) + verified against Zandronum source
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** native C++ class in Zandronum (`src/g_shared/a_sharedglobal.h:185–192`, `AMapMarker : public AActor`, implementation in `src/g_shared/a_mapmarker.cpp`; default DECORATE definition in `wadsrc/static/actors/shared/mapmarker.txt`); ZScript class in UZDoom (`wadsrc/static/zscript/actors/shared/mapmarker.zs`, `class MapMarker : Actor` — an ordinary scripted class with no native backing beyond what `Actor` itself provides; automap-side rendering lives in `src/am_map.cpp`'s `DAutomap::drawAuthorMarkers()`, starting at line 3263).
**Source excerpt:** This file quotes Zandronum engine source verbatim (the `MapMarker` DECORATE definition, `wadsrc/static/actors/shared/mapmarker.txt`); reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

A built-in actor class representing an automap-only marker. MapMarker actors do not appear in the 3D view — they appear only on the automap with their sprite rendered at a specified location. Typical use is to mark points of interest, secret areas, or tracked actors for the player.

**Critical:** A MapMarker must have `BeginPlay()` called without interruption. The implementation calls `ChangeStatNum(STAT_MAPMARKER)` to register the marker with the automap renderer. If a subclass overrides `BeginPlay()` without chaining to the parent, the marker is silently never rendered — no error occurs, but the actor will be invisible on the automap. This holds unchanged on UZDoom: `MapMarker`'s ZScript `override void BeginPlay()` (`mapmarker.zs`) does the identical `ChangeStatNum(STAT_MAPMARKER)` call and, like Zandronum's version, does not itself chain to `Super.BeginPlay()` — a subclass overriding `BeginPlay()` in ZScript needs an explicit `Super.BeginPlay()` call to avoid the same silent-invisibility failure mode.

## Placement and visibility control

MapMarker is **not** a pickup and should not be inherited from `Inventory`. It is placed in the world as a standalone actor, similar to `MapSpot`. After spawning, a MapMarker's visibility can be toggled:

- **`Activate(activator)`** — sets the `MF2_DORMANT` flag, which **hides** the marker from the automap (the automap render loop checks this flag and skips rendering if set).
- **`Deactivate(activator)`** — clears the `MF2_DORMANT` flag, which **shows** the marker on the automap.

In multiplayer, **on Zandronum** the server propagates these activation/deactivation calls to all clients via `SERVERCOMMANDS_ThingActivate`, so visibility is synchronized consistently — this is part of Zandronum's client/server-authoritative netcode model. In ACS/BCS, use `Thing_Activate` / `Thing_Deactivate` to toggle visibility; in ZScript (UZDoom only), call the methods directly. Grepping UZDoom's source tree turns up no `SERVERCOMMANDS`-style construct at all (that split client/server command-propagation layer is a Zandronum-specific concept), so this isn't "differs" so much as a mechanism that doesn't exist on UZDoom in that form — see "Zandronum-specific: `SERVERCOMMANDS_ThingActivate` multiplayer sync" below for what that means in practice.

Note: The Zandronum engine source at `a_mapmarker.cpp:47–48` contains a misleading comment ("To enable display of the sprite, activate it") that contradicts the code — the comment is reversed. The actual behavior (verified in Zandronum's automap renderer at `am_map.cpp:2852–2855`) is that `Activate` hides and `Deactivate` shows the marker. This is a clean agreement across engines, not a divergence: UZDoom's `mapmarker.zs` carries the identical (also reversed) comment above its own `Activate`/`Deactivate` overrides, and its behavior matches — `Activate` sets `bDormant = true` (hides), `Deactivate` sets `bDormant = false` (shows), the same `MF2_DORMANT`-backed flag Zandronum uses.

## Arguments and behavior

The actor's special arguments control marker behavior:

| Argument | Value | Behavior |
|----------|-------|----------|
| `args[0]` | 0 | Display the marker sprite at the MapMarker actor's own location. |
| `args[0]` | N (nonzero) | Display the marker sprite at the location of any actor with TID matching N. If multiple actors share that TID, the marker is drawn at each one's location. |
| `args[1]` | 0 (default) | Display the marker always, regardless of visibility state. |
| `args[1]` | 1 | Display the marker only after its (or the followed actor's, if `args[0]` is set) sector has been drawn on the automap — i.e., after the player has explored that area. For `args[0] != 0` (TID follow mode), this check is applied per-followed-actor. On Zandronum maps without GL nodes, this uses whole-sector `SECF_DRAWN`; with GL nodes, it uses per-subsector `SSECF_DRAWN` for finer granularity. **UZDoom** always uses per-subsector drawn-tracking unconditionally — see "Zandronum-specific: whole-sector `args[1]` fallback without GL nodes" below. |
| `args[2]` | 0 (default) | Display the marker at constant scale, regardless of automap zoom. On Zandronum this is the only behavior — see below. |
| `args[2]` | 1 | **UZDoom only:** scale the marker relative to the automap zoom instead of holding a constant size. On Zandronum, `args[2]` is ignored — Zandronum's automap renderer has no code path for it and always draws markers at constant scale. See "Engine-family divergence: args[2] scaling" below for the UZDoom-side citation. |

`args[0]`/`args[1]`/`args[2]` are re-read from the live actor on every automap draw, not snapshotted at spawn: on UZDoom, `drawAuthorMarkers()` is called each frame from `DAutomap::Drawer()` (`src/am_map.cpp:3430`) and reads all three fresh, with no per-marker cache. Changing a marker's arguments at runtime takes effect on the next automap redraw; there is no re-registration step — `BeginPlay()`/`ChangeStatNum` run once only, to put the actor on the `STAT_MAPMARKER` thinker list.

## Engine-family divergence: args[2] scaling

The ZDoom wiki mentions a third argument for automap-zoom scaling — "If the third argument is 1, the map marker scales relative to the automap zoom, rather than keep a constant scale." This feature exists in UZDoom/GZDoom but **does not exist in Zandronum** (version 3.2.1). Zandronum's automap renderer has no code path for `args[2]` and always draws markers at constant scale. A MapMarker subclass that sets `args[2] = 1` will compile and run on Zandronum without error, but the argument will be silently ignored.

Verified against UZDoom source: the feature is real and present as described. `DAutomap::drawAuthorMarkers()` (`src/am_map.cpp:3311–3318`, tagged with an `[MK]` author comment matching the wiki's description) checks `mark->args[2] == 1` and, if set, runs the marker's interpolated X/Y scale through `MTOF` (map-units-to-frame-buffer, the same conversion the rest of the automap uses for zoom) before drawing — otherwise the raw actor scale is used unconverted.

## Zandronum-specific: whole-sector `args[1]` fallback without GL nodes

Zandronum's `AM_drawAuthorMarkers()` (`src/am_map.cpp:2893–2896`) branches on `hasglnodes` for the `args[1] == 1` "explored" check: with GL nodes it tests the followed actor's subsector flag (`marked->subsector->flags & SSECF_DRAWN`); without GL nodes it falls back to the whole *sector's* flag (`marked->Sector->MoreFlags & SECF_DRAWN`) instead, since accurate subsector-level drawn-tracking depends on GL nodes being built for the map.

UZDoom's equivalent check (`DAutomap::drawAuthorMarkers()`, `src/am_map.cpp:3323`) has no such branch — it unconditionally tests `marked->subsector->flags & SSECMF_DRAWN` (note the renamed flag: `SSECMF_DRAWN`, not Zandronum's `SSECF_DRAWN` — same bit purpose, different name after a subsector-flags refactor). GZDoom-family engines always build proper node data for the renderer, so there is no non-GL-node fallback path to have. Practical consequence: on Zandronum, a map without GL nodes gets coarser (whole-sector) `args[1] == 1` visibility gating than one with GL nodes; on UZDoom, the granularity is always per-subsector regardless of map data. Worth keeping in mind for anyone porting a Zandronum map/mod that happens to rely on the whole-sector fallback's coarser behavior.

## Zandronum-specific: `SERVERCOMMANDS_ThingActivate` multiplayer sync

Zandronum's client/server-authoritative netcode model requires the server to explicitly propagate a `Thing_Activate`/`Thing_Deactivate` special's effect to every connected client via `SERVERCOMMANDS_ThingActivate`, so a MapMarker's visibility state stays consistent across all observers. UZDoom has no `SERVERCOMMANDS`-style construct anywhere in its source tree — that split client/server command-propagation layer is specific to Zandronum's netcode architecture and has no equivalent to check on UZDoom. This entry does not attempt to characterize how UZDoom's own multiplayer model keeps `Activate`/`Deactivate` state consistent across peers (that's outside a single-actor doc's scope) — only that the specific `SERVERCOMMANDS_ThingActivate` mechanism the wiki/Zandronum source names does not exist there.

## DECORATE definition

```text
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

This is Zandronum's DECORATE form specifically. UZDoom's default `MapMarker` (`wadsrc/static/zscript/actors/shared/mapmarker.zs`, GPL-3.0 — not reproducible here verbatim per this tree's licensing rules) is an equivalent ZScript `class MapMarker : Actor` with the same default block and the same defaults shown above (`+NOBLOCKMAP +NOGRAVITY +DONTSPLASH +INVISIBLE`, `Scale 0.5`, single-frame `AMRK A -1; Stop;` Spawn state, same `9040 = MapMarker` doomednum mapping in `wadsrc/static/mapinfo/common.txt`) — just ZScript syntax and an explicit `override void BeginPlay()`/`Activate()`/`Deactivate()` instead of native C++ methods.

## Inheritance and customization

To create a custom map marker, inherit from `MapMarker`:

```text
ACTOR MyMarker : MapMarker
{
	Scale 1.0
	// Customize the scale, sprite, or other properties
}
```

A subclass can override the sprite (default `AMRK`), the scale factor, or the render color/translation through actor properties, and inherit the automap-rendering and activation/deactivation behavior from the parent. Be sure to set all properties before `BeginPlay()` is called, or chain to the parent's `BeginPlay()` if overriding it. See "Arguments and behavior" above for how argument changes at runtime take effect.
