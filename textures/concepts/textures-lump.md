# The `TEXTURES` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `TEXTURES` (https://zdoom.org/w/index.php?title=TEXTURES&oldid=54519, retrieved 2026-09-28) + verified against the UZDoom source's `src/common/textures/texturemanager.cpp`
(`LoadTextureDefs`, `ParseTextureDef`, `CheckForTexture`, `AddGameTexture`, `AddTexturesForWad`,
`SortTexturesByType`, `AddTextures`, the `SPROFS` loop), `src/common/textures/multipatchtexturebuilder.cpp`
(`ParseTexture`, `MakeTexture`, `ResolveAllPatches`), `src/common/textures/gametexture.cpp`
(`r_spriteadjust`, sprite trimming), `src/common/filesystem/source/resourcefile.cpp` (`entrycmp`),
`src/maploader/maploader.cpp` and `src/r_data/sprites.cpp`; and the Zandronum source's
`src/textures/texturemanager.cpp` (`LoadTextureDefs`, `CheckForTexture`, `AddTexture`,
`AddTexturesForWad`, `SortTexturesByType`), `src/textures/multipatchtexture.cpp` (text-definition
constructor, `ParseXTexture`), `src/resourcefiles/file_zip.cpp` (`lumpcmp`), `src/sc_man.cpp`
(`ScriptError`), `src/p_setup.cpp` and `src/r_data/sprites.cpp`. UDB
`Build/Scripting/ZDoom_TEXTURES.cfg` and SLADE `dist/res/config/languages/zdoom.txt` checked for
their keyword lists.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

TEXTURES is a text lump of top-level statements. Almost every statement is a definition: a
use-type keyword, a name, a size, and an optional `{ }` block of properties and patches. The
engine builds each definition into a texture that competes with same-named textures from
TEXTURE1/2, `flats/`, `sprites/`, `textures/` and other files under fixed precedence rules. Patch
sub-blocks have their own page: [patch-blocks.md](patch-blocks.md).

```text
// 128x64 wall made from two patches, drawn at half size in the world
walltexture "BRICKWAL", 128, 64
{
    XScale 2.0
    YScale 2.0
    Patch "BRIKPAT1", 0, 0
    Patch "BRIKPAT2", 64, 0 { FlipX }
}

// Replace a flat, silently skipping a patch that might not exist
flat optional "FLOOR7_1", 64, 64
{
    Patch "MYFLOOR", 0, 0
}
```

## Top-level statements

Keywords are case-insensitive on both engines. `//` and `/* */` comments work anywhere.

| Statement | UZDoom | Zandronum | What it does |
|---|---|---|---|
| `texture` | yes | yes | definition, use type Override (see below) |
| `walltexture` | yes | yes | definition, use type Wall |
| `flat` | yes | yes | definition, use type Flat |
| `sprite` | yes | yes | definition, use type Sprite |
| `graphic` | yes | yes | definition, use type MiscPatch |
| `remap` | yes | yes | HIRESTEX statement: swap an existing texture's image for a lump |
| `define` | yes | yes | HIRESTEX statement: define a texture straight from one lump |
| `#include "<full path>"` | yes | no | parse another lump inline (see below) |
| `notrim <sprite>` | yes | no | turn off hardware sprite-border trimming for an existing sprite |

Anything else at top level is a fatal script error, "Texture definition expected, found
'<word>'" (UZDoom `texturemanager.cpp:858`, Zandronum `texturemanager.cpp:736`). On Zandronum that
includes `#include` and `notrim`.

## The definition header

```text
<use-type> [optional] "<name>", <width>, <height> [ { <properties and patches> } ]
```

- **`optional`** only silences the "Unknown patch" warning for patches in this definition that
  can't be found. The texture is still defined; missing patches are dropped from it. It does not
  mean "define only if the patches exist". A texture literally named `optional` is recognised
  when the next token is the comma (both engines' parser special-cases it).
- **Name** is uppercased. Zandronum truncates it to 8 characters
  (`multipatchtexture.cpp:1237-1238`); UZDoom keeps the full name (`multipatchtexturebuilder.cpp:622-623`),
  so long names only work there.
- **Width and height** are integers in texels. A width or height of 0 or less prints "Texture
  <name> has invalid dimensions" and demotes the definition to a 1x1 null texture (UZDoom
  `multipatchtexturebuilder.cpp:746-751`, Zandronum `multipatchtexture.cpp:1327-1332`).
- **The block is optional.** Without it the texture has no patches.

### What each use type is visible to

The use type decides which lookups see the definition. Map loading asks for a wall or flat with
the "overridable" and "try any" flags (Zandronum `p_setup.cpp:625`, UZDoom
`maploader.cpp:144`), so:

