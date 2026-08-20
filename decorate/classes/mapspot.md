# `MapSpot`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki Classes:MapSpot (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Classes%3AMapSpot&oldid=42840) + verified against
Zandronum source `wadsrc/static/actors/shared/sharedmisc.txt` (DECORATE definition), `src/p_teleport.cpp`
(teleport-destination fallback), and `src/gamemode.cpp` (damage-event script context).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `wadsrc/static/actors/shared/sharedmisc.txt` (DECORATE-only class; no native C++ class).

A built-in actor class that serves as an invisible, non-physical anchor point on the map. MapSpot
itself has no intrinsic behavior — its purpose is to provide a TID-assignable location (via actor
coordinates) that other systems can reference. It is defined purely in DECORATE and inherits
directly from `AActor` with no custom engine-side overrides.

## Definition

```decorate
ACTOR MapSpot 9001
{
	+NOBLOCKMAP
	+NOSECTOR
	+NOGRAVITY
	+DONTSPLASH
	RenderStyle None
}
```

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under
Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## Common uses

MapSpot's primary value is as a **teleport destination** and **positional reference** in ACS
scripts:

- **Teleport destinations** (no dedicated marker required): When a teleport-by-TID search fails to
  find a dedicated teleport destination actor, the engine's teleport code falls back to accepting a
  MapSpot as the destination (see `src/p_teleport.cpp`, fallback path when `tag == 0` and no
  sector-tag destination is found) — this fallback is identical on UZDoom and Zandronum.
- **ACS position lookup**: ACS can query a MapSpot's position via `GetActorX()`, `GetActorY()`,
  `GetActorZ()` on its TID, allowing scripts to reference pre-placed map locations.
- **Patrol points** (via `Thing_SetGoal`): ACS can direct a monster to patrol through a series of
  MapSpots by TID.
- **Script context actors** (engine-side, Zandronum only): In Zandronum's damage-event system
  (Zandronum Customization Pack addition), temporary MapSpots are spawned as script-context holders
  to pass actor pointers (target/source/inflictor) to ACS event scripts (see `src/gamemode.cpp`).
  No UZDoom/GZDoom-family equivalent exists — see "Zandronum-specific: Damage-event script-context
  actors" below.

## Subclasses

### `MapSpotGravity`

```decorate
ACTOR MapSpotGravity : MapSpot 9013
{
	-NOBLOCKMAP
	-NOSECTOR
	-NOGRAVITY
}
```

Same as MapSpot but with gravity enabled and blockmap/sector involvement restored. Useful when a
map location must be a solid, gravity-affected checkpoint.

### `FS_Mapspot` (Legacy editor compatibility)

```decorate
ACTOR FS_Mapspot : Mapspot 5004
{
}
```

An editor-number alias for MapSpot (DoomEd number 5004) for compatibility with legacy map editors
that predate the current editor-number namespace. Functionally identical to MapSpot.

## Zandronum-specific: Damage-event script-context actors

The "Script context actors" use case above has no UZDoom/GZDoom-family equivalent at all. UZDoom's
engine source has no `GAMEEVENT_ACTOR_DAMAGED`/`GAMEEVENT_ACTOR_DAMAGED_PREMOD` event, and nothing
that spawns a temporary MapSpot to smuggle target/source/inflictor pointers into an ACS event
script — that mechanism (`GAMEMODE_HandleDamageEvent` in Zandronum's `src/gamemode.cpp`) is a
Zandronum Customization Pack addition with no counterpart upstream. A map/mod targeting UZDoom
cannot rely on a MapSpot ever appearing as the activator of a damage-related script.

## Engine-family divergence

**UZDoom/GZDoom-family additions:** The UZDoom/GZDoom implementations add two properties not
present in Zandronum's version:

- `+NOTONAUTOMAP` — excludes the actor from automap display.
- `CameraHeight 0` — sets an explicit camera-mounting height for any actor that treats this as a
  camera position (rarely used for MapSpot specifically, more relevant for custom camera-anchor
  classes inheriting from it).

Zandronum MapSpots do not support these properties. A map targeting Zandronum should not add them.

## See also

- [Teleport destination actors](https://zdoom.org/wiki/Teleport) (ZDoom Wiki external) — a
  dedicated teleport-destination class alternative when TeleportDest is preferred over MapSpot.
- ACS `GetActorX()`, `GetActorY()`, `GetActorZ()` — position-query functions tied to actor TID.
- ACS `Thing_SetGoal` — assigns a patrol-point TID to a monster.
