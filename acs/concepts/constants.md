# Constants

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `Constants - ZDoom Wiki.html` (https://zdoom.org/w/index.php?title=Constants&oldid=54415), verified 2026-07-29 against the zt-bcc source (preprocessor/language source + wiki).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

The wiki page mixes three unrelated languages under one "Constants" heading: base ACS (as
compiled by `acc`), DECORATE, and ZScript. Only base ACS/BCS is covered on this page — BCS
(compiled by `bcc`, a superset of ACS) is the language this file is scoped to. **The Zandronum
engine fork has no ZScript at all** (same finding already recorded in `concepts/activation.md`), so
on that engine the wiki's entire "ZScript" section (untyped `const`, `EMyEnum : uint`, cross-class
enum access) has nothing to apply to. UZDoom *does* have ZScript, so that section is out of this
page's scope there for a different reason — see the "Engine-family divergence" section at the
bottom before reusing the Zandronum reasoning on UZDoom.
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

```text
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
Constants" section) is still a real, unmodified directive in `bcc`, and it behaves as the wiki
describes. No divergence found here. Worth knowing how it's actually implemented, though: in the
`zt-bcc` compiler fork it and the plain (non-preprocessor) ACS `#define` are **the same code path** —
one shared reader in `src/parse/library.c` allocating one constant object, with the directive's own
spelling setting a single "hidden" bit. `#define` produces a hidden constant, `#libdefine` an
exported one; that visibility bit is the entire difference between the two directives.

## BCS has no constant-declaring `const` — use `enum` instead, and it's richer than ACS's

The wiki's "Use of operators" and "String Constants" sections describe plain-ACS constants that
are really just `#define` text substitution (an int constant referencing another, or a string
alias). The wiki's separate DECORATE section additionally shows a `const int X = 1;`
declaration syntax — **BCS has no constant-*declaring* `const`.** `const` is nonetheless a
reserved keyword in BCS (it lexes to `TK_CONST` in the `zt-bcc` compiler fork's reserved-identifier
table, `src/parse/token/user.c`, and the compiler's own Grammar reference lists it among the
identifiers that cannot be reused as a name for your own objects). Its one and only use in the
parser is the legacy base-ACS `const:` call-argument prefix — `SomeFunc(const: 1, 0)`, read in
`src/parse/expr.c`'s `read_call`, which the compiler's own source notes is an unnecessary relic now
that it picks the constant instruction variant on its own. No declaration-parsing path in
`src/parse/dec.c` accepts `TK_CONST`, so `const int X = 1;` is a syntax error in BCS rather than a
declaration. The BCS equivalent for a genuine named constant (as opposed to a
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

## Engine-family divergence

**Everything above is a property of the `zt-bcc` compiler fork, not of any engine, so it holds
identically for a UZDoom-targeted build.** UZDoom ships no ACS compiler of its own: the only
ACS-related C++ in the UZDoom source is `src/playsim/p_acs.cpp`, which is the bytecode VM plus its
object-file loader (it accepts the plain `ACS\0` format and both enhanced variants, `ACSE` and
`ACSe` — the same pair `bcc` emits, with `#nocompact` selecting the big `ACSE` form). Every
mechanism this page documents — the `#define`/`#include` gating and the `raw` pragmas that lift it,
`#libdefine`, the absence of a declaring `const`, `enum`'s typed bases and enum-typed variables, and
the `T`-suffix typename rule — is resolved entirely at compile time, before any engine sees the
object file. (`#libdefine`'s exported-vs-hidden bit outlives the source, but only as a
compile/link-time property consumed by an `#import`ing translation unit, never by the engine.) No
named constant survives as a runtime concept an engine could observe, so there is no
UZDoom-vs-Zandronum behavior difference to document for any of it.

**The reason the wiki's ZScript section is out of scope does change, though, and the Zandronum
reasoning must not be reused for UZDoom.** Zandronum simply has no ZScript to apply it to. UZDoom
does: it carries the full GZDoom-family ZScript frontend (`src/common/scripting/frontend/`), whose
scanner and parser have real `const` and `enum` keywords (`TK_Const`/`TK_Enum`, mapped to the
grammar's `ZCC_CONST`/`ZCC_ENUM`) — so the wiki's untyped `const`, `EMyEnum : uint` typed enum
bases, and cross-class enum access are live, accurate material *for that language* on UZDoom. They
stay off this page because ZScript is a different language from ACS/BCS, not because the feature is
missing. Nothing about ZScript's `const`/`enum` transfers back to BCS — in particular, ZScript's
untyped `const NAME = value;` still has no BCS counterpart. The `zscript/` section of this tree has
no page covering ZScript's own `const`/`enum` declarations yet.

The DECORATE half of the top-of-page routing note is unchanged on UZDoom: `const`/`enum` are still
keywords the engine itself parses while loading a WAD/PK3, via `ParseConstant`/`ParseEnum` in the
UZDoom source's `src/scripting/decorate/thingdef_parse.cpp` (a different file path from Zandronum's
`src/thingdef/thingdef_parse.cpp`, same mechanism), at both global and per-`actor` scope.
