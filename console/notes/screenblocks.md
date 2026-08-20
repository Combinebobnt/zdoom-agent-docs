# `screenblocks` (cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** ZDoom Wiki `CVARs:Display` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3ADisplay&oldid=54715) + verified against Zandronum source's `src/r_utility.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

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

## Engine-family divergence: default value

UZDoom keeps the ZDoom Wiki's default of 10 (a normal status bar). Zandronum's source carries an explicit override, with an inline comment noting the default is intentionally raised to 11, so a stock Zandronum install starts in full-screen-with-overlaid-HUD mode instead of the classic status-bar view. Everything else about the cvar, the 3–12 clamp, the `CVAR_ARCHIVE` flag, the `CUSTOM_CVAR` recompute-on-change behavior, and the meaning of each value in the "Behavior" section above, is identical between the two engines.

## Related cvars

- `hud_althud` — changes what HUD is displayed in full-screen mode (screenblocks 11).
