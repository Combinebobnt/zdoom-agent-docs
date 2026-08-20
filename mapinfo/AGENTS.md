# mapinfo/ — MAPINFO keys and block structure

MAPINFO semantics for UZDoom/GZDoom-family (primary) and Zandronum where they diverge. **Read
`../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

If the `zdoom-docs-lookup` subagent is registered, prefer delegating a lookup question to it
instead of reading this tree by hand — see the root [`AGENTS.md`](../AGENTS.md)'s "Subagents"
section.

## Layout

- `INDEX.md` — this section's router.
- `inventory/<block>.md` — generated tables of MAPINFO keys, grouped by block type (`map`,
  `clusterdef`, `episode`, `gameinfo`, etc. — one inventory file per block makes more sense here
  than one giant table, since key sets don't overlap across blocks). Archetype 2, generated half.
  No generator exists for this yet — see the note in `INDEX.md`.
- `notes/<key-name>.md` — curated prose for a key that earns it. Archetype 2, curated half.
- `concepts/<topic>.md` — cross-block knowledge (inheritance between `map`/`defaultmap`/
  `adddefaultmap`, include-file resolution order, the level-flags bitfield model). Archetype 3.

## Where MAPINFO parsing lives

Zandronum: `src/g_mapinfo.cpp` (`FMapInfoParser::ParseMapInfo`, `G_ParseMapInfo`) plus level-flag
consumption in `src/g_level.cpp`. UZDoom: `src/gamedata/g_mapinfo.cpp`. Record which file/line a
key's parsing lives in when writing a `notes/` entry, same reasoning as every other section's
bucket convention.

## Status

Scaffolded, no content yet. A tier-B prose source already exists locally for when someone picks
this up: `sources.local.md`'s `udb` key → `Build/Scripting/ZDoom_MAPINFO.cfg`.
