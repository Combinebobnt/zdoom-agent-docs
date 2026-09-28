# `transsouls` (cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `CVARs:Display` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3ADisplay&oldid=54715) + verified against Zandronum source's `src/g_doom/a_lostsoul.cpp` and `wadsrc/static/actors/doom/lostsoul.txt:23`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Controls the alpha transparency level for actors drawn with the `SoulTrans` render style. On Zandronum this includes the stock Lost Soul; on UZDoom no stock actor uses the style (see below).

## Default and clamping

Default is 0.75. The cvar enforces strict bounds: values are clamped to the range [0.25, 1.0]:

- Values below 0.25 are forced to 0.25 (minimum visibility).
- Values above 1.0 are forced to 1.0 (full opacity).

The clamping is enforced in the `CUSTOM_CVAR` callback when the value is changed.

## Scope and persistence

The cvar carries the `CVAR_ARCHIVE` flag, so changes persist to the config file.

## Interaction with render styles

Only affects actors whose render style is `SoulTrans` (set by DECORATE `RenderStyle`, UDMF `renderstyle` or DEHACKED). For those actors the cvar's value replaces the actor's own alpha.

On Zandronum, the stock Doom `LostSoul` is the only built-in actor with this style (`wadsrc/static/actors/doom/lostsoul.txt:23`), and the Display options menu exposes the cvar as "Lost Soul translucency". Other actors use `Normal` or another style unless a mod gives them `SoulTrans`.

On UZDoom, no stock actor uses `SoulTrans`: Lost Souls are drawn opaque by default, so the cvar only matters for actors a mod or DEHACKED patch gives this style.
