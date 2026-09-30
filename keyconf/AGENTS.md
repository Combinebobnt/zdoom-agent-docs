# keyconf/ — the KEYCONF lump

KEYCONF is a console script run once at startup under a restricted allowlist of nine commands:
key-binding menu sections, default binds, aliases, weapon slots, and player classes. **Read
`../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

**Both engines parse KEYCONF**, with a line reader and allowlist that are near-identical. Every
file here stamps `Applies to: UZDoom=yes, Zandronum=yes` plus a `Verified against:` pair, and
carries an `## Engine-family divergence` heading wherever the two differ.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router.
- `concepts/<topic>.md`: Archetype 3. The lump itself, plus cross-command topics (unsafe
  aliases, weapon slots, player classes).

**No `inventory/`/`notes/` here.** The nine KEYCONF commands are ordinary console commands, so
each command's own prose lives in `../console/notes/<command>.md`, promoted from its row in the
generated `../console/inventory/ccmds.md` by `tools/gen_inventory.py console-ccmds`. A KEYCONF
concept page links to those notes rather than duplicating them.

## Where KEYCONF is implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| Lump reader (`D_LoadWadSettings`) | `src/gamedata/keysections.cpp` | `src/keysections.cpp` |
| Allowlist (`KeyConfCommands[]`) and the `ParsingKeyConf` gate | `src/common/console/c_dispatch.cpp` | `src/c_dispatch.cpp` |
| Call site (startup order) | `src/d_main.cpp` | `src/d_main.cpp` |
| `addkeysection`/`addmenukey` | `src/gamedata/keysections.cpp` | `src/keysections.cpp` |
| `setslot`/`addslotdefault`/`weaponsection` | `src/gamedata/a_weapons.cpp` | `src/g_shared/a_weapons.cpp` |
| `clearplayerclasses`/`addplayerclass` | `src/gamedata/keysections.cpp` | `src/p_user.cpp` |

Tier-B backing prose: UDB `Build/Scripting/ZDoom_KEYCONF.cfg` (keyword list only, and it wrongly
includes `bind`; see the lump concept).
