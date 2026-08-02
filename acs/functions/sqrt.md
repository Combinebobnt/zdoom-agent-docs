# Sqrt

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked against the Zandronum source's master/3.3-alpha checkout; both `ACSF_Sqrt`/`ACSF_FixedSqrt` are plain math wrappers with no netcode surface, so the 3.2.1-vs-3.3-alpha gap is not a concern here).
**Provenance:** `_intake/Sqrt - ZDoom Wiki.html` (zdoom.org, oldid 50468), verified against engine source 2026-07-29.
**Bucket:** Extension function (`zcommon.bcs` `special` table, index -48 for `Sqrt`, index -49 for `FixedSqrt` — both negative).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

`int Sqrt(int number)`
`fixed FixedSqrt(fixed number)`

## Usage

Both are real, implemented `ACSF_*` cases in `p_acs.cpp` (not a never-backported stub like
`SpawnParticle`/`GetMaxInventory`/`StrArg` elsewhere in this fork) — `Sqrt` takes/returns a plain
`int`, `FixedSqrt` takes/returns a `fixed`:

```c
case ACSF_Sqrt:
    return xs_FloorToInt(sqrt(double(args[0])));

case ACSF_FixedSqrt:
    return FLOAT2FIXED(sqrt(FIXED2DBL(args[0])));
```

`FixedSqrt` is a straightforward 16.16 fixed round-trip (`FIXED2DBL`/`FLOAT2FIXED` are the
ordinary `/65536.0` and `xs_Fix<16>::ToFix` conversions used everywhere else in this fork — see
`FixedDiv`'s doc) and behaves exactly like the wiki describes for non-negative input.

## `Sqrt`'s return value is truncated (floored), not rounded, despite the wiki's wording

The wiki's "Return value" section says `Sqrt` gives "the rounded integer... square root of the
number," implying round-to-nearest. That is not what this fork (or, going by the same
`xs_FloorToInt` call, upstream ZDoom) actually does. `xs_FloorToInt` is documented in its own
header (`xs_Float.h`) as `// Round down`, and its magic-number implementation is the standard
"subtract ~0.5, then round" floor trick — it truncates towards negative infinity, it does not
round to the nearest integer.

For a perfect square this is invisible (e.g. `Sqrt(9)` is `3` either way), but for anything else
it matters: `Sqrt(3)` returns `1` (`sqrt(3.0) = 1.732...`, floored to `1`), not `2` as "rounded"
would imply. Anywhere the exact boundary matters (e.g. deciding whether `n` is itself a perfect
square by comparing `Sqrt(n)*Sqrt(n) == n`), this floor behavior is actually what you want and
happens to make that idiom correct — but don't rely on the wiki's "rounded" phrasing if you need
true nearest-integer rounding instead.

## Negative input is unspecified, not a clean `0` or error

Neither case guards against a negative argument. `sqrt()` of a negative `double` is `NaN` in
C++, and both `xs_FloorToInt(NaN)` and `FLOAT2FIXED(NaN)` feed that `NaN` through the same
magic-number float-to-int bit-manipulation trick that `xs_Float.h` itself notes is unsafe outside
its designed range (see the comment above `xs_CRoundToInt`'s magic-number path). The result is an
unspecified garbage integer/fixed value, not a guaranteed `0`, `-1`, or ACS-level error — if
`number` can be negative in your script, clamp it yourself before calling either function instead
of assuming a safe fallback.

## Parameters

- `number` — value to take the square root of; `int` for `Sqrt`, `fixed` for `FixedSqrt`.
  Negative values are not handled safely (see above).

## Return value

- `Sqrt`: the square root of `number`, **floored** to the next lower integer (not rounded).
- `FixedSqrt`: the square root of `number`, as a normal 16.16 fixed-point value (true fractional
  precision, no floor/round distinction to worry about the way the int form has).

## See also

- `FixedDiv` (`functions/fixeddiv.md`) — same `FIXED2DBL`/`FLOAT2FIXED` conversion macros used
  here.
- The wiki page's "Manual calculation" section (pure-ACS Newton's-method/bisection `sqrt()`
  helper functions for engines predating this extension function) is moot for this fork —
  `ACSF_Sqrt`/`ACSF_FixedSqrt` are real and implemented, so there's no need to hand-roll one.
