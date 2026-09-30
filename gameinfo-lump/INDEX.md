# GAMEINFO lump doc index

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse the GAMEINFO lump.** Looking for MAPINFO's `GameInfo { ... }` block
(menus, intermission, weapon slots, game-wide defaults) instead? That is a different thing, at
[`../mapinfo/concepts/gameinfo-block.md`](../mapinfo/concepts/gameinfo-block.md).

## Concepts

- [The GAMEINFO lump](concepts/gameinfo-lump.md) — tier A. Startup lump read only from `-file`
  files, last one wins, parsed before IWAD selection; full key table (7 shared keys, 5
  UZDoom-only: `LOADLIGHTS`, `LOADBRIGHTMAPS`, `LOADWIDESCREEN`, `DISCORDAPPID`, `STEAMAPPID`);
  per-engine `IWAD` matching, `LOAD` lookup and ordering, `NOSPRITERENAME` actually enabling
  renames everywhere, Windows-only startup keys on Zandronum, fatal script errors, quoting traps.
