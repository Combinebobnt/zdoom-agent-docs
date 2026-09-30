# Automap block definition

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `MAPINFO/Automap definition` (retrieved 2026-09-28, https://zdoom.org/w/index.php?title=MAPINFO/Automap_definition&oldid=47157) + verified against the Zandronum source's `src/am_map.cpp:476–547` (`FMapInfoParser::ParseAMColors`) and the UZDoom source's `src/am_map.cpp:778–854` (`FMapInfoParser::ParseAMColors`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Overview

An `automap` or `automap_overlay` block in MAPINFO defines mod-specific automap colorset settings. These blocks control the appearance of the automap display in regular mode (`automap`) and overlay mode (`automap_overlay`), including the color scheme for walls, items, and other visual elements.

## Syntax

```text
automap {
    property = value
    property = value
    ...
}

automap_overlay {
    property = value
    property = value
    ...
}
```

- `automap` — defines colors for the automap in regular (full-screen) mode.
- `automap_overlay` — defines colors for the automap in overlay mode (displayed on top of the game view).

Both blocks share identical property sets. Multiple `automap` blocks can be defined; each one starts again from an all-white colorset, so the last one encountered replaces earlier ones entirely rather than layering on them. Similarly for `automap_overlay`. Either colorset is only used while the `am_customcolors` cvar is on (the default).

## Properties

### Base colorset

**`base = "<preset>"`**
- Sets the base color palette that the automap will use as a starting point. If a color property is not explicitly defined in the block, the base colorset's value is used instead. Valid values are `"Doom"`, `"Strife"`, or `"Raven"` (case-insensitive). If `base` is not specified, a white colorset is used by default. The `base` property must be specified before any color properties; specifying `base` after any color property triggers a parse error: `'base' must be specified before the first color`.

### Display options

**`showlocks = <bool>`**
- Determines whether locked doors are displayed with a separate color (via the `LockedColor` property) on the automap. Defaults to `false` if not specified. Valid boolean values: `true` / `false`.

### Color properties

The following color properties can be set to customize the automap's visual appearance. Each property takes a color value (a quoted string), which can be either a named color from the CVARINFO color definitions (e.g., `"red"`, `"green"`), or an RGB value as three space-separated hex numbers (e.g., `"ff 00 00"` for red). Color values are case-insensitive.

**Wall colors:**
- **`WallColor`** — Color of one-sided (solid) walls and secret walls (when viewed without the `am_cheat` cheat).
- **`TwoSidedWallColor`** — Color of two-sided lines that have no difference in floor or ceiling heights on either side. Only visible when using the `am_cheat` cheat.
- **`FloorDiffWallColor`** — Color of two-sided lines where the floor height differs between the front and back sides.
- **`CeilingDiffWallColor`** — Color of two-sided lines where the ceiling height differs between the front and back sides.
- **`ExtraFloorWallColor`** — Color of 3D floor boundaries (lines where 3D floors are attached).
- **`SecretWallColor`** — Color of lines marked as secret when using the `am_cheat` cheat. When `am_cheat` is not active, secret walls are drawn using `WallColor`.

**Background and display elements:**
- **`Background`** — Color of the automap's background/canvas.
- **`GridColor`** — Color of the automap grid overlay (if enabled via the `am_showgrid` console variable).
- **`XHairColor`** — Color of the small crosshair dot drawn at the center of the automap.

**Player representation:**
- **`YourColor`** — Color of the arrow or icon representing the player in single-player games.

**Actor/thing colors:**
- **`ThingColor`** — Default color for things (actors) revealed with the `am_cheat` map cheat.
- **`ThingColor_Item`** — Color for items (actors with the `COUNTITEM` flag, or actors of the `Item` class) revealed with the map cheat.
- **`ThingColor_CountItem`** — Color for count items (actors with the `COUNTITEM` flag set) revealed with the map cheat.
- **`ThingColor_Monster`** — Color for hostile monsters (living enemies) revealed with the map cheat.
- **`ThingColor_NocountMonster`** — Color for non-counted, non-friendly monsters revealed with the map cheat. These are monsters that do not contribute to kill counts and are not allied with the player.
- **`ThingColor_Friend`** — Color for allied players and friendly monsters (actors with the `FRIENDLY` flag) revealed with the map cheat.

**Special walls and teleporters:**
- **`SpecialWallColor`** — Color of lines with an action special (other than door-opening specials).
- **`LockedColor`** — Color of lines that open locked doors. This is used only when `showlocks` is true and the lock has no custom color defined in the LOCKDEFS lump.
- **`IntraTeleportColor`** — Color of intra-level teleporters (lines that teleport the player to a different location on the same map).
- **`InterTeleportColor`** — Color of inter-level teleporters (lines that teleport the player to a different map).
- **`SecretSectorColor`** — Color of the boundary lines of secret sectors on the automap.

**Unseen and visibility:**
- **`NotSeenColor`** — Color of lines that have not yet been seen by the player. Only visible when a computer area map item has been picked up. Once the player sees a line, it is drawn in its appropriate normal color.
- **`AlmostBackgroundColor`** — Color used to represent invisible and partially invisible players (players with the `INVISIBILITY` or partial invisibility powerup).

## Engine-family divergence: UZDoom-only properties

**`SectorFillAlpha = <float>`** (UZDoom only)
- Controls the opacity of the automap's sector fill display when sector-fill mode is enabled (via `am_textured` or related rendering modes). Valid range: `0.0` (fully transparent) to `1.0` (fully opaque); values outside this range are clamped. The value must be written as a float literal (`1.0`, not `1`); an integer literal is a parse error. Zandronum has no such key, and an unknown key is a fatal `Unknown key '...'` script error there.

**`PortalColor`, `SectorFillColor`, `UnexploredSecretColor`** (UZDoom only)
- These three names are in UZDoom's colorset key table but not in Zandronum's (Zandronum `src/am_map.cpp:189-214`, UZDoom `src/am_map.cpp:375-403`). On Zandronum each is the same fatal `Unknown key` error. Do not include them in MAPINFO if Zandronum compatibility is required.
  - **`PortalColor`** — Color of lines that belong to a portion of the map connected to the player's current area by a portal.
  - **`SectorFillColor`** — Color used when rendering sector fills in textured automap mode.
  - **`UnexploredSecretColor`** — Color of unexplored secret sector boundaries.

## Wiki provenance note

The original ZDoom Wiki page describes `PortalColor` and `ShowLocks` but does not document UZDoom-specific properties like `SectorFillAlpha`, `SectorFillColor`, or `UnexploredSecretColor` (which are UZDoom additions not present in the upstream ZDoom that the wiki documents). Zandronum's parser accepts only `base`, `showlocks`, and the 22 original color names.

## Examples

### Simple Doom-based automap

```text
automap {
    base = "Doom"
    showlocks = true
    Background = "00 00 00"
    YourColor = "ff ff 00"
    WallColor = "00 80 00"
    GridColor = "00 40 00"
}
```

### Custom colorset from scratch

```text
automap {
    Background = "00 49 49"
    YourColor = "00 33 33"
    WallColor = "00 66 66"
    TwoSidedWallColor = "66 66 66"
    FloorDiffWallColor = "66 66 66"
    CeilingDiffWallColor = "66 66 66"
    ExtraFloorWallColor = "66 66 66"
    ThingColor = "88 88 88"
    ThingColor_Item = "20 9c fc"
    ThingColor_CountItem = "fc f4 20"
    ThingColor_Monster = "fc 00 00"
    ThingColor_Friend = "00 33 33"
    SpecialWallColor = "00 77 77"
    SecretWallColor = "00 aa aa"
    GridColor = "00 88 88"
    XHairColor = "00 00 00"
    NotSeenColor = "00 50 50"
    LockedColor = "00 00 00"
    IntraTeleportColor = "00 00 00"
    InterTeleportColor = "00 00 00"
    SecretSectorColor = "00 00 00"
    AlmostBackgroundColor = "00 50 50"
}
```

### Separate overlay mode colors

```text
automap_overlay {
    base = "Raven"
    showlocks = false
    Background = "00 00 00"
    YourColor = "ff ff 00"
    GridColor = "00 ff 00"
}
```

## See also

- Related CVARs: `am_cheat`, `am_textured`, `am_showgrid`, `am_showsubsector`, `am_showalllines`
- Related lumps: LOCKDEFS (for custom lock colors), [LANGUAGE](../../language/concepts/language-lump.md) (for localizable color names)
- Automap concept page (on ZDoom Wiki, for general automap behavior)
