# `transsouls` (cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `CVARs:Display` (retrieved 2026-08-02, oldid=54715) + verified against Zandronum source's `src/g_doom/a_lostsoul.cpp`.

Controls the alpha transparency level for lost souls and other actors using the `SoulTrans` render style.

## Default and clamping

Default is 0.75. The cvar enforces strict bounds: values are clamped to the range [0.25, 1.0]:

- Values below 0.25 are forced to 0.25 (minimum visibility).
- Values above 1.0 are forced to 1.0 (full opacity).

The clamping is enforced in the `CUSTOM_CVAR` callback when the value is changed.

## Scope and persistence

The cvar carries the `CVAR_ARCHIVE` flag, so changes persist to the config file.

## Interaction with render styles

Only affects actors with `RenderStyle` set to `SoulTrans`. Standard actors and most lost souls in Doom/Doom II use this render style by default, but custom actors can opt out by using a different render style.
