# GLDEFS lump format overview

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `GLDEFS` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=GLDEFS&oldid=55416), verified against Zandronum source's `src/gl/dynlights/gl_dynlight.cpp`, `src/gl/dynlights/gl_glow.cpp`, `src/gl/textures/gl_texture.cpp`, and `src/gl/textures/gl_skyboxtexture.cpp`; light runtime (offset, `sectorlight` scale) against `src/gl/dynlights/a_dynlight.cpp:316,354-357`; `HardwareShader` parsing against `src/gl/shaders/gl_shader.cpp:648-706`. GZDoom-family keyword presence verified via UZDoom 4.15pre source's `src/r_data/gldefs.cpp` but behavior beyond keyword existence not exhaustively traced.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

GLDEFS lumps define graphical effects supported only by the OpenGL renderer: dynamic lights (point/pulse/flicker lights bound to actors), skyboxes, brightmaps (brightness masks for sprites/textures/flats), glowing flats, and hardware shaders. The lump supports `#include` directives. Both engines also read the current game's own defs lump (`DOOMDEFS`, `HTICDEFS`, `HEXNDEFS`, `STRFDEFS` or `CHEXDEFS`) with the same syntax. Zandronum parses every game defs lump first, then every `GLDEFS` lump; UZDoom walks both names together in load order.

## Top-level block support matrix

Zandronum and GZDoom-family diverge significantly in GLDEFS scope. The following table enumerates which top-level blocks parse in each engine. On Zandronum, any other top-level keyword is a fatal parse error ("Error parsing defs. Unknown tag"), not silently skipped.

| Block | Zandronum 3.2.1 | GZDoom family | Notes |
|---|---|---|---|
| `#include` | yes | yes | Supports both WAD lump names and PK3 file paths |
| `pointlight` | yes | yes | Dynamic light type |
| `pulselight` | yes | yes | Dynamic light type; pulses between two sizes |
| `flickerlight` | yes | yes | Dynamic light type; flickers between two sizes (per-frame chance) |
| `flickerlight2` | yes | yes | Dynamic light type; random-size flicker within bounds (replaces size with randomness interval) |
| `sectorlight` | yes | yes | Dynamic light type; intensity derives from sector light level |
| `object` | yes | yes | Binds lights to actor classes and sprite frames |
| `clearlights` | yes | yes | Clears all previously defined lights. On Zandronum it also drops every `object` binding parsed so far. |
| `skybox` | yes | yes | Textured cube skybox (6-face or 3-face + wall) |
| `glow` | yes | yes | Glowing flats/textures |
| `brightmap` | yes | yes | Brightmap definition for sprite/texture/flat |
| `hardwareshader` | yes | yes | Legacy per-graphic fragment shader (not `PostProcess` variant) |
| `detail` | parse-only | yes | GLBoom+ detail texture block. Zandronum parses and discards it; detail texturing is not implemented (UZDoom's parser at the stamped revision is the same no-op stub). |
| `shader` | parse-only | — | Zandronum: a ZDoomGL compatibility stub with no functionality. It consumes only the next token, so a braced body after it is not skipped. GZDoom: `shader` is internal-only, not a GLDEFS top-level block. |
| `clearshaders` | parse-only | — | Zandronum: parsed but no-op. |
| `disable_fullbright` | parse-only | — | Zandronum: accepted but not implemented (source comment). It consumes no argument, so a class name written after it is read as the next top-level keyword and aborts parsing. |
| `lightsizefactor` | **no** | yes | Top-level command to scale attenuated light sizes; only in GZDoom family. |
| `material` | **no** | yes | PBR/specular material definition (normal/roughness/metallic/AO maps); GZDoom family only. |
| `colorization` | **no** | yes | Color blending effect definition; GZDoom family only. |

## Dynamic lights in Zandronum

All five dynamic light types accept the same core property keywords except `additive`, plus light-type-specific ones. Any keyword a light type doesn't accept is a fatal "Unknown tag" parse error.

### Common light properties

| Keyword | Argument | Required | Notes |
|---|---|---|---|
| `color` | RGB float triplet (0.0-1.0 each) | yes (not enforced) | Converted to byte RGB (0-255) internally, clamped if necessary. Omitted, it defaults to 0 0 0, an invisible light. |
| `offset` | X Y Z float triplet (map units) | no | Relative to the bound actor's position and rotated with its angle: X is forward, Y is height, Z is sideways (positive Z is to the actor's right). Defaults to 0,0,0. |
| `subtractive` | 1 or 0 | no | Darkens instead of illuminates. Sets `MF4_SUBTRACTIVE` flag. |
| `additive` | 1 or 0 | no | **`pointlight` only**; any other light type rejects it as an unknown tag. Additive blend mode. Sets `MF4_ADDITIVE` flag. (Not listed on ZDoom Wiki for any light type.) |
| `halo` | 1 or 0 | no | Accepted and stored, but no renderer code reads it, so it has no visible effect. (Not listed on ZDoom Wiki for any light type.) |
| `dontlightself` | 1 or 0 | no | Light does not affect the actor it is bound to. Sets `MF4_DONTLIGHTSELF` flag. |

