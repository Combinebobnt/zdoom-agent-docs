# GLDEFS lump format overview

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `GLDEFS` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=GLDEFS&oldid=55416), verified against Zandronum source's `src/gl/dynlights/gl_dynlight.cpp`, `src/gl/dynlights/gl_glow.cpp`, `src/gl/textures/gl_texture.cpp`, and `src/gl/textures/gl_skyboxtexture.cpp`. GZDoom-family keyword presence verified via UZDoom 4.15pre source's `src/r_data/gldefs.cpp` but behavior beyond keyword existence not exhaustively traced.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

GLDEFS lumps define graphical effects supported only by the OpenGL renderer: dynamic lights (point/pulse/flicker lights bound to actors), skyboxes, brightmaps (brightness masks for sprites/textures/flats), glowing flats, and hardware shaders. The lump supports `#include` directives and game-specific aliases (`DOOMDEFS`, `HTICDEFS`, `HEXNDEFS`, `STRFDEFS`).

## Top-level block support matrix

Zandronum and GZDoom-family diverge significantly in GLDEFS scope. The following table enumerates which top-level blocks parse in each engine:

| Block | Zandronum 3.2.1 | GZDoom family | Notes |
|---|---|---|---|
| `#include` | yes | yes | Supports both WAD lump names and PK3 file paths |
| `pointlight` | yes | yes | Dynamic light type |
| `pulselight` | yes | yes | Dynamic light type; pulses between two sizes |
| `flickerlight` | yes | yes | Dynamic light type; flickers between two sizes (per-frame chance) |
| `flickerlight2` | yes | yes | Dynamic light type; random-size flicker within bounds (replaces size with randomness interval) |
| `sectorlight` | yes | yes | Dynamic light type; intensity derives from sector light level |
| `object` | yes | yes | Binds lights to actor classes and sprite frames |
| `clearlights` | yes | yes | Clears all previously defined lights |
| `skybox` | yes | yes | Textured cube skybox (6-face or 3-face + wall) |
| `glow` | yes | yes | Glowing flats/textures (brightness mask) |
| `brightmap` | yes | yes | Brightmap definition for sprite/texture/flat |
| `hardwareshader` | yes | yes | Legacy per-graphic fragment shader (not `PostProcess` variant) |
| `detail` | yes | yes | Texture detail map definition |
| `shader` | parse-only | — | Zandronum: parsed but not executed ("no functionality"). GZDoom: `shader` is internal-only, not a GLDEFS top-level block. |
| `clearshaders` | parse-only | — | Zandronum: parsed but no-op. |
| `disable_fullbright` | parse-only | — | Zandronum: parsed but not implemented (source comment). |
| `lightsizefactor` | **no** | yes | Top-level command to scale attenuated light sizes; only in GZDoom family. |
| `material` | **no** | yes | PBR/specular material definition (normal/roughness/metallic/AO maps); GZDoom family only. |
| `colorization` | **no** | yes | Color blending effect definition; GZDoom family only. |

## Dynamic lights in Zandronum

All five dynamic light types support the same core property keywords, with light-type-specific requirements:

### Common light properties

| Keyword | Argument | Required | Notes |
|---|---|---|---|
| `color` | RGB float triplet (0.0-1.0 each) | yes | Converted to byte RGB (0-255) internally, clamped if necessary. |
| `offset` | X Y Z float triplet (map units) | no | Relative to actor sprite origin (Y = height, Z = depth). Defaults to 0,0,0. |
| `subtractive` | 1 or 0 | no | Darkens instead of illuminates. Sets `MF4_SUBTRACTIVE` flag. |
| `additive` | 1 or 0 | no | Additive blend mode. Sets `MF4_ADDITIVE` flag. (Not listed on ZDoom Wiki for any light type.) |
| `halo` | 1 or 0 | no | Renders a halo sprite around the light. (Not listed on ZDoom Wiki for any light type.) |
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
- `sectorlight` does not accept `size` or secondary properties; `scale` is its intensity control instead.

### Properties NOT in Zandronum (GZDoom family only)

The following properties parse in UZDoom/GZDoom but not Zandronum:

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
- Multiple `light` keywords bind multiple lights to one frame; only the first two are rendered (one per type: explicit frame binding, or sprite-wide binding).
- If several lights bind to the same frame, **only the last one applies**.
- **Inheritance difference:** Bindings in DECORATE preserve through actor inheritance; bindings in GLDEFS apply only to the named actor class.

Zandronum does not support `dontlightactors`, `dontlightothers`, or `dontlightmap` keywords, so those light types cannot be fully controlled via GLDEFS in Zandronum — they require DECORATE binding or are unavailable entirely.

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

The optional `fliptop` keyword corrects for non-standard top-face orientation (e.g., for Quake 2/3 or Half-Life skyboxes). Present in both Zandronum and GZDoom family.

## Brightmaps

Brightmaps are brightness masks applied to sprites, textures, or flats. They clamp the minimum brightness of pixels, ignoring sector darkness for masked pixels.

### Automatic assignment

Place a brightmap image in `brightmaps/auto/` or `materials/brightmaps/auto/` with the same name as the target graphic (8-char limit). This method has no GLDEFS entry required; the engine auto-applies.

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

## Glowing flats (Glow block)

The `Glow` block marks textures/flats to emit light. Supports two methods:

```text
Glow
{
  Flats { FLAT1 FLAT2 ... }
  Walls { TEX1 TEX2 ... }
  Texture "FLAT1", C010A8 [, height] [fullbright]
  Texture "FLAT2", SlateGray1 [, height] [fullbright]
}
```

Default behavior for `Flats`/`Walls` lists: glow height 64, color auto-averaged from texture, fullbright enabled.

For `Texture` entries (present in both engines):

- Color: RGB hex triplet (e.g., `C010A8`) or X11 color name (e.g., `SlateGray1`).
- Optional height: glow vertical extent (integer map units). Omit or 0 for no glow height.
- Optional `fullbright` keyword: enables fullbright. Without it, texture is not fullbright.

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

Type can be `Flat`, `Sprite`, `Texture`, or `PostProcess` (PostProcess unsupported in Zandronum). File is a text lump containing a GLSL `Process(vec4 color)` function returning a `vec4` pixel color.

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
