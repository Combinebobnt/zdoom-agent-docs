# ANIMDEFS `skyoffset` and `firetexture`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/textures/animations.cpp` (`InitAnimDefs`, `ParseFireTexture`, `UpdateAnimations`, `ResetTimers`), `src/common/textures/firetexture.cpp` and `firetexture.h` (`FireTexture::Reset`, `SetPalette`, `Update`, `GetBgraBitmap`, `Get8BitPixels`), `src/common/textures/gametexture.h` (`SetSkyOffset`/`GetSkyOffset`), `src/common/textures/texturemanager.cpp` (`AddGameTexture`, `CheckForTexture`), `src/common/engine/sc_man.cpp` (`GetNumber`, `ScanValue`, `ScriptError`), `src/rendering/swrenderer/plane/r_skyplane.cpp` (`RenderSkyPlane`), `src/common/rendering/hwrenderer/data/hw_skydome.cpp` and `hw_skydome.h` (`SetupMatrices`, `RenderDome`, `RenderBox`), `src/rendering/hwrenderer/scene/hw_skyportal.cpp`, `src/rendering/r_sky.cpp` (`r_skymode`), `src/gamedata/g_mapinfo.cpp` (`forcenoskystretch`), `src/p_setup.cpp` (`ClearLevelData`) and `src/d_main.cpp` (the `UpdateAnimations` call), and the Zandronum source's `src/textures/animations.cpp` (`InitAnimDefs`), `src/textures/textures.h` (`SkyOffset`), `src/gl/scene/gl_skydome.cpp` (`RenderDome` and its callers) and `src/sc_man.cpp` (`GetNumber`, `ScriptError`). Keyword list cross-checked against UltimateDoomBuilder's `Build/Scripting/ZDoom_ANIMDEFS.cfg` and SLADE's `z_animdefs` block in `dist/res/config/languages/zdoom.txt`.

Two small top-level ANIMDEFS statements. **`skyoffset`** shifts a sky texture vertically; both
engines parse it, but only some renderers and sky sizes honor it. **`firetexture`** creates a
procedural PSX-style fire texture and exists only in UZDoom. For the lump's outer grammar (no
braces, a block ends at the first word it doesn't know) and load order, see the
[lump page](animdefs-lump.md).

## `skyoffset`

```text
skyoffset <texture> <offset>
```

| Argument | Meaning |
|---|---|
| `<texture>` | Sky texture name, looked up as a wall texture (any namespace accepted as a fallback), at the moment the line is parsed |
| `<offset>` | Integer, in sky texture pixels. Negative values and a `0x` hex prefix are accepted. Stored as a signed 16-bit value on both engines (UZDoom `src/common/textures/gametexture.h:145`, Zandronum `src/textures/textures.h:204`) |

Parsing is identical on both engines (UZDoom `animations.cpp:335-344`, Zandronum
`src/textures/animations.cpp:302-311`):

- **Missing texture: silently ignored.** The number is still read, so the line is consumed
  cleanly and parsing continues.
- **Non-integer offset** (`10.5`, a word) is fatal: `SC_GetNumber: Bad numeric constant "..."`.
- **A later `skyoffset` for the same texture replaces the earlier value.**
- **Order matters for textures ANIMDEFS itself creates.** The name resolves when the line is
  read, so a `skyoffset` for a `firetexture` (or a `cameratexture` that creates a new texture)
  must come after that definition, or it hits an older texture of that name or nothing.

Direction: both renderers add the offset to the same term as the size-based shift that lowers
tall skies, so by that arithmetic a **positive value moves the image up** on screen, showing more
of its lower part above the horizon. The hardware path scales one texel to 57 world units of dome
translation (UZDoom `hw_skydome.h:32`, Zandronum `gl_skydome.cpp:255`).

### Which sky rendering paths honor it

