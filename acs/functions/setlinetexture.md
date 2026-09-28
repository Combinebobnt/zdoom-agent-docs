# `SetLineTexture`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** `SetLineTexture - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=SetLineTexture&oldid=35840`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_SETLINETEXTURE` at lines 11431-11433,
`DLevelScript::SetLineTexture` at lines 4027-4093, declaration at `p_acs.h:1095`),
the Zandronum source's `src/sv_commands.cpp` (`SERVERCOMMANDS_SetLineTextureByID` at lines 3468-3479),
the Zandronum source's `src/textures/texturemanager.cpp` (`FTextureManager::GetTexture` at lines
308-328, its empty-string check at lines 312-315; `FTextureManager::CheckForTexture` at lines
151-230, its `"-"` special case at lines 164-167; `DefaultTexture`'s `"-NOFLAT-"` assignment at
line 988) for the `"-"`/empty-string/unrecognized-name resolution paths, the Zandronum source's
`src/cl_main.cpp` (`ServerCommands::SetLineTextureByID::Execute` at lines 7096-7108) for the
client-side re-execution behavior (2026-09-25),
and the zt-bcc source's `lib/zcommon.bcs` (constant definitions at lines 67-69 for `SIDE_*`, lines 74-76
for `TEXTURE_*`) on 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin — `zt-bcc/src/builtin.c:247`: `{ "setlinetexture", "iiis", NULL }`
(four required int/string args), compiling to `PCD_SETLINETEXTURE`
(`zt-bcc/src/builtin.c:395`). Not a `zcommon.bcs` `special`-table entry.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## Syntax

```text
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

```text
SIDE_FRONT = 0   // front sidedef of the linedef
SIDE_BACK  = 1   // back sidedef of the linedef
```

**Important:** the `line_side` parameter is clamped to 0 or 1 via `side = !!side` (convert to
boolean, cast back to int) before any texture lookup. Any non-zero value becomes 1; negative values
become 1. So `SetLineTexture(id, 2, TEXTURE_TOP, "WALL01")` is equivalent to `SetLineTexture(id,
SIDE_BACK, TEXTURE_TOP, "WALL01")`, not an error.

## Texture position constants

```text
TEXTURE_TOP    = 0   // upper texture of sidedef
TEXTURE_MIDDLE = 1   // middle (wall) texture of sidedef
TEXTURE_BOTTOM = 2   // lower texture of sidedef
```

The position parameter is used directly as a switch index; values outside 0–2 are silently ignored
(the switch has an empty `default:` case, so an invalid position does nothing to the texture).

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

**Exception:** the special string `"-"` is a literal one-character string, not an empty one. It
resolves from the string table as itself, so it is *not* `NULL` and passes the guard above the
same as any other name; it is then handed to `TexMan.GetTexture` (see below) exactly like any
other texture name. The special-casing happens inside the texture manager, not the ACS string
table: `FTextureManager::CheckForTexture` explicitly checks for the literal name `"-"` (a
Doom-era convention predating ACS) and returns the no-texture dummy (texture ID 0) for it
directly, without ever attempting a real texture lookup. This is the documented way to remove a
texture; it is not a silent failure, just a special-case name.

A resolved string that is genuinely empty (`""`, not `"-"`) also ends up at texture ID 0, but via
a separate check: `FTextureManager::GetTexture` tests for a zero-length name itself and returns
texture ID 0 immediately, before `CheckForTexture` (and its `"-"` special case) is ever reached.

An unresolved string (one that compiles fine but the string index is out of range at runtime) is
distinct from a resolved empty string and is truly silent.

## Texture name validation — `texname` must be a valid, loaded texture name, "-", or ""

Once `texname` is non-`NULL`, it is always looked up via `TexMan.GetTexture(texname,
FTexture::TEX_Wall, FTextureManager::TEXMAN_Overridable)`, including for `"-"` and `""` (handled
as above). For any other, unrecognized texture name, the lookup fails to find a match; the
texture manager prints `Unknown texture: "<name>"` to the console and returns the engine's
default/missing-texture placeholder (the `-NOFLAT-` checkered graphic). The matched sidedef
segment's texture is then set to this placeholder. This differs from other string-lookup failures
on this function (NULL pointer case) and from `ReplaceTextures`' behavior — a typo in
`texturename` is *visible* as a console message and a visible broken-texture appearance, not
silent.

## Zandronum-specific: netcode replication (not on the ZDoom wiki)

The implementation checks `NETWORK_GetState()` after the local texture change loop, not before it:

```cpp
if ( NETWORK_GetState( ) == NETSTATE_SERVER )
    SERVERCOMMANDS_SetLineTextureByID( lineid, side, position, texname );
```

On a server, the local sidedef textures are updated first, then the change is broadcast to all
connected clients via the `SetLineTextureByID` server command. Each client re-runs the same
texture-lookup and texture-set logic independently against the string the server sends. This keeps
network traffic constant regardless of how many linedefs match the ID. A `NULL` string resolution
returns early before this broadcast is ever reached, so it stays server-local; clients never see a
command for it. An unrecognized texture name does reach clients (the server still sends the
resolved string), and each client's own `TexMan.GetTexture` call prints its own `Unknown texture`
warning and falls back to the same placeholder independently. In single-player or as a client-side
script, the network call is skipped.

UZDoom's version of this function has no equivalent check or broadcast step — it always runs the
lookup-and-set logic directly, with no server/client branch. This is consistent with that engine's
different networking model, where connected clients execute identical ACS from a shared command
stream rather than relying on server-authoritative broadcast of individual state changes.

## Zandronum-specific: map-reset bookkeeping (not on the ZDoom wiki)

Each affected linedef has a `TexChangeFlags` bitmask updated to track which of its six texture
segments (three per side) were modified:

```cpp
ulShift = 0;
ulShift += position;
if ( side )
    ulShift += 3;
lines[linenum].TexChangeFlags |= 1 << ulShift;
```

This bookkeeping is internal to the engine and used for map reset/reload restoration. Not
user-facing — just explains why this field is touched if seen elsewhere in engine or ACS source.

UZDoom's version of this function has no equivalent bitmask or bookkeeping step — its texture
assignment ends at the sidedef texture-set call, with nothing tracking which segments were
touched.

## See also

- [`ReplaceTextures`](replacetextures.md) — replaces *every* occurrence of a texture name across
  the entire map, instead of targeting linedefs by ID.
