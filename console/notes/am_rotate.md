# `am_rotate`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/am_map.cpp:84` (CVAR declaration) and consuming code throughout the file; comparison with ZDoom Wiki `CVARs:Automap` (oldid=54516).

Controls whether the automap rotates to match the player's view direction. Takes integer values 0–2 (not a boolean, despite the wiki's boolean description).

## Mode behavior

- **0**: Normal mode. The automap is always drawn with north at the top of the screen, regardless of player orientation.
- **1**: Always rotated. The automap rotates so that lines toward the top of the screen always point in the direction the player is facing. Useful for navigation.
- **2**: Automatic. The automap is rotated only in overlay mode (`am_overlay` > 0) when the player is actively viewing the game world (`viewactive`), reverting to normal (non-rotated) orientation in fullscreen automap. This provides rotation-assisted navigation without disorienting the player in stationary overhead-view scenarios.

## Persistence

Marked `CVAR_ARCHIVE`, so this setting persists to the config file.

## Related cvars

- **`am_overlay`** — enables overlay automap modes that change how `am_rotate` behaves (mode 2)
- **`am_followplayer`** — toggles whether the automap centers on the player