| Renderer / sky | UZDoom | Zandronum |
|---|---|---|
| Hardware (OpenGL etc.), sky texture 200-240 px tall | Yes (`hw_skydome.cpp:388-393`) | Yes, GL renderer (`gl_skydome.cpp:285-289`) |
| Hardware, taller than 240 px | Yes (`hw_skydome.cpp:394-399`) | Yes (`gl_skydome.cpp:290-293`) |
| Hardware, 128 px or shorter, map has MAPINFO `forcenoskystretch` | Yes (the tiled branch, `hw_skydome.cpp:369-374`) | No (no tiled branch) |
| Hardware, under 200 px otherwise | No | No |
| Hardware, the sky mist layer | Yes, from the mist texture's own offset: always when the level gives the mist a vertical scale (`hw_skydome.cpp:401-404`, called from `hw_skyportal.cpp:102`), otherwise by the size rules above | No mist layer |
| Hardware skybox (`FSkyBox`, from GLDEFS) | No (`RenderBox` never reads it) | No |
| Software renderer | Only if **all** hold: the level's `sky1` texture is at least 200 px tall, `r_skymode` is 2 (the default, `src/rendering/r_sky.cpp:44`), and the map doesn't set `forcenoskystretch` (`r_skyplane.cpp:86`) | **Never.** The software renderer doesn't read the value at all |

Per-layer detail:

- **UZDoom hardware and Zandronum GL** read each layer's own texture, so `sky1` and a
  double-sky `sky2` each use their own offset (UZDoom `hw_skyportal.cpp:79` and `:87`, Zandronum
  `gl_skydome.cpp:600` and `:610`).
- **UZDoom software** reads only the level's `sky1` texture (the MAPINFO one, even with swapped
  skies) and applies the result to every default sky plane, including `sky2`. A sky transferred
  from a line (MBF sky transfer specials) uses that sidedef's Y offset instead
  (`r_skyplane.cpp:189`).
- **`forcenoskystretch` pulls the two UZDoom renderers apart.** It disables the offset in
  software but enables it in hardware for skies 128 px or shorter.

**A console variable shares the name.** Both engines' hardware sky code has a developer cvar
called `skyoffset` (default 0, not archived; UZDoom `hw_skydome.cpp:42`, Zandronum
`gl_skydome.cpp:247`) that is added to every texture's ANIMDEFS offset. It has no effect in the
software renderer. (UZDoom's software sky code also has an unrelated `RenderSkyPlane` member
named `skyoffset`, `r_skyplane.h:55`, set at `r_skyplane.cpp:79` for sky stretching; it is not
this value.) All heights in the table are after the texture's scale is applied.

## `firetexture` (UZDoom-only)

```text
firetexture <name> tics <n> [allowdecals]
    color <r> <g> <b> <a>     // any mix of color and palette lines,
    palette <index>           // 1 to 256 entries in total
```

`firetexture` creates a new **64 x 128** texture (fixed; there is no size argument,
`firetexture.cpp:33-34`) that burns with a random, upward-drifting fire in the style of PSX
Doom's fire sky. The colors listed are the fire's own palette: each pixel stores an index into
it, not a game palette index.

| Part | Arguments | Meaning |
|---|---|---|
| `<name>` | texture name | Name of the new texture. It's created as a wall texture and added last, so it takes precedence over an older wall texture of the same name; a flat of the same name still wins where a flat is looked up (`texturemanager.cpp:407`, `CheckForTexture`). Unlike `cameratexture`, it never modifies the existing texture |
| `tics <n>` | number, fractions allowed | Time between fire steps. The word `tics` is required; the `rand <min> <max>` form that animation frames take is not accepted here. Converted to milliseconds (x 1000 / 35, truncated) (`animations.cpp:801-803`) |
| `allowdecals` | none | Fire textures refuse decals by default. Only accepted as the word directly after the `tics` value (`animations.cpp:808-818`) |
| `color <r> <g> <b> <a>` | four integers, 0-255 | Appends one palette entry. `<a>` is alpha: 255 opaque, 0 fully transparent. Any value strictly between 0 and 255 marks the whole texture translucent (`animations.cpp:833-836`) |
| `palette <index>` | integer, 0-255 | Appends the game palette's color at that index. Black becomes fully transparent, every other color fully opaque (`animations.cpp:845-850`) |

**Entry order matters.** The first entry is the value of burnt-out pixels (usually transparent or
black). The last entry is the hottest color: the bottom row is always lit with it, and each step
pixels climb one row, drift sideways a pixel or two at random and cool by 0 or 1 palette steps
(`firetexture.cpp:67-88`). Each row climbed cools by half a step on average, so flame height
grows with the number of entries and a short list gives short flames.

```text
// Transparent above the flames, then dark red up to yellow-white at the base
firetexture MYFIRE tics 1.5
    color 0 0 0 0
    color 96 16 0 255
    color 160 40 0 255
    color 224 96 8 255
    color 255 176 32 255
    color 255 240 176 255

// From game palette entries, coolest first (index 0 is black, so transparent).
// The other indices are placeholders: pick them from your own palette
firetexture MYFIRE2 tics 2 allowdecals
    palette 0
    palette 176
    palette 168
    palette 160
    palette 231
```

