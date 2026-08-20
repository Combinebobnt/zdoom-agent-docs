# Integer arithmetic: signedness, shifts, and modulus

**Tier:** A (both claims traced directly to the relevant `PCD_*` opcode implementations in `p_acs.cpp` on each engine, not wiki-sourced or inferred; the Zandronum read is against that source's `master` HEAD, a `3.3-alpha` development snapshot ahead of the 3.2.1 target — this is core VM instruction behavior, stable across that gap).
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-16)
**Provenance:** derived directly from the Zandronum source's `src/p_acs.cpp` (`PCD_RSHIFT` line 10635, `PCD_MODULUS` line 9601, `FACSStackMemory` typedef line 359) while reviewing a hand-ported Mersenne Twister implementation in a real project's script that assumed unsigned 32-bit shift/modulus semantics throughout. Cross-checked that BCS has no unsigned type or logical-shift operator via `zt-bcc.wiki/Types.md` and `Grammar.md`.

There is no `unsigned` type in BCS/ACS — `int` (and `raw`) are always signed 32-bit
(confirmed: `zt-bcc.wiki/Types.md` lists only `int`, `fixed`, `bool`, `str` as primitives, no
unsigned variant, and no `>>>`/logical-shift operator exists in the grammar). This matters
because it makes two operators behave differently than a port from a spec written against
`uint32_t` (e.g. a textbook algorithm) would assume.

## `>>` is an arithmetic (sign-extending) shift, not a logical one

`PCD_RSHIFT` in `p_acs.cpp` is implemented as plain C++ `STACK(2) = STACK(2) >> STACK(1)` where
the stack is `int32_t` (`FACSStackMemory = BoundsCheckingArray<int32_t, STACK_SIZE>`,
`p_acs.cpp:359`). Right-shifting a negative `int32_t` in C++ is sign-extending on every mainstream
compiler target (GCC/Clang/MSVC on x86/ARM) — so `x >> n` in ACS fills the top `n` bits with the
sign bit, not with zero, whenever `x` is negative (bit 31 set).

**Practical consequence:** any algorithm that treats its operand as an *unsigned* 32-bit word and
relies on `x >> n` zero-filling from the left (bit manipulation, hashing, PRNGs like Mersenne
Twister, CRCs, etc.) will silently diverge from spec on every call where the operand's sign bit
happens to be set — roughly half of all values in a well-mixed bit pattern. There is no built-in
logical-shift operator to reach for instead; the workaround is to mask after shifting with a
literal (not a shifted `-1`, which is itself corrupted by the same bug — see below):

```text
// WRONG: intended to build a 0x7FFFFFFF mask, actually stays 0xFFFFFFFF
int lower_mask = 0xffffffff >> 1; // -1 >> 1 == -1 (sign-extended), not 0x7fffffff

// RIGHT: use the literal directly, or mask after an arithmetic shift
int lower_mask = 0x7fffffff;
int logical_shift_11 = (x >> 11) & 0x001fffff; // zero out the 11 sign-extended bits
```

## `%` follows C-style truncated division (sign follows the dividend), and traps on zero

`PCD_MODULUS` (`p_acs.cpp:9601`) does `STACK(2) = STACK(2) % STACK(1)` on `int32_t`, i.e. plain
C++ `%`: the result's sign matches the *dividend's* sign, and it can be negative or zero — it does
**not** floor to a non-negative remainder the way e.g. Python's `%` does. `x % 0` doesn't crash the
engine: it sets the script's ACS-VM `state` to `SCRIPT_ModulusBy0`, which halts the interpreter
loop at that instruction. It is **not silent** — once the loop exits, the engine prints a
`Modulus by zero in <script presentation>` line to the console, then flips the state to
`SCRIPT_PleaseRemove` and unlinks the script, killing that run outright. There is no catchable
error and no resumption; a `Divide by zero` on `/` takes the identical path via `SCRIPT_DivideBy0`.

**Practical consequence:** `SomeValueThatCanBeNegative() % N` does not land in `[0, N-1]` — it
lands in `(-N, N)` with the sign of the value being reduced. Any "map a value into an inclusive
range" pattern like `(v % (max - min + 1)) + min` silently produces results below `min` (as low as
`min - (max - min)`) whenever `v` is negative. If `v` comes from a bit-manipulation routine whose
output is meant to be read as a full-range unsigned 32-bit word (again, e.g. a ported PRNG), around
half its outputs will be "negative" as a signed ACS int and this bug will fire on roughly half of
all calls. Guard with `((v % N) + N) % N` (still using this same signed `%`, but now guaranteed
non-negative) or mask/`abs()` before the modulus, depending on what distribution you actually want.