### Per-light-type keywords

| Light type | `size` | `secondarySize` | `interval` | `chance` | `scale` |
|---|---|---|---|---|---|
| `pointlight` | yes (0-255) | — | — | — | — |
| `pulselight` | yes (0-255) | yes (0-255) | yes (seconds) | — | — |
| `flickerlight` | yes (0-255) | yes (0-255) | — | yes (0.0-1.0) | — |
| `flickerlight2` | yes (0-255 lower bound) | yes (0-255 upper bound) | yes (0.1 = 1 sec) | — | — |
| `sectorlight` | — | — | — | — | yes (0.0-1.0 of sector light) |

**Behavioral notes:**

- **Size clamping differs between engines** (see Engine-family divergence section below).
  - Zandronum: `size` and `secondarySize` are clamped to 0-255 during parsing.
  - UZDoom/GZDoom: `size` and `secondarySize` are clamped to 1-1024 during parsing.
- **`flickerlight2` auto-swap:** If `secondarySize < size`, the engine silently swaps them at parse time. The wiki's "SECSIZE must be greater than SIZE" describes the intended design, not an error condition; incorrect orderings are corrected, not rejected.
- `pointlight` does not accept `secondarySize` or `interval`/`chance` (they will error as unknown tags).
- `sectorlight` does not accept `size` or secondary properties; `scale` is meant as its intensity control instead. On Zandronum the parsed `scale` never reaches the spawned light (only the color bytes are copied to it), so a GLDEFS-bound `sectorlight`'s size always tracks the sector's full light level.

### Properties NOT in Zandronum (GZDoom family only)

The following properties parse in UZDoom/GZDoom but not Zandronum, where each is a fatal "Unknown tag" parse error:

| Keyword | Argument | Light types | Notes |
|---|---|---|---|
| `spot` | INNER OUTER (angles in degrees) | all | Spot light cone angles. |
| `attenuate` | 1 or 0 | all | Surfaces facing away from light receive progressive dimming. |
| `noshadowmap` | 1 or 0 | all | Disable shadow map emission on void surfaces. |
| `dontlightactors` | 1 or 0 | all | Light only affects level geometry, not actors. |
| `dontlightothers` | 1 or 0 | all | Light only affects the bound actor, not other actors. |
| `dontlightmap` | 1 or 0 | all | Light only affects actors, not level geometry. |
| `intensity` | float multiplier (default 1.0) | all | Intensity scale; over 1.0 requires unclamped light blend mode in GZDoom. |

## Binding lights to actors (object blocks)

Lights are bound to actors via `object` blocks, which specify an actor class and optionally individual sprite frames:

```text
object CLASSNAME
{
    frame SPRITENAME { light LIGHTNAME ... }
    frame SPRITEFRAME { light LIGHTNAME ... }
}
```

- `CLASSNAME` is the DECORATE actor class.
- `SPRITENAME` is a sprite name (4 chars, e.g. `MISL`) or sprite frame (5 chars, e.g. `MISLA`).
- If several `light` keywords bind to the same actor and frame name (in one `frame` block or across blocks), **only the last one applies**: each later one replaces the earlier binding.
- An actor can still show several lights at once when bindings under different frame names match its current state, e.g. a 4-char sprite-wide binding plus a 5-char frame binding.
- On Zandronum, a DECORATE `Light()` state binding is used only when no GLDEFS `object` binding matches the current sprite/frame.
- An `object` block for a class that doesn't exist prints a warning ("dynamic lights attached to non-existent actor") and is otherwise ignored.
- **Inheritance difference:** Bindings in DECORATE preserve through actor inheritance; bindings in GLDEFS apply only to the named actor class.

Zandronum does not support the `dontlightactors`, `dontlightothers`, or `dontlightmap` keywords. A DECORATE `Light()` binding only names a GLDEFS light definition, so it offers no way around this: the behavior is unavailable on Zandronum.

## Skyboxes

Skyboxes are defined as textured cubes. Support two formats:

```text
Skybox MYSKY6 [fliptop]
{
  TEXTURE_N    // North
  TEXTURE_E    // East
  TEXTURE_S    // South
  TEXTURE_W    // West
  TEXTURE_T    // Top
  TEXTURE_B    // Bottom
}

Skybox MYSKY3 [fliptop]
{
  TEXTURE_W    // Wall (all four sides)
  TEXTURE_T    // Top
  TEXTURE_B    // Bottom
}
```

The optional `fliptop` keyword corrects for non-standard top-face orientation (e.g., for Quake 2/3 or Half-Life skyboxes). Present in both Zandronum and GZDoom family. On Zandronum, a face count other than 3 or 6 is a fatal parse error ("Skybox definition requires either 3 or 6 faces").

## Brightmaps

