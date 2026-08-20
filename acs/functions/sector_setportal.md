# `Sector_SetPortal(int tag, int type, int plane, int misc, int opacity)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `Sector_SetPortal - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=Sector_SetPortal&oldid=51874`) + source-verified against `p_lnspec.cpp:3657` (runtime `LS_NOP`), `p_spec.cpp:1320-1380`
(`P_SpawnPortal`), `p_spec.cpp:1604-1802` (`P_SpawnSpecials`'s per-line scan, confirming this runs
once at map load, independent of ACS/the action-special dispatcher), `g_shared/a_skies.cpp:91-141`
(`ASkyCamCompat`, the type-2 companion actor), `zcommon.bcs:1417` (declared as special 57). Corrects
an earlier pass on this file that only checked the `LS_NOP` runtime path and wrongly concluded the
special was "not implemented in Zandronum" outright.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Linedef action for a **map-editor-placed, static-at-load-time** floor/ceiling "stacked sector"
portal — the pre-GZDoom ZDoom mechanism for making one sector's floor/ceiling visually continue
into another sector (skybox/3D-bridge-style). This is a completely different feature from the
modern GZDoom linked-portal system the ZDoom wiki page actually documents (see "Wiki/engine
divergence" below) — most of the wiki's parameter values and portal types **do not apply on
Zandronum** (see "Engine-family divergence" further below for what UZDoom actually builds).

**This special has two entirely separate, independently-verified code paths on Zandronum — do not
conflate them:**

1. **ACS-callable / runtime-triggered path: non-functional.** `p_lnspec.cpp:3657` maps action
   special #57 to `LS_NOP` in the `LineSpecials[]` runtime dispatch table (used for both
   `Sector_SetPortal(...)` called from ACS/BCS and a player crossing/using/shooting a live line
   with this special assigned). Calling or triggering it this way compiles cleanly (`zcommon.bcs:1417`)
   but is a genuine no-op — it always returns `false` and does nothing.
2. **Map-editor / static-at-load path: functional.** If a mapper assigns special #57 directly to a
   linedef's Special field in the map data (Hexen/UDMF format — not executed via ACS at all), it is
   processed exactly once by `P_SpawnSpecials()` when the map loads (`p_spec.cpp:1676`, `case
   Sector_SetPortal:`), which calls `P_SpawnPortal()` (`p_spec.cpp:1320`) to actually build the
   portal. **This path works** in both the software and OpenGL/hardware renderers (`r_plane.cpp`,
   `gl/scene/gl_portal.h`, `gl/scene/gl_sky.cpp` all have live handling for the resulting
   `AStackPoint`/`FloorSkyBox`/`CeilingSkyBox` sector fields).

## What actually gets built (static path only)

`P_SpawnPortal` implements exactly two of the wiki's portal types, using an **anchor line +
reference line pair** convention, not a single self-contained call:

- **`type` = `0` (normal):** requires two lines both with special #57 and the same `tag` (arg0) —
  one flagged as the "anchor" (`args[3]==0`) and one as the "reference" (`args[3]==1`). The anchor
  line triggers `P_SpawnPortal`, which spawns a pair of linked `AStackPoint` actors at each line's
  midpoint and assigns them to `FloorSkyBox`/`CeilingSkyBox` (per `plane`) on every sector matching
  `tag`. `args[4]` (alpha, 0-255) sets the portal plane's opacity, read from the anchor line only.
- **`type` = `1` (copy):** a second scan in the same `P_SpawnPortal` call copies the
  already-built portal onto other sectors — a line with `args[1]==1` and `args[3]==sectortag` of
  the type-0 anchor's reference sector, targeting either `frontsector` (`args[0]==0`) or all
  sectors matching a further tag (`args[0]!=0`).
