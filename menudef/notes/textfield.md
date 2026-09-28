# `TextField` (option menu item)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-09); UZDoom 5.1.0-pre @98b16b78f (2026-09-09)
**Provenance:** Zandronum Wiki `MENUDEF` (retrieved 2026-09-09, https://wiki.zandronum.com/w/index.php?title=MENUDEF&oldid=1549) + verified against Zandronum `src/menu/menudef.cpp` and `src/menu/optionmenuitems.h`; UZDoom `wadsrc/static/zscript/engine/ui/menu/optionmenuitems.zs`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Defines a text input field for displaying and editing the value of a string-type CVar.

## Syntax

```text
TextField <label>, <cvar> [, <graycheck>]
```

- **label**: Display name for the field.
- **cvar**: Name of the CVar to bind. Typically a string CVar, but any CVar type may be used; the input will be passed to the CVar as a string, and its type's own conversion logic applies.
- **graycheck** (optional): Name of a CVar whose value gates whether the field is selectable. If specified, the field becomes grayed out and non-interactive if the graycheck CVar evaluates to false (boolean `0`). If omitted or empty, the field is always available unless another condition blocks it (e.g., locked by a feature gate).

## Behavior and limits

Selecting the field and pressing Enter enters text-editing mode, opening a dedicated text-entry submenu. Input length is capped at **127 characters** on Zandronum (the underlying buffer is 128 bytes, minus 1 for the null terminator); UZDoom has no documented fixed limit.

## Engine-family divergence

Both engines implement text entry via a modal submenu (`DTextEnterMenu` on Zandronum, `TextEnterMenu` on UZDoom), with identical MENUDEF keyword and parameter semantics. The functional difference is the input length cap: Zandronum enforces 127 characters maximum, while UZDoom delegates to the text-entry menu's own limit, which is not statically defined in MENUDEF context.
