# The `TEXTCOLO` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `TEXTCOLO` (https://zdoom.org/w/index.php?title=TEXTCOLO&oldid=50270, retrieved 2026-09-28) + verified against the UZDoom source's `src/common/fonts/v_font.cpp` (`V_InitFontColors`, `V_FindFontColor`, `V_ParseFontColor`, `V_LogColorFromColorRange`, `CreateLuminosityTranslationRanges`), `src/common/fonts/v_font.h` (`EColorRange`), `src/common/utility/cmdlib.cpp` (`strbin`, the `\c` escape), `src/common/utility/palette.cpp` (`V_GetColor`, X11R6RGB names), `src/common/2d/v_drawtext.cpp`, `src/common/platform/posix/sdl/i_system.cpp` and `src/widgets/errorwindow.cpp` (log-window use of `Flat:`), `src/d_main.cpp` (init order) and `wadsrc/static/textcolors.txt`, and the Zandronum source's `src/v_font.cpp` (same functions, the `GI_NOTEXTCOLOR` skip, the `\c?` escape), `src/v_font.h`, `src/v_text.h` (`TEXTCOLOR_*`), `src/v_text.cpp` (`CR_UNDEFINED` handling), `src/cmdlib.cpp` (`strbin`), `src/v_video.cpp` (`V_GetColor`), `src/d_iwad.cpp` (`NoTextcolor` IWADINFO flag), `src/p_acs.cpp` (`HUDMSG_COLORSTRING` resolution, `SERVERCOMMANDS_PrintACSHUDMessage` calls), `src/network.cpp` (connect-time lump authentication list), `src/resourcefiles/resourcefile.cpp` (`LumpNameSetup`, pk3 short names), `src/win32/i_system.cpp` (log-window color use), `wadsrc/static/textcolors.txt` and `wadsrc/static/textcolors.za`. Keyword list cross-checked against SLADE's `z_textcolors` block in `dist/res/config/languages/zdoom.txt` (UltimateDoomBuilder has no TEXTCOLO config).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

TEXTCOLO defines the **named text colors**: the palette of colors a string can switch to with a
`\c` escape, and that a `HudMessage` color argument selects. Each color is a set of **gradient
ranges**. A glyph is reduced to brightness first, and each brightness level is mapped onto the
color's gradient, so any font (see [the `FONTDEFS` lump](fontdefs-lump.md)) can be drawn in any
color. A color has two gradients: one for ordinary fonts and one for the console font.

## When it is read

- **Once at startup**, before fonts are built. **Every lump named `TEXTCOLO`** is read, in load
  order, and the engine's own `textcolors.txt` loads first.
- **Redefining a name replaces it in place**, so a later lump can restyle a stock color and keep
  its position (see "Color numbers and letter codes" for why position matters).
- **Zandronum only:** for an IWAD whose IWADINFO entry has the `NoTextcolor` flag (Chex Quest 3),
  the IWAD's own TEXTCOLO is skipped. UZDoom's parser has no such check.

## Grammar

```text
<name> [<alias> ...]
{
    <dark color> <light color> [<start> <end>]      // one or more normal ranges
    ...
    Console:
    <dark color> <light color> [<start> <end>]      // optional console ranges
    ...
    Flat: <color>                                    // optional single color
}
```

- Everything before `{` is a name for this color. Names are case-insensitive; quote a name that
  contains spaces.
- A color is `#RRGGBB` or any other form the engine's color parser takes, including a name from
  the `X11R6RGB` lump.
- The lump uses the classic Hexen tokenizer: `//`, `/* */` and `;` comments.

Example (invented colors):

```text
Seafoam "Sea Foam"
{
    #0A2A22  #6FE0C0     0  128
    #6FE0C0  #EFFFFA   129  256
Console:
    #000000  #2F8070     0  128
    #2F8070  #E0FFF8   129  256
Flat:
    #50C8A8
}
```

### Ranges

A range maps the brightness span `<start>`..`<end>` of a glyph onto a gradient from the first
color to the second. Brightness runs **0 to 256** in both engines' checks, and the stock lumps end
their last range at 256.

- With explicit bounds, the first range must start at 0, every bound must be within 0-256, each
  range must start after the previous one ends, and its end must be greater than its start.
- Without bounds, a range starts one past the previous range's end (0 for the first) and runs to
  256. So an unbounded range is only useful as the only range, or as the last one after a range
  ending below 256. A second unbounded range is the error "The color has too many ranges".
- `Console:` starts the console ranges, with the same rules, restarting from 0. It may appear
  once. **If a color has no `Console:` ranges, its console gradient is black to white.**
- `Flat:` sets the one color used where a single color stands for the whole range. Both engines use it
  in log/startup windows (UZDoom's error windows and SDL/POSIX/Cocoa console; Zandronum's Windows console),
  and UZDoom also for some text drawing (`v_drawtext.cpp`); the default is `#DFDFDF`.
- A color needs at least one normal range. Every rule above is a fatal script error.

### `Untranslated`

