# `str + str` silently does raw integer addition instead of concatenation, unless both operands are literal constants

**Tier:** B
**Applies to:** N/A — zt-bcc code-generation bug; the corrupt bytecode is identical regardless of
which engine (Zandronum/UZDoom) eventually runs it, so there is no engine-specific behavior to
stamp a version against.
**Verified against:** none
**Compiler:** `zt-bcc` 0.10.0-alpha-8 (`bcc -version`; installed via a `/usr/bin/bcc` wrapper script
invoking `/usr/libexec/zt-bcc -i /usr/share/bcc/lib`, library files diff-clean against a
`~/source/zt-bcc` checkout at commit `d2d7da3`).
**Provenance:** Found 2026-08-06/07 while building an in-game test fixture for an unrelated
project, when a "several-KB adversarial string" built via 20 chained `+` operations came back
empty (length 0) after a real round-trip on real hardware. Root-caused by disassembling the actual
compiled bytecode with `~/source/acs_decompile`'s `disasm.disassemble_entry`/`format_instr` (raw
opcode dump, not the higher-level decompiler output, which was misleading here - see below) rather
than trusting `zt-bcc`'s own source, which reads as though this should work correctly.

## The gap

`zt-bcc`'s source (`src/semantic/expr.c`'s `perform_bop_primitive`, `BOP_ADD` case) type-checks
`str + str` correctly, setting `binary->operand_type` to mark it for string-concatenation codegen,
and `src/codegen/expr.c` has a real `concat_str()` function (present since at least 2016,
`git log`) that builds the result via `PCD_BEGINPRINT`/`PCD_PRINTSTRING`/`PCD_PRINTSTRING`/
`PCD_SAVESTRING` - the same, working mechanism `StrParam` uses. Reading the source alone gives no
reason to expect a problem.

**Empirically, only one of the two ways to reach `str + str` actually uses that path:**

- **Both operands compile-time-constant (e.g. two string literals directly, `"abc" + "def"`):**
  correctly **constant-folded** at compile time into a single new literal - disassembly confirms
  this compiles to a plain `PUSHBYTE`/`ASSIGNSCRIPTVAR` of the pre-computed concatenated string's
  index, no `ADD`, no `PRINTSTRING` sequence, no runtime cost. This works.
- **At least one operand is a `str`-typed local variable holding a value that isn't itself
  compile-time-constant** (the overwhelmingly common real case - e.g. `str chunk = "abc"; str two
  = chunk + chunk;`, or building a string incrementally in a loop): compiles to a plain, raw
  **`ADD` opcode** on the two operands' underlying integer values (the string-pool index numbers),
  **never reaching `concat_str`/the print-based codegen path at all.** The `ADD`'s numeric result
  is then treated as if it were a valid string-pool index by whatever consumes it - almost always
  invalid (the sum of two real indices rarely equals a third real index), so the "concatenated"
  value silently reads back as an empty string (or, worse, whatever unrelated string happens to
  live at that coincidental index) with **no compile error, no runtime error, no warning of any
  kind.**

## Confirmed via raw disassembly (not the higher-level decompiler)

This one is easy to mis-diagnose because `acs_decompile`'s *pretty* output (`--target bcs`) prints
`l1 = l0 + l0;` for the broken case - which *reads* like a plausible string-concat expression and
doesn't itself reveal that the underlying opcode is a raw `ADD`, not a print-sequence. The
distinction only becomes obvious from the raw instruction stream:

```text
; str chunk = "abc"; str two = chunk + chunk;   -- BROKEN
PUSHBYTE       [1]
ASSIGNSCRIPTVAR[0]      ; chunk = "abc"'s pool index
PUSHSCRIPTVAR  [0]
PUSHSCRIPTVAR  [0]
ADD            []       ; <-- plain integer add, not PCD_BEGINPRINT/PRINTSTRING/SAVESTRING
ASSIGNSCRIPTVAR[1]      ; two = (garbage index)
```

```text
; str two = "abc" + "def";                       -- WORKS (constant-folded)
PUSHBYTE       [3]      ; pre-computed index of the new literal "abcdef"
ASSIGNSCRIPTVAR[0]
```

## The fix

Use [`StrParam`](../functions/strparam.md)'s format-item list instead of `+` for any string
concatenation involving a non-constant operand: `StrParam(s:a, s:b, s:c, ...)` builds the result
via the same underlying print-based mechanism `concat_str` was *supposed* to use, and is confirmed
working (round-tripped a 1980-byte, non-ASCII, 20-chunk string byte-for-byte through a real disk
write/read cycle on real hardware, 2026-08-07). `StrParam` takes an arbitrary number of format
items in one call, so this isn't a design downgrade even for building up long strings from many
pieces - just don't reach for `+` unless every operand is a literal constant.

## See also

[String literal vs. pool equality](string-literal-vs-pool-equality.md) - a different, unrelated
`str`-handling gap found in the same investigation (that one is engine-side, about `==`/`!=`
comparison, not compiler-side codegen for `+`). [`StrParam`](../functions/strparam.md) for the
working concatenation mechanism.
