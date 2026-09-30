# `==`/`!=` between a compiled string literal and a runtime-built string: never matches outside a `#library` module

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-29); Zandronum 3.3-alpha @bdd0f7beb (2026-09-29)
**Provenance:** Source-verified against `zt-bcc/src/codegen/expr.c:438,468,487,588,608,615,643`
(every `BOP_EQ`/`BOP_NE` codegen path emits plain `PCD_EQ`/`PCD_NE`, no type-directed dispatch for
`str` operands), `zt-bcc/src/codegen/expr.c:2175-2184` (`c_push_string`: `PCD_TAGSTRING` after
every literal when the main library is `importable`), `zt-bcc/src/parse/library.c:718-730`
(`read_library`: `#library` sets `importable`), `zt-bcc/src/codegen/chunk.c:97-103` (`MSTR`/`ASTR`/
`ATAG` chunks written only for an importable library), `zt-bcc/src/codegen/stmt.c:344-375`
(`write_string_switch`) and `zt-bcc/src/codegen/pcode.c:43`; the Zandronum source's
`src/p_acs.cpp:9613-9619` (`PCD_EQ`/`PCD_NE`, raw `STACK(2) == STACK(1)` integer comparison),
`src/p_acs.cpp:9266-9269` (`PCD_TAGSTRING`), `src/p_acs.cpp:2588-2660` (`MSTR`/`ASTR`/`ATAG` load-time
pooling), `src/p_acs.cpp:2350` (`LibraryID`), `src/p_acs.cpp:3318-3330` (`StaticLookupString`),
`src/p_acs.h:98-103` and `src/p_acs.cpp:474-498` (`LIBRARYID_MASK`, `STRPOOL_LIBRARYID_OR`,
`ACSStringPool::AddString`); the UZDoom source's `src/playsim/p_acs.h:82-87`,
`src/playsim/p_acs.cpp:985-1017` (`AddString`), `:7074-7077` (`PCD_TAGSTRING`), `:7443`
(`PCD_EQ`) and `:2515-2585` (load-time pooling), all equivalent; and the ACC checkout's `parse.c`
string-literal case (described, not quoted: ACC is not open source). Found 2026-08-06 while
building and runtime-testing (headless, `xvfb-run` + a real engine binary) a fixture for a project
unrelated to this tree. Scope corrected 2026-09-29: the first version said a literal never equals
a pool string in any module, which is wrong for `#library` modules.

## The gap

`StrParam`'s own doc already establishes that `ACSStringPool::AddString` interns by content.
Two calls that build the same text always get the same pool index. It's tempting to conclude from
that alone that `==` between any two `str` values with the same text is safe. **That only holds
when both sides are pool strings.** Whether a compiled string literal is a pool string depends on
how its module was compiled.

`==`/`!=` on `str` never does anything type-aware: `zt-bcc` compiles both operands as plain `int`s
and always emits `PCD_EQ`/`PCD_NE` (`expr.c`'s `BOP_EQ`/`BOP_NE` cases, no `str`-specific branch
anywhere in that dispatch), and the VM opcode is a raw stack-integer comparison with zero
string-content awareness (`p_acs.cpp:9613-9619`). So the comparison means "same text" only when
both integers came from the same interning scheme:

- **Any runtime-built string** comes from `GlobalACSStrings`/`ACSStringPool`, whose entries are
  **unconditionally OR'd with `STRPOOL_LIBRARYID_OR`** (`STRPOOL_LIBRARYID = INT_MAX >> 20`,
  `0x7FF`, the largest 12-bit value a positive `int` can carry in its top bits) before being
  returned. That covers `StrParam`, string concatenation, `PCD_TAGSTRING`, and the return value
  of any function handing a string back to ACS (`GetActorClass`, `GetCVarString`, a `ScriptCall`
  bridge returning a ZScript `String`, and so on).
- **A string literal in a module compiled without `#library`** (typically a map's own
  `BEHAVIOR`) is pushed as the raw index into that module's own string table, with nothing in the
  top 12 bits. The VM resolves such an index through module 0, the first module loaded: the
  map's `BEHAVIOR` when the map has one, since it loads before any `LOADACS` library
  (`StaticLookupString`, `p_acs.cpp:3318-3330`; `LibraryID` is the module's load order shifted
  left 20, `p_acs.cpp:2350`).
