# Patch sub-blocks in TEXTURES

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/common/textures/multipatchtexturebuilder.cpp`
(`ParsePatch`, `ParseTexture`, `ResolvePatches`, `ResolveAllPatches`),
`src/common/textures/formats/multipatchtexture.cpp` (`GetBlendMap`, `CopyToBlock`),
`src/common/textures/texturemanager.cpp` (`CheckForTexture`) and
`src/common/utility/palette.cpp`/`palutil.h` (special colormaps); and the Zandronum source's
`src/textures/multipatchtexture.cpp` (`ParsePatch`, text-definition constructor, `MakeTexture`,
`GetBlendMap`, the `bRedirect` paths), `src/textures/texture.cpp` (`CopyToBlock`),
`src/textures/texturemanager.cpp` (`CheckForTexture`), `src/r_data/r_translate.cpp` and
`src/r_data/colormaps.cpp`. UDB `Build/Scripting/ZDoom_TEXTURES.cfg` and SLADE
`dist/res/config/languages/zdoom.txt` checked for their keyword lists.

A definition block in a [TEXTURES lump](textures-lump.md) builds its image from patch
sub-blocks. Each one names a source image, places it on the texture's canvas, and can flip,
rotate, recolor or blend it. Patches are drawn in the order listed, later ones over earlier ones.

```text
walltexture "PANEL01", 128, 128
{
    Patch "PANBASE", 0, 0
    Patch "PANLITE", 32, -8 { Rotate 90 FlipY }
    Graphic "graphics/rivets.png", 0, 96 { Style Translucent Alpha 0.5 }
    Patch "PANTRIM", 0, 120 { Translation "176:191=112:127" }
    Patch "PANTRIM", 0, 0 { Blend "ff 80 00", 0.25 }
}
```

## Syntax

```text
Patch   "<name>", <x>, <y> [ { <patch properties> } ]
Graphic "<name>", <x>, <y> [ { <patch properties> } ]
Sprite  "<name>", <x>, <y> [ { <patch properties> } ]    // UZDoom only
```

The three keywords differ only in which use type the name is looked up as first:

| Keyword | UZDoom | Zandronum | Looked up as | Short-name lump fallback (Zandronum) |
|---|---|---|---|---|
| `Patch` | yes | yes | wall patch | `patches/` namespace |
| `Graphic` | yes | yes | graphic (MiscPatch) | `graphics/` namespace |
| `Sprite` | yes | no | sprite | none |

`Sprite` is a fatal "Unknown texture property" on Zandronum.

## Coordinates

- `<x>, <y>` is where the patch's top-left corner lands on the canvas, in texels. Both are
  integers and may be negative.
- Anything outside the canvas is clipped, on both sides (`ClipCopyPixelRect`, used by both
  engines' `CopyToBlock`). A patch at `-8` loses its first 8 columns or rows.
- A patch's own offsets are ignored unless `UseOffsets` is given, which subtracts the patch's left
  and top offsets from `<x>, <y>`. That lets a patch drawn with sprite-style offsets line up by its
  anchor instead of its corner.

## How a patch name is found

The lookup always tries the texture table first, with "try any type" set: an entry of the preferred
use type wins, otherwise the newest same-named texture of another type. Past that, the engines
differ.

**Zandronum resolves each patch while parsing** (`multipatchtexture.cpp:994-1036`). If the texture
lookup fails, it tries the name as a full lump path (reusing that lump's texture if it has one),
then, for a name of 8 characters or fewer with no `.` or `/`, a short-name lump in `patches/`
(`Patch`) or `graphics/` (`Graphic`). The patch is bound to whatever that finds at that moment.

**UZDoom records the name and resolves every patch after all files have loaded**
(`ResolveAllPatches`, called from `AddTextures` in `texturemanager.cpp:1207`). The lookup is the
texture table, then a full-path lump lookup when the name contains `/`, then texture aliases.
Composite textures that use other composites are then built in dependency order.

Consequences of the timing difference:

- **Forward references.** A patch that names a TEXTURES texture defined further down the lump, in a
  later lump, or in a later file works on UZDoom. On Zandronum the texture doesn't exist yet, so
  it is only found if a lump of that name happens to exist.
- **Later replacements.** If a later file replaces a patch or texture that an earlier composite
  uses, UZDoom's composite picks up the replacement; Zandronum's keeps the one bound at parse time.
- **Self-reference** (`walltexture "FOO"` containing `Patch "FOO"`, the usual way to rescale or
  re-offset an existing texture). On Zandronum the new definition isn't in the table while it is
  parsed, so the lookup finds the older `FOO` of any kind. On UZDoom the new definition is already
  registered, so the lookup can find itself; it then falls back to the oldest other `FOO` that is
  backed directly by an image lump (the candidate list runs newest-first and is scanned from the
  end) (`multipatchtexturebuilder.cpp:769-795`). An older `FOO` that is
  itself a composite (TEXTURE1/2 or TEXTURES) doesn't qualify there, and the patch is dropped
  with the warning "Texture '<name>' references itself as patch".
- **Cycles (UZDoom).** Composites that depend on each other in a loop can't be built. UZDoom
  prints "<n> Unresolved textures remain" plus their names, then turns each into a null texture
  with an empty name, so nothing can find it (`multipatchtexturebuilder.cpp:912-922`).

### Missing and invalid patches

- A name that resolves to nothing prints "Unknown patch '<patch>' in texture '<texture>'" and the
  patch is left out. The texture is still defined with its remaining patches. The definition
  header's `optional` keyword suppresses the message; it doesn't skip the texture.
- UZDoom also drops a patch that resolves to a texture with no image of its own to copy from, for
  example a camera or canvas texture, with "Invalid patch '<patch>' in texture '<texture>'"
  (`multipatchtexturebuilder.cpp:822-829`). Zandronum keeps such a patch but skips it when drawing
  a palette-mode composite (`MakeTexture`, "cannot use camera textures as patch").

## Patch properties

All are case-insensitive and may appear in any order. **An unknown word inside a patch block is
silently ignored on both engines**: the property loop has no `else` branch, so a typo such as
`FlipXX` or `Rotation 90` does nothing and reports nothing.

| Property | UZDoom | Zandronum | Meaning |
|---|---|---|---|
| `FlipX` | yes | yes | mirror horizontally |
| `FlipY` | yes | yes | mirror vertically |
| `Rotate <deg>` | yes | yes | rotate by a multiple of 90 degrees |
| `Translation <spec>` | yes | yes | recolor through a palette translation or preset |
| `Colormap r, g, b [, r2, g2, b2]` | yes | yes | recolor through a custom colormap ramp |
| `Blend <color> [, <alpha>]` | yes | yes | tint or multiply toward a color |
| `Alpha <float>` | yes | yes | opacity for non-`copy` styles, 0.0 to 1.0, default 1.0 |
| `Style <name>` | yes | yes | how the patch combines with what is under it |
| `UseOffsets` | yes | yes | place the patch by its own offsets (see Coordinates) |

### `FlipX`, `FlipY`, `Rotate`

`Rotate` takes an integer that is normalised with `((n + 90) % 360) - 90` and must then be 0, 90,
180 or -90. So 0, 90, 180, 270, -90 and their positive multiples-of-360 equivalents work; -180
and -270 are a fatal "Rotation must be a multiple of 90 degrees." A repeated `Rotate` keeps the
last value. The flips and the rotation are folded into one orientation after the block is read
(`FlipY` becomes a 180-degree turn plus a toggled `FlipX`), so their order inside the block doesn't
matter. Any flip or rotation also stops the single-patch shortcut described below.

### `Translation`

`Translation` takes one of:

- a preset: `Inverse`, `Gold`, `Red`, `Green`, `Blue` (the built-in special colormaps: inverted
  grayscale, gold, red, greenish-white, blue), `Ice`, or `Desaturate, <n>` with `n` clamped to
  1..31;
- one or more comma-separated translation range strings in the usual `"a:b=c:d"` forms, applied
  to an identity table in order.

The presets give the same colors on both engines, although the preset tables are listed in a
different order in each source. UZDoom's `Inverse` uses a separate copy of the inverse map, so
the player's `cl_customizeinvulmap` setting doesn't recolor TEXTURES patches
(`palutil.h`'s `REALINVERSECOLORMAP`, `r_data/colormaps.cpp` `R_UpdateInvulnerabilityColormap`).

A malformed range string is a fatal script error on Zandronum (`r_translate.cpp:473`). UZDoom
catches it and prints "Error in translation '<string>'", then carries on
(`multipatchtexturebuilder.cpp:483-490`).

### `Colormap`

The patch is reduced to grayscale brightness, and each level is mapped onto a linear ramp from a
start color (at black) to an end color (at white), the same mechanism as the `Translation`
presets. Three floats give the end color with a black start; six give the start color then the
end color. Each factor is clamped to 0.0-2.0, where 1.0 is full channel intensity; above 1.0 the
channel reaches 255 before white and clips there (`AddSpecialColormap`).

### `Blend`

`Blend` takes a color, either a quoted color string or three integers `r, g, b` (0-255), with an
optional alpha:

- **No alpha:** the patch's colors are multiplied by the blend color.
- **Alpha above 0:** each color is mixed toward the blend color by that fraction (stored clamped
  to 1..254 of 255).
- **Alpha 0 or less:** no blend at all.

`Translation` and `Blend` each clear the other, so only the last one in a block has any effect.
`Colormap` sets the same internal field without clearing the translation.

The integer form differs between engines: see the divergence section.

### `Style` and `Alpha`

`Style` is one of `Copy` (default), `Translucent`, `Add`, `Subtract`, `ReverseSubtract`,
`Modulate`, `CopyAlpha`, `CopyNewAlpha`, `Overlay`. Any other word is a fatal error
(`MustMatchString`). Any style other than `Copy` makes the whole texture composite in true color,
so the patch can be blended onto what is already drawn. `Alpha` only takes effect with a
non-`Copy` style; both engines' sources note it on the `Alpha` branch.

### The single-patch shortcut

When a definition has exactly one patch at `0, 0`, the same size as the texture, with no flip or
rotation, and nothing marked it complex, both engines use the patch's image directly instead of
compositing (Zandronum `multipatchtexture.cpp:1314-1323`, UZDoom
`multipatchtexturebuilder.cpp:889-895`). `Translation`, `Blend` and non-`Copy` styles mark the
texture complex; **`Colormap` does not**. So a lone `Colormap` on such a patch is silently lost on
both engines. Adding a non-`Copy` `Style` to the patch marks it complex and avoids this.

## Engine-family divergence

- **`Sprite` sub-block:** UZDoom only; fatal on Zandronum.
- **Resolution timing:** parse time on Zandronum, after all files on UZDoom. See "How a patch name
  is found" for forward references, later replacements, self-reference and cycles.
- **Integer `Blend` on Zandronum needs a trailing comma.** Zandronum demands a `,` after the blue
  value before it checks for an alpha (`multipatchtexture.cpp:1160`). So `Blend 255, 128, 0` with
  nothing after it is a fatal "Expected ','", and `Blend 255, 128, 0, 0.5` consumes the comma as
  that separator, finds no second comma, and blends at full strength; the `0.5` is then skipped as
  an unknown property. On Zandronum, write `Blend 255, 128, 0,` for no alpha and
  `Blend 255, 128, 0,, 0.5` for alpha. UZDoom dropped that extra comma
  (`multipatchtexturebuilder.cpp:548`), so the Zandronum spellings break there. **The quoted
  string form, `Blend "ff 80 00", 0.5`, parses the same way on both engines**; use it in shared
  mods.
- **Bad translation strings:** fatal on Zandronum, a printed message on UZDoom.
- **Full-path patch names:** Zandronum tries any name as a full lump path; UZDoom only does so for
  names containing `/`.
