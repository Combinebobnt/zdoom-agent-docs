# `PlayerField` (option menu item)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-09)
**Provenance:** Zandronum Wiki `MENUDEF` (retrieved 2026-09-09, https://wiki.zandronum.com/w/index.php?title=MENUDEF&oldid=1549) + verified against Zandronum `src/menu/menudef.cpp` (parsing, lines 896-908) and `src/menu/optionmenuitems.h:1302-1337` (FOptionMenuPlayerField class).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Zandronum-only option menu item that provides an interactive player selector, storing the selected player's index in a CVar.

## Syntax

```text
PlayerField <label>, <cvar> [, <attributes>]
```

- **label**: Display name for the field.
- **cvar**: Name of the CVar to bind. Should be an integer CVar; the selected player's index (0 to MAXPLAYERS-1) is written here.
- **attributes** (optional, comma-separated): Zero or more of:
  - `nobots`: Exclude bot players from the selectable range.
  - `notself`: Exclude the local player (console player) from the selectable range.

## Behavior

Pressing Left or Right arrow, or Enter, advances or retreats the selection to the next valid player. The selection skips invalid players (those not currently in-game) and wraps around the full player list.

If the current CVar value points to an invalid player (one that has left, or never existed), the field displays `"Unknown"` and seeking does not advance from that starting position (seeking returns false and plays no sound).

Returns `false` (no sound, no CVar write) if the seek operation cannot find any valid player other than the starting selection (e.g., the local player is the only valid choice and `notself` is set).

## Zandronum-specific: team and player-selection menus

This item type does not exist in UZDoom. It was introduced to support Zandronum's team and player-selection menus for join-in-progress gameplay; custom menus may use it for similar purposes.
