# The `FONTDEFS` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `FONTDEFS` (https://zdoom.org/w/index.php?title=FONTDEFS&oldid=54089, retrieved 2026-09-28) + verified against the UZDoom source's `src/common/fonts/v_font.cpp` (`V_InitCustomFonts:206-397`, `V_GetFont:92-158`), `src/common/fonts/font.cpp` (`FFont::FFont:168+`, `FFont::FindFont:659-673`, `GetCharCode:1146-1235`), `src/common/fonts/specialfont.cpp` (`FSpecialFont`), `src/gamedata/doomfont.cpp` (`InitDoomFonts`), `src/d_main.cpp` (init order), `src/common/filesystem/source/filesystem.cpp` (`GetFilesInFolder`), `src/common/engine/sc_man_scanner.re:305-310` (classic Hexen scanner rules), `wadsrc/static/fontdefs.txt` (line 100 `WICOLON` example), and the Zandronum source's `src/v_font.cpp` (`V_InitCustomFonts:2173-2324`), `src/r_main.cpp` and `src/r_utility.cpp` (fonts initialised on servers too), `src/p_acs.cpp` (`DoSetFont`), `src/sv_commands.cpp` (`SERVERCOMMANDS_PrintHUDMessage`, `SERVERCOMMANDS_PrintACSHUDMessage`), `src/cl_main.cpp` (`PrintHUDMessage::Execute`), `src/network.cpp` (connect-time lump authentication list), `src/sc_man_scanner.re` (classic mode), and `wadsrc/static/fontdefs.txt`. Keyword list cross-checked against UltimateDoomBuilder's `Build/Scripting/ZDoom_FONTDEFS.cfg` and SLADE's `z_fontdefs` block in `dist/res/config/languages/zdoom.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

FONTDEFS defines **fonts made of individual graphics**, one per character. A font it defines can
be selected by name wherever a font name is accepted, for example ACS
[`SetFont`](../../acs/functions/setfont.md), SBARINFO and MENUDEF. It can also replace an engine font by using that
font's name. For how a font's glyphs get recolored, see [the `TEXTCOLO` lump](textcolo-lump.md).
UZDoom adds two ways to define a font without FONTDEFS at all: folder fonts and TrueType fonts
(see "UZDoom-only: fonts without FONTDEFS").

## When it is read

- **Once at startup**, after TEXTCOLO. **Every lump named `FONTDEFS`** is read, in load order,
  and the engine's own `fontdefs.txt` loads first.
- FONTDEFS runs **before** the engine sets up its stock fonts (`SmallFont`, `BigFont` and the
  rest). Each stock font is first looked up by name, so a FONTDEFS font called `SmallFont` or
  `BigFont` is used instead of the stock one.
- **A later definition of the same name wins.** New fonts go on the front of the font list and
  lookup takes the first match, on both engines. Nothing warns about the duplicate.
- Glyph graphics resolve at parse time.
- **Zandronum servers load fonts too.** `R_Init` calls `V_InitFonts` on every Zandronum process,
  so a server's `SetFont` resolves against the server's own FONTDEFS.

## Grammar

A file is a sequence of font blocks. There is no top-level keyword:

```text
<font name>
{
    <keyword or character line>
    ...
}
```

The lump uses the classic Hexen tokenizer: `//` and `/* */` comments, and **`;` also starts a
comment to the end of the line**. Keywords are case-insensitive. Font names are compared
case-insensitively.

Each block is one of two kinds, decided by which keywords it uses. **Mixing the two is a fatal
error** ("Invalid combination of properties in font"), and so is a block with neither.

### Templated fonts

The block names a `printf`-style pattern, and the engine builds each glyph name from a character
code:

| Keyword | Default | Meaning |
|---|---|---|
| `TEMPLATE <pattern>` | none | Glyph name pattern, given the lump number, e.g. `MYFNT%03d`. |
| `FIRST <n>` | 33 | Character code of the first glyph. |
| `BASE <n>` | 33 | Number fed to the pattern for the first glyph. Set it when the graphics are numbered from something other than the character code. |
| `COUNT <n>` | 223 | Number of characters to try. |

Glyph *i* (from 0) is character `FIRST + i`, looked up under the name the pattern gives for
`BASE + i`. Missing glyphs are skipped silently.

```text
MYHUDFONT
{
    TEMPLATE MYFNT%03d        // MYFNT065 is 'A', MYFNT066 is 'B', ...
}
DIGITFONT
{
    TEMPLATE DIGIT%d
    FIRST 48                  // '0'
    BASE 0                    // DIGIT0 is '0', DIGIT1 is '1', ...
    COUNT 10
}
```