`Untranslated` is reserved: it may have no aliases and no ranges (the stock lump defines it as an
empty block to reserve its position). It means "draw the glyphs in their own colors".

## Color numbers and letter codes

Colors are numbered in the order their names first appear across all TEXTCOLO lumps, stock lump
first. The single-letter escapes `\cA`, `\cB`, ... and a `HudMessage` color number (`CR_*`) select
by that number, not by name.

| Letter | Color | Letter | Color | Letter | Color |
|---|---|---|---|---|---|
| A | Brick | J | White | S | DarkBrown |
| B | Tan | K | Yellow | T | Purple |
| C | Gray | L | Untranslated | U | DarkGray |
| D | Green | M | Black | V | Cyan |
| E | Brown | N | LightBlue | W | Ice (UZDoom) |
| F | Gold | O | Cream | X | Fire (UZDoom) |
| G | Red | P | Olive | Y | Sapphire (UZDoom) |
| H | Blue | Q | DarkGreen | Z | Teal (UZDoom) |
| I | Orange | R | DarkRed | | |

UZDoom has 26 built-in colors, `\cA`-`\cZ`. Zandronum has 22, `\cA`-`\cV`.

- A new name from a mod gets the next free number, after all stock colors, so it is reachable
  only by name: `\c[Name]`, or `HudMessage` with `HUDMSG_COLORSTRING`.
- **Redefine a multi-name color under all of its names.** Redefining only `Gray` (not `Grey`)
  gives `Gray` a new entry while `Grey` keeps the old one, and each gets its own number. Every
  color after it shifts up by one, so `\cD` shows the old gray instead of green, and every
  letter and `CR_*` value from there on is off by one.

## `\c` escapes

In ACS strings and LANGUAGE strings, `\c` becomes the color escape byte (0x1C). The character after
it chooses the color:

| Escape | Color |
|---|---|
| `\cA`-`\cZ` (either case) | Built-in color by letter (table above) |
| `\c[Name]` | Color named `Name`, any name or alias from any TEXTCOLO lump |
| `\c-` | The message's normal color |
| `\c+` | The message's bold color |
| `\c*` | The chat color |
| `\c!` | The team chat color |
| `\c?` | The private chat color (**Zandronum only**) |

- **An unknown name** in `\c[...]` gives `Untranslated`: the glyphs' own colors.
- **An unknown letter** leaves the color unchanged and the letter is swallowed. This includes
  `\cW`-`\cZ` and `\c?` on the engine that lacks them.

## Engine-family divergence

- **Built-in colors:** UZDoom adds Ice, Fire, Sapphire and Teal (`\cW`-`\cZ`). On Zandronum those
  letters are unknown, so text stays in its previous color.
- **Zandronum's extra named colors.** Zandronum ships a second stock TEXTCOLO lump,
  `textcolors.za` (its pk3 short name is `TEXTCOLO`), with **365 more colors**. Each has a short
  code, a one-word name and a spaced name (for example `A0`, `MiamiRetro` and `"Miami Retro"`), all
  usable as `\c[...]`. None exist on UZDoom, where those escapes fall back to `Untranslated`.
- **`\c?`** (private chat color) is Zandronum-only.
- **The Chex Quest 3 IWAD skip** is Zandronum-only (see "When it is read").
- The parsers themselves are the same code.

## Which Zandronum machine decides what

TEXTCOLO is not in Zandronum's connect-time lump authentication list (`network.cpp`), so the
server's and a client's copies can differ without a connect error.

- **Escapes in a string resolve on each client.** The server sends the text with its escape bytes
  intact, and every client looks up `\c[Name]` and letter codes in its own colors.
- **A `HUDMSG_COLORSTRING` name resolves on the server.** The server turns the name into a color
  number with its own TEXTCOLO and sends the number, which each client applies to its own list.
  If a mod's colors are loaded in a different order on the client, the number points to a
  different color.
- Load the same TEXTCOLO lumps in the same order on both sides.

## Wiki/engine divergence

Where the ZDoom Wiki page disagrees with both engines' source:

- **Brightness bound.** The wiki says 0 to 255; the parsers accept 256 (UZDoom
  `src/common/fonts/v_font.cpp:496-509`, Zandronum `src/v_font.cpp:2432-2442`), and the stock
  lumps end their last range at 256 (see [Ranges](#ranges)).
- **Default console range.** The wiki calls it "a range of whites". A color with no `Console:`
  ranges gets one black-to-white gradient over 0-256 (Zandronum `src/v_font.cpp:2481-2488`, same
  in UZDoom).
- **The wiki's `Teal` example** replaces a stock color on UZDoom, whose `textcolors.txt` defines
  `Teal`. Zandronum has no stock `Teal`, so the same definition adds a new color there, reachable
  only as `\c[Teal]`.

## Related

- [The `FONTDEFS` lump](fontdefs-lump.md): fonts, and `NOTRANSLATION`/`DONTTRANSLATE` for
  glyphs that should not be recolored.
- [`HudMessage`](../../acs/functions/hudmessage.md): the `color` argument and
  `HUDMSG_COLORSTRING`.
