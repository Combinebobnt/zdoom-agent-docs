# ZScript menus

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `ZScript_menus` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_menus&oldid=55217) + verified against
the UZDoom source's `wadsrc/static/zscript/engine/ui/menu/`; re-verified 2026-08-03 against
UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found in the
claims this doc makes (base `OptionMenuItem`/`ListMenuItem` constructor signatures, the
`Menu`/`ListMenu`/`OptionMenu`/`GenericMenu` hierarchy, `ui`-scope rules, and the
`Menu.SetMenu()` sole-`clearscope`-member status all still hold), despite a large internal
rework of the slider item classes in `optionmenuitems.zs` in this pull (see note below); a
pre-existing doc inaccuracy was also corrected in this pass (the `OptionMenuItemValueScroll`
example class does not exist in the UZDoom stdlib at either commit — replaced with
`OptionMenuItemSlider`, which does).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Menu support was exported to ZScript as of GZDoom/UZDoom 2.4, allowing modders to create customizable menus. The menu system is one of the most complex in ZScript; understanding scope semantics (see below) is essential before working with menus.

## Scope semantics

Every menu class and menu-related function operates in **`ui` scope**, with one significant exception: `Menu.SetMenu()` is marked `clearscope`, allowing it to access actor-state methods that are unavailable elsewhere in the menu tree. The `ui` scope restriction means that most approved functions available in menu code are those explicitly marked `clearscope` in actor definitions — for example, `Actor.CountInv()` (defined in the UZDoom source's `wadsrc/static/zscript/actors/inventory_util.zs`) is marked `clearscope` so it can be called from menu code.

## Menu base classes

All menus inherit from the `Menu` base class (defined in `wadsrc/static/zscript/engine/ui/menu/menu.zs`). Several built-in subclasses exist:

- **`Menu`** — the root superclass for all menus.
- **`ListMenu`** — used for the main menu and similar list-driven interfaces. Comes with pre-built functionality for list navigation and selection.
- **`OptionMenu`** — used for options/settings menus. Includes handling for toggles, sliders, and value lists with extensive built-in rendering.
- **`GenericMenu`** — a blank template for fully custom menu implementations. Inherits from `Menu` without adding or modifying any initialization logic beyond calling `Super.Init()`.

When creating a completely custom menu from scratch, inherit from `GenericMenu` rather than `Menu` directly.

## Menu items

Menu items are objects displayed on screen within a menu, whether interactive or static. All items inherit from `MenuItemBase` (defined in `wadsrc/static/zscript/engine/ui/menu/menuitembase.zs`).

Two primary item base classes are provided:

- **`OptionMenuItem`** — base class for items used in `OptionMenu`. The init method (in `wadsrc/static/zscript/engine/ui/menu/optionmenuitems.zs`) takes a label string, command name, centered flag, and optional gray-check parameters (`CVar`, value, mode). That `Init()` is `protected`, so only subclasses can call it; inherit to create specific option types.
- **`ListMenuItem`** — base class for items used in `ListMenu`. The base class provides helper methods for drawing text and textures, but does not itself define an init signature; subclasses define their own initialization needs.

Each menu type has its own set of specialized item subclasses (e.g. `OptionMenuItemSlider` for slider-style options, `ListMenuItemStaticPatch` for static sprite/patch display) that are part of the stdlib. See the UZDoom/GZDoom stdlib documentation for a complete listing.

## Wiki/engine divergence

The ZDoom Wiki page describes `OptionMenuItem` and `ListMenuItem` parameter lists that differ from the UZDoom source: the wiki lists a simpler parameter set than the full signatures in the stdlib. When inheriting from either class in a custom menu, consult the actual stdlib source (`optionmenuitems.zs` for `OptionMenuItem`, `listmenuitems.zs` for `ListMenuItem`) rather than relying on the wiki page's examples.

## Note on the 2026 `optionmenuitems.zs` rework

As of the 2026-08-01 UZDoom snapshot, `optionmenuitems.zs` underwent a large internal rework of the slider item classes (`OptionMenuSliderBase` and its subclasses `OptionMenuItemSlider`/`OptionMenuItemScaleSlider`): sliders gained the ability to accept direct numeric text entry (via `TextEnterMenu`), an accelerating hold-to-drag step size, a "reset to CVar default" action bound to a new clear/reset menu key, and optional display-scale/value-format parameters for the slider's `Init()`. Several other option item classes (`OptionMenuItemColorPicker`, `OptionMenuItemOption`) also picked up a reset-to-default action on that same key. None of this changed the base `OptionMenuItem`/`ListMenuItem` constructor signatures, the `Menu`/`ListMenu`/`OptionMenu`/`GenericMenu` class hierarchy, the `ui`-scope rules, or the `Menu.SetMenu()` sole-`clearscope`-member status documented above — verified directly against the diff and against current HEAD (commit fbad53bff5). Treat any slider-specific parameter list you find in older third-party examples as potentially stale; check the current stdlib source for the exact `Init()` signature of the specific slider subclass you're using.
