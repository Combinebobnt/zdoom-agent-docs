# `int Ceiling_MoveToValue(int tag, int speed, int height [, int negative, int UNUSED])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `Ceiling_MoveToValue - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-29, `https://zdoom.org/w/index.php?title=Ceiling_MoveToValue&oldid=31384`) + source-verified (`p_lnspec.cpp:610-615`, `p_ceiling.cpp:690-726`,
`dsectoreffect.cpp:157-192`). The wiki page covers `tag`/`speed`/`height`/`neg` and the
`tag == 0` convention accurately but says nothing about the dead 5th argument, the `SPEED()` `/8`
scaling, the hardcoded-off crushing, or the unimplemented `Ceiling_MoveToValueAndCrush` sibling
— those are this doc's source-verified additions, not wiki-sourced.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special.

Moves the ceiling(s) of sector(s) matching `tag` to an absolute height, at a given speed. Action
special (positive index 47 in `zcommon.bcs`'s `special` table), semantics in
the Zandronum source's `src/p_lnspec.cpp`, `FUNC(LS_Ceiling_MoveToValue)` (line 610), which forwards
into `EV_DoCeiling` (`p_ceiling.cpp:690`).

- `tag` — sector tag to affect. **`0` is a "manual trigger" convention wired directly into
  `EV_DoCeiling`** (`p_ceiling.cpp:701-709`, generic across ZDoom-family floor/ceiling specials, not
  special-cased just here): the special affects only the sector on the *back side of the
  triggering line* instead of any tagged sector, and does nothing if the line has no back sector
  (`!line || !line->backsector` → returns `false`/`0`). Confirmed against the wiki's own
  "If tag is 0, then the sector on the line's back side is used" note.
- `speed` — **not map-units-per-tic directly.** Passed through the `SPEED(a)` macro
  (`p_lnspec.cpp:76`: `#define SPEED(a) ((a)*(FRACUNIT/8))`), i.e. the raw integer you pass is
  divided by 8 to get map-units-per-tic in fixed point. Pass `8` for 1.0 units/tic, `16` for 2.0
  units/tic, etc. — **not** a literal "8 units/tic."
- `height` — absolute target height in **map units** (plain int); the engine multiplies by
  `FRACUNIT` internally (`arg2*FRACUNIT`) before handing it to `EV_DoCeiling`, so callers do not
  pre-convert to fixed point themselves.
- `negative` *(optional)* — if non-zero, the target height is negated (`arg2*FRACUNIT*(arg3?-1:1)`)
  before use. Use this to target a height below 0, since `height` itself is always read as a
  positive magnitude.
- **The declared 5th argument (second optional int, `zcommon.bcs:1407`:
  `Ceiling_MoveToValue(int,int,int;int,int)`) is read into `arg4` by every action special's calling
  convention (`p_lnspec.cpp:73-74`, the shared `FUNC` macro always receives `arg0..arg4`) but
  `LS_Ceiling_MoveToValue`'s body (line 613-615) never references `arg4` at all** — it's silently
  ignored. Passing a 5th argument compiles and has **zero effect** on behavior. This isn't documented
  as deprecated anywhere; it's simply dead on the receiving end in the Zandronum engine fork.
- **Crushing is hardcoded off**, unlike the sister function `Ceiling_MoveToValueAndCrush` (declared
  as index 280 in `zcommon.bcs` but **not implemented in the Zandronum engine fork's `LineSpecials[]` table
  at all** — lines 3647-3855 of `p_lnspec.cpp` enumerate indices 0-255, and the table stops at 255;
  calling index 280 via ACS compiles fine and silently does nothing at runtime, same as the
  `SpawnParticle`/`GetMaxInventory` pattern already documented in `families/spawning.md` and
  `families/inventory.md`). `LS_Ceiling_MoveToValue` explicitly passes `crush=-1` to `EV_DoCeiling`
  (line 613), which initializes a ceiling thinker's `m_Crush` field to "no crushing." This is
  distinct from `Floor_MoveToValue`'s `crush=0`, but functionally equivalent—both prevent damage on
  impact.

## Engine-family divergence: 5th argument and the `AndCrush` sibling

Two of the claims above, both source-verified against the Zandronum engine fork only, do not hold
on UZDoom:

- **The 5th argument is not dead on UZDoom.** UZDoom's `LS_Ceiling_MoveToValue` (the UZDoom
  source's `src/playsim/p_lnspec.cpp`) reads `arg4` through a `CHANGE(a)` macro
  (`((a) >= 0 && (a)<=7) ? ChangeMap[a] : 0`) and passes the result straight into `EV_DoCeiling`'s
  `change` parameter — the same generic "copy the new sector's texture and/or type" mechanism
  other ZDoom-family floor/ceiling specials expose via their own `change` argument. On UZDoom,
  passing a 5th argument to `Ceiling_MoveToValue` therefore has a real, observable effect, unlike
  the "zero effect... dead on the receiving end" behavior documented above for the Zandronum
  engine fork.
- **`Ceiling_MoveToValueAndCrush` (index 280) is implemented on UZDoom.** UZDoom's action-special
  table (the UZDoom source's `src/playsim/actionspecials.h` and dispatch table in
  `src/playsim/p_lnspec.cpp`) has a real `LS_Ceiling_MoveToValueAndCrush` at index 280, forwarding
  into the same `EV_DoCeiling` with a real (non-forced) crush value. This is the opposite of the
  Zandronum engine fork, where index 280 falls off the end of a table that stops at 255 and calling
  it silently no-ops.

**Example — move sector tag 5's ceiling to height 256 at 1.0 map units/tic:**

```text
Ceiling_MoveToValue(5, 8, 256);
```

**Returns:** `int`, per the declared signature (`EV_DoCeiling`'s `bool` result, `1`/`0`) — whether
at least one sector matching `tag` was found and started moving.
