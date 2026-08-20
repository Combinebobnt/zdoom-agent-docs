# `am_rotate`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/am_map.cpp:84` (CVAR declaration) and consuming code throughout the file; comparison with ZDoom Wiki `CVARs:Automap` (https://zdoom.org/w/index.php?title=CVARs%3AAutomap&oldid=54516).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Controls whether the automap rotates to match the player's view direction. Takes integer values 0–2 (not a boolean, despite the wiki's boolean description). It's a plain `CVAR`, not a `CUSTOM_CVAR`, in both engines, so this range isn't enforced — an out-of-range value simply falls through to mode-0 (non-rotated) behavior at every `am_rotate == 1 || (am_rotate == 2 && viewactive)` check site.

UZDoom declares the identical `Int`/`0`/`CVAR_ARCHIVE` cvar (`src/am_map.cpp:143`) and gates rotation on the same `am_rotate == 1 || (am_rotate == 2 && viewactive)` condition throughout `src/am_map.cpp` — clean agreement with the Zandronum behavior described below (line numbers differ between the two checkouts; Provenance above cites Zandronum's `:84`, not UZDoom's `:143`).

## Mode behavior

- **0**: Normal mode. The automap is always drawn with north at the top of the screen, regardless of player orientation.
- **1**: Always rotated. The automap rotates so that lines toward the top of the screen always point in the direction the player is facing. Useful for navigation.
- **2**: Automatic. The automap is rotated only in overlay mode (`am_overlay` > 0) when the player is actively viewing the game world (`viewactive`), reverting to normal (non-rotated) orientation in fullscreen automap. This provides rotation-assisted navigation without disorienting the player in stationary overhead-view scenarios. Both engines set `viewactive = (am_overlay != 0)` at the same automap-entry site (Zandronum's automap-toggle handler around `src/am_map.cpp:1480`; UZDoom's equivalent around `src/am_map.cpp:3573`), so mode 2's rotation condition evaluates identically on both.

## Persistence

Marked `CVAR_ARCHIVE`, so this setting persists to the config file.

## Related cvars

- **`am_overlay`** — enables overlay automap modes that change how `am_rotate` behaves (mode 2)
- **`am_followplayer`** — toggles whether the automap centers on the player