Brightmaps are brightness masks applied to sprites, textures, or flats. They clamp the minimum brightness of pixels, ignoring sector darkness for masked pixels.

### Automatic assignment

Place a brightmap image in `brightmaps/auto/` or `materials/brightmaps/auto/` with the same name as the target graphic (8-char limit). This method has no GLDEFS entry required; the engine auto-applies. GZDoom family only: Zandronum has no folder-based automatic assignment, so every custom brightmap there needs a GLDEFS `brightmap` entry.

### Manual assignment

Define in GLDEFS:

```text
brightmap sprite POSSA1
{
  map "brightmaps/enemies/zombieman/POSSA1.png"
  [iwad]
  [thiswad]
  [disablefullbright]
}
```

Supported keywords (present in both Zandronum and GZDoom family):

- `iwad` — brightmap applies only if the sprite is from the IWAD (not replaced by a PWAD).
- `thiswad` — brightmap applies only if the sprite is from the same WAD/PK3 as the brightmap definition.
- `disablefullbright` — overrides the `bright` state keyword in DECORATE/ZScript, allowing brightmaps to dim fullbright sprites.

If both `iwad` and `thiswad` are specified, the brightmap applies if either condition is true.

**Zandronum `thiswad` bug:** Zandronum compares the graphic's file index against the defining GLDEFS lump's *lump* index instead of that lump's file index, so the test essentially never passes. A `thiswad` brightmap is dropped on Zandronum unless `iwad` is also given and matches. UZDoom compares the two containers correctly.

## Glowing flats (Glow block)

The `Glow` block marks textures/flats to emit light. Supports two methods:

```text
Glow
{
  Flats { FLAT1 FLAT2 ... }
  Walls { TEX1 TEX2 ... }
  Texture "FLAT1", C010A8 [, height] [, fullbright]
  Texture "FLAT2", SlateGray1 [, height] [, fullbright]
}
```

Default behavior for `Flats`/`Walls` lists: glow height 128, color auto-averaged from texture, fullbright enabled.

For `Texture` entries (present in both engines):

- Color: RGB hex triplet (e.g., `C010A8`) or X11 color name (e.g., `SlateGray1`). A color that resolves to black leaves the texture non-glowing.
- Optional height: glow vertical extent (integer map units). Omitted, the default 128 applies.
- Optional `fullbright` keyword, which needs its own preceding comma: enables fullbright. Without it, texture is not fullbright. Written without the comma, `fullbright` is silently skipped, since the block ignores any token it doesn't recognize.

Glows only appear on floors/ceilings; they are silently ignored on walls despite configuration.

## Hardware shaders

Zandronum supports `HardwareShader` for per-graphic fragment shaders only. The `PostProcess` variant (screenspace shaders, BeforeBloom/Scene/Screen stages) is **not** supported in Zandronum — it exists only in GZDoom family and requires ZScript control via `PPShader` class (which Zandronum lacks entirely).

```text
HardwareShader [Type] <LumpName>
{
  Shader "<File>"
  [NoMipmap]
  [Speed <Value>]
  [Define <Name> [= <Value>]]
  [Texture <Name> "<Source>"]
}
```

Type can be `Flat`, `Sprite`, `Texture`, or `PostProcess`. File is a text lump containing a GLSL `Process(vec4 color)` function returning a `vec4` pixel color.

On Zandronum the block reads only `Shader` and `Speed`. `NoMipmap`, `Define` and `Texture` lines are consumed token by token and ignored. `PostProcess` is not a recognized type there, so it is taken as the graphic name and the block fails to parse. User shaders are only compiled on hardware with shader model 3 or higher.

## Engine-family divergence: Light size parameter ranges

While both Zandronum and UZDoom/GZDoom support the same light types and most properties, the valid range for `size` and `secondarySize` differs:

- **Zandronum:** Clamps light size parameters to 0-255 (byte range). The wiki documentation describing the "0-255" range reflects Zandronum's implementation.
- **UZDoom/GZDoom:** Clamps light size parameters to 1-1024. Sizes larger than 255 allow for much brighter, more intensive lights in the renderer.

This affects all light types accepting `size`/`secondarySize` — `pointlight`, `pulselight`, `flickerlight`, and `flickerlight2`. A GLDEFS lump meant for use on both engines should keep sizes in the 1-255 overlap range to avoid unexpected behavior on either engine.

## Unsupported GZDoom-family-only blocks

The following GLDEFS sections are absent from Zandronum and present only in UZDoom/GZDoom:

- **`material` block:** PBR (physically-based rendering) or specular-map material definition with normal/roughness/metallic/AO maps. Requires advanced fragment shaders. Present in UZDoom source's `src/r_data/gldefs.cpp`.
- **`colorization` block:** Color blending effect with desaturation, inversion, additive/modulative/blended colors. Present in UZDoom source.
- **PostProcess shaders:** Screenspace post-processing shaders with uniform/texture binding and ZScript control. Requires `PPShader` class (UZDoom/GZDoom only). Present in UZDoom source. Not supported in Zandronum.