- **A string literal in a module compiled with `#library`** is a pool string. Both compilers
  follow every literal with `PCD_TAGSTRING` when compiling a `#library` file: `zt-bcc`'s
  `c_push_string` emits it whenever the main library is `importable`, which `#library` sets
  (`library.c`'s `read_library`), and ACC does the same when it is in exporting mode. Both engines
  now implement `PCD_TAGSTRING` as "look the literal up in the running module's table and
  `AddString` its text" (Zandronum `p_acs.cpp:9266-9269`, UZDoom `p_acs.cpp:7074-7077`; the old
  "OR in the library ID" line is commented out in both). A `#library` module's `str` map
  variables and array elements initialized from literals are pooled the same way at load time,
  from the `MSTR`/`ASTR`/`ATAG` chunks (Zandronum `p_acs.cpp:2588-2660`). That load-time pass only
  runs for a module with a nonzero `LibraryID`, so it skips module 0 (see the exception below).

`STRPOOL_LIBRARYID` is a reserved sentinel that can never collide with a real module's library ID,
so a raw literal index and a pool index **can never be numerically equal even if their text is
byte-identical**. The two live in disjoint halves of the same integer space.

## Which comparisons work

| Left | Right | `==` compares text? |
|---|---|---|
| Pool string (runtime-built) | Pool string | Yes (content-interned; this is the case `strparam.md` covers) |
| Literal in a `#library` module | Pool string | Yes: the literal was pooled by `PCD_TAGSTRING` |
| Literal in a `#library` module | Literal in any `#library` module | Yes: both pooled, even across libraries |
| Literal in a non-library module | Literal in the same module | Yes when the compiler dedupes the text to one table slot |
| Literal in a non-library module | Pool string | **No: always false for `==`, always true for `!=`** |
| Literal in a non-library module | Literal from a `#library` module | **No**: raw index vs pool index |

**Exception for a `#library` module loaded as module 0** (a map `BEHAVIOR` compiled with
`#library`, or the first `LOADACS` library on a map without a `BEHAVIOR`): its literals in
expressions are still pooled by `PCD_TAGSTRING`, but its `str` map variables and array elements
initialized from literals stay raw indices, because the load-time pass is skipped. So inside that
one module, `initializedVar == "text"` is always false even when the text matches.

The last table row is easy to miss: a map script that passes a literal into a library function
(`LibFunc("red")`) hands the library a raw index. If the library then does `if (arg == "red")`, its
own literal is pooled and the comparison is always false.

A `switch` on a `str` in `zt-bcc` is safe everywhere: it compiles each `case` to a `StrCmp` call
(`stmt.c`'s `write_string_switch`), not an integer comparison.

## What actually triggers the broken case

Any `==`/`!=` in a module **compiled without `#library`** where one side is a literal and the other
is any of:

- `StrParam(...)` (see `strparam.md`), or string concatenation.
- A built-in that returns a string (`GetActorClass`, `GetCVarString`, `GetWeapon`, and the like).
- **A `ScriptCall`/extension-function binding that returns a `str` built from a ZScript `String` or
  a C++ `FString`.** The return value has to enter the pool to become a valid ACS `str` handle at
  all, so it is pool-origin by construction, however the callee built it.

A caller that does `if (GetActorClass(0) == "SomeClass") ...` in map `BEHAVIOR` will find the `if`
branch permanently unreachable: not flaky, not content-dependent, always false, even when printing
both sides (e.g. via `Log`) shows identical text. This is a silent wrong result, not a crash:
nothing surfaces a warning, and the code compiles and runs without complaint. The same line inside
a `#library` file compares correctly.

## The fix

Use [`StrCmp`/`StrIcmp`](../functions/strcmp.md) (`StrCmp(a, b) == 0`) whenever the code might be
compiled outside `#library`, or might compare against a string handed in from another module.
`StrCmp` resolves both handles to their actual character data via `FBehavior::StaticLookupString`
before comparing, so it is correct regardless of where each side came from. `==` on `str` is
reliable only inside a `#library` module comparing values that originated there or in the pool.

## See also

[`StrParam`](../functions/strparam.md) for the pool's own interning guarantee.
[`StrCmp`/`StrIcmp`](../functions/strcmp.md) for the comparison that's safe across the
literal/pool boundary. [Libraries](libraries.md) for `#library` itself.
[`ScriptCall`](../functions/scriptcall.md) if present: any binding returning `str` through it
returns a pool string.
