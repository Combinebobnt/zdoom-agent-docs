# Constants (`const`/`enum`)

**Tier:** A (wiki-sourced sections below); B (the "Named constants are not accepted as plain
property values" section, added from direct source reading with no wiki starting point)
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** ZDoom Wiki "Constants" (retrieved 2026-07-29, https://zdoom.org/w/index.php?title=Constants&oldid=54415)'s "DECORATE usage"
section, verified against the Zandronum source's `src/thingdef/thingdef_parse.cpp`
(`ParseConstant`/`ParseEnum`). The property-value section below adds source-only verification of
`src/thingdef/thingdef_parse.cpp:649-651` (`ParsePropertyParams`) and `:1261-1265`
(`GlobalSymbols` registration) — no wiki page covers this distinction.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

**This is a different mechanism from ACS/BCS's constants, not the same one with different
syntax** — see [`../../shared/concepts/constants.md`](../../shared/concepts/constants.md) for why
that distinction matters before assuming anything from the ACS/BCS side carries over. DECORATE has
**no `#define` preprocessor at all**; `const` and `enum` are real keywords parsed directly by the
engine while loading a WAD/PK3.

## `const`

`const <type> NAME = <value>;` declares a named constant, valid at global scope or inside an
`actor { ... }` block (`TK_Const` is handled in both `ParseDecorate`'s and `ParseActor`'s switch
statements). `ParseConstant` only accepts `TK_Int` or `TK_Float` as the declared type — anything
else is a hard error (`sc.ScriptMessage("Numeric type required for constant")`). This matches the
wiki's claim that DECORATE constants "cannot be strings."

## `enum`

`enum { NAME1, NAME2 = 5, NAME3, ... }` auto-increments from 0 by default, the same as the wiki
describes, with an explicit `= value` overriding the running counter for that member and
subsequent members continuing to increment from there. Also valid at global or per-actor scope.

## Named constants are not accepted as plain property values (verified)

**Tier:** B — source-verified, no wiki starting point.

The wiki's own "Constants" page additionally claims "constants cannot be used for defining actor
parameters." That claim is **true, and stronger than it sounds**, once traced against the actual
property parser. DECORATE property parameters declared `'I'` (int) or `'F'` (fixed_t/float) in the
engine's property-parsing tables are parsed by `ParsePropertyParams` via `sc.MustGetNumber()` (the
`'I'` case, Zandronum `src/thingdef/thingdef_parse.cpp:649-651`; UZDoom
`src/scripting/decorate/thingdef_parse.cpp:688-691`) or the equivalent `sc.MustGetFloat()` for
`'F'`. Both bottom out in `FScanner`'s own `GetNumber()`/`CheckNumber()` (Zandronum `src/sc_man.cpp`;
UZDoom `src/common/engine/sc_man.cpp`), which special-case only the literal `MAXINT` token and
otherwise call `strtol()`/`strtod()` directly on the token text — there is no symbol-table lookup
anywhere in that path on either engine.

Meanwhile, a `const int`/`enum` declared per this page is registered into Zandronum's `GlobalSymbols`
(Zandronum `src/thingdef/thingdef_parse.cpp:1261-1265`; UZDoom `src/scripting/decorate/thingdef_parse.cpp:1285-1291`),
and that table (or namespace table in UZDoom) is consulted only by `ParseExpression()` — the parser
used for `'X'`-type property parameters (expression-in-parentheses properties) and for action-function
call arguments. It is **never** consulted by the plain `'I'`/`'F'` property-value path above on
either engine.

**Net effect:** a DECORATE property declaration like `SomeProperty SOME_NAMED_CONSTANT` does not
compile, even when `SOME_NAMED_CONSTANT` is a real `const int`/`enum` member that resolves fine one
line later as an action-function argument in the very same actor body. Property values in this
position must always be a bare numeric literal — the parser that would resolve a named constant
simply never runs for them. This is a real, easy-to-hit authoring trap: nothing about the
declaration syntax distinguishes an `'I'`/`'F'` property from an `'X'` one, so whether a constant
works is invisible without checking this file or the engine source.

## Engine-family divergence

**Symbol table scope:** In Zandronum, global-scope constants are registered into a single engine-wide `GlobalSymbols` table. In UZDoom, constants are registered into a namespace-scoped `Symbols` table (`PNamespace::Symbols`), making them namespace-local. Both systems register constants at global or per-actor scope identically from a user perspective, but UZDoom's namespace scope also makes these constants accessible to the ZScript compiler for the same namespace, a capability Zandronum lacks (it has no ZScript).

**Optional symbol resolution in number parsing:** UZDoom's `FScanner::GetNumber()` function (used by `MustGetNumber()`) accepts an `evaluate` parameter (default `false`) that, when true, performs symbol-table lookup for unrecognized numeric tokens. Zandronum's `GetNumber()` has no such capability. However, both engines' `ParsePropertyParams` function (used to parse plain 'I' and 'F' typed property values) calls `MustGetNumber()` without requesting evaluation. The practical result is identical on both: named constants do not resolve in plain property values.

**Float precision in property value application:** When applying a value to a float-typed property, Zandronum's `ParsePropertyParams` explicitly narrows the double-precision value with a cast (`float(sc.Float)` → 32-bit float); UZDoom preserves double precision in the intermediate storage (`sc.Float` → `conv.d`, 64-bit double). This is a sub-ulp-level difference observable only when a float property's value interacts with float-precision-sensitive code; typical usage sees no practical divergence. Both engines store `const float` declarations as double-precision internally.

## Not independently re-verified for this page

- ZScript's own `const`/`enum` variants (untyped `const`, `enum : uint` typed bases, cross-class
  enum access) — covered by the `zscript/` section's own documentation (see
  `../../shared/AUTHORING.md`'s "Engine scope" for the section split).
- Other narrower DECORATE-authoring claims the wiki makes beyond the property-value case verified
  above — not traced against source for this page.
