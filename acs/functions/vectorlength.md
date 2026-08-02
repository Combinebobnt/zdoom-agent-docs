# VectorLength

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked against the Zandronum source's master/3.3-alpha checkout)
**Provenance:** `VectorLength - ZDoom Wiki.html` (intake), verified against fork source 2026-07-29.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

`fixed VectorLength(fixed x, fixed y)` — extension function (negative index `-50` in
`zt-bcc/lib/zcommon.bcs`'s `special` table). Implemented in
the Zandronum source's `src/p_acs.cpp`, `case ACSF_VectorLength:`:

```cpp
case ACSF_VectorLength:
    return FLOAT2FIXED(TVector2<double>(FIXED2DBL(args[0]), FIXED2DBL(args[1])).Length());
```

Returns the magnitude (`sqrt(x*x + y*y)`) of the 2D vector `(x, y)`, as a fixed-point value.

## Wiki/fork divergence

The ZDoom wiki page declares the signature as `int VectorLength(int x, int y)`, and
`zcommon.bcs` itself types both parameters and the return as `raw` (`VectorLength(raw,raw):raw`),
not `fixed` — unlike, e.g., `FixedSqrt(fixed):fixed` a few lines above it in the same table.
Despite that, the engine implementation unconditionally reinterprets both arguments as
**fixed-point (16.16)** via `FIXED2DBL` and returns a fixed-point result via `FLOAT2FIXED`. `raw`
in BCS means "untyped 32-bit value, no implicit-cast checking" (see zt-bcc wiki's Types page) —
it does not mean the engine treats the bits as plain integers. Concretely:

- Pass already-fixed values (actor `x`/`y` coordinates, angle/velocity components, or an
  int explicitly converted with a fixed literal/cast) as the arguments.
- Passing plain small integers (e.g. `VectorLength(3, 4)` expecting `5`) will not give the
  naive integer answer — `3` and `4` are reinterpreted as the fixed-point values `3.0/65536` and
  `4.0/65536`, so the result is a tiny fixed-point number, not `5`. Convert with `IntToFixed()`
  (or a `1.0` fixed literal multiply) first if the inputs originate as integers.

The wiki's "See Also" link to a `distance` function (for engine versions older than ZDoom r3883)
does not exist anywhere in this fork — no `ACSF_Distance`/`PCD_DISTANCE` entry and no `distance`
name in `zcommon.bcs` or `builtin.c`. Treat that cross-reference as inapplicable to Zandronum.

## Example (from the wiki, adapted)

```c
// 3D vector length by composing two 2D calls.
function fixed VLength3d(fixed x, fixed y, fixed z)
{
    fixed len = VectorLength(x, y);
    len = VectorLength(z, len);
    return len;
}
```

## See also

- `FixedSqrt` (`zcommon.bcs` index `-49`) — plain fixed-point square root, if you already have
  `x*x + y*y` computed and just need the root.
