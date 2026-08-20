# `==`/`!=` between a compiled string literal and a runtime-built string never matches, even with identical content

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-16)
**Provenance:** Source-verified against `zt-bcc/src/codegen/expr.c:438,468,487,588,608,615,643`
(every `BOP_EQ`/`BOP_NE` codegen path emits plain `PCD_EQ`/`PCD_NE`, no type-directed dispatch for
`str` operands) and `zt-bcc/src/codegen/pcode.c:43`; the Zandronum source's
`src/p_acs.cpp:9613-9619` (`PCD_EQ`/`PCD_NE`'s VM implementation, raw `STACK(2) == STACK(1)`
integer comparison) and `src/p_acs.h:82-103`/`src/p_acs.cpp:474-498` (`LIBRARYID_MASK`,
`STRPOOL_LIBRARYID_OR`, `ACSStringPool::AddString`); cross-checked identical in the UZDoom source's
`src/playsim/p_acs.h:82-87` and `src/playsim/p_acs.cpp:985-1017`. Found 2026-08-06 while building
and runtime-testing (headless, `xvfb-run` + a real engine binary) a fixture for a project unrelated
to this tree — see `../functions/strparam.md`'s "Interning" bullet, which documents the pool's
own content-deduplication but not this gap.

## The gap

`StrParam`'s own doc already establishes that `ACSStringPool::AddString` interns by content —
two calls that build the same text always get the same pool index. It's tempting to conclude from
that alone that `==` between any two `str` values with the same text is safe. **It is not**, the
moment either side is a *compiled string literal* rather than a pool-built string.

`==`/`!=` on `str` never does anything type-aware: `zt-bcc` compiles both operands as plain `int`s
and always emits `PCD_EQ`/`PCD_NE` (`expr.c`'s `BOP_EQ`/`BOP_NE` cases, no `str`-specific branch
anywhere in that dispatch), and the VM opcode is a raw stack-integer comparison with zero
string-content awareness (`p_acs.cpp:9613-9619`). Whether that integer comparison happens to mean
"same text" depends entirely on where each operand's index came from:

- **A string literal compiled into a `BEHAVIOR`/library** gets its index from that module's own
  static string table, tagged with that module's real (small) **library ID** in the top 12 bits
  (`LIBRARYID_MASK = 0xFFF00000`, `LIBRARYID_SHIFT = 20`).
- **Any runtime-built string** — `StrParam`, string concatenation, `PCD_TAGSTRING`, or (relevant
  to any ACS binding that forwards a ZScript/C++ `FString` back into ACS, e.g. a `ScriptCall`
  bridge returning a `str`) — comes from `GlobalACSStrings`/`ACSStringPool`, whose entries are
  **unconditionally OR'd with `STRPOOL_LIBRARYID_OR`** (`STRPOOL_LIBRARYID = INT_MAX >> 20`, i.e.
  every bit of that 12-bit field set) before being returned (`AddString`, both overloads,
  `p_acs.cpp:985-1017`).

`STRPOOL_LIBRARYID` is a reserved sentinel value specifically so pool indices can never collide
with a real module's library ID — by construction, a literal's index and a pool string's index
**can never be numerically equal even if their text is byte-identical**, because they live in
disjoint halves of the same integer space. `==`/`!=` between them is not "usually works, edge case
fails" — it is **always false for `==` / always true for `!=`, unconditionally, regardless of
content**, for any comparison that mixes a literal with a pool-origin string on either side.

Two pool-origin strings compare correctly (both sides go through the same content-deduplicating
`AddString`, so identical text really does yield identical integers — this is the case
`strparam.md` already covers). Two literals from the **same compiled module** compare correctly
too (the compiler itself can fold/dedupe identical literal text to one table slot within a
module — not verified across separately-compiled libraries in this pass, treat cross-library
literal-vs-literal `==` as unverified rather than assumed safe). **The broken case specifically is
literal-vs-pool.**

## What actually triggers this

Any of the following put a value on the "pool" side, making a subsequent `==`/`!=` against a
literal unreliable:

- `StrParam(...)` (see `strparam.md`).
- String concatenation / any other `PCD_TAGSTRING`-style "build a string at runtime" opcode.
- **A `ScriptCall`/extension-function binding that returns a `str` built from a ZScript `String` or
  a C++ `FString`** — the return value has to enter the pool somehow to become a valid ACS `str`
  handle at all, so it is pool-origin by construction, never a literal, no matter how the callee
  built it internally (even `return "some fixed text";` on the ZScript/C++ side still goes through
  `AddString` on the way back into ACS).

A caller that does `if (SomeBoundFunction(...) == "expected") ...` will observe the `if` branch as
permanently unreachable — not flaky, not content-dependent, always false — even when printing both
sides (e.g. via `Log`) shows visibly identical text. This is a silent-wrong-result bug, not a
crash: nothing in the engine surfaces a warning, and the code compiles and runs without complaint.

## The fix

Use [`StrCmp`/`StrIcmp`](../functions/strcmp.md) (`StrCmp(a, b) == 0`) for any comparison where
either side might be pool-origin — `StrCmp` resolves both handles to their actual character data
via `FBehavior::StaticLookupString` before comparing, so it is correct regardless of which side is
a literal and which is pool-built. Reserve `==`/`!=` on `str` for cases both sides are known
literals from the same compiled module (e.g. comparing a `str` parameter against a fixed set of
known-constant literals declared in that same file).

## See also

[`StrParam`](../functions/strparam.md) for the pool's own interning guarantee (correct for
pool-vs-pool, not what this page is about). [`StrCmp`/`StrIcmp`](../functions/strcmp.md) for the
comparison that's actually safe across the literal/pool boundary.
[`ScriptCall`](../functions/scriptcall.md) if present — any binding returning `str` through it
inherits this gap for its return value.
