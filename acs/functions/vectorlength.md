# `fixed VectorLength(fixed x, fixed y)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki `VectorLength` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=VectorLength&oldid=54145) + verified against
the Zandronum source's `src/p_acs.cpp` (`case ACSF_VectorLength:`) and `src/m_fixed.h`
(`FIXED2DBL`/`FLOAT2FIXED` macros).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index `-50` in `zt-bcc/lib/zcommon.bcs`'s `special` table;
dispatched as `ACSF_VectorLength`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Implemented in the Zandronum source's `src/p_acs.cpp`, `case ACSF_VectorLength:`:

```cpp
case ACSF_VectorLength:
    return FLOAT2FIXED(TVector2<double>(FIXED2DBL(args[0]), FIXED2DBL(args[1])).Length());
```

Returns the magnitude (`sqrt(x*x + y*y)`) of the 2D vector `(x, y)`.

The function is **scale-invariant** — it produces the same result whether its inputs are
interpreted as fixed-point coordinates or as plain integers. Mathematically:

```text
VectorLength(a, b) = FLOAT2FIXED( sqrt((a/65536)² + (b/65536)²) )
                   = round( 65536 · √(a²+b²)/65536 )
                   = round( √(a²+b²) )
```

So `VectorLength(3, 4)` returns `5` (rounded), regardless of whether `3` and `4` are fixed-point
`3.0` and `4.0` or plain integers. This is why the ZDoom wiki's `int VectorLength(int x, int y)`
and the compiler's `zcommon.bcs` declaration `VectorLength(raw,raw):raw` are both defensible. The
`raw` type in BCS means "untyped 32-bit value, no implicit-cast checking" (see zt-bcc wiki's
Types page), which is appropriate here because the function's behavior is independent of the
input interpretation — the type system need not enforce fixed-point strictness.

**Contrast:** `FixedSqrt` (at the same table, index `-49`) is **not** scale-invariant — it's
`FLOAT2FIXED(sqrt(FIXED2DBL(arg0)))`, which has degree ½. `FixedSqrt(4)` returns
`round(65536 · sqrt(4/65536)) ≈ 512`, not `2`. This degree-2 difference is exactly why `FixedSqrt`
is typed `fixed:fixed` in `zcommon.bcs` (enforcing fixed input for sensible results), while
`VectorLength` is not.

## Precision and overflow

- **Rounding:** Results are rounded to the nearest integer via `xs_CRoundToInt`, using round-to-even
  (banker's rounding) for ties.
- **Overflow:** The maximum reachable length is `√2 · 32767.99998 ≈ 46341`, exceeding the
  fixed-point output range (~32768). Overflow is reachable with legal fixed-point inputs (e.g., a
  diagonal across full map coordinates). **There is no saturation:** results above ~32768.0 wrap
  around due to signed 32-bit integer overflow.

The wiki's "See Also" link to a `distance` function (for engine versions older than ZDoom r3883)
does not exist anywhere in the Zandronum engine fork or the zt-bcc compiler fork — no
`ACSF_Distance`/`PCD_DISTANCE` entry and no `distance` name in `zcommon.bcs` or `builtin.c`.
Treat that cross-reference as inapplicable to Zandronum. The same absence holds on UZDoom: no
`ACSF_Distance` case in `src/playsim/p_acs.cpp`.

## Example

```acs
// Compute 3D vector length by composing two 2D calls.
// VectorLength(x, y) computes sqrt(x² + y²), so calling it twice computes sqrt(z² + sqrt(x² + y²)²).
function fixed VLength3d(fixed x, fixed y, fixed z)
{
    fixed len = VectorLength(x, y);   // len = sqrt(x² + y²)
    len = VectorLength(z, len);       // len = sqrt(z² + len²)
    return len;
}
```

## See also

- `FixedSqrt` (`zcommon.bcs` index `-49`) — plain fixed-point square root, if you already have
  `x*x + y*y` computed and just need the root.
