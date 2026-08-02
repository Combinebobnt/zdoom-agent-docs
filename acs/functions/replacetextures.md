# `ReplaceTextures`

**Bucket:** compiler builtin — `zt-bcc/src/builtin.c:148`: `{ "replacetextures", ";ss;i" }`
(two required string args, one optional int), compiling to `PCD_REPLACETEXTURES`
(`zt-bcc/src/builtin.c:296`). Not a `zcommon.bcs` `special`-table entry.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see
"Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `ReplaceTextures - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=ReplaceTextures&oldid=35847`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_REPLACETEXTURES` at lines 11436-11439,
`DLevelScript::ReplaceTextures` int-overload at lines 4095-4101, the real const-`char*` overload
that does the work at lines 4104-4168, declarations at `p_acs.h:1096,1098`),
the Zandronum source's `src/textures/texturemanager.cpp` (`FTextureManager::GetTexture` at lines
308-328, texture index 0 reserved as the "no texture" dummy at lines 973-974, `DefaultTexture`
init at line 988), the Zandronum source's `src/sv_commands.cpp` (`SERVERCOMMANDS_ReplaceTextures` at
lines 5114-5120), the Zandronum source's `src/cl_main.cpp` (`ServerCommands::ReplaceTextures::Execute`
at lines 9622-9625), and the zt-bcc source's `lib/zcommon.bcs` (`NOT_*` flag values at lines 371-375)
on 2026-07-29.

## Syntax

```
void ReplaceTextures(str oldtexturename, str newtexturename, int flags = 0);
```

Replaces every wall-side texture/sector flat in the currently loaded map that exactly matches
`oldtexturename` with `newtexturename`, restricted by `flags`. This matches the wiki's basic
description — no divergence found there, this is a real, fully-implemented Zandronum function, not
one of the ZDoom-ahead-of-fork traps this bucket is usually checked for.

## Flags — matches the wiki's list, verified against the fork's bit values

```
NOT_BOTTOM  = 0x1   // don't touch wall lower textures
NOT_MIDDLE  = 0x2   // don't touch wall middle textures
NOT_TOP     = 0x4   // don't touch wall upper textures
NOT_FLOOR   = 0x8   // don't touch sector floor flats
NOT_CEILING = 0x10  // don't touch sector ceiling flats
```

Combine with `|` as the wiki says. Internally the wall pass and the flat pass are each skipped
entirely only when *all* of that pass's bits are set (e.g. `flags == NOT_BOTTOM|NOT_MIDDLE|NOT_TOP`
skips the wall loop outright); any other combination still walks every sidedef/sector and checks
bits individually, so passing all five flags at once is a documented no-op, not an error.

## Silent no-op on an unresolved `oldtexturename` string index — not on the wiki

`DLevelScript::ReplaceTextures(int, int, int)` (`p_acs.cpp:4095-4101`) resolves both string
arguments via `FBehavior::StaticLookupString` before doing anything, then the real overload
(`p_acs.cpp:4104`) starts with:

```cpp
if (fromname == NULL)
    return;
```

An out-of-range/invalid string-table index resolves to a `NULL` `char*`, and the whole call
silently does nothing — no console message, no return value (the function is `void`) to detect
it. This guard is on the *pointer*, not the string content.

## Empty-string `oldtexturename` is a real, distinct gotcha the NULL guard does not catch

A **resolved** empty string (`ReplaceTextures("", "BLOOD1")`, or any string-table entry that
happens to be `""`) is not `NULL`, so it passes the guard above and reaches
`FTextureManager::GetTexture`:

```cpp
if (name == NULL || name[0] == 0)
    return FTextureID(0);
```

Texture index `0` is not an arbitrary sentinel — it is the engine's actual reserved "no texture"
dummy texture, unconditionally registered first at texture-manager init
(`texturemanager.cpp:973-974`, `// Texture 0 is a dummy texture used to indicate "no texture"`).
Every sidedef segment that has no upper/lower texture assigned, and by extension a lot of ordinary
two-sided linedefs, already carries texture ID `0` on those unused segments. So
`ReplaceTextures("", "SOMETEX")` does not fail or no-op — it matches and overwrites **every
currently-blank wall segment (and, via the flat pass, no equivalent blank case for
floors/ceilings since sectors always have a real flat) in the map** with `SOMETEX`. This is
silent and easy to trigger by accident (e.g. an empty string literal, or a string-returning
expression that can evaluate to `""`), and is functionally very different from the NULL-pointer
no-op case above despite both stemming from "the old texture name didn't really name a texture."

## Unresolvable `newtexturename` falls back to the default texture, with a console print — asymmetric with `oldtexturename`'s NULL case

`GetTexture` on a non-empty name that still doesn't match any loaded texture doesn't return the
`0` dummy; it prints `Unknown texture: "<name>"` to the console and returns
`FTextureManager::DefaultTexture` (the `-NOFLAT-` checkered/missing texture, set up once at
`texturemanager.cpp:988`). So a typo'd `newtexturename` is not silent like a typo'd
`oldtexturename` lookup-miss — it visibly reports itself in the console, and every matched
old-texture surface becomes the missing-texture placeholder rather than staying unchanged.

## Zandronum-only netcode replication — absent from the ZDoom wiki, which predates Zandronum's client/server split

Before touching any geometry, the const-`char*` overload checks `NETWORK_GetState()`:

```cpp
if ((NETWORK_GetState() == NETSTATE_SERVER))
    SERVERCOMMANDS_ReplaceTextures(fromname, toname, flags);
```

The server sends the raw `(fromname, toname, flags)` triple to clients rather than a diff of which
sidedefs/sectors actually changed — each client's `ServerCommands::ReplaceTextures::Execute`
(`cl_main.cpp:9622-9625`) re-runs the identical `DLevelScript::ReplaceTextures` logic locally
against its own copy of the map. This keeps network traffic constant regardless of map size, but
means the replacement logic (including both silent-failure modes above) runs independently on the
server and on every client — a script that fires `ReplaceTextures` only from a server-exclusive
code path can still leave clients out of sync if the client's local texture set ever differs from
the server's (e.g. mid-game texture packs), which the wiki has no reason to mention since it
predates any of Zandronum's multiplayer split.

## Map-reset bookkeeping — Zandronum addition, not on the wiki

Every wall-side change sets a bit in that linedef's `TexChangeFlags`, and every flat change sets
`sector_t::bFlatChange = true` (`p_acs.cpp:4137-4138, 4157, 4163-4164`) — bookkeeping so the engine
can restore original textures when the map resets (e.g. a hub return or `ResetMap`-style reload).
Not user-facing behavior to code around, just documents why those fields exist if you see them
elsewhere.

## See also

[`SetLineTexture`](setlinetexture.md) (tier C in this tree currently — signature only) for
per-linedef-ID texture changes instead of a global find/replace across the whole map.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
