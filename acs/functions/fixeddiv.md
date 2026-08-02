# FixedDiv

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked against the Zandronum source's master/3.3-alpha checkout; the macro chain involved is old Build-engine-derived code unlikely to have changed across that gap).
**Provenance:** `_intake/FixedDiv - ZDoom Wiki.html` (zdoom.org, oldid 37311), verified against engine source 2026-07-28.
**Bucket:** Compiler builtin (`zt-bcc/src/builtin.c` `g_funcs[]` entry `"fixeddiv", "f;ff"` → `PCD_FIXEDDIV`).

`fixed FixedDiv(fixed a, fixed b)`

## Usage

Divides fixed-point `a` by fixed-point `b`, returning a fixed-point result. Do not use the plain
`/` operator for fixed/fixed division expecting a fixed-point result — integer division truncates
the raw 16.16 representation and gives a near-zero garbage value (the wiki's own example:
`1.0 / 0.5` prints `0.000030518`, not `2.0`). Dividing a fixed value by a plain **int** is fine
with `/` and does not need `FixedDiv`.

## Implementation and failure behavior (not on the wiki)

`PCD_FIXEDDIV` (`p_acs.cpp`) calls the engine's `FixedDiv`, which is `#define`d to
`SafeDivScale16` (`m_fixed.h`) — a *saturating*, not a *trapping*, divide:

```c
inline SDWORD SafeDivScale16 (SDWORD a, SDWORD b)
{
    if ((DWORD)abs(a) >> 15 >= (DWORD)abs(b))
        return (a^b) < 0 ? FIXED_MIN : FIXED_MAX;
    return DivScale16(a, b);
}
```

Consequences worth knowing before assuming this behaves like a normal division:

- **Division by zero does not crash, trap, or throw an ACS error.** When `b == 0`, the guard
  condition `abs(a) >> 15 >= abs(b)` reduces to `abs(a) >> 15 >= 0`, which is always true, so the
  function *always* takes the saturation branch — it returns `FIXED_MAX` (`0x7fffffff`, i.e. the
  largest representable fixed value) when `a` and `b` have the same sign (including `a == 0`,
  `b == 0`, since `0 ^ 0 = 0` is not `< 0`), or `FIXED_MIN` (`0x80000000`) when they'd have
  differed in sign. There is no way to distinguish "true division by zero" from "result would
  have overflowed" from the return value alone — both saturate to the same two sentinel values.
- **Near-overflow also saturates instead of wrapping.** If `abs(a)` is large enough relative to
  `abs(b)` that the true fixed-point quotient wouldn't fit in 32 bits (roughly `|a/b| >= 32768`
  in real-number terms, since the check is against `abs(a) >> 15`), the result silently clamps
  to `FIXED_MAX`/`FIXED_MIN` rather than wrapping around to a nonsense value the way raw integer
  overflow would. This is what "Safe" in `SafeDivScale16` refers to.
- Ordinary in-range divisions fall through to `DivScale16(a, b)`, i.e. `(a << 16) / b` at full
  precision — standard 16.16 fixed-point division, nothing unusual.

## Parameters

- `a` — fixed-point dividend.
- `b` — fixed-point divisor.

## Return value

`a / b` as a fixed-point value, or a saturated `FIXED_MAX`/`FIXED_MIN` sentinel per the failure
behavior above (including for `b == 0`).

## See also

- `FixedMul` (`#define`d to `MulScale16`, the multiplication counterpart — not similarly guarded
  against overflow the same way since `zcommon.bcs` also uses `PCD_FIXEDMUL`; not verified in
  this pass).