| Keyword | Use type | Picked by |
|---|---|---|
| `texture` | Override | wall **and** flat lookups from map data, ahead of Wall/Flat entries of the same name in the same file |
| `walltexture` | Wall | wall lookups; flat lookups only as a last-resort "any type" fallback |
| `flat` | Flat | flat lookups; wall lookups only as the fallback |
| `sprite` | Sprite | sprite-frame setup: a Sprite-type texture with a name of 6+ characters is scanned into the sprite tables like a `sprites/` lump (UZDoom `r_data/sprites.cpp:335`, Zandronum `r_data/sprites.cpp:275`). See [sprite naming](../../sprites/concepts/sprite-naming.md) for the name format |
| `graphic` | MiscPatch | general by-name image lookups (HUD, status bar, menus), whose default use type is this one |

## Block-level properties

| Property | UZDoom | Zandronum | Meaning |
|---|---|---|---|
| `XScale <float>` | yes | yes | texels per world unit horizontally; 2.0 draws the texture at half width. 0 is a fatal error |
| `YScale <float>` | yes | yes | same, vertically |
| `Offset <x>, <y>` | yes | yes | left/top offset, the anchor for sprites and graphics |
| `Offset2 <x>, <y>` | yes | no | second, "adjusted" offset pair (see below) |
| `WorldPanning` | yes | yes | texture panning on lines/sectors is in world units, not texels, so it scales with `XScale`/`YScale` |
| `NoDecals` | yes | yes | decals are not placed on walls using this texture |
| `NullTexture` | yes | yes | use type becomes Null: a wall lookup that reaches it returns "no texture" |
| `NoTrim` | yes | no | same as the top-level `notrim` statement, for this definition |
| `Patch "<name>", <x>, <y> [{...}]` | yes | yes | add a patch, looked up as a wall patch |
| `Graphic "<name>", <x>, <y> [{...}]` | yes | yes | add a patch, looked up as a graphic |
| `Sprite "<name>", <x>, <y> [{...}]` | yes | no | add a patch, looked up as a sprite |

An unknown block-level word is a fatal "Unknown texture property '<word>'" on both engines
(Zandronum `multipatchtexture.cpp:1302`, UZDoom `multipatchtexturebuilder.cpp:741`). On Zandronum that
includes `Offset2`, `NoTrim` and `Sprite`, so a definition using them stops a Zandronum startup
outright rather than degrading.

**`Offset2` and `r_spriteadjust` (UZDoom).** UZDoom keeps two offset pairs per texture. `Offset`
sets both unless `Offset2` has already been given; `Offset2` sets only the second
(`multipatchtexturebuilder.cpp:717-737`). A renderer uses the second pair when its bit of the
`r_spriteadjust` cvar is set: value 1 selects it for the software renderer, 2 for the hardware
renderer, 3 for both; the default is 2 (`gametexture.cpp:425-428`). So `Offset2` lets a sprite
carry a different anchor for the hardware renderer than for the software one.

**`notrim`/`NoTrim` (UZDoom).** The hardware renderer trims fully transparent borders off sprite
images; this flag turns that off for one sprite (`gametexture.cpp:336`). The top-level statement
form needs a sprite that already exists by that point; a name that doesn't resolve as a sprite is
a fatal "NoTrim: <name> is not a sprite" (`texturemanager.cpp:805-819`).

## Which definition wins

Every texture from every loaded file goes into one table, and a name lookup walks a hash chain
newest-first (`AddTexture`/`AddGameTexture` push to the chain head). After each file is loaded, the
engine re-adds that file's new textures grouped by use type in a fixed order: Sprite, Null,
FirstDefined, WallPatch, Wall, Flat, Override, MiscPatch, SkinGraphic (`SortTexturesByType`,
identical list on both engines). Consequences:

- **For any one lookup, the newest texture of a use type that lookup accepts wins**, so a later
  file beats an earlier one. A lookup skips types it doesn't accept and only falls back to them
  when nothing acceptable exists.
- **Within one file, use type decides, not definition order.** A `texture` (Override) beats a
  same-named TEXTURE1 entry or `walltexture` for wall lookups even if it appears first. A
  `NullTexture` definition sorts before Wall, so it does not hide a same-file wall of the same name.
- **Within one file and one use type, the later definition wins.** TEXTURES is read after the same
  file's TEXTURE1/2, `flats/` and `textures/` entries, so a `walltexture` or `flat` definition
  replaces a same-file entry of the same name.
- A definition does not delete what it overrides. The older texture stays in the table and can
  still be reached by a lookup for a type the newer one doesn't match, or as a patch.

## Load order and multiple TEXTURES lumps

