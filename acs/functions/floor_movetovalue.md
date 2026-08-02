# `int Floor_MoveToValue(int tag, int speed, int height [, int negative, int UNUSED])`

Moves the floor(s) of sector(s) matching `tag` to an absolute height, at a given speed. Action
special (positive index 37 in `zcommon.bcs`'s `special` table), semantics in
the Zandronum source's `src/p_lnspec.cpp`, `FUNC(LS_Floor_MoveToValue)` (line 384), which forwards
into `EV_DoFloor` (`p_floor.cpp:519`).

**Bucket:** action special.

- `tag` — sector tag to affect. **`0` is a "manual trigger" convention wired directly into
  `EV_DoFloor`** (`p_floor.cpp:532-538`, generic across ZDoom-family floor/ceiling specials, not
  special-cased just here): the special affects only the sector on the *back side of the
  triggering line* instead of any tagged sector, and does nothing if the line has no back sector
  (`!line || !line->backsector` → returns `false`/`0`). Confirmed against the wiki's own
  "If tag is 0, then the sector on the line's back side is used" note.
- `speed` — **not map-units-per-tic directly.** Passed through the `SPEED(a)` macro
  (`p_lnspec.cpp:76`: `#define SPEED(a) ((a)*(FRACUNIT/8))`), i.e. the raw integer you pass is
  divided by 8 to get map-units-per-tic in fixed point. Pass `8` for 1.0 units/tic, `16` for 2.0
  units/tic, etc. — **not** a literal "8 units/tic."
- `height` — absolute target height in **map units** (plain int); the engine multiplies by
  `FRACUNIT` internally (`arg2*FRACUNIT`) before handing it to `EV_DoFloor`, so callers do not
  pre-convert to fixed point themselves.
- `negative` *(optional)* — if non-zero, the target height is negated (`arg2*FRACUNIT*(arg3?-1:1)`)
  before use. Use this to target a height below 0, since `height` itself is always read as a
  positive magnitude.
- **The declared 5th argument (second optional int, `zcommon.bcs:1397`:
  `Floor_MoveToValue(int,int,int;int,int)`) is read into `arg4` by every action special's calling
  convention (`p_lnspec.cpp:73-74`, the shared `FUNC` macro always receives `arg0..arg4`) but
  `LS_Floor_MoveToValue`'s body never references `arg4` at all** — it's silently ignored. Passing
  a 5th argument compiles and has **zero effect** on behavior. This isn't documented as
  deprecated anywhere; it's simply dead on the receiving end in this fork. Confirmed independently
  by `UltimateDoomBuilder`'s own arg-name list (`Assets/Common/Scripting/ZDoom_ACS.cfg:156`:
  `"Floor_MoveToValue(tag, speed, height, neg)"`) which also only names 4 params.
- **Crush/change/reset are hardcoded off**, not caller-controllable: `LS_Floor_MoveToValue` calls
  `EV_DoFloor(..., 0 /*crush*/, 0 /*change*/, false /*hexencrush*/, false)` — there is no way to
  make this specific special crush or change the floor texture/type; use
  `Floor_MoveToValueAndCrush` (index 279) if crushing is needed.

**Example — move sector tag 5's floor to height 128 at 1.0 map units/tic:**

```
Floor_MoveToValue(5, 8, 128);
```

**Returns:** `int`, per the declared signature (`EV_DoFloor`'s `bool` result, `1`/`0`) — whether
at least one sector matching `tag` was found and started moving.

**Provenance:** wiki page `Floor_MoveToValue - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-28, `oldid=31421`) + source-verified (`p_lnspec.cpp:384-389`, `p_floor.cpp:519-538`,
`p_lnspec.cpp:73-76`) + cross-checked against
`UltimateDoomBuilder/Assets/Common/Scripting/ZDoom_ACS.cfg:156`. The wiki page covers `tag`/
`speed`/`height`/`neg` and the `tag == 0` convention accurately but says nothing about the dead
5th argument, the `SPEED()` `/8` scaling, or the hardcoded-off crush/change/reset — those are
this doc's source-verified additions, not wiki-sourced. **Engine:** Zandronum 3.2.1 (verified
against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
