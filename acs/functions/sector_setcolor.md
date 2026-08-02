# Sector_SetColor

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Sector_SetColor - ZDoom Wiki (https://zdoom.org/w/index.php?title=Sector_SetColor&oldid=36901), verified against Zandronum 3.2.1 source (p_lnspec.cpp line 2497, p_sectors.cpp line 696).

**Signature:** `Sector_SetColor(tag, r, g, b[, desat]):int` (action special 212)

Sets the color tint of light in all sectors matching `tag`. Returns 1 unconditionally — the return value is not a success/failure signal and does not indicate how many sectors were affected (the loop inside `LS_Sector_SetColor` calls `SetColor` on each match, but the function returns true regardless of the count).

## Parameters

- **`tag`** — Sector tag. Resolves via `P_FindSectorFromTag`, which uses modular arithmetic and can match multiple sectors. Passing `tag=0` behaves like any other tag value (matches sectors with numeric tag 0, if any exist), not a wildcard.
- **`r`, `g`, `b`** — Red, green, blue intensity values, each an int in range 0–255. White light (255, 255, 255) is the default. Values outside this range are passed directly to the engine's `GetSpecialLights` function, which clamps them to 0–255 internally.
- **`desat`** — **Optional** (trailing parameter). Desaturation level, 0–255, where 0 = normal colors and 255 = grayscale. If omitted, defaults to 0 (no desaturation). The parameter name is slightly inconsistent with the wiki's `desaturate` — the engine code uses `desat` throughout.

## Return value

Always `1` (`true`). No distinction between "no sectors matched the tag" and "sectors updated successfully" — a zero-match tag still returns 1.

## Netcode

Server-side only in multiplayer: the server calls `SetColor` locally, then broadcasts the change to all clients via `SERVERCOMMANDS_SetSectorColorByTag(tag, r, g, b, desat)`. Client-side ACS scripts (marked `CLIENTSIDE`) can call this function and will have it execute locally on the client via the `ACS_IsCalledFromScript()` gate in `LS_Sector_SetColor` (line 2507) — however, **client changes do not broadcast back to the server**. This is a visual-only effect per the code comments.

## Fork note

The ZDoom wiki's mention of applying a UDMF `color` property and fixed-point desaturation in the map editor is correct for ZDoom but not verified as behavior in Zandronum itself; this function is the runtime equivalent regardless of map format.

## See also

- [Sector_SetFade](sector_setfade.md) — companion function setting the fade (background) color instead of light color.
- [GetSectorFloorZ](getsectorfloorz.md) — uses the same `P_FindSectorFromTag` resolution logic for tag matching.
