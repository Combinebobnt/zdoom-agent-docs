# bots/ — BOTINFO and the compiled botscript lump

Zandronum's bot definition surface: the `BOTINFO` text lump that declares a bot, and the compiled
binary botscript lump that drives its behavior. **Read `../shared/AUTHORING.md` and
`../shared/ARCHETYPES.md` first.**

**This section is Zandronum-only.** UZDoom/GZDoom-family engines have no `BOTINFO` parsing and no
botscript interpreter — their bot code is a different, much smaller subsystem with no ACS
reachability. Every file here carries `Applies to: UZDoom=no, Zandronum=yes` and a divergence
heading; don't add a UZDoom-side claim without re-verifying that one exists at all.

**The other eight Zandronum/Skulltag-native lump formats are not here.** `ANCRINFO`, `AUTHINFO`,
`CMPGNINF`, `GAMEMODE`, `MEDALDEF`, `SCORINFO`, `SECTINFO`, `SKININFO`, and `VOTEINFO` live in
[`zandronum-lumps/`](../zandronum-lumps/AGENTS.md) — a separate, later-added section for the rest
of that wiki category. This section keeps only `BOTINFO` and the compiled botscript format.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand — see the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md` — this section's router.
- `concepts/<topic>.md` — knowledge about the two format-shaped lumps (a stack-machine bytecode
  layout, a key/value block), which aren't tables of independently addressable named entries, so
  archetype 3 fits and archetype 1 does not. Archetype 3.
- `inventory/bot-commands.md` — generated, complete table of every entry in the Zandronum source's
  `src/botcommands.cpp` (`g_BotCommands[]`, 114 entries). Archetype 2, generated half. Regenerate
  with `python3 tools/gen_inventory.py bots-commands`. No `Zan`/`UZD` columns — see "This section is
  Zandronum-only" above.
- `notes/<name>.md` — curated prose for a bot command that earns it (lowercase filename matching
  the inventory row's `Command` column). Archetype 2, curated half.

## Where the bot subsystem is declared

Zandronum only. `src/bots.h` carries `DATAHEADERS_e` (the bytecode opcode enum), `BOTEVENT_e`, the
`BOTINFO_t` struct with every field's buffer size, and the fixed capacity limits. `src/bots.cpp`
carries `BOTS_ParseBotInfo` (the `BOTINFO` parser), `CSkullBot::GetStatePositions` (the bytecode
layout pass) and `CSkullBot::ParseScript` (the execution pass). `src/botcommands.cpp` carries the
command table and `BOTCMD_RunCommand`. The A\* pathfinder the bot commands reach is separate again,
in `src/astar.cpp`.

## Verifying a claim about the bytecode format

The five stock botscript lumps in the Zandronum source's `wadsrc/static/` (`humanbot.lump` and its
siblings) are the only known real specimens of this format, and there is no compiler for it in the
Zandronum tree or anywhere else. They are therefore the ground truth for any claim the parser
source leaves ambiguous — several facts in `concepts/botscript-lump-format.md` (string padding,
total-size alignment) were settled by measuring those lumps rather than by reading the parser, and
are marked as such. Prefer measuring them over inferring from `GetStatePositions` alone.
