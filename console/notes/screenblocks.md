# `screenblocks` (cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `CVARs:Display` (retrieved 2026-08-02, oldid=54715) + verified against Zandronum source's `src/r_utility.cpp`.

Determines the size of the view window and valid range for display scaling.

## Default and range

Wiki documentation states the default is 10. **In Zandronum, the default is 11** — see source comment "Zandronum uses 11 instead of 10 as default value." Both enforce the same valid range: values are clamped to 3–12 inclusive.

## Behavior

- **3:** smallest view window.
- **10:** normal status bar at the bottom of the screen (ZDoom default).
- **11:** full screen with a small overlaid HUD (Zandronum default).
- **12:** full screen with no HUD.

Setting values outside the 3–12 range will cause them to be truncated to the nearest boundary.

The cvar carries flags `CVAR_ARCHIVE`, allowing changes to persist to the config file, and has a `CUSTOM_CVAR` callback in the source that recomputes view size when changed.

## Related cvars

- `hud_althud` — changes what HUD is displayed in full-screen mode (screenblocks 11).
