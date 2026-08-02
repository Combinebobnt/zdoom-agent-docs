# `SetLineTexture`

**Bucket:** compiler builtin — `zt-bcc/src/builtin.c:247`: `{ "setlinetexture", "iiis", NULL }`
(four required int/string args), compiling to `PCD_SETLINETEXTURE`
(`zt-bcc/src/builtin.c:395`). Not a `zcommon.bcs` `special`-table entry.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see
"Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `SetLineTexture - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=SetLineTexture&oldid=35840`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_SETLINETEXTURE` at lines 11431-11433,
`DLevelScript::SetLineTexture` at lines 4027-4093, declaration at `p_acs.h:1095`),
the Zandronum source's `src/sv_commands.cpp` (`SERVERCOMMANDS_SetLineTextureByID` at lines 5041-5070),
and the zt-bcc source's `lib/zcommon.bcs` (constant definitions at lines 67-69 for `SIDE_*`, lines 74-76
for `TEXTURE_*`) on 2026-07-29.

## Syntax

```
void SetLineTexture(int lineid, int line_side, int sidedef_texture, str texturename);
```

Changes the specified wall texture on all lines matching a line ID. The function iterates through
every linedef in the map and updates the texture on those whose ID matches `lineid`.

## Parameters

- **`lineid`**: the linedef ID to match. Assigned by the `Line_SetIdentification` action special or
  directly in UDMF map format. All linedefs with this ID will be updated.
- **`line_side`**: which side of the matched linedefs to affect. See **Side constants** below.
- **`sidedef_texture`**: which texture segment on that side to change. See **Texture position
  constants** below.
- **`texturename`**: the name of the texture to set, as a string. Use `"-"` (single hyphen) as a
  special case to *remove* the texture from that segment (equivalent to setting it to no texture —
  the engine's texture ID 0).

## Side constants

```
SIDE_FRONT = 0   // front sidedef of the linedef
SIDE_BACK  = 1   // back sidedef of the linedef
```

**Important:** the `line_side` parameter is clamped to 0 or 1 via `side = !!side` (convert to
boolean, cast back to int) before any texture lookup. Any non-zero value becomes 1; negative values
become 1. So `SetLineTexture(id, 2, TEXTURE_TOP, "WALL01")` is equivalent to `SetLineTexture(id,
SIDE_BACK, TEXTURE_TOP, "WALL01")`, not an error.

## Texture position constants

```
TEXTURE_TOP    = 0   // upper texture of sidedef
TEXTURE_MIDDLE = 1   // middle (wall) texture of sidedef
TEXTURE_BOTTOM = 2   // lower texture of sidedef
```

The position parameter is used directly as a switch index; values outside 0–2 are silently ignored
(the switch has no default case, so an invalid position does nothing to the texture).

## Special behavior: string resolution and the empty-string "-" case

The `texturename` parameter is resolved as a string ID via `FBehavior::StaticLookupString(name)`
*before* any texture changes are applied. If the string ID is out of range or invalid, the lookup
returns a `NULL` pointer:

```cpp
const char *texname = FBehavior::StaticLookupString (name);
if (texname == NULL)
    return;
```

The function returns early without raising an error, console message, or return value to indicate
the failure.

**Exception:** the special string `"-"` (resolved to a valid empty string in the string table) is
*not* `NULL`, so it passes the guard above and is handed to the texture manager as the name to
look up. The texture manager treats empty strings as a request for the no-texture dummy (texture
ID 0), which is then set on the matched sidedef segments. This is the documented way to remove a
texture; it is not a silent failure, just a special-case name.

A resolved-but-empty string that is not `"-"` (e.g., a string-table entry that happens to be
`""`) behaves the same way: it sets the segment to no texture.

An unresolved string (one that compiles fine but the string index is out of range at runtime) is
distinct from a resolved empty string and is truly silent.

## Texture name validation — `texname` must be a valid, loaded texture name or "-"

If `texname` is neither `NULL` nor `"-"`, it is looked up in the texture manager via
`TexMan.GetTexture(texname, FTexture::TEX_Wall, ...)`. An unrecognized texture name does not
cause an error; the texture manager prints `Unknown texture: "<name>"` to the console and returns
the engine's default/missing-texture placeholder (the `-NOFLAT-` checkered graphic). The matched
sidedef segment's texture is then set to this placeholder. This differs from other string-lookup
failures on this function (NULL pointer case) and from `ReplaceTextures`' behavior — a typo in
`texturename` is *visible* as a console message and a visible broken-texture appearance, not
silent.

## Zandronum-only netcode replication — not on the ZDoom wiki

The implementation checks `NETWORK_GetState()` before textures are changed:

```cpp
if ( NETWORK_GetState( ) == NETSTATE_SERVER )
    SERVERCOMMANDS_SetLineTextureByID( lineid, side, position, texname );
```

On a server, the function broadcasts the texture change to all connected clients via the
`SetLineTextureByID` server command. Each client re-runs the same texture-lookup and texture-set
logic independently. This keeps network traffic constant regardless of how many linedefs match the
ID, but means any lookup failures (NULL string resolution, unrecognized texture name) happen
identically on server and clients. In single-player or as a client-side script, the network call
is skipped.

## Map-reset bookkeeping — Zandronum addition, not on the ZDoom wiki

Each affected linedef has a `TexChangeFlags` bitmask updated to track which of its six texture
segments (three per side) were modified:

```cpp
ulShift = position;
if ( side )
    ulShift += 3;
lines[linenum].TexChangeFlags |= 1 << ulShift;
```

This bookkeeping is internal to the engine and used for map reset/reload restoration. Not
user-facing — just explains why this field is touched if seen elsewhere in engine or ACS source.

## See also

- [`ReplaceTextures`](replacetextures.md) — replaces *every* occurrence of a texture name across
  the entire map, instead of targeting linedefs by ID.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