For each file in load order, the engine adds sprites, `patches/`, TEXTURE1/2, flats, `textures/`
and loose graphics; then every `TEXTURES` lump in that file; then every `HIRESTEX` lump; then
hires replacements; then sorts (UZDoom `texturemanager.cpp:1028-1029`, Zandronum
`texturemanager.cpp:895-896`). `LoadTextureDefs` loops over every lump named `TEXTURES` and
handles the ones belonging to the current file, so **one archive can carry many**:
`TEXTURES.walls`, `TEXTURES.hud` and `TEXTURES.sprites` are all lumps named `TEXTURES` (see
[PK3 lump names](../../shared/concepts/pk3-lump-naming.md)). Both engines sort PK3 and directory entries by
full path before assigning lump numbers (Zandronum `file_zip.cpp:152`, UZDoom
`resourcefile.cpp:303-309`), so within one PK3 or directory they run in alphabetical path order.
Several `TEXTURES` lumps in a WAD run in WAD directory order.

## `#include` (UZDoom)

`#include "<path>"` parses another lump immediately, as if its text were at that point
(`texturemanager.cpp:841-855`). The path is a full archive path, looked up across all loaded
files; a missing target is a fatal "Lump '<path>' not found". The included lump's definitions join
the current file's batch.

Name include targets something other than `TEXTURES.*` at the archive root. A root-level
`TEXTURES.extra` is already parsed by the lump loop, and including it as well parses it twice.

## HIRESTEX statements accepted here

Both engines accept these because TEXTURES and HIRESTEX share one statement loop:

- **`remap [wall|flat|sprite] <texture> <lump>`** replaces the image of every existing texture
  named `<texture>` (optionally only of that use type) with the lump, keeping the old display size
  and scaling the offsets. The lump is looked up in `patches/` then `graphics/`. A missing texture
  or lump prints "Attempting to remap ..." and continues.
- **`define <lump> [force32bit] <width> <height>`** creates a texture named after the lump's base
  name (cut to 8 characters) from the lump, at the given display size, with world panning on. If a
  texture of that name already exists (a graphic preferred), it is replaced; otherwise the new
  texture is added. `force32bit` is parsed and ignored by both.

## Errors

| Situation | Result |
|---|---|
| Unknown top-level word | fatal: "Texture definition expected, found '<word>'" |
| Unknown block property | fatal: "Unknown texture property '<word>'" |
| `XScale 0` / `YScale 0` | fatal: "Texture <name> is defined with null x-scale" (or y) |
| Width or height 0 or less | warning, texture becomes 1x1 and null |
| Missing patch | warning "Unknown patch", unless `optional` (see [patch-blocks.md](patch-blocks.md)) |
| Unknown patch-block property | silently ignored (see [patch-blocks.md](patch-blocks.md)) |
| `#include` target missing (UZDoom) | fatal: "Lump '<path>' not found" |

"Fatal" means `FScanner::ScriptError`, which calls `I_Error` with "Script error, "<lump>" line
<n>" and aborts startup on both engines (Zandronum `sc_man.cpp:888-906`).

## Engine-family divergence

- **Extra UZDoom keywords:** `#include`, the `notrim` statement, the `NoTrim` and `Offset2` block
  properties, and the `Sprite` patch sub-block. Each is a fatal error on Zandronum, not an ignored
  word. A mod shared between engines must keep them out of any TEXTURES lump Zandronum loads.
- **Name length:** 8 characters on Zandronum, unlimited on UZDoom.
- **Patch resolution timing:** Zandronum looks up each patch while parsing; UZDoom looks them all
  up after every file has loaded, so forward references and later-file patch replacements behave
  differently. See [patch-blocks.md](patch-blocks.md).
- **`iwad`/`iwadforced` are not TEXTURES keywords.** They are options of UZDoom's `SPROFS`
  sprite-offset lump (`texturemanager.cpp:1501-1523`), which Zandronum doesn't have. At the top
  level or in a definition block of TEXTURES they are a fatal error on both engines (inside a
  patch block, like any unknown word, they are ignored).

## Wiki/engine divergence

- **`optional`:** the wiki says that when a required patch is missing "the virtual image simply
  won't be created". Neither engine does that. `optional` only suppresses the "Unknown patch"
  warning; the definition is still added, with the missing patches dropped, even when none are
  found (UZDoom `multipatchtexturebuilder.cpp:832-837` drops unresolved patches and then builds
  the texture from what's left; Zandronum `ParseXTexture` adds the texture unconditionally).

## Related

- [Patch sub-blocks](patch-blocks.md): patch lookup, coordinates and per-patch properties.
- [PK3 lump names drop the extension](../../shared/concepts/pk3-lump-naming.md): why
  `TEXTURES.*` files are all one lump name, and why searching an archive for a composite
  texture's name finds no file.
- [Sprite naming](../../sprites/concepts/sprite-naming.md): the name format a `sprite`
  definition needs to become a sprite frame.
- [GLDEFS overview](../../gldefs/concepts/gldefs-overview.md): brightmaps and glows name textures,
  including TEXTURES-defined ones.
