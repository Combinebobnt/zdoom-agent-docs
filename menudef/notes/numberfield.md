# `NumberField` (option menu item)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-09); UZDoom 5.1.0-pre @98b16b78f (2026-09-09)
**Provenance:** Zandronum Wiki `MENUDEF` (retrieved 2026-09-09, https://wiki.zandronum.com/w/index.php?title=MENUDEF&oldid=1549) + verified against Zandronum `src/menu/menudef.cpp` (parsing) and `src/menu/optionmenuitems.h:1159-1212` (MenuEvent); UZDoom `wadsrc/static/zscript/engine/ui/menu/optionmenuitems.zs` (OptionMenuItemNumberField).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Defines a numeric input field displaying a single numeric value bound to a CVar, with arrow-key navigation and wrapping behavior.

## Syntax

```text
NumberField <label>, <cvar> [, <minimum>, <maximum> [, <step> [, <graycheck>]]]
```

- **label**: Display name for the field.
- **cvar**: Name of the CVar to bind. Typically an integer or float CVar; string CVars are coerced to numeric form on read and written back as numbers.
- **minimum** (optional, default: `0`): Lower bound for valid values.
- **maximum** (optional, default: `100`): Upper bound for valid values.
- **step** (optional, default: `1`): Increment/decrement size per keypress. Must be positive; if `<= 0` is specified, it is silently normalized to `1`.
- **graycheck** (optional): Name of a CVar whose value gates selectability. If specified, the field becomes grayed out and non-interactive if the graycheck CVar evaluates to false (boolean `0`).

## Behavior

- Left arrow decrements the current value by **step**. If the result falls below **minimum**, the value wraps to **maximum**.
- Right arrow or Enter increments the current value by **step**. If the result exceeds **maximum**, the value wraps to **minimum**.
- If **minimum** > **maximum**, they are automatically swapped at construction time.
- No clamping occurs: values always wrap at boundaries, unlike a traditional slider's behavior.

## Engine-family divergence

Both Zandronum and UZDoom implement the same wrapping semantics and auto-normalization of parameters. The behavior difference to note is cosmetic: Zandronum displays the raw numeric value (`GetCVar().Float`); UZDoom formats it with three decimal places (`String.format("%.3f", mCVar.GetFloat())`).
