# Sector_SetFade

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2025-07-29)
**Provenance:** ZDoom Wiki (https://zdoom.org/w/index.php?title=Sector_SetFade&oldid=36174), verified against Zandronum source 2025-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action special, index 213

## Signature

```text
int Sector_SetFade (int tag, int r, int g, int b)
```

## Description

Sets the fog fade color for all sectors with the given `tag`. The fade color is applied using the sector's current lighting level, creating a "fog" effect that blends distant geometry toward the fade color.

**Parameters:**
- `tag`: Tag number of affected sectors (literal tag 0 searches for sectors with tag 0, no line-back-sector fallback)
- `r`: Red component of fade color (0-255; values outside this range are silently truncated via `BYTE` cast)
- `g`: Green component of fade color (0-255)
- `b`: Blue component of fade color (0-255)

**Return value:** Always `true` (regardless of whether any matching sector was found)

## Behavior

The fade color is stored in the sector's colormap via `GetSpecialLights(ColorMap->Color, fade, ColorMap->Desaturate)`. The rendering engine applies the fade proportionally based on distance and the sector's light level:
- A sector with light value 255 (maximum bright) shows virtually no visible fade (the fade color is mostly washed out)
- A sector with light value 0 (fully dark) appears nearly as a solid fade color
- Intermediate light levels blend proportionally

## Multiplayer and Client-side Behavior

On a server, the special sends `SERVERCOMMANDS_SetSectorFadeByTag` to replicate the change to all clients.

The `bExecuteOnClient` parameter (passed as `ACS_IsCalledFromScript()`) allows the fade to be set client-side: if the special is called from **any** ACS script (whether `CLIENTSIDE` or otherwise), that execution path also updates the sector's colormap on the local client. The comment in the source code aspires to "only if the special was called from a CLIENTSIDE ACS script," but the actual guard is `g_pCurrentScript != NULL` (true for any script), not a CLIENTSIDE-only check.

## UDMF Equivalent

UDMF maps can set a static fade color at map load time without invoking this special:
- Sector properties include a `fadecolor` field (integer in hex `RRGGBB` format, e.g. `0xFF8800`)
- This is optional; if omitted, the default fade is the level's `MAPINFO` `fade` property, or black if not specified

## Notes

- **Tag 0 semantics:** Unlike some sector specials (e.g., `Floor_MoveToValue`), tag 0 does not refer to the triggering line's back sector. It searches for sectors literally tagged with 0.
- **Dynamic changes:** The fade can be changed mid-level. If you need to test fade colors interactively, the `testfade` console command is available (cheats must be enabled for non-host players in multiplayer).

## Wiki/engine divergence

The wiki states the function "works inside CLIENTSIDE scripts," implying CLIENTSIDE-only behavior. **Zandronum actually allows any ACS script to set fades client-side** (checked via `ACS_IsCalledFromScript()`, not `CLIENTSIDE` flag). This is the broader condition intended for purely visual effects (the fade is rendered-only and has no gameplay impact).

## Engine-family divergence: no client/server replication step on UZDoom

The entire "Multiplayer and Client-side Behavior" section above is specific to Zandronum's
client/server network architecture and does not carry over to UZDoom. UZDoom's implementation of
this special does the sector lookup and applies the new fade color directly and unconditionally —
there is no equivalent of Zandronum's `bExecuteOnClient` parameter, no `ACS_IsCalledFromScript()`
check, and no network command sent to propagate the change to other participants. UZDoom (a
GZDoom-family engine) doesn't split ACS execution between an authoritative server and replicated
clients the way Zandronum's netcode does, so there's simply no separate "did this run on the
client" question for this special to answer: wherever the owning script runs, the fade is set
there, full stop. `CLIENTSIDE` still exists as a script-type concept in UZDoom for other purposes,
but it has no bearing on how this particular special behaves.
