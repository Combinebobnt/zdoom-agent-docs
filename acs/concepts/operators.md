# Operators: short-circuit evaluation, divide/modulus-by-zero, and fixed-point `++`/`--`

**Tier:** A (all three claims traced to the actual codegen/semantic/interpreter source, not inferred from the wiki or from signatures).
**Applies to:** UZDoom=yes, Zandronum=yes — the short-circuit, fixed-point `++`/`--` and `str + str` findings are `zt-bcc` toolchain behavior rather than engine behavior, and hold whichever engine ends up running the emitted bytecode. The Zandronum entry below reads a `master` HEAD checkout whose own `version.h` reports `3.3-alpha`, a development snapshot ahead of the 3.2.1 target; this is core interpreter-loop behavior, stable across that gap.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-16)
**Provenance:** `zt-bcc/src/codegen/expr.c` (`write_logical` short-circuit codegen and its own comment, line ~658; `inc_var`/`inc_fixed`/`inc_indexed`, line ~1168-1235), `zt-bcc/src/semantic/expr.c` (`perform_primitive_inc`, line ~1465), and the Zandronum source's `src/p_acs.cpp` (`PCD_DIVIDE` line 9589, `PCD_MODULUS` line ~9601-9604, `PCD_ANDLOGICAL`/`PCD_ORLOGICAL` line ~10594-10602, the divide/modulus-by-zero console-print-and-`SCRIPT_PleaseRemove` handling around line 13018-13027), verified against the ZDoom wiki's `Operators - ZDoom Wiki.html` (https://zdoom.org/w/index.php?title=Operators&oldid=51290) intake page.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

The ZDoom wiki's [Operators](https://zdoom.org/w/index.php?title=Operators&oldid=51290) page
lists the full operator set (`=`, arithmetic, bitwise, relational, `&&`/`||`, `!`, `++`/`--`,
compound assignment) with a one-line description and a usage snippet each — accurate as far as it
goes, but it's a base-ACS page that frames everything in terms of plain `int`, doesn't say whether
`&&`/`||` evaluate both sides, and is vague about what "will cause an error" means for division by
zero. Three things below aren't obvious from that page and needed reading `zt-bcc`'s codegen and
Zandronum's VM loop to pin down. Signed-shift (`>>`) and truncated-division-sign (`%`) semantics
are **not** repeated here — see [Integer arithmetic](integer-arithmetic.md) (tier A) for those.

## `&&` and `||` genuinely short-circuit

Confirmed directly in `zt-bcc/src/codegen/expr.c`'s `write_logical()`, which carries its own
comment: `// Logical-or and logical-and both perform shortcircuit evaluation.` The right operand
is compiled behind a conditional jump (`PCD_IFGOTO` for `&&`, `PCD_IFNOTGOTO` for `||`) over the
left operand's value, not evaluated unconditionally and then combined — e.g. for `x && y`, if `x`
is falsy the jump skips straight past `y`'s bytecode entirely.

**Practical consequence:** a right operand with a side effect (a function call that increments a
counter, calls `SetResultValue`, etc.) will **not** run when the left operand already determines
the result — `x != 0 && DoSomething()` never calls `DoSomething()` when `x == 0`. This matches C's
short-circuit rules and is probably what most authors assume, but it's worth stating explicitly
because the wiki page never says so, and the engine separately exposes non-short-circuiting
`PCD_ANDLOGICAL`/`PCD_ORLOGICAL` opcodes (`p_acs.cpp`, plain `STACK(2) = STACK(2) && STACK(1)` /
`||`) that `bcc` never emits for `&&`/`||` — those opcodes exist for other producers of ACS
bytecode (e.g. the original `acc`), not this toolchain, so don't infer non-short-circuit behavior
from their presence in the engine's opcode table.

## Divide-by-zero and modulus-by-zero terminate the script, they don't crash the engine

`PCD_DIVIDE` and `PCD_MODULUS` in `p_acs.cpp` both check the divisor and, on zero, set the VM
`state` to `SCRIPT_DivideBy0`/`SCRIPT_ModulusBy0` instead of performing the C++ `/`/`%` (which
would otherwise be undefined behavior at the CPU level for real division-by-zero). After the
current instruction dispatch, the interpreter prints `"Divide by zero in <script>"` /
`"Modulus by zero in <script>"` to the console and forces `state = SCRIPT_PleaseRemove` — i.e. the
**offending script instance is terminated**, not the engine, not the map, and not with a catchable
ACS-level error. Other running scripts are unaffected. This is a firmer, more mechanical claim
than the wiki's "will cause an error" — there's no possibility of catching or recovering from it
from within ACS; guard the divisor/modulus operand before the operation if the value can be
attacker- or data-controlled (e.g. a map-computed denominator).

## `++`/`--` are fixed-point-aware — they don't naively touch the raw storage word

This one *looks* like a footgun from a shallow read of the engine tables (`PCD_INCSCRIPTVAR` is
literally `++locals[N]` on the raw `int32_t` word — that would add `1` (the smallest possible
fixed-point fraction, 1/65536) rather than `1.0` if applied naively to a `fixed` variable) but
`bcc` actually special-cases it correctly: `zt-bcc/src/semantic/expr.c`'s `perform_primitive_inc()`
sets `inc->fixed = (operand->type.spec == SPEC_FIXED)`, and `zt-bcc/src/codegen/expr.c`'s
`inc_fixed()` compiles a fixed `x++`/`x--` as push-`65536`-then-add/subtract (`AOP_ADD`/`AOP_SUB`)
instead of emitting the raw `PCD_INC*VAR`/`PCD_INC*ARRAY` opcode family. So `fixedVar++` adds a
true `1.0`, matching what you'd expect from `fixedVar += 1.0`, for both plain fixed variables and
fixed array elements. This distinction only exists because `fixed` is a `bcc`/BCS extension type
absent from base ACS and the ZDoom wiki page's examples — worth recording precisely because the
"obvious" inference from the raw opcode table is wrong.

## `==`/`!=` on `str` is a raw index comparison, not a content comparison

No type-directed dispatch exists for `str` operands — both compile to the same `PCD_EQ`/`PCD_NE`
used for `int`, a plain stack-integer comparison. This is safe between two runtime-built
(`StrParam`/pool-origin) strings, but **always false/true respectively** when one
side is a compiled string literal and the other is pool-origin, even with byte-identical text —
the two live in disjoint index ranges by construction (a reserved library-ID tag on every
pool-origin string). See
[String literal vs. pool equality](string-literal-vs-pool-equality.md) for the full mechanism and
[`StrCmp`/`StrIcmp`](../functions/strcmp.md) for the comparison that's actually safe across that
boundary.

## `+` on `str` only concatenates when BOTH operands are literal constants — otherwise it silently adds pool indices as integers

A `zt-bcc` compiler bug (confirmed via raw opcode disassembly), not an engine issue.
`"literal" + "literal"` correctly constant-folds to a real concatenated string at compile time,
but `variable + variable` (or any operand that isn't itself compile-time-constant) compiles to a
plain `ADD` on the two operands' raw pool-index integers — never reaching the print-based
concatenation codegen path (`concat_str()`) that exists in `zt-bcc`'s own source and looks like it
should handle this. The result is a bogus index that almost always reads back as an empty string,
with no compile or runtime error. See
[String `+` operator variable bug](string-concat-operator-variable-bug.md) for the full evidence
and the fix (`StrParam`'s format-item list instead of `+`).
