# `int Floor_MoveToValue(int tag, int speed, int height [, int negative, int UNUSED])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `Floor_MoveToValue - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://zdoom.org/w/index.php?title=Floor_MoveToValue&oldid=31421`) + source-verified (`p_lnspec.cpp:384-389`, `p_floor.cpp:519-538`,
`p_lnspec.cpp:73-76`) + cross-checked against
`UltimateDoomBuilder/Assets/Common/Scripting/ZDoom_ACS.cfg:156`. The wiki page covers `tag`/
`speed`/`height`/`neg` and the `tag == 0` convention accurately but says nothing about the dead
5th argument, the `SPEED()` `/8` scaling, or the hardcoded-off crush/change/reset — those are
this doc's source-verified additions, not wiki-sourced.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special.

Moves the floor(s) of sector(s) matching `tag` to an absolute height, at a given speed. Action
special (positive index 37 in `zcommon.bcs`'s `special` table), semantics in
the Zandronum source's `src/p_lnspec.cpp`, `FUNC(LS_Floor_MoveToValue)` (line 384), which forwards
into `EV_DoFloor` (`p_floor.cpp:519`).

- `tag` — sector tag to affect. **`0` is a "manual trigger" convention wired directly into
  `EV_DoFloor`** (`p_floor.cpp:532-538`, generic across ZDoom-family floor/ceiling specials, not
  special-cased just here): the special affects only the sector on the *back side of the
  triggering line* instead of any tagged sector, and does nothing if the line has no back sector
  (`!line || !line->backsector` → returns `false`/`0`). Confirmed against the wiki's own
  "If tag is 0, then the sector on the line's back side is used" note.
- `speed` — **not map-units-per-tic directly.** Passed through the `SPEED(a)` macro
  (Zandronum `p_lnspec.cpp:76`: `#define SPEED(a) ((a)*(FRACUNIT/8))`), i.e. the raw integer you pass is
  divided by 8 to get map-units-per-tic in fixed point. Pass `8` for 1.0 units/tic, `16` for 2.0
  units/tic, etc. — **not** a literal "8 units/tic." On UZDoom, the `SPEED()` macro implementation differs (divides as a floating-point literal rather than multiplying by a fixed-point constant), but the semantics are identical — the same speed values produce the same movement rates on both engines.
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
  deprecated anywhere; it's simply dead on the receiving end in the Zandronum engine fork. Confirmed independently
  by `UltimateDoomBuilder`'s own arg-name list (`Assets/Common/Scripting/ZDoom_ACS.cfg:156`:
  `"Floor_MoveToValue(tag, speed, height, neg)"`) which also only names 4 params.
- **Crush/change/reset are hardcoded off**, not caller-controllable: `LS_Floor_MoveToValue` calls
  `EV_DoFloor(..., 0 /*crush*/, 0 /*change*/, false /*hexencrush*/, false)` — there is no way to
  make this specific special crush or change the floor texture/type; use
  `Floor_MoveToValueAndCrush` (index 279) if crushing is needed.

## Engine-family divergence: 5th argument

The "dead 5th argument" claim above, source-verified against the Zandronum engine fork only, does
not hold on UZDoom. UZDoom's `LS_Floor_MoveToValue` (UZDoom source's `src/playsim/p_lnspec.cpp`,
`FUNC(LS_Floor_MoveToValue)`) reads `arg4` through a `CHANGE(a)` macro
(`((a) >= 0 && (a)<=7) ? ChangeMap[a] : 0`) and passes the result straight into `EV_DoFloor`'s
`change` parameter — the same generic "copy the new sector's texture and/or type" mechanism other
ZDoom-family floor/ceiling specials expose via their own `change` argument. On UZDoom, passing a
5th argument to `Floor_MoveToValue` therefore has a real, observable effect, unlike the "zero
effect... dead on the receiving end" behavior documented above for the Zandronum engine fork.
Crushing stays hardcoded off on UZDoom too (`crush=-1` passed to `EV_DoFloor`), so this divergence
is scoped to the change behavior only, not crushing.

**Example — move sector tag 5's floor to height 128 at 1.0 map units/tic:**

```text
Floor_MoveToValue(5, 8, 128);
```

**Returns:** `int`, per the declared signature (`EV_DoFloor`'s `bool` result, `1`/`0`) — whether
at least one sector matching `tag` was found and started moving.
