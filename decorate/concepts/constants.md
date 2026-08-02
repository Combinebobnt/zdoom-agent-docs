# Constants (`const`/`enum`)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki "Constants" (retrieved 2026-07-29, oldid=54415)'s "DECORATE usage"
section, verified against the Zandronum source's `src/thingdef/thingdef_parse.cpp`
(`ParseConstant`/`ParseEnum`).

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

## Not independently re-verified for this page

- ZScript's own `const`/`enum` variants (untyped `const`, `enum : uint` typed bases, cross-class
  enum access) — out of scope, since Zandronum has no ZScript at all (see
  `../../shared/AUTHORING.md`'s "Engine scope").
- Narrower DECORATE-authoring claims the wiki also makes (e.g. "constants cannot be used for
  defining actor parameters") — these are usage restrictions rather than parser behavior and
  weren't traced against source for this page.
