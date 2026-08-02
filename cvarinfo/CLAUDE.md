# cvarinfo/ — CVARINFO declaration syntax and semantics

CVARINFO is the lump format mods use to declare new console cvars; this is distinct from
`console/`, which documents the engine's own *built-in* cvars and commands (see that section for
the actual `AddBot`-style cvar inventory). This section covers the *declaration mechanism* itself
— types, flags, default-value syntax. **Read `../shared/AUTHORING.md` and
`../shared/ARCHETYPES.md` first.**

If the `zdoom-docs-lookup` subagent is registered, prefer delegating a lookup question to it
instead of reading this tree by hand — see the root [`CLAUDE.md`](../CLAUDE.md)'s "Subagents"
section.

## Layout

- `INDEX.md` — this section's router.
- `inventory/cvarinfo-types.md`, `inventory/cvarinfo-flags.md` — generated tables of the types
  (`int`, `float`, `bool`, `string`, `color`) and flags a CVARINFO declaration can use. Archetype
  2, generated half. No generator exists yet.
- `notes/<name>.md` — curated prose. Archetype 2, curated half.
- `concepts/<topic>.md` — how a CVARINFO-declared cvar interacts with save-game/config
  persistence, server-cvar replication. Archetype 3.

## Where CVARINFO parsing lives

Zandronum: no dedicated file — `ParseCVarInfo()` in `src/d_main.cpp:1709-1718` (looked up via
`Wads.FindLump("CVARINFO", ...)`, called from `d_main.cpp:2864`). Archiving of CVARINFO-declared
cvars: `src/gameconfigfile.cpp:462,557`.

## Status

Scaffolded, no content yet. Tier-B prose source once picked up: `sources.local.md`'s `udb` key →
`Build/Scripting/ZDoom_CVARINFO.cfg`.
