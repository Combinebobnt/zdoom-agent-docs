# `am_cheat`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/am_map.cpp:631` (CUSTOM_CVAR declaration) and consuming code throughout the file; verified against wiki description (ZDoom Wiki `CVARs:Automap`, oldid=54516).

Controls the level of detail and cheat features visible on the automap. Takes integer values 0–6, with each mode adding visibility beyond the previous.

## Mode behavior

- **0**: No cheat. Only architecture the player has seen is shown.
- **1**: All architecture is shown, regardless of whether the player has seen it. Equivalent to one `iddt` cheat code input.
- **2**: In addition to mode 1, all things in the map are shown as arrows pointing in the direction they face. Equivalent to two `iddt` inputs.
- **3**: In addition to mode 2, all things are wrapped in a bounding box showing their collision size. No vanilla equivalent (ZDoom extension).
- **4–6**: Same as modes 1–3 respectively, except lines flagged as "hidden" (`ML_DONTDRAW`) are not shown. This differs from the vanilla behavior where mode 1–3 always show hidden lines.

## Storage behavior

This cvar is declared with no flags (`0`), meaning it does **not** persist to the config file when the game exits. Its value resets to the default (0) on every game start unless explicitly set via console, CVARINFO, or ACS script. For persistent automap cheat state across sessions, the config file must be manually edited.

## Related cvars

- **`am_showkeys`** — whether keys are highlighted with symbols
- **`am_showthingsprites`** — sprite display options for revealed things
