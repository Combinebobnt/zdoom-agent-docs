# `am_drawmapback`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/am_map.cpp:94` (CVAR declaration) and `src/am_map.cpp:1654–1660` (consuming code); comparison with ZDoom Wiki `CVARs:Automap` (https://zdoom.org/w/index.php?title=CVARs%3AAutomap&oldid=54516).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Controls how the AUTOPAGE map background graphic is drawn in fullscreen automap. Takes integer values 0–2 (not a boolean, despite the wiki's boolean description). The cvar itself, its default value, and its `CVAR_ARCHIVE` persistence are identical on UZDoom (`src/am_map.cpp:162`) and Zandronum (`src/am_map.cpp:94`); mode 2's exact gate differs between the two engines — see the divergence section below.

## Mode behavior

- **0**: Do not draw the background.
- **1**: Always draw the background (default). This is the standard mode when using the built-in color sets.
- **2**: Draw the background only when using mod-defined custom colors (set via `am_customcolors = true` and MAPINFO/CVARINFO color definitions) or the Raven color set (`am_colorset = 3`). This mode prevents the background from appearing when using Doom or Strife stock color sets. On UZDoom, this also fires when `am_colorset` is left at its auto-detect default rather than explicitly set to 3 — see below.

## Persistence

Marked `CVAR_ARCHIVE`, so this setting persists to the config file on both engines. Changes take effect the next time the automap is activated.

## Related cvars

- **`am_customcolors`** — whether to use mod-defined color settings
- **`am_colorset`** — selects which built-in or custom color set to use (0 = custom, 1 = Doom, 2 = Strife, 3 = Heretic/Hexen). Zandronum's default is 0 (custom); UZDoom's default is -1 (auto-detect, see below).

## Engine-family divergence: `am_colorset` auto-detect and the mode-2 gate

Zandronum's mode-2 gate (`src/am_map.cpp:1654–1660`) restricts the drawn background to an explicit `am_colorset` value of 3 whenever the level isn't using mod-defined custom colors. UZDoom's equivalent gate in `DAutomap::clearFB` (`src/am_map.cpp:1625–1632`) additionally treats `am_colorset`'s auto-detect sentinel value (-1) as satisfying the Raven condition, but only when the loaded game's `gameinfo.gametype` is itself Raven-derived (Heretic/Hexen).

This traces back to a difference in `am_colorset`'s own default and resolution logic, not just the mode-2 gate. Zandronum defaults `am_colorset` to 0 and resolves colors with a plain `switch` on that value (`src/am_map.cpp:91`, `:1298–1320`) — value 0 always falls through to the "custom `am_*` cvars" branch, with no game-family auto-detection anywhere in that path. UZDoom defaults `am_colorset` to -1 (`src/am_map.cpp:159`) and, before the equivalent switch, resolves -1 to 1/2/3 based on `gameinfo.gametype` (`GAME_DoomChex` → 1, `GAME_Strife` → 2, `GAME_Raven` → 3; anything else falls through to the custom-cvars branch) in `AM_initColors` (`src/am_map.cpp:724–733`).

Net effect: a fresh UZDoom config running a genuine Heretic/Hexen-family IWAD gets the mode-2 background drawn out of the box (colors resolve to Raven via the -1 default), while the equivalent fresh Zandronum config does not, because Zandronum's default (0) never resolves to "Raven" without the player explicitly setting `am_colorset` to 3.
