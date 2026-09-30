# Fonts doc index (FONTDEFS, TEXTCOLO)

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse FONTDEFS and TEXTCOLO**; folder fonts, `font.inf`, `fonts/dynamic/` TrueType
fonts, the FONTDEFS keywords `DONTTRANSLATE`/`KERNING`/`IGNOREOFFSETS`/`MINLUMINOSITY`/
`MAXLUMINOSITY` and the colors behind `\cW`-`\cZ` are UZDoom-only; `\c?` and the extra
`textcolors.za` colors are Zandronum-only.

## Concepts

- [The FONTDEFS lump](concepts/fontdefs-lump.md) — tier A. When it's read (every `FONTDEFS`,
  before the stock fonts, later definition wins); templated vs explicit fonts (mixing is fatal);
  character keys (first byte only, quoting `;` and `"`, the UZDoom-only `-{`/`-}` escapes);
  keywords valid in both kinds and which settings leak into later fonts; engine font names a
  block can replace; UZDoom's folder, `font.inf` and TrueType fonts; engine differences
  (`SPACEWIDTH` templated-only on Zandronum); which Zandronum machine's copy decides what (a
  client missing the font drops the HUD message).
- [The TEXTCOLO lump](concepts/textcolo-lump.md) — tier A. When it's read (every `TEXTCOLO`,
  redefinition in place, Zandronum's Chex Quest 3 skip); grammar (names and aliases, normal and
  `Console:` ranges and their bounds, `Flat:`, `Untranslated`); how colors get numbers and why
  redefining one alias shifts every later letter code; the `\c` escape forms; 26 vs 22 built-in
  colors and Zandronum's 365 extra named colors; which Zandronum machine's copy decides what
  (`HUDMSG_COLORSTRING` resolves server-side).