### How it animates

- **On the renderer's millisecond clock**, like texture animations
  (`src/d_main.cpp:1216-1217`), so it keeps burning while the game is paused or a menu is open.
- **At most one step per rendered frame.** After a step, the next is scheduled `tics` after the
  current frame's time, not after the previous deadline (`animations.cpp:1139-1143`). So the real
  period is `tics` rounded up to a whole frame, and the fire slows down at low frame rates rather
  than catching up.
- **Restarts on every level load.** `ClearLevelData` (`src/p_setup.cpp:304`) calls
  `ResetTimers`, which clears the image to just the lit bottom row, so the flames grow back
  from nothing on each map (`animations.cpp:1188-1196`).
- The random drift uses the non-gameplay random generator (`M_Random`), so it can't desync
  anything.
- **8-bit software rendering** has no partial alpha: an entry with alpha below 128 draws fully
  transparent, the rest fully opaque (`firetexture.cpp:107-137`).

### Bad input

| Condition | Result |
|---|---|
| `tics` missing | Fatal `Expected 'tics', got '...'.` |
| `tics` value not a number | Fatal `Numeric constant expected` |
| `tics` negative | Not rejected; converted to an unsigned millisecond count with unpredictable results. Don't |
| A `color` or `palette` value that isn't an integer (`1.5`, a word) | Fatal `Integer constant expected` |
| A value outside 0-255 (including negative) | Accepted, but kept in 8 bits, so it wraps (256 is 0, -1 is 255) |
| More than 256 entries | Fatal `Too many colors specified!` |
| No entries at all | Not rejected. The texture then indexes an empty list; always give at least one entry |
| `allowdecals` after a `color`/`palette` line, or any other unknown word inside the block | Ends the block, then fatal `Bad syntax.` as an unknown top-level keyword (see the [lump page](animdefs-lump.md)) |
| `tics` below 0.035 (including `tics 0`) | The duration truncates to 0 ms, and the update loop at `animations.cpp:1139-1143` then never exits, so the game hangs on the first rendered frame after the fire starts. Observed live (2026-09-29, UZDoom 5.1.0-pre local test build): `tics 0.02` hung right after the level started, with the fire texture on no surface at all, while `tics 1` ran normally. The exact 0.035 threshold is from the arithmetic only. Use at least `tics 0.04` |

## Engine-family divergence

- **`firetexture` is UZDoom-only.** Zandronum's `InitAnimDefs` (`src/textures/animations.cpp:266-318`)
  has no such keyword, and neither does any other part of its source. Since `firetexture` is itself
  a top-level word, Zandronum stops right there with the unknown-keyword error, `Script error,
  "<lump>" line <n>: Bad syntax.` through `I_Error` (`src/sc_man.cpp:876`), which aborts
  startup. Its `color`/`palette` lines are never reached. A mod that must also run on Zandronum
  has to keep `firetexture` out of any ANIMDEFS lump Zandronum loads.
- **`skyoffset` parsing is identical**, but where it takes effect differs (see the table above):
  - Zandronum's software renderer ignores it entirely; UZDoom's honors it for `sky1` textures at
    least 200 px tall under the default `r_skymode 2`.
  - UZDoom's hardware renderer also honors it for skies 128 px or shorter on maps with
    `forcenoskystretch`, and for the sky mist layer; Zandronum's GL renderer has neither.

## Zandronum-specific: which machine's copy is used

`skyoffset` is presentation only, resolved by each client from its own ANIMDEFS (ANIMDEFS isn't
checksummed at connect; see the [lump page](animdefs-lump.md)). Because Zandronum's software renderer
ignores it, two clients with identical lumps see a tall sky at different heights if one uses the
OpenGL renderer and the other the software renderer.

## See also

- [The ANIMDEFS lump](animdefs-lump.md) for the outer grammar, load order, redefinition and the
  error model.
- [Camera and canvas textures](camera-canvas-textures.md), the other ANIMDEFS blocks that create
  textures.
- [Texture and flat animations](texture-flat-animations.md) for the millisecond animation clock
  fire textures share.
- [`../../mapinfo/concepts/map-block-and-inheritance.md`](../../mapinfo/concepts/map-block-and-inheritance.md)
  for the MAPINFO `Sky1`/`Sky2` keys that pick the sky texture.
