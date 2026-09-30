# TEXTURES doc index

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse TEXTURES.** UZDoom adds five keywords; every other keyword below exists on
both. The same parser also reads HIRESTEX, so its `remap`/`define` statements are covered here.

## Concepts

- [The TEXTURES lump](concepts/textures-lump.md) — tier A. Top-level statements and the
  `texture`/`walltexture`/`flat`/`sprite`/`graphic` header (`optional`, name, size); block
  properties (`XScale`, `YScale`, `Offset`, `Offset2`, `WorldPanning`, `NoDecals`, `NullTexture`,
  `NoTrim`); which same-named texture wins (later file, then use-type order within a file); many
  `TEXTURES.*` lumps per archive in path order; UZDoom `#include` and `notrim`; HIRESTEX
  `remap`/`define`; fatal vs warning errors; Zandronum's 8-character names.
- [Patch sub-blocks](concepts/patch-blocks.md) — tier B. `Patch`/`Graphic`/`Sprite` placement,
  clipping and negative offsets; parse-time (Zandronum) vs after-all-files (UZDoom) patch
  resolution, with forward references, self-reference and cycles; `FlipX`, `FlipY`, `Rotate`,
  `Translation`, `Colormap`, `Blend`, `Alpha`, `Style`, `UseOffsets`; unknown patch properties are
  silently ignored; a lone `Colormap` lost to the single-patch shortcut; Zandronum's
  trailing-comma integer `Blend`.

## Which page covers which keyword

| Keyword | Where | UZDoom | Zandronum | Page |
|---|---|---|---|---|
| `texture`, `walltexture`, `flat`, `sprite`, `graphic` | top level | yes | yes | [textures-lump](concepts/textures-lump.md) |
| `optional` | definition header | yes | yes | [textures-lump](concepts/textures-lump.md) |
| `remap` (with `wall`/`flat`/`sprite`), `define` (with `force32bit`) | top level | yes | yes | [textures-lump](concepts/textures-lump.md) |
| `#include` | top level | yes | no | [textures-lump](concepts/textures-lump.md) |
| `notrim` | top level | yes | no | [textures-lump](concepts/textures-lump.md) |
| `XScale`, `YScale`, `Offset`, `WorldPanning`, `NoDecals`, `NullTexture` | block | yes | yes | [textures-lump](concepts/textures-lump.md) |
| `Offset2`, `NoTrim` | block | yes | no | [textures-lump](concepts/textures-lump.md) |
| `Patch`, `Graphic` | block | yes | yes | [patch-blocks](concepts/patch-blocks.md) |
| `Sprite` (as a sub-block) | block | yes | no | [patch-blocks](concepts/patch-blocks.md) |
| `FlipX`, `FlipY`, `Rotate`, `UseOffsets` | patch | yes | yes | [patch-blocks](concepts/patch-blocks.md) |
| `Translation` (`Inverse`, `Gold`, `Red`, `Green`, `Blue`, `Ice`, `Desaturate`, range strings) | patch | yes | yes | [patch-blocks](concepts/patch-blocks.md) |
| `Colormap`, `Blend`, `Alpha` | patch | yes | yes | [patch-blocks](concepts/patch-blocks.md) |
| `Style` (`Copy`, `Translucent`, `Add`, `Subtract`, `ReverseSubtract`, `Modulate`, `CopyAlpha`, `CopyNewAlpha`, `Overlay`) | patch | yes | yes | [patch-blocks](concepts/patch-blocks.md) |
| `iwad`, `iwadforced` | not TEXTURES: UZDoom's `SPROFS` lump | n/a | n/a | [textures-lump](concepts/textures-lump.md) (divergence section) |
