# `am_drawmapback`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/am_map.cpp:94` (CVAR declaration) and `src/am_map.cpp:1654–1660` (consuming code); comparison with ZDoom Wiki `CVARs:Automap` (oldid=54516).

Controls how the AUTOPAGE map background graphic is drawn in fullscreen automap. Takes integer values 0–2 (not a boolean, despite the wiki's boolean description).

## Mode behavior

- **0**: Do not draw the background.
- **1**: Always draw the background (default). This is the standard mode when using the built-in color sets.
- **2**: Draw the background only when using mod-defined custom colors (set via `am_customcolors = true` and MAPINFO/CVARINFO color definitions) or the Raven color set (`am_colorset = 3`). This mode prevents the background from appearing when using Doom or Strife stock color sets.

## Persistence

Marked `CVAR_ARCHIVE`, so this setting persists to the config file. Changes take effect the next time the automap is activated.

## Related cvars

- **`am_customcolors`** — whether to use mod-defined color settings
- **`am_colorset`** — selects which built-in or custom color set to use (0 = custom, 1 = Doom, 2 = Strife, 3 = Heretic/Hexen)
