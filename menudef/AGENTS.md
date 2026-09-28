# menudef/ — MENUDEF block/menu-item grammar

MENUDEF semantics for UZDoom/GZDoom-family (primary) and Zandronum where they diverge. **Read
`../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand — see the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Archetype choice

MENUDEF is one format, like MAPINFO — not a container of unrelated lump types like
`zandronum-lumps/`. It mirrors `mapinfo/`'s shape: base format scaffolded, engine-source buckets
documented, content added incrementally, rather than `zandronum-lumps/`'s
container-of-many-formats layout. There is deliberately no archetype-1 (Callable) directory here:
individual menu-item types are closer to DECORATE flags (many, similar shape, most not earning
individual prose) than to DECORATE actions, so they use the `inventory/`/`notes/`-promotion model
instead of one-file-per-item-type.

## Layout

- `INDEX.md` — this section's router.
- `inventory/<block>.md` — generated tables of menu-item keywords/classes, grouped by block
  family (e.g. `listmenu-items.md`, `optionmenu-items.md`). Archetype 2, generated half. No
  generator exists for this yet (see the note in `INDEX.md`) — rows are hand-written until one is
  built.
- `notes/<item-name>.md` — curated prose for a menu-item type that earns it (parameter semantics,
  failure behavior). Archetype 2, curated half.
- `concepts/<topic>.md` — cross-block knowledge, most importantly the item-keyword dispatch model
  and any Zandronum-specific-additions writeups sourced from the wiki. Archetype 3.

## Where MENUDEF parsing lives

Both engines parse MENUDEF from a near-identical shared codebase, forked when Zandronum "picked
up" the ZDoom menu rewrite as of 3.0 per the Zandronum wiki:

- **Zandronum:** `src/menu/menudef.cpp` — item-keyword dispatch is a hardcoded `sc.Compare(...)`
  chain constructing a fixed C++ class per keyword (`src/menu/optionmenuitems.h`,
  `src/menu/listmenuitems.h` if present). The item-type set is closed: a mod cannot add a new
  MENUDEF keyword without engine changes.
- **UZDoom:** `src/common/menu/menudef.cpp` — the parser builds `FStringf
  buildname("OptionMenuItem%s", sc.String)` (and the `ListMenuItem%s` equivalent) and resolves it
  via `PClass::FindClass`, requiring a public (non-`protected`/`private`) `Init` method. The
  item-type set is open: any ZScript class deriving from `OptionMenuItem`/`ListMenuItem` with a
  public `Init` becomes a usable MENUDEF keyword. The stock set lives in
  `wadsrc/static/zscript/engine/ui/menu/{listmenuitems,optionmenuitems}.zs`, plus a few more
  classes contributed by sibling files under `ui/menu/` (e.g. `joystickmenu.zs`,
  `reverbedit.zs`) — enumerate the true count from source rather than trusting any one doc's
  running total.

See [concepts/item-dispatch-model.md](concepts/item-dispatch-model.md) for the full writeup of
this divergence; record which file/line a keyword's parsing lives in when writing a `notes/`
entry, same reasoning as every other section's bucket convention.

## Status

All three phases of `maintainer/plans/2026-09-09_menudef_section.md` (maintainer-only) are done:
scaffolding and the pilot concept page, the full base-grammar/addition-list source sweep
(`inventory/listmenu-items.md`, `inventory/optionmenu-items.md`), and tier-A promotion of the
Zandronum-specific delta via wiki intake (`TextField`, `NumberField`, `PlayerField`,
`NetgameOnly` in `notes/`). A tier-B prose source also exists locally for the base grammar:
`sources.local.md`'s `udb` key → `Build/Scripting/ZDoom_MENUDEF.cfg`.
