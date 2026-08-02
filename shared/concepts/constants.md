# Constants across ACS/BCS and DECORATE

**Tier:** A
**Engine:** Zandronum 3.2.1 (DECORATE `const`/`enum`); `zt-bcc` toolchain itself, which has no
separate version number tied to the engine target (ACS/BCS `#define`/`enum`).
**Provenance:** `Constants - ZDoom Wiki.html`
(https://zdoom.org/w/index.php?title=Constants&oldid=54415), verified 2026-07-29/2026-08-01
against the `zt-bcc` source and the Zandronum source's `src/thingdef/thingdef_parse.cpp`.

The ZDoom Wiki's "Constants" page covers ACS, DECORATE, and ZScript under one heading, which
invites an assumption this tree deliberately corrects: **"a named constant" means two unrelated
mechanisms depending which language you're in**, not one concept with two syntaxes.

- **ACS/BCS constants are a preprocessor artifact, not a real declared symbol.** `#define NAME
  VALUE` is text substitution performed before the compiler ever sees a token stream — there is
  no "constant" object at the language level, just inlined literal text (or, for BCS's richer
  `enum`, a compile-time-checked value with no runtime representation either). See
  [`../../acs/concepts/constants.md`](../../acs/concepts/constants.md) for the full detail,
  including a real BCS-vs-base-ACS divergence in when `#define`/`#include` are honored as full
  preprocessor directives at all.
- **DECORATE constants are a real, engine-parsed language construct**, unrelated to any
  preprocessor — DECORATE has no `#define` at all. `const`/`enum` are keywords `ParseConstant`/
  `ParseEnum` (`src/thingdef/thingdef_parse.cpp`) parse directly while loading a WAD/PK3, valid at
  global scope or inside an `actor { }` block. See
  [`../../decorate/concepts/constants.md`](../../decorate/concepts/constants.md) for the full
  detail.

**Don't assume familiarity with one transfers to the other.** A BCS project's `#define`-based
shared-constants header (which needs specific pragmas to behave as a real preprocessor — see the
ACS-side file) and a DECORATE actor's `const int MYVALUE = 5;` declaration look superficially
similar but are handled by entirely different code paths (an external preprocessor pass in one
case, the engine's own WAD-loading parser in the other) with different rules about what's legal
(BCS's richer typed/named `enum` vs. DECORATE's `const` being restricted to `int`/`float` only).

This page intentionally carries no rules of its own beyond this routing/divergence note — see
`../ARCHETYPES.md`'s Archetype 3 for why a genuinely cross-section topic lives here instead of
being duplicated (or, worse, silently living in only one section while the other section's reader
never finds it).
