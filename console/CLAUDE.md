# console/ — console cvars and CCMDs

The engine's own built-in console variables and commands (distinct from `../cvarinfo/`, which
covers the mod-facing *declaration mechanism* for adding new cvars). **Read
`../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

If the `zdoom-docs-lookup` subagent is registered, prefer delegating a lookup question to it
instead of reading this tree by hand — see the root [`CLAUDE.md`](../CLAUDE.md)'s "Subagents"
section.

## Layout

- `INDEX.md` — this section's router.
- `inventory/cvars.md`, `inventory/ccmds.md` — generated, complete tables of every built-in cvar
  and console command. Archetype 2, generated half. Regenerate with
  `python3 tools/gen_inventory.py console-cvars` / `console-ccmds`.
- `notes/<name>.md` — curated prose for a cvar/ccmd that earns it (lowercase filename matching the
  inventory row's name column). Archetype 2, curated half.
- `concepts/<topic>.md` — cross-cutting knowledge (`CVAR_SERVERINFO`/`CVAR_LATCH`-style flag
  semantics, save/config persistence, server replication of cvars). Archetype 3.

## Where cvars/ccmds are declared

Zandronum: `CVAR`/`CUSTOM_CVAR` macros in `src/c_cvars.h`/`c_cvars.cpp`; `CCMD` macro in
`src/c_dispatch.h`, with individual command bodies spread across ~197 `.cpp` files tree-wide (not
one central file — the generator greps the whole `src/` tree, same reasoning as DECORATE's action
functions). The first-party prose reference for what a given cvar/command actually does, better
than re-deriving it from source: `zandronum/docs/commands.txt` (1742 lines) — use this for
`notes/` prose, the macros for the inventory extraction itself.

## Cvar flags worth knowing before writing a `notes/` entry

`CVAR`/`CUSTOM_CVAR`'s flag argument (`CVAR_SERVERINFO`, `CVAR_LATCH`, `CVAR_ARCHIVE`, etc.)
determines whether a cvar is replicated to clients, requires a map change to take effect, or
persists to the config file — these are exactly the kind of "beyond the type" facts that earn a
`notes/` file per the Authoring rule, much more often than the cvar's own default value would.
