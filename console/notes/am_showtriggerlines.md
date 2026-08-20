# `am_showtriggerlines`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/am_map.cpp:96` (CVAR declaration); comparison with ZDoom Wiki `CVARs:Automap` (https://zdoom.org/w/index.php?title=CVARs%3AAutomap&oldid=54516).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Controls whether lines with player-triggerable action specials are drawn in a distinct color on the automap. **Type differs by engine-family**: it's an `Int` cvar on UZDoom (matching the wiki's 3-value enum) but a plain `Bool` on Zandronum, which only ever behaves like UZDoom's value `1`.

## UZDoom behavior

`am_showtriggerlines` is an `Int` cvar defaulting to `0` and flagged `CVAR_ARCHIVE` (`src/am_map.cpp:164`). The automap wall-drawing routine gates trigger-line colorization on the cvar being nonzero at all (`src/am_map.cpp:2747`), then a helper (`AM_isTriggerBoundary`, `src/am_map.cpp:2560`) branches on the exact value: when it's `1`, a line only qualifies if it carries a special with door specials (`Door_Open`, `Door_Close`, `Door_CloseWaitOpen`, `Door_Raise`, `Door_Animated`, `Generic_Door`) explicitly excluded; for any other nonzero value, the same qualifying check runs without that door exclusion, so doors get colorized too. In practice this reproduces the wiki's 3-value enum exactly:
- **0**: disabled — trigger lines drawn in their normal wall color.
- **1**: trigger lines colorized with `am_specialwallcolor`, excluding doors.
- **2** (or any other nonzero value): trigger lines colorized including doors.

## Zandronum behavior

In Zandronum, this is a simple **boolean (true/false) toggle**:
- **false (0)**: Option is disabled. Trigger lines are drawn in their normal color.
- **true (1)**: Trigger lines are colorized with `am_specialwallcolor` (for non-door action specials only).

The qualifying check (`src/am_map.cpp:2351`) excludes the same door specials UZDoom's value-`1` path does, and additionally requires the line's `activation` flags include `SPAC_PlayerActivate` — a filter UZDoom's version doesn't have (UZDoom instead requires `FLineSpecial::max_args >= 0`, i.e. that the special has been registered as having a real argument count).

## Engine-family divergence: value type and door-inclusion behavior

Zandronum only implements the boolean equivalent of UZDoom's value `1` (colorize triggers, always excluding doors). It has no way to reach UZDoom's value-`2` behavior (colorize triggers *including* doors) — there is no third state to set. A script or config file written against UZDoom-family semantics that relies on `am_showtriggerlines 2` will silently behave the same as `am_showtriggerlines 1` on Zandronum, since Zandronum's `Bool` cvar type clamps any nonzero value to `true`.

## Persistence

Marked `CVAR_ARCHIVE` on both engines, so this setting persists to the config file.

## Related cvars

- **`am_specialwallcolor`** — the color used to draw trigger lines when this option is enabled. Same `Color` type, same default (`0xffffff`), same `CVAR_ARCHIVE` flag on both engines.
- **`am_cheat`** — trigger-line colorization (like all non-secret wall coloring in the wall-drawing pass) is only evaluated for a line once it's visible on the automap at all: either `am_cheat != 0`, or the line has already been walked near and revealed in normal play (`ML_MAPPED`). This gate is identical on both engines (Zandronum `src/am_map.cpp:2273`, UZDoom `src/am_map.cpp:2684`). `am_textured` is unrelated — it drives a separate textured-subsector overlay pass that runs independently of the trigger-line-coloring wall pass this cvar controls, on both engines.
