# `int Plat_DownWaitUpStayLip(int tag, int speed, int delay, int lip [, int sound])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `Plat_DownWaitUpStayLip - ZDoom Wiki.html` (retrieved from
`https://zdoom.org/w/index.php?title=Plat_DownWaitUpStayLip&oldid=44647`, 2026-07-29) +
source-verified against `p_lnspec.cpp:754–760`, `p_plats.cpp:412–538` (EV_DoPlat call path,
specifically lines 527–538 for `platDownWaitUpStay`/`platDownWaitUpStayStone` behavior), and
`doomdef.h:60` (TICRATE definition). The wiki's description is broadly accurate on the visible
behavior; this doc adds the `lip` mandatory-argument divergence, the clamping clamp behavior
(silent no-op on visual motion), the `PlaneMoving` guard's tag-dependent return semantics, the
`sound` truthiness test over explicit value matching, the SNDSEQ sequence-name nature of sound
selection, and Zandronum-specific netcode replication — none of which appear in the wiki page.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special.

Lowers a platform to a specific height (the lowest adjacent sector's floor plus a lip amount),
waits for a delay period, then raises it back to its original position. Action special (positive
index 206 in `zcommon.bcs`'s `special` table), semantics in the Zandronum source's `src/p_lnspec.cpp`,
`FUNC(LS_Plat_DownWaitUpStayLip)` (lines 754–760), which forwards into `EV_DoPlat`
(`p_plats.cpp:412–538`), specifically the `DPlat::platDownWaitUpStay` /
`DPlat::platDownWaitUpStayStone` branches (lines 527–538).

## Parameters

- `tag` — sector tag to affect. **`0` is a "manual trigger" convention** (`p_plats.cpp:425–432`):
  affects only the sector on the *back side of the triggering line*, and returns `false`/`0` if
  the line has no back sector. All other values use the standard tag-lookup loop,
  `P_FindSectorFromTag` (`p_plats.cpp:448`), so multiple matching sectors are all affected.
- `speed` — **not map-units-per-tic directly.** Passed through the `SPEED(a)` macro
  (`p_lnspec.cpp:76`: `#define SPEED(a) ((a)*(FRACUNIT/8))`), i.e. the raw integer you pass is
  divided by 8 to get map-units-per-tic in fixed point. Pass `8` for 1.0 units/tic, `16` for 2.0
  units/tic, etc. See `functions/floor_movetovalue.md` for the same macro verified at greater
  depth; `../concepts/units-and-encodings.md` also documents this pattern.
- `delay` — **tics before the platform returns to its original height.** Passed through the
  `TICS(a)` macro (`p_lnspec.cpp:77`: `#define TICS(a) (((a)*TICRATE)/35)`). Since `TICRATE == 35`
  (per `doomdef.h:60`), this is an identity: `TICS(delay) = delay`. The wiki's example "Vanilla
  Doom lifts waited for 3 seconds, or 105 tics" assumes 35 tics/second on a real Doom engine; the
  caveat in `../concepts/units-and-encodings.md` applies — measured time will be ~0.98 seconds per 35
  tics on the Zandronum engine fork due to truncating integer division, so 105 tics is ~2.94
  seconds, not exactly 3. (That caveat's own divergence section notes UZDoom does not have this
  drift — 35 tics there is a full real second.)
- `lip` — **mandatory here, unlike the wiki's phrasing.** The compiled signature in `zcommon.bcs:1545`
  is `Plat_DownWaitUpStayLip(int,int,int,int;int)`, where the semicolon marks the last parameter
  optional — but the wiki's own `"Conversions from linedef types"` table shows 3-argument calls
  like `Plat_DownWaitUpStayLip (tag, 32, 105)` for Doom 21:S1 Lift, which would fail to compile
  here (missing the mandatory `lip` arg). **All actual calls under the `zt-bcc` compiler fork need
  all four.**
  Semantically: lip is a plain **map unit offset** applied to the target floor height. Engine
  multiplies by `FRACUNIT` internally (`p_plats.cpp:529`: `lip*FRACUNIT`), so callers do not
  pre-convert to fixed point themselves. The target height is computed as *lowest floor in
  surrounding sectors, plus `lip` map units*. If this target lands at or above the sector's
  current floor height, the computed low point is clamped to the current floor (`p_plats.cpp:532–533`),
  and the platform does not visibly move — but the call still returns true, still creates and
  starts a thinker, still plays the sound. A silent success with zero visible effect.
- `sound` *(optional)* — determines which sound sequence to play. A **truthiness test**: any
  nonzero value selects `DPlat::platDownWaitUpStayStone` and plays the "Floor" sound sequence
  (`p_lnspec.cpp:758`, `p_plats.cpp:537`); zero/false selects `DPlat::platDownWaitUpStay` and
  plays the "Platform" sound sequence instead. These are SNDSEQ sequence names, overridable per
  map via its own `SNDSEQ` lump, so "Platform" and "Floor" are sequence identifiers, not direct
  sound asset names.

## Return value and behavior

**Returns:** `int`, per the declared signature — whether the platform started moving. **Return
semantics differ by `tag` value:**

- **When `tag != 0` (sector-tag lookup path):** returns `true`/`1` if *at least one* matching
  sector started moving. Sectors whose floor is already moving (`PlaneMoving(sector_t::floor)`
  check, line 453) are skipped, so a second call on a sector mid-motion returns false for that
  sector but may return true if other matching sectors were free to move.
- **When `tag == 0` (manual trigger path):** returns `false`/`0` immediately if the line has no
  back sector, or if that back sector's floor is already moving. Unlike the tag path, there is no
  loop — only one sector is affected.

## Sequence

1. Lowers the platform to the lowest adjacent floor height plus `lip` map units (clamped not to
   go *above* the starting floor — silent no-op if the clamp activates).
2. Waits for `delay` tics while the floor sits at its lowered height.
3. Returns the platform to its original height.
4. Repeats only if triggered again — unlike `Plat_PerpetualRaiseLip`, this is not a loop.

## Zandronum netcode

Server-side only: when `NETWORK_GetState() == NETSTATE_SERVER` (line 472–473 in `p_plats.cpp`),
the engine allocates a unique platform ID (`P_GetFirstFreePlatID()`) for replication to clients.
This platform's state changes are broadcast server→client via `SERVERCOMMANDS_*` calls (e.g.
line 621, `SERVERCOMMANDS_PlayPlatSound`). This behavior is Zandronum-only and has no ZDoom
equivalent.

## Engine-family divergence: fixed-point vs. floating-point internals

All of the observable behavior above (return semantics, the `speed`/8 scaling, `lip` as a
map-unit offset, the raise-clamp, the sound-truthiness test) is confirmed identical on UZDoom.
The *internal representation* backing `speed` and `lip` is not:

- **`SPEED(a)` is `(a) / 8.` on UZDoom** — a native double division — not the Zandronum engine
  fork's `(a)*(FRACUNIT/8)` fixed-point multiply. UZDoom's platform thinker (`DPlat::m_Speed`,
  `m_Low`, `m_High` in the UZDoom source's `src/playsim/mapthinkers/a_plats.cpp`) and its sector
  floor-height plane (`sector_t::floorplane`) are native doubles throughout, not `FRACUNIT`
  fixed-point ints requiring conversion at the boundary.
- **`lip` is added directly to a double**, not multiplied by `FRACUNIT`. UZDoom's
  `EV_DoPlat` computes the lowered target as `FindLowestFloorSurrounding(sec, &spot) + lip`
  (`FindLowestFloorSurrounding` returns `double` map units directly), with no fixed-point
  conversion step — unlike the Zandronum engine fork's `lip*FRACUNIT`.

Net effect: the numeric scaling (divide `speed` by 8) and the semantic meaning of `lip` (a plain
map-unit offset) are unchanged, so calls behave the same on both engines. Only the mechanism
description above ("in fixed point", "engine multiplies by `FRACUNIT` internally") is
Zandronum-engine-fork-specific implementation detail that does not apply to UZDoom's native
floating-point sector geometry.

## Related

- `Plat_UpWaitDownStay` — the inverse (raises, waits, lowers).
- `Plat_DownByValue` — lowers a specific distance instead of to a surrounding floor.
- `Floor_MoveToValue` — similar speed/height/destination semantics but for a single destination.
