# textures/: the TEXTURES lump

TEXTURES defines composite images in text: walls, flats, sprites and HUD/menu graphics built from
one or more patches, plus per-texture scale, offsets and flags. **Read `../shared/AUTHORING.md`
and `../shared/ARCHETYPES.md` first.**

**Both engines parse TEXTURES**, with the same statement dispatcher and near-identical definition
and patch parsers. Every file here stamps `Applies to: UZDoom=yes, Zandronum=yes` plus a
`Verified against:` pair, and carries an `## Engine-family divergence` heading wherever the two
differ. UZDoom adds five keywords (`#include`, the `notrim` statement, the `NoTrim` and `Offset2`
block properties, and the `Sprite` sub-block) and resolves patches after every file is loaded
rather than while parsing.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router, with a keyword-to-page table.
- `concepts/<topic>.md`: Archetype 3. The lump and its definition blocks, and the patch
  sub-blocks inside them.

**No `inventory/`/`notes/` here.** The keyword set is small and fixed, so both concept pages carry
per-keyword engine availability in their own tables rather than a generated inventory.

**TEXTURES and HIRESTEX share one parser.** Both engines run the same statement loop over every
`TEXTURES` lump and then every `HIRESTEX` lump, so HIRESTEX's `remap`/`define` statements are legal
in TEXTURES and definition blocks are legal in HIRESTEX. This section documents the shared grammar
once, under TEXTURES; HIRESTEX has no page of its own.

## Where TEXTURES is implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| Lump loop (`LoadTextureDefs`) | `src/common/textures/texturemanager.cpp` | `src/textures/texturemanager.cpp` |
| Statement dispatch | `ParseTextureDef`, same file | inline in `LoadTextureDefs` |
| Definition block | `FMultipatchTextureBuilder::ParseTexture`, `src/common/textures/multipatchtexturebuilder.cpp` | `FMultiPatchTexture` text constructor and `FTextureManager::ParseXTexture`, `src/textures/multipatchtexture.cpp` |
| Patch sub-block | `FMultipatchTextureBuilder::ParsePatch`, same file | `FMultiPatchTexture::ParsePatch`, same file |
| Deferred patch resolution | `ResolvePatches`/`ResolveAllPatches`, same file | none (resolved while parsing) |
| Compositing | `src/common/textures/formats/multipatchtexture.cpp` | `src/textures/multipatchtexture.cpp` (`MakeTexture`) |
| Per-file load order | `AddTexturesForWad`, `AddTextures` in `texturemanager.cpp` | `AddTexturesForWad` in `texturemanager.cpp` |
| Name lookup and precedence | `CheckForTexture`, `AddGameTexture`, `SortTexturesByType` in `texturemanager.cpp` | `CheckForTexture`, `AddTexture`, `SortTexturesByType` in `texturemanager.cpp` |
| Sprite-frame pickup of `sprite` definitions | `src/r_data/sprites.cpp` | `src/r_data/sprites.cpp` |

Tier-B backing prose: UDB `Build/Scripting/ZDoom_TEXTURES.cfg` and SLADE
`dist/res/config/languages/zdoom.txt` (its `z_textures` block), keyword lists only. Both omit
`Colormap` and the `Blue` translation; UDB also lacks `NoTrim`, `Offset2`, `Sprite`, `#include`,
`remap` and `define`, and SLADE lacks `Offset2`, `Sprite` and `#include`.
