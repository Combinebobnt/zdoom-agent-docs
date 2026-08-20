# gldefs/ — GLDEFS keys (dynamic lights, glows, etc.)

GLDEFS semantics for UZDoom/GZDoom-family (primary) and Zandronum where they diverge. **Read
`../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

If the `zdoom-docs-lookup` subagent is registered, prefer delegating a lookup question to it
instead of reading this tree by hand — see the root [`AGENTS.md`](../AGENTS.md)'s "Subagents"
section.

## Layout

- `INDEX.md` — this section's router.
- `inventory/<block>.md` — generated tables of GLDEFS keys, grouped by block type (`pointlight`,
  `pulselight`, `flickerlight`, `object`/actor-light-binding, `glow`, etc.). Archetype 2, generated
  half. No generator exists yet.
- `notes/<key-name>.md` — curated prose. Archetype 2, curated half.
- `concepts/<topic>.md` — cross-block knowledge (light-type inheritance, how `object` blocks bind
  a light definition to a DECORATE actor/frame). Archetype 3.

## Where GLDEFS parsing lives

Zandronum: `src/gl/dynlights/gl_dynlight.cpp` (`gl_LoadGLDefs`, `gl_ParseDefs`), related
`gl_dynlight1.cpp`/`gl_glow.cpp`. UZDoom: `src/r_data/gldefs.cpp` (renamed/relocated from
Zandronum's location — a concrete instance of the file-layout drift `shared/AUTHORING.md`'s
"Engine scope" warns about generally).

## Status

Scaffolded, no content yet. Tier-B prose source once picked up: `sources.local.md`'s `udb` key →
GZDoom's own GLDEFS `.cfg` if UDB has one, or SLADE's `dist/res/config/languages/` files.
