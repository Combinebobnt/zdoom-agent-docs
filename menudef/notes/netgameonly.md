# `NetgameOnly` (option menu descriptor flag)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-09)
**Provenance:** Zandronum Wiki `MENUDEF` (retrieved 2026-09-09, https://wiki.zandronum.com/w/index.php?title=MENUDEF&oldid=1549) + verified against Zandronum `src/menu/menudef.cpp:923-926` (parsing, sets descriptor flag) and `src/menu/menu.cpp:560-564` (consumer, checks and blocks on single-player).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

A descriptor-level flag (not an item keyword) that restricts menu access to netgame contexts only.

## Syntax

```text
NetgameOnly
```

Place this keyword in the descriptor section of an OptionMenu (alongside `Class`, `Title`, `Position`, etc.), not within the menu's item list.

## Behavior

When a menu is marked with `NetgameOnly`, the engine checks the network state when the menu is opened:

- If the engine is in a netgame (online multiplayer), the menu opens normally.
- If the engine is in single-player or listening-server mode, the menu does **not** open, and the player sees an error message: `"You must be in a netgame to use this.\n\npress a key."`

This gate is applied at menu-open time, not at descriptor parse time, so a modder can conditionally create a different menu in single-player and apply `NetgameOnly` only to the multiplayer-specific version.

## Zandronum-specific notes

This flag does not exist in UZDoom. It was introduced to support multiplayer-specific menus (such as team and player selection) without requiring duplicate menu definitions for single-player contexts.