### Explicit fonts

Each line maps one character to one graphic:

```text
SCOREFONT
{
    0 SCRNUM0
    1 SCRNUM1
    % SCRPCT
    ";" SCRSEMI               // quoted: an unquoted ; starts a comment
    "\"" SCRQUOTE
    NOTRANSLATION 180 181     // palette indices left uncolored
}

STATUSFONT
{
    - STTMINUS
    0 STTNUM0
    1 STTNUM1
    2 STTNUM2
    3 STTNUM3
    4 STTNUM4
    5 STTNUM5
    6 STTNUM6
    7 STTNUM7
    8 STTNUM8
    9 STTNUM9
    % STTPRCNT
    / STTSLASH
    NOTRANSLATION 109        // STTNUM shadow index stays uncolored
}
```

- **Only the first byte of the character token is used.** `10 LUMP` maps the character `1`. An
  explicit font covers character codes 0-255 only.
- The graphic is looked up by texture/graphic name, or by full path for a pk3 file. If it
  doesn't exist, a warning is printed (unless the definition is the engine's own) and the
  character is left empty.
- **Any word that isn't a keyword is a character line**, so a misspelled keyword silently maps a
  character (its first letter) to whatever token follows. In a templated block it is the fatal
  mixing error instead.
- **Only `;`, `"` and the braces need quoting.** The wiki also quotes `:`, but an unquoted `:` works
  (the stock `fontdefs.txt` has `: WICOLON`). `;` must be quoted since it starts a comment, `"`
  is written `"\""`, and braces are covered below.
- The font covers the lowest to the highest character that got a graphic.
- `NOTRANSLATION <index> ...` takes palette indices (0-255) and marks them as never recolored by a
  text color. It counts as an explicit-font keyword, so it can't appear in a templated block.
  **Put it last in the block.** Its number loop stops at a line break only after reading the next
  token, so a following line that starts with a digit (`0 GLYPH0`) loses its key, and the graphic
  name is then read as a character line of its own.
- **Braces.** `}` ends the block even when quoted, since the check doesn't look at quoting. On
  UZDoom, write `"-{"` and `"-}"` to map the `{` and `}` characters. **Zandronum has no such
  escape**: `"-{"` maps the `-` character, overwriting any minus glyph. A bare `{` works as a
  character on both engines.

### Keywords valid in both kinds

| Keyword | Meaning |
|---|---|
| `CURSOR <char>` | Character drawn as the text-entry cursor (default `_`). |
| `SPACEWIDTH <n>` | Width of a space in pixels. Default: half the width of `N` (rounded up), or 4 with no `N`. **On Zandronum it counts as a templated keyword**, so it is a fatal error in an explicit font. |
| `DONTTRANSLATE` | UZDoom-only. The font is never recolored. |
| `KERNING <n>` | UZDoom-only. The font's default kerning: pixels added between characters. |
| `IGNOREOFFSETS` | UZDoom-only. Drop the glyph graphics' offsets. |
| `MINLUMINOSITY <n>`, `MAXLUMINOSITY <n>` | UZDoom-only, explicit fonts only (parsed but ignored in a templated block). Clamped to 0-255. Override the brightness range used to map glyph pixels onto a color's ranges. |

**Some settings leak into later fonts.** Both engines set `CURSOR` once, outside the per-font
loop, so a `CURSOR` line keeps applying to every font defined after it, in the same lump and later
ones, until another `CURSOR` line. UZDoom does the same with `IGNOREOFFSETS` and the two
luminosity keywords, which have no way to switch back off. `SPACEWIDTH`, `KERNING` and
`DONTTRANSLATE` reset per font. Put a leaking keyword in the last font of the last lump, or
repeat `CURSOR _` where the default is wanted.

## Engine fonts and names

The names the engine's text code uses, which a FONTDEFS block of the same name replaces:
`SmallFont`, `SmallFont2` (Strife; elsewhere the same font as `SmallFont`), `BigFont`,
`ConsoleFont` and `IntermissionFont`. The stock `fontdefs.txt` also defines the alternative HUD's
and status bar's number fonts (`HUDFONT_DOOM`, `HUDFONT_RAVEN`, `INDEXFONT_DOOM`,
`INDEXFONT_RAVEN`), plus `INDEXFONT_STRIFE_YELLOW`/`_GREEN` on UZDoom, and `IntermissionFont_Doom`
on both. UZDoom has more engine fonts (`NewSmallFont`, `NewConsoleFont`, `BigUpper`,
`OriginalSmallFont`, `OriginalBigFont`) and maps the lump-style names `DBIGFONT`, `CONFONT` and
`INDEXFON` to `BigFont`, `ConsoleFont` and `IndexFont` when looked up.