- **`type` = `2` ("EE-style skybox", comment in `p_spec.cpp:1681`):** **not built by
  `P_SpawnPortal`/`P_SpawnSpecials` at all** — `P_SpawnPortal` is only called when
  `args[1]==0 && args[3]==0` (`p_spec.cpp:1686`), so a type-2 line is silently skipped by the
  static scan. Instead it's a companion actor's job: `ASkyCamCompat` (`g_shared/a_skies.cpp:91`),
  a Thing a mapper places in the *destination* sector, scans its own sector's lines at
  `BeginPlay()` for a `Sector_SetPortal` special with `args[1]==2`, reads that line's `tag`/`plane`/
  `alpha` from it, and skyboxifies every sector matching the tag (also force-changes their floor/
  ceiling texture to the F_SKY1 flat — `SetTexture(..., skyflatnum, false)` — a side effect the
  wiki doesn't mention).
- **Any other `type` value:** genuinely unhandled by any code path (reserved per the
  `p_spec.cpp:1682` comment) — a straightforward no-op, both statically and at runtime.

`plane` (arg2): `0`=floor, `1`=ceiling, `2`=both — verified identical to the wiki's meaning, used
directly to gate `SetPortal()`'s floor/ceiling branches.

## Critical limitation: floor/ceiling rendering only, no actor passage

This is the classic ZDoom "stacked sectors" feature (same `AStackPoint`/`ASkyViewpoint` actor
classes used by the older, manually-placed `LowerStackLookOnly`/`UpperStackLookOnly` Things, via
`P_SetupPortals()` in the same file) — **not** a true line/wall portal. `FloorSkyBox`/
`CeilingSkyBox` are read only by rendering code (`r_plane.cpp`, `r_bsp.cpp`, the GL renderer);
grepping `p_map.cpp`/`p_mobj.cpp`/`p_floor.cpp` (actor movement and collision) turns up zero
references to either field. An actor cannot walk, shoot, or otherwise interact through a
`Sector_SetPortal` portal — it only makes one sector's floor or ceiling plane visually continue as
if you were looking into the other sector, the same effect used for skyboxes and 3D-bridge tricks.
This engine has **no true line/wall portal implementation anywhere** — confirmed by the complete
absence of any `Line_SetPortal` handling in this codebase (see
[Line_SetPortal](line_setportal.md)) and the lack of any dedicated portal-rendering source file
(`r_portal.cpp`/`hw_portal.cpp`-style) outside the GL-specific stacked-sector code already cited
above.

## Return value

`false` unconditionally when called/triggered live via the `LS_NOP` runtime path (matching the
wiki's bool-result framing, but the value carries no meaning here — it's not a real success/failure
signal). The static map-load path has no return value concept at all; it either builds the portal
or silently skips the line if the args don't match one of the two handled shapes above.

## Wiki/engine divergence

The ZDoom wiki page describes the modern (2013+) GZDoom linked-portal system: 7 portal types
including horizon/plane/interactive/copy-to-line variants, a `misc` parameter, and general
actor-crossing support. **None of that system exists on Zandronum.** What Zandronum actually has
under this same special number is the much older, narrower "stacked sector" mechanism (predates
the wiki's documented feature by years) — floor/ceiling-only, anchor/reference-line-pair or
companion-actor setup, no actor passage. Only use this doc's parameter tables above for Zandronum;
the wiki page's parameter semantics do not apply to Zandronum at all (see "Engine-family
divergence" below — UZDoom is a different story).

## Engine-family divergence: linked portals are actor-passable on UZDoom

UZDoom's static map-load handling of this special (`src/maploader/specials.cpp`, `case
Sector_SetPortal:` around line 728 — its own per-line scan at map load, structurally the same
anchor/reference-line convention described above) recognizes the same seven `type` values the wiki
page describes, not Zandronum's narrower handful:

- `type` 0 (normal) and `type` 6 (linked) both feed the same anchor/reference-line search
  (`SpawnPortal`, `specials.cpp:356`) and differ only in which kind of portal gets built: `type` 0
  builds the same non-interactive stacked-sector portal Zandronum has (`PORTS_PORTAL`); `type` 6
  builds UZDoom's "linked" portal kind (`PORTS_LINKEDPORTAL`), which the engine's own portal-type
  enum (`src/playsim/portal.h:244-249`) comments as "interactive".
- `type` 1 (copy) behaves the same as documented above for Zandronum.
- `type` 2 (EE-style skybox) is still handled by a companion camera-object actor that scans its own
  sector's lines at spawn time, matching this doc's existing description of that mechanism.
- `type`s 3 and 4 (EE-style "plane" and "horizon" portals) are additionally recognized on UZDoom —
  neither exists on Zandronum at all. Both are hardware-renderer-only; UZDoom's own software
  renderer does not implement them.
- `type` 5 (copy portal to line) is also new on UZDoom: it attaches an already-built portal to a
  target linedef instead of a sector, feeding into the separate line-portal system mentioned below.

**The headline behavioral difference: a `type`-6 linked portal is genuinely actor-passable, unlike
every portal kind Zandronum builds (and unlike UZDoom's own `type` 0/1/2/3/4 portals).** UZDoom's
actor movement/collision code (`src/playsim/p_map.cpp`, dozens of call sites) and its
portal-traversal code (`src/playsim/portal.cpp`) both gate floor/ceiling-plane crossing on
`sector_t::PortalBlocksMovement()` (`src/g_levellocals.h:934`), which only reports "not blocked"
for a sector plane whose portal is the linked kind. Practically: once a mapper builds a `type`-6
portal pair, monsters, players, and projectiles can walk, fall, or fly straight through from one
linked sector's floor/ceiling into the destination sector — not just see it, the way every other
portal kind here (including `type` 0's otherwise-identical-looking stacked-sector portal) only ever
affects rendering. This overturns the "no actor passage" claim above specifically for the
`type`-6 case on UZDoom; that claim still holds for `type` 0/1/2/3/4 on UZDoom, and for everything
Zandronum builds.

Relatedly, `Line_SetPortal` (special #156, `case Line_SetPortal:`/`case Line_QuickPortal:` in the
same source file around `specials.cpp:753-754`) is a real, separate line/wall portal implementation
on UZDoom — the "Related" note below that it has zero implementation describes Zandronum only.

Runtime behavior is unaffected: `Sector_SetPortal` (special #57) still maps to `LS_NOP` in UZDoom's
action-special runtime dispatch table (`src/playsim/p_lnspec.cpp:3604`), so calling it from ACS/BCS
or triggering a live line with the special assigned remains a no-op on UZDoom too, exactly as
documented above for Zandronum.

## Related

- [Line_SetPortal](line_setportal.md) (special #156) — the wiki's line/wall portal special; unlike
  this one, has **zero** implementation on Zandronum (neither the runtime `LS_NOP` path nor any
  static/`P_SpawnSpecials` equivalent — confirmed by grep across the whole source tree). UZDoom
  does implement it — see "Engine-family divergence" above.
- `Sector_Set3DFloor`, `ExtraFloor_LightOnly` — genuinely unimplemented (`LS_NOP` with no static
  counterpart) 3D-geometry specials; do not assume they share `Sector_SetPortal`'s
  static/map-editor escape hatch.
