# fonts/: the FONTDEFS and TEXTCOLO lumps

FONTDEFS defines fonts built from individual graphics; TEXTCOLO defines the named text colors
that `\c` escapes and `HudMessage` color arguments select. They share a section because both feed
the same text drawing: a font's glyphs are recolored through TEXTCOLO's ranges. **Read
`../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

**Both engines parse both lumps**, so a page about either lump stamps
`Applies to: UZDoom=yes, Zandronum=yes` plus a `Verified against:` pair, with an
`## Engine-family divergence` heading where they differ. A page about a UZDoom-only feature
(`fonts/<name>/` folder fonts and `font.inf`, `fonts/dynamic/` TrueType fonts, the FONTDEFS
keywords `DONTTRANSLATE`, `KERNING`, `IGNOREOFFSETS`, `MINLUMINOSITY`, `MAXLUMINOSITY`) stamps
`UZDoom=yes, Zandronum=no`. The TEXTCOLO parsers are the same code on both engines; the
differences are in the built-in colors and the `\c` escape set.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router.
- `concepts/<topic>.md`: Archetype 3.

**No `inventory/`/`notes/` here.** Each lump has a small fixed keyword set, which the concept
pages cover directly; a generated inventory would add nothing.

## Where fonts and text colors are implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| FONTDEFS parser (`V_InitCustomFonts`) | `src/common/fonts/v_font.cpp` | `src/v_font.cpp` |
| TEXTCOLO parser (`V_InitFontColors`), name lookup (`V_FindFontColor`) | `src/common/fonts/v_font.cpp` | `src/v_font.cpp` |
| `\c` escape resolution (`V_ParseFontColor`) | `src/common/fonts/v_font.cpp` | `src/v_font.cpp` |
| Built-in color enum (`CR_*`, `NUM_TEXT_COLORS`) | `src/common/fonts/v_font.h` | `src/v_font.h` |
| Font lookup by name (`V_GetFont`, `FFont::FindFont`) | `src/common/fonts/v_font.cpp`, `src/common/fonts/font.cpp` | `src/v_font.cpp` |
| Stock font setup (`SmallFont`, `BigFont`, ...) | `src/gamedata/doomfont.cpp` (`InitDoomFonts`), `src/common/fonts/v_font.cpp` (`V_InitFonts`) | `src/v_font.cpp` (`V_InitFonts`) |
| Folder fonts and `font.inf` (UZDoom-only) | `src/common/fonts/font.cpp` (`FFont::FFont`) | none |
| `fonts/dynamic/` TrueType fonts (UZDoom-only) | `src/common/fonts/v_font.cpp` (`FontFromTTF`) | none |
| Init order (TEXTCOLO, then fonts) | `src/d_main.cpp` | `src/d_main.cpp` (`V_InitFontColors`), `src/r_utility.cpp` (`R_Init` calls `V_InitFonts`) |
| Font name sent with a HUD message | none | `src/sv_commands.cpp` (`SERVERCOMMANDS_PrintHUDMessage`, `SERVERCOMMANDS_PrintACSHUDMessage`), `src/cl_main.cpp` (`PrintHUDMessage::Execute`) |
| Stock definitions | `wadsrc/static/fontdefs.txt`, `wadsrc/static/textcolors.txt` | `wadsrc/static/fontdefs.txt`, `wadsrc/static/textcolors.txt`, `wadsrc/static/textcolors.za` |

UltimateDoomBuilder's `Build/Scripting/ZDoom_FONTDEFS.cfg` and SLADE's `z_fontdefs` and
`z_textcolors` blocks in `dist/res/config/languages/zdoom.txt` are secondary tier-B backing for
keyword names only. Both FONTDEFS lists stop at the templated/explicit keywords (SLADE adds
`DONTTRANSLATE`); neither has `KERNING`, `IGNOREOFFSETS` or the luminosity keywords. Neither
editor has any config for `font.inf`.
