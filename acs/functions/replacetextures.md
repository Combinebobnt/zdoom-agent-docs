# `ReplaceTextures`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `ReplaceTextures - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=ReplaceTextures&oldid=35847`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_REPLACETEXTURES` at lines 11436-11439,
`DLevelScript::ReplaceTextures` int-overload at lines 4095-4101, the real const-`char*` overload
that does the work at lines 4104-4168, declarations at `p_acs.h:1096,1098`),
the Zandronum source's `src/textures/texturemanager.cpp` (`FTextureManager::GetTexture` at lines
308-328, texture index 0 reserved as the "no texture" dummy at lines 973-974, `DefaultTexture`
init at line 988), the Zandronum source's `src/sv_commands.cpp` (`SERVERCOMMANDS_ReplaceTextures` at
lines 5114-5120), the Zandronum source's `src/cl_main.cpp` (`ServerCommands::ReplaceTextures::Execute`
at lines 9623-9626), the Zandronum source's `protocolspec/spec.misc.txt` (`textureFlags` sent as a
`Byte` at line 58), the Zandronum source's `src/g_game.cpp` (`GAME_ResetMap` restoring flagged line
textures at lines 3541-3563 and flagged flats at lines 3665-3669), the Zandronum source's
`src/sv_main.cpp` (`SERVER_UpdateSectors`/`SERVER_UpdateLines` sending flagged flats and line
textures to a connecting client at lines 3494-3495 and 3692-3693), and the zt-bcc source's `lib/zcommon.bcs` (`NOT_*` flag values at lines 371-375)
on 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin — `zt-bcc/src/builtin.c:148`: `{ "replacetextures", ";ss;i" }`
(two required string args, one optional int), compiling to `PCD_REPLACETEXTURES`
(`zt-bcc/src/builtin.c:296`). Not a `zcommon.bcs` `special`-table entry.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## Syntax

```text
void ReplaceTextures(str oldtexturename, str newtexturename, int flags = 0);
```

Replaces every wall-side texture/sector flat in the currently loaded map that exactly matches
`oldtexturename` with `newtexturename`, restricted by `flags`. This matches the wiki's basic
description. It is fully implemented on Zandronum.

## Flags — matches the wiki's list, verified against the fork's bit values

```text
NOT_BOTTOM  = 0x1   // don't touch wall lower textures
NOT_MIDDLE  = 0x2   // don't touch wall middle textures
NOT_TOP     = 0x4   // don't touch wall upper textures
NOT_FLOOR   = 0x8   // don't touch sector floor flats
NOT_CEILING = 0x10  // don't touch sector ceiling flats
```

Combine with `|` as the wiki says. Internally the wall pass and the flat pass are each skipped
outright only when `flags` equals exactly that pass's group and nothing else (an XOR test, e.g.
`flags == NOT_BOTTOM|NOT_MIDDLE|NOT_TOP` skips the wall loop). Any other value still walks every
sidedef/sector and checks bits individually. So passing all five flags at once skips neither loop,
but both loops change nothing: an effective no-op, not an error.

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
`ReplaceTextures("", "SOMETEX")` does not fail or no-op. It matches and overwrites **every
currently-blank wall segment in the map** with `SOMETEX`. The flat pass matches the same way, but
only a sector whose floor or ceiling is itself blank, which ordinary maps rarely have. The name
`"-"` resolves to the same index 0 (the texture manager's "-" means "no texture" check,
`texturemanager.cpp:164-167`), so `ReplaceTextures("-", "SOMETEX")` behaves identically. This is
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

## Zandronum-specific: netcode replication for client/server sync

Before touching any geometry, the const-`char*` overload checks `NETWORK_GetState()`:

```cpp
if ((NETWORK_GetState() == NETSTATE_SERVER))
    SERVERCOMMANDS_ReplaceTextures(fromname, toname, flags);
```

Offline, and on a client (e.g. from a `CLIENTSIDE` script), the call just runs locally with no
broadcast; a client-side call changes only that client's map. On the server it also sends the raw
`(fromname, toname, flags)` triple to clients rather than a diff of which sidedefs/sectors
actually changed. Each client's `ServerCommands::ReplaceTextures::Execute`
(`cl_main.cpp:9623-9626`) re-runs the identical `DLevelScript::ReplaceTextures` logic locally
against its own copy of the map. This keeps network traffic constant regardless of map size, but
means the replacement logic (including both silent-failure modes above) runs independently on the
server and on every client. Clients resolve the names against their own loaded textures, so a
client missing `newtexturename` gets the default texture while the server does not. `flags`
travels as a `Byte` (`protocolspec/spec.misc.txt:58`); all five flags fit, so the truncation has
no visible effect.

A client that connects later never receives this command. Instead the server sends it the current
textures of every line and flats of every sector flagged by the bookkeeping below
(`sv_main.cpp:3692-3693`, `3494-3495`).

## Zandronum-specific: map-reset/change-tracking bookkeeping

Every wall-side change sets a bit in that linedef's `TexChangeFlags`, and every flat change sets
`sector_t::bFlatChange = true` (`p_acs.cpp:4137-4138, 4157, 4163-4164`). `GAME_ResetMap` reads
these to restore the map's original line textures and both flats of each flagged sector
(`g_game.cpp:3541-3563`, `3665-3669`). That reset runs on round resets in modes such as survival,
last man standing, duel and invasion, and on a map reset requested through ACS `ResetMap`. So a
`ReplaceTextures` change is reverted by a map reset, not by a hub return. The same flags drive
the late-join updates described above.

## Engine-family divergence: no change-tracking bookkeeping on UZDoom

UZDoom's equivalent (`FLevelLocals::ReplaceTextures`, `src/playsim/p_sectors.cpp:1457-1491`) runs
the same two-pass wall/flat replacement described above: matching flag semantics (the wall pass and
flat pass are each skipped outright only when every bit in that pass's group is set, otherwise every
sidedef/sector is walked and each bit checked individually), the same `fromname == nullptr`
early-return before anything else runs, and — via its own texture manager's name-to-ID lookup
(`src/common/textures/texturemanager.cpp:327-345`) — the same empty-string-resolves-to-the
reserved "no texture" index-0 sentinel and unresolved-name-falls-back-to-the-default-texture-with-
a-console-print behavior documented above. Where it differs: the wall and sector texture writes
it makes (`src/gamedata/r_defs.h`) are plain field assignments with no further side effect. There
is nothing in UZDoom analogous to Zandronum's per-linedef `TexChangeFlags` bits or per-sector
`bFlatChange` flag — a search across the UZDoom source finds no field or mechanism filling that
role. On Zandronum those fields turn out to feed the same client/server-sync machinery as the
netcode section above (relaying accumulated state to a late-joining client, and per-reset texture
restoration), which tracks with UZDoom having no equivalent: without a dedicated server process
distinct from the players, there is no "what changed since a client last saw this map" question for
a `ReplaceTextures` call to answer. A tool or script that inspected Zandronum's
`TexChangeFlags`/`bFlatChange` bits to detect an ACS-driven texture change has no equivalent hook
on UZDoom.

## See also

[`SetLineTexture`](setlinetexture.md) (tier C in this tree currently — signature only) for
per-linedef-ID texture changes instead of a global find/replace across the whole map.
