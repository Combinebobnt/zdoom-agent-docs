# Constants across ACS/BCS and DECORATE

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes — DECORATE `const`/`enum` parsing is shared engine
behavior; the ACS/BCS half of this note is a zt-bcc/compiler-side preprocessor artifact, not an
engine feature.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** `Constants - ZDoom Wiki.html`
(https://zdoom.org/w/index.php?title=Constants&oldid=54415), verified 2026-07-29/2026-08-01
against the `zt-bcc` source and the Zandronum source's `src/thingdef/thingdef_parse.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

The ZDoom Wiki's "Constants" page covers ACS, DECORATE, and ZScript under one heading, which
invites an assumption this tree deliberately corrects: **"a named constant" means two unrelated
mechanisms depending which language you're in**, not one concept with two syntaxes.

- **ACS/BCS constants are compile-time-only symbol objects, not runtime values.** `#define NAME
  VALUE` allocates a real compile-time constant object in the compiler's symbol table (a hidden
  object within the translation unit, unlike `#libdefine` which exports it); `#libdefine` exports
  it for cross-unit visibility. Neither has a runtime representation in the compiled output. BCS's
  richer `enum` is similarly a compile-time-checked, strongly-typed constant with no runtime
  artifact. See [`../../acs/concepts/constants.md`](../../acs/concepts/constants.md) for the full
  detail, including a real BCS-vs-base-ACS divergence in when `#define`/`#include` are honored as
  full preprocessor directives at all.
- **DECORATE constants are a real, engine-parsed language construct**, unrelated to any
  preprocessor — DECORATE has no `#define` at all. `const`/`enum` are keywords `ParseConstant`/
  `ParseEnum` parse directly while loading a WAD/PK3, valid at global scope or inside an `actor { }`
  block. Both Zandronum (`src/thingdef/thingdef_parse.cpp`) and UZDoom
  (`src/scripting/decorate/thingdef_parse.cpp`) implement this identically. See
  [`../../decorate/concepts/constants.md`](../../decorate/concepts/constants.md) for the full
  detail.

**Don't assume familiarity with one transfers to the other.** A BCS project's `#define`-based
shared-constants header (which needs specific pragmas to behave as a real preprocessor — see the
ACS-side file) and a DECORATE actor's `const int MYVALUE = 5;` declaration look superficially
similar but are handled by entirely different code paths (external compiler preprocessing in one
case, the engine's own WAD-loading parser in the other) with different rules about what's legal
(BCS's richer typed/named `enum` vs. DECORATE's `const` being restricted to `int`/`float` only).
The two mechanisms have no engine-level divergence between UZDoom and Zandronum — DECORATE
parsing is architecturally identical on both engines (only source file paths differ), and
ACS/BCS preprocessing is entirely compiler-side (zt-bcc), independent of which engine runs the
compiled output. For specifics on DECORATE constant scope and symbol registration, see the
`decorate/concepts/constants.md` Engine-family divergence section.

This page intentionally carries no rules of its own beyond this routing note — see `../ARCHETYPES.md`'s
Archetype 3 for why a genuinely cross-section topic lives here instead of being duplicated (or,
worse, silently living in only one section while the other section's reader never finds it).
