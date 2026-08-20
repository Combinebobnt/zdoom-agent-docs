# PK3 lump names drop the extension, so `NAME.<suffix>` files are all one lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-14)
**Provenance:** read directly from the Zandronum source, verified 2026-08-14. No wiki page
backs this; it is not documented in the wiki's PK3 page.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under
Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

A lump inside a PK3 is not named by its filename. `FResourceLump::LumpNameSetup`
(`resourcefile.cpp:97-105`) takes the basename, cuts everything from the **last** dot, and
uppercases it into a fixed 8-char field:

```cpp
const char *lname = strrchr(iname,'/');
lname = (lname == NULL) ? iname : lname + 1;
FString base = lname;
base = base.Left(base.LastIndexOf('.'));
uppercopy(Name, base);
Name[8] = 0;
FullName = copystring(iname);
```

Three consequences that are easy to get wrong:

## 1. One PK3 can carry many lumps of the same name

`TEXTURES.tex`, `TEXTURES.hud`, `TEXTURES.cmap` are three separate files that are all
lumps named `TEXTURES`. This is the supported way to split a large definition set across
files, and it works for any format the engine **enumerates** rather than looks up once.
`FTextureManager::LoadTextureDefs` (`texturemanager.cpp:602`) is the verified example:

```cpp
while ((remapLump = Wads.FindLump(lumpname, &lastLump)) != -1)
```

The distinction matters: a format the engine reads with a single `CheckNumForName` gets
only one winner (the last loaded), so splitting it across suffixed files silently discards
the rest. Check which access pattern a given format uses before assuming the split is safe.

## 2. Searching for an exact lump name gives false negatives

Listing a PK3 and grepping for an entry named exactly `TEXTURES` finds nothing in an
archive that uses the suffixed form. Glob `TEXTURES*` instead. This is a live trap when
answering "does asset X exist in this archive?" — a composite texture defined in a
suffixed `TEXTURES` lump corresponds to **no image file of its own name**, so both the
exact-lump search and a filename search for the asset come back empty while the asset
exists and renders fine.

## 3. Names truncate to 8 characters, and the truncation can collide

`Name[8] = 0` means `MYVERYLONGNAME.txt` and `MYVERYLONGOTHER.txt` are both `MYVERYLO`.
`FullName` keeps the original path, so full-path lookups still distinguish them, but any
8.3-style name lookup does not.

## Related: directory-to-namespace mapping

The same function assigns the namespace from the leading directory (`flats/` → `ns_flats`,
`textures/` → `ns_newtextures`, `sprites/` → `ns_sprites`, `graphics/` → `ns_graphics`,
`acs/` → `ns_acslibrary`, and others). A file in the archive root gets the global
namespace, which is why definition lumps like `TEXTURES` live at the root rather than under
a subdirectory.
