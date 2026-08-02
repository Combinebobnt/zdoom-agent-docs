# VectorAngle

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked against the Zandronum source's master/3.3-alpha checkout)
**Provenance:** `VectorAngle - ZDoom Wiki.html` (intake, `oldid=53344`), verified against fork source 2026-07-29.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

`fixed VectorAngle(fixed x, fixed y)` — **compiler builtin**, not an extension function. Listed in
the zt-bcc source's `src/builtin.c`'s `g_funcs[]` as `{ "vectorangle", "f;ff" }` (return fixed, two
fixed params), compiled directly to opcode `PCD_VECTORANGLE`. Implemented in
the Zandronum source's `src/p_acs.cpp`, `case PCD_VECTORANGLE:`:

```cpp
case PCD_VECTORANGLE:
    STACK(2) = R_PointToAngle2 (0, 0, STACK(2), STACK(1)) >> 16;
    sp--;
    break;
```

Returns the angle of the 2D vector `(x, y)` — equivalent to `atan2(y, x)` — as a **fixed-point
fraction of a full turn** (`0` = East, `0.25` = North, `0.5` = West, `0.75` = South, moving
counterclockwise), the same angle encoding used by `GetActorAngle`, `Sin`, and `Cos`. See
[units-and-encodings.md](../concepts/units-and-encodings.md) for that encoding in general — not
re-derived here.

## How the result is produced

`R_PointToAngle2(fixed_t x1, fixed_t y1, fixed_t x2, fixed_t y2)` (`r_utility.cpp:190`) returns an
`angle_t` — a 32-bit BAM value where a full turn is `0x100000000` (wraps in the unsigned 32-bit
space). Right-shifting by 16 keeps the top 16 bits, which is exactly the ACS 16.16 fixed-point
representation of the same fraction-of-turn (`raw_angle_t / 2^32 == (raw_angle_t >> 16) / 65536`).
This is the standard octant/slope-table `atan2` used throughout the renderer and AI code for
actor-facing/movement-angle calculations — `VectorAngle` just exposes it to ACS.

## Wiki says `int x, y` — bcc already types it correctly as `fixed`

The ZDoom wiki declares the signature as `int VectorAngle(int x, int y)`. **This is imprecise, and
bcc does not repeat the mistake**: `builtin.c` types both parameters `f` (fixed), matching
`R_PointToAngle2`'s real C++ signature (`fixed_t x1, fixed_t y1, fixed_t x, fixed_t y` —
`r_utility.h:59`). Pass genuine fixed-point map-unit deltas (e.g.
`GetActorX(tid2) - GetActorX(tid1)`), not plain small integers — a bcc-compiled call with
un-cast `int` arguments will be type-checked/coerced as fixed, so (unlike the sibling
[VectorLength](vectorlength.md), where `zcommon.bcs` itself under-types the params as `raw` and a
plain-ACS caller can silently pass bad units) this function's own compiler-side signature already
guards against the wiki's `int` framing being taken literally in bcc code.

## Edge cases (verified against `r_utility.cpp:190-198`)

- **`(0, 0)` input returns exactly `0`**, not an error or undefined value:
  `if ((x | y) == 0) { return 0; }` runs before any octant/slope logic.
- **Overflow guard**: the octant math is only exact "if the values get larger than `INT_MAX/4`"
  (source comment, `r_utility.cpp:200-203`) — i.e. `x`/`y` fixed-point deltas larger than roughly
  `±8192.0` map units in raw terms will not compute correctly. Not a realistic concern for
  on-map actor-to-actor vectors, but relevant if composing this from unbounded velocity/momentum
  values.
- **Small-magnitude precision note**: a separate call site's own comment
  (`p_effect.cpp:489`, `P_RunEffect`) states "512 is the limit below which `R_PointToAngle2` does
  no longer return usable values" when fed raw actor velocity components — i.e. inputs with both
  `|x|` and `|y|` at or below `512` (raw fixed units, `≈0.0078` map units) can yield a
  low-precision/unreliable angle from the slope-table lookup. Not independently re-derived from
  the `SlopeDiv`/`tantoangle` table math in this pass — flagging it as an engine-author-acknowledged
  caveat worth knowing if you call `VectorAngle` on very small displacement or velocity vectors.

## Example (from the wiki)

Draws a `^` at the bottom of the screen pointing toward the actor with TID `1`:

```c
script 1 ENTER
{
    int vang, angle;
    while(TRUE)
    {
        vang = VectorAngle (GetActorX (1) - GetActorX (0), GetActorY (1) - GetActorY (0));
        angle = (vang - GetActorAngle (0) + 1.0) % 1.0;

        if (angle < 0.2 || angle > 0.8)
        {
            int sx = 320 - (320 * Sin (angle) / Cos (angle));

            SetHudSize (640, 480, 0);
            HudMessage (s:"^"; HUDMSG_PLAIN, 1, CR_RED, sx * 1.0, 480.2, 0);
        }
        else
        {
            HudMessage (s:""; HUDMSG_PLAIN, 1, 0, 0, 0, 0);
        }

        Delay (1);
    }
}
```

The wiki also notes `VectorAngle` is "more commonly known as `atan2`", and that
`VectorAngle(1.0, x)` gives `atan(x)` — not independently re-derived here, but consistent with the
octant math above (`atan2(x, 1)` reduces to `atan(x)` for the principal branch).

## See also

- [VectorLength](vectorlength.md) — sibling vector function (magnitude instead of angle);
  contrast its `zcommon.bcs`/wiki `int`/`raw` mistyping against this function's correctly-typed
  `fixed` signature.
- [units-and-encodings.md](../concepts/units-and-encodings.md) — fixed-point angle encoding used
  by this function's return value.
