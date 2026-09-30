# language/: the LANGUAGE lump

LANGUAGE defines the engine's named, localizable text strings: level names, pickup and lock
messages, menu text, anything a lump or script refers to as `$LABEL`. **Read
`../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.** Not to be confused with BCS/ACS
*language* questions, which live under `../acs/`.

**Both engines parse LANGUAGE's classic format**, so a page about the lump itself stamps
`Applies to: UZDoom=yes, Zandronum=yes` plus a `Verified against:` pair, with an
`## Engine-family divergence` heading where they differ. A page about a UZDoom-only feature (the
CSV format, `LMACROS`) stamps `UZDoom=yes, Zandronum=no`. The biggest difference is override
order: a mod's `[default]` string replaces a stock one on UZDoom but not on Zandronum.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router.
- `concepts/<topic>.md`: Archetype 3.

**No `inventory/`/`notes/` here.** The lump's labels are open-ended, user-defined names, so there
is no engine keyword table to generate an inventory from.

## Where LANGUAGE is implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| Parser (`LoadStrings`, `LoadLanguage`) and string table | `src/common/engine/stringtable.cpp` | `src/stringtable.cpp` |
| CSV parser (`ParseLanguageCSV`), `LMACROS`, language-tag mapping (`GetID`, `ForEachLangID`) | `src/common/engine/stringtable.cpp` | none |
| `language` cvar | `src/common/engine/i_interface.cpp` | `src/doomstat.cpp`; language IDs from `src/win32/i_system.cpp` / `src/sdl/i_system.cpp` (`SetLanguageIDs`) |
| Startup load | `src/d_main.cpp` (plus `src/d_iwad.cpp` for the IWAD picker) | `src/d_main.cpp` |
| `$ifgame` / CSV `filter` game test | `src/d_main.cpp` (`StrTable_ValidFilter`) | `src/gi.h` (`GameTypeName`) |
| ACS `l:` (`PCD_PRINTLOCALIZED`) | `src/playsim/p_acs.cpp` | `src/p_acs.cpp` |
| Stock strings | `language.csv`, generated at build time from `libraries/Translation/`; `wadsrc/static/language.def`, `wadsrc/static/lmacros.csv` | `wadsrc/static/language.enu` (`[enu default]`), `.fr`, `.ita`, `.ptb` |

No UDB or SLADE definition file covers LANGUAGE, so tier-B pages here are written from engine
source alone.