Without a `SmallFont` FONTDEFS block, both engines next try a single-lump font (FON1/FON2) named
`SMALLFNT`, then build the font from the game's `STCFN`/`FONTA` graphics (UZDoom
`src/gamedata/doomfont.cpp:39`, Zandronum `src/v_font.cpp:2685-2700`). A name that no FONTDEFS block or engine font defines can still work: lookup falls back to a single-lump font (FON1, FON2 or BMF format) of that lump name, then to a one-character font made from a graphic of that name. [`SetFont`](../../acs/functions/setfont.md) covers the ACS side of that lookup.

## UZDoom-only: fonts without FONTDEFS

- **Folder fonts.** When a font name isn't already defined, UZDoom looks for a `fonts/<name>/`
  folder in a pk3. Each glyph is a graphic named with its **Unicode code point in hex** (for
  example `fonts/myfont/0041.png` for `A`), so folder fonts go beyond the 0-255 limit of explicit
  FONTDEFS fonts. The folder is atomic: only the last-loaded resource file that has that folder
  contributes glyphs.
- **Folder versus lump.** A single-lump font or a graphic with the same name as the folder is
  used instead of the folder only if it comes from the same or a later resource file. A FONTDEFS
  font of that name always wins, since it already exists by the time the folder is looked for.
- **`font.inf`** in the folder sets `Kerning`, `Scale` (one or two values), `SpaceWidth`,
  `FontHeight`, `CellSize <w>, <h>` (turns the folder into a sheet font of fixed-size cells),
  `MinLuminosity`/`MaxLuminosity`, `TranslationType console|standard`, `Altfont <name>` and
  `LowercaseLatinOnly`. Unknown keys are ignored silently. The engine's own folders under
  `fonts/` (for example `consolefont`, `indexfont`) use this format.
- **`fonts/dynamic/`**: every `.ttf` file under this folder becomes a font at startup, named
  after the file's short lump name. A font without a Unicode character map is an error. The
  folder is atomic too, so a mod that adds a file there hides the engine's own
  `fonts/dynamic/` fonts rather than adding to them.

None of these exist on Zandronum: a `fonts/` folder is ignored there, and a font name that resolves
only through one simply isn't found.

## Engine-family divergence

- **UZDoom-only keywords:** `DONTTRANSLATE`, `KERNING`, `IGNOREOFFSETS`, `MINLUMINOSITY`,
  `MAXLUMINOSITY`. On Zandronum an unknown word inside a block is read as a character line: its
  first byte becomes the character and the next token the graphic name. So `KERNING 1` maps the
  character `K` to a graphic named `1`, with a missing-texture warning, and in a templated block it
  is the fatal mixing error.
- **`SPACEWIDTH`** is templated-only on Zandronum (fatal in an explicit font), and valid in both
  kinds on UZDoom.
- **`"-{"`/`"-}"` brace escapes** exist only on UZDoom.
- **Folder, `font.inf` and TrueType fonts** are UZDoom-only (see above).
- **Stock fonts.** UZDoom's stock `fontdefs.txt` also defines the two Strife inventory number
  fonts; Zandronum's doesn't.

## Which Zandronum machine decides what

FONTDEFS is not in Zandronum's connect-time lump authentication list (`network.cpp`), so a
client's copy can differ from the server's without a connect error.

- `SetFont` in a server-side script resolves on the **server**. If the server doesn't know the
  name, the script falls back to `SmallFont` and no font name is sent.
- A HUD message carries the font **name**. Each **client** looks that name up in its own fonts.
  **If the client's lookup fails, the client drops the whole message** instead of drawing it in a
  default font.
- So a font that exists only client-side is never requested, and one that exists only
  server-side makes the message vanish on the clients. Ship the FONTDEFS lump and its graphics in
  the same file on both sides.
- Glyph shapes, cursor and spacing are pure presentation, decided by each client's copy.

## Related

- [The `TEXTCOLO` lump](textcolo-lump.md): the color ranges a font is recolored with.
- [`SetFont`](../../acs/functions/setfont.md) and
  [`HudMessage`](../../acs/functions/hudmessage.md): the ACS side of choosing a font.
