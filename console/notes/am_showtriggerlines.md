# `am_showtriggerlines`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/am_map.cpp:96` (CVAR declaration); comparison with ZDoom Wiki `CVARs:Automap` (oldid=54516).

Controls whether lines with player-triggerable action specials are drawn in a distinct color on the automap. **Type is Boolean in Zandronum** (not the 3-value enum described in the wiki).

## Zandronum behavior

In Zandronum, this is a simple **boolean (true/false) toggle**:
- **false (0)**: Option is disabled. Trigger lines are drawn in their normal color.
- **true (1)**: Trigger lines are colorized with `am_specialwallcolor` (for non-door action specials only).

## Wiki divergence

The ZDoom Wiki describes this as a 3-value enum:
- 0: Option disabled
- 1: Triggerable lines colorized except doors
- 2: Triggerable lines colorized including doors

**This 3-value behavior does not exist in Zandronum.** Zandronum does not distinguish between door and non-door triggers — the boolean implementation always excludes doors from colorization. If you need ZDoom-family behavior with door colorization, this cvar will not provide it in Zandronum.

## Persistence

Marked `CVAR_ARCHIVE`, so this setting persists to the config file.

## Related cvars

- **`am_specialwallcolor`** — the color used to draw trigger lines when this option is enabled
- **`am_cheat`** — must be >= 1 or `am_textured` must be active for trigger lines to be visible at all
