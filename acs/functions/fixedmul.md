# `fixed FixedMul(fixed a, fixed b)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `FixedMul - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`https://zdoom.org/w/index.php?title=FixedMul&oldid=37312`) + source-verified against the Zandronum source's `src/p_acs.cpp:11600-11601`,
`m_fixed.h:79`, `basicinlines.h:43`, and the zt-bcc source's `src/builtin.c:79/227`. No wiki/fork
discrepancy found — this ZDoom-wiki page describes a compiler builtin that Zandronum/`zt-bcc`
implements identically; the only gap is the wiki not mentioning the 64-bit-intermediate overflow
protection. The `strict namespace` exceptions below are from the zt-bcc source's
`src/codegen/expr.c:458-466` (`write_binary_fixed`), `src/semantic/phase.c:163-178` (`s_spec`) and
`src/parse/library.c:160-161`, plus a compile test at zt-bcc `d2d7da3`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Multiplies two 16.16 fixed-point numbers and returns a fixed-point result. Compiler builtin
(`PCD_FIXEDMUL`, the zt-bcc source's `src/builtin.c:79`/`:227`), implementation in
`DLevelScript::RunScript`'s main switch:

```cpp
case PCD_FIXEDMUL:
    STACK(2) = FixedMul (STACK(2), STACK(1));
```

(the Zandronum source's `src/p_acs.cpp:11600-11601`). `FixedMul` itself is `#define FixedMul
MulScale16` (the Zandronum source's `src/m_fixed.h:79`), and `MulScale16` is:

```cpp
static __forceinline SDWORD MulScale16 (SDWORD a, SDWORD b) { return (SDWORD)(((SQWORD)a * b) >> 16); }
```

(the Zandronum source's `src/basicinlines.h:43`).

- **Why this exists instead of just using `*`:** Outside a BCS `strict namespace`, the `*`
  operator does *integer* multiplication with no knowledge of fixed-point scaling. Multiplying two fixed-point values
  (each already scaled by `1<<16`) with `*` compounds the scale factor instead of correcting for
  it — the wiki's own example shows `0.5 * 0.5` printing as `16384` (i.e. `0x8000 * 0x8000` done as
  plain integer multiply, then reinterpreted through `print(f:...)`'s fixed-point formatting)
  where `FixedMul(0.5, 0.5)` correctly prints `0.25`. In plain ACS and in BCS outside a `strict
  namespace`, `FixedMul` is not a convenience wrapper. It's the only correct way to multiply two
  runtime fixed-point values there.
  Inside a BCS `strict namespace` the types are enforced, and zt-bcc compiles `*` (and `*=`) on two
  `fixed` operands to `PCD_FIXEDMUL` itself. So there `a * b` on `fixed` variables already is a
  fixed multiply.
- **Overflow behavior:** `MulScale16` does the multiply in `SQWORD` (64-bit signed) before
  shifting right by 16, not a naive 32-bit `a * b` followed by a shift. This means intermediate
  products that would overflow a 32-bit `int` (anything where `|a * b|` exceeds ~2^31 before the
  shift) do not wrap/truncate the way a hand-rolled `(a * b) >> 16` in 32-bit arithmetic would —
  the truncation to a 32-bit `SDWORD` only happens on the final, already-shifted-down result. This
  is a genuine correctness advantage over reimplementing fixed multiply by hand with 32-bit ACS
  ints, and isn't mentioned by the wiki at all.
- **Multiplying a fixed value by a plain integer is a different case:** the wiki notes `a *
  intConstant` (fixed times int, not fixed times fixed) "yields a fixed point value still" and
  that `FixedMul` must *not* be used there — this is consistent with the scaling math (fixed *
  int keeps one factor unscaled, so plain `*` already lands on the right scale) but the wiki's own
  supporting example (`int z = 1.2 * 3;`) relies on the *compiler's* constant-folding of a literal
  fixed-point expression, which is `bcc`/`zt-bcc` compile-time behavior, not something this file
  traces through `zt-bcc`'s constant-expression evaluator. Treat that specific example as
  illustrative rather than independently verified here; the `FixedMul`-vs-`*` distinction itself
  (fixed×fixed needs `FixedMul`, fixed×int doesn't) is confirmed by the scaling arithmetic above
  regardless. Inside a BCS `strict namespace`, fixed times int does not compile at all ("left-operand
  type (`int`) different from right-operand type (`fixed`)").
- Parameters and return are both `fixed` (`f;ff` in `builtin.c`'s signature table). In plain ACS
  and non-strict BCS, passing plain `int` args compiles because `int`/`fixed` share the same 32-bit
  representation. Inside a BCS `strict namespace` it is a compile error ("argument type (`int`)
  different from parameter type (`fixed`)"). Either way the *value* must already be in 16.16
  fixed-point form (a literal like `0.5`, or an `int` produced by `IntToFixed`/left-shift by 16).
  Passing a raw integer count does not do what it looks like. `FixedMul(3, 0.5)` intending "3
  times 0.5" reads the raw bits of `3` as the fixed value 3/65536, so the result is
  `(3 * 0x8000) >> 16`, the raw value `1` (1/65536), not 1.5. Use `3 * x` with plain `*` (fixed
  times int, per the previous bullet) or `FixedMul(3.0, x)` instead. In a `strict namespace`,
  write `3.0 * x`.
