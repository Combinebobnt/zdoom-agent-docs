# `int Ceiling_MoveToValue(int tag, int speed, int height [, int negative, int UNUSED])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `Ceiling_MoveToValue - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-29, `https://zdoom.org/w/index.php?title=Ceiling_MoveToValue&oldid=31384`) + source-verified (`p_lnspec.cpp:610-615`, `p_ceiling.cpp:690-726`,
`dsectoreffect.cpp:157-192`, `dsectoreffect.cpp:274-283,340-346`, `p_map.cpp:6226`,
`p_lnspec.cpp:3598-3856,3933-3937`, `p_acs.h` pcode enum, `p_acs.cpp:12991-12994`, zt-bcc
`src/codegen/expr.c:1626-1637`). The wiki page covers `tag`/`speed`/`height`/`neg` and the
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
  as index 280 in `zcommon.bcs` but **not implemented in the Zandronum engine fork at all**. The
  `LineSpecials[256]` table (`p_lnspec.cpp:3598-3856`) stops at index 255, `actionspecials.h` has no
  `AndCrush` row, and `P_ExecuteSpecial` returns 0 for any number above 255 (`p_lnspec.cpp:3933-3937`).
  A zt-bcc call does not even reach that guard, though. zt-bcc emits any special numbered 256 or
  higher as the `PCD_LSPEC5EX` pcode (`src/codegen/expr.c:1626-1637` in zt-bcc), which Zandronum's
  interpreter does not implement. Its pcode number, 381, is Zandronum's own
  `PCD_GETTEAMPLAYERCOUNT` (`p_acs.h` enum; handler at `p_acs.cpp:12991-12994`). So the script
  runs the wrong instruction on its argument stack and then decodes the special number that follows
  as bytecode. The exact result depends on those bytes, but it is corrupted script execution, not a
  clean no-op. Don't call it on Zandronum.) `LS_Ceiling_MoveToValue` explicitly passes `crush=-1` to `EV_DoCeiling`
  (line 613), which initializes a ceiling thinker's `m_Crush` field to "no crushing." On Zandronum,
  `Floor_MoveToValue` passes `crush=0` instead, and the two are not equivalent. Neither deals damage,
  since crush damage needs a value above 0 (`p_map.cpp:6226`). But with `crush=-1` a plane that hits
  a blocking actor moves back to where it was that tic (`dsectoreffect.cpp:279-283`, `344-346`),
  while with `crush=0` it keeps its new position and returns `crushed` (`dsectoreffect.cpp:274-278`,
  `340-343`).

## Engine-family divergence: 5th argument and the `AndCrush` sibling

Two of the claims above, both source-verified against the Zandronum engine fork only, do not hold
on UZDoom:

- **The 5th argument is not dead on UZDoom.** UZDoom's `LS_Ceiling_MoveToValue` (the UZDoom
  source's `src/playsim/p_lnspec.cpp`) reads `arg4` through a `CHANGE(a)` macro (values 0-7 index a
  change-mode table; anything else means no change) and passes the result straight into `EV_DoCeiling`'s
  `change` parameter — the same generic "copy the new sector's texture and/or type" mechanism
  other ZDoom-family floor/ceiling specials expose via their own `change` argument. On UZDoom,
  passing a 5th argument to `Ceiling_MoveToValue` therefore has a real, observable effect, unlike
  the "zero effect... dead on the receiving end" behavior documented above for the Zandronum
  engine fork.
- **`Ceiling_MoveToValueAndCrush` (index 280) is implemented on UZDoom.** UZDoom's action-special
  table (the UZDoom source's `src/playsim/actionspecials.h` and dispatch table in
  `src/playsim/p_lnspec.cpp`) has a real `LS_Ceiling_MoveToValueAndCrush` at index 280, forwarding
  into the same `EV_DoCeiling` with a real (non-forced) crush value. This is the opposite of the
  Zandronum engine fork, which has no index 280 at all. There a zt-bcc call compiles to a pcode
  Zandronum reads as a different instruction, so the script's execution is corrupted (see above).

**Example — move sector tag 5's ceiling to height 256 at 1.0 map units/tic:**

```text
Ceiling_MoveToValue(5, 8, 256);
```

**Returns:** `int`, per the declared signature (`EV_DoCeiling`'s `bool` result, `1`/`0`) — whether
at least one sector matching `tag` was found and started moving.
