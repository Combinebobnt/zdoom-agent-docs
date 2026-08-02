# Constants

**Tier:** A
**Engine:** Zandronum 3.2.1 (compiled BCS output's target); the preprocessor/enum behavior itself was verified against the `zt-bcc` toolchain, which has no separate version number tied to the engine target.
**Provenance:** `Constants - ZDoom Wiki.html` (https://zdoom.org/w/index.php?title=Constants&oldid=54415), verified 2026-07-29 against the zt-bcc source (preprocessor/language source + wiki).

The wiki page mixes three unrelated languages under one "Constants" heading: base ACS (as
compiled by `acc`), DECORATE, and ZScript. Only base ACS/BCS is covered on this page — BCS
(compiled by `bcc`, a superset of ACS) is the language this file is scoped to. **This fork has no
ZScript at all** (same finding already recorded in `concepts/activation.md`), so the wiki's entire
"ZScript" section (untyped `const`, `EMyEnum : uint`, cross-class enum access) does not apply.
**DECORATE's own `const`/`enum` is a separate, engine-parsed mechanism, not a BCS/ACS one** — see
[`../../decorate/concepts/constants.md`](../../decorate/concepts/constants.md) for that side, and
[`../../shared/concepts/constants.md`](../../shared/concepts/constants.md) for why the two
shouldn't be assumed to work alike.

## `#define`/`#include` gating is a real BCS-vs-ACS divergence

The wiki describes plain ACS's `#define NAME VALUE` and `#include` as always active, unconditional
directives. **BCS's preprocessor does not work that way by default.** Per `zt-bcc`'s own
Preprocessor doc: to stay compatible with base ACS's directive semantics, BCS's
preprocessor-based `#define` and `#include` **only take effect if they appear inside an
`#if`/`#ifdef`/`#ifndef` block** — otherwise they're parsed as the plain (non-preprocessor) ACS
`#define`/`#include` directives instead, which are less capable (no macro parameters, no `#include`
inside a script body, etc.). To make them unconditionally active from a point in the file onward,
use `#pragma raw define on` / `#pragma raw include on`. A real project's shared-constants header
does exactly this at the top of the file:

```
#pragma raw define on
#pragma raw include on
#nocompact

#ifndef MYDEFS_INCLUDE
#define MYDEFS_INCLUDE
...
```

Without those two pragmas (or without wrapping every `#define` in an `#if` block), a BCS
`#define` may silently compile as the weaker plain-ACS directive instead of the full
preprocessor macro the wiki describes.

Beyond that gating difference, BCS's `#define` is otherwise a fuller C99-style preprocessor than
what the wiki shows for ACS: it supports function-like macros with parameters, the `#` stringize
operator, string-literal concatenation of adjacent literals, backslash line continuation for
breaking a macro across lines, and two BCS-only predefined macros (`__IMPORTED__`, present while
preprocessing an `#import`ed library; `__INCLUDED__`, present while preprocessing an `#include`d
file) that have no equivalent on the wiki page.

## `#libdefine` is unchanged

`#libdefine NAME VALUE` (for constants exported from a library, per the wiki's "Library
Constants" section) is still a real, unmodified directive in `bcc` — it appears as its own
production in the BCS grammar, separate from `#define`. No divergence found here.

## BCS has no `const` keyword — use `enum` instead, and it's richer than ACS's

The wiki's "Use of operators" and "String Constants" sections describe plain-ACS constants that
are really just `#define` text substitution (an int constant referencing another, or a string
alias). The wiki's separate DECORATE section additionally shows a `const int X = 1;`
declaration syntax — **that `const` keyword does not exist in BCS at all** (no `const` token in
`zt-bcc`'s lexer/parser). The BCS equivalent for a genuine named constant (as opposed to a
`#define` text macro) is `enum`, and it is substantially richer than the wiki's plain
auto-incrementing ACS/DECORATE enum:

- A BCS enum can have an explicit non-`int` base type (e.g. `enum : str { ... }`), in which case
  **every** enumerator's value must be set explicitly (no auto-increment).
- A BCS enum can be named (`enum FruitT { ... }`) and then used as a strongly-typed variable type
  — assigning anything to that variable other than one of its own enumerators is a compile error,
  unlike a plain ACS/DECORATE `int`.
- A named enum's name doubles as an implicit type alias if it follows the `...T` naming
  convention some BCS projects use for their own `#define`-based type aliases (`TID_T`,
  `ScriptBool_T`, etc., rather than `enum`) — the same `T`-suffix convention is a
  `bcc`-recognized type-name pattern for real type aliases and named enums alike.

None of this — typed enum bases, enum-typed variables, or the type-name convention — appears on
the wiki page.
