# DamageType block

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28)
**Provenance:** ZDoom Wiki `MAPINFO/Damage type definition` (retrieved 2026-09-28, https://zdoom.org/w/index.php?title=MAPINFO/Damage_type_definition&oldid=52397) + verified against UZDoom source (`src/gamedata/g_mapinfo.cpp:2603-2613`, `src/gamedata/info.cpp:868-967`, `src/gamedata/info.h:209-235`, `src/playsim/p_interaction.cpp:211-269`, `src/scripting/decorate/thingdef_parse.cpp:1207-1245`) and Zandronum source (`src/thingdef/thingdef_parse.cpp:1180-1217,1303-1306`, `src/g_mapinfo.cpp:1999`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

A damage type definition block in MAPINFO declares custom damage types with associated default properties. This feature is used in conjunction with actor-level `DamageFactor` properties to control how actors respond to different types of damage and to customize player death messages.

## Syntax

```mapinfo
DamageType <Name>
{
    Factor = <value>
    ReplaceFactor
    NoArmor
    Obituary = "<string>"
}
```

The block begins with the `DamageType` keyword followed by the damage type name, then contains zero or more property declarations enclosed in braces.

### Parsing notes

- Property names are case-insensitive (matched with `Compare()` in the source).
- `Factor` and `Obituary` require an `=` sign; `ReplaceFactor` and `NoArmor` are bare flags.
- An unknown property inside the block causes a fatal `ScriptError` ("Unexpected data (...) in damagetype definition.").
- `DamageType` in an old-format MAPINFO lump causes a fatal error: "damagetype definitions not supported with old MAPINFO syntax." In an indeterminate-format lump, encountering `DamageType` promotes the lump to new format.
- Declaring a damage type with the same name as a previously-defined type resets all its properties to the defaults; the new declaration's values override everything (UZDoom source `src/gamedata/info.cpp:868-871`).

## Properties

- **`Factor = <value>`** — defines the default damage multiplication factor for this damage type when an actor has no specific `DamageFactor` defined for this type. The value is a floating-point number; default is `1.0`. When `Factor` is set to `0`, `ReplaceFactor` is automatically enabled. If an actor has a `DamageFactor` defined for this specific type, that actor's factor is returned immediately and the damage type definition's `Factor` is not consulted. If the actor has no type-specific factor but has a "Normal" (untyped) factor defined, that is multiplied by this `Factor` (see "Damage factor application" below).

- **`ReplaceFactor`** — a flag that, when present, causes damage calculations to skip the "Normal" (untyped) fallback damage factor. Without this flag, if an actor defines an untyped damage factor, both it and the damage type definition's `Factor` are applied as multiplicative modifiers. With this flag, only the definition's `Factor` is applied (or the actor's type-specific factor if defined). This flag is automatically set if `Factor` is `0`.

- **`NoArmor`** — a flag that, when present, causes damage of this type to always bypass armor, regardless of the actor's armor or armor absorption settings.

- **`Obituary = "<string>"`** — defines a default death message for this damage type (MAPINFO form only; neither engine's DECORATE `damagetype` parser accepts it). The string is displayed when a player dies from this damage type and the attacker is unknown (no actor caused the damage). The string supports standard obituary substitutions such as `%o` (the victim's name) and `%k` (the killer's name; with no attacker the engine substitutes the victim, so `%k` also prints the victim's name here). If no custom obituary is defined or if an attacker exists, the engine falls back to built-in damage-type strings (e.g., `$OB_LAVA` for fire damage, `$OB_WATER` for drowning).

## Damage factor application

The damage calculation follows this precedence order:

1. If the actor has a specific `DamageFactor` defined for this damage type, that factor is applied and the calculation ends.
2. If the actor has a "Normal" (untyped) damage factor defined:
   - If `ReplaceFactor` is set on the damage type definition, apply only this damage type's `Factor` (ignore the Normal factor).
   - If `ReplaceFactor` is not set, multiply both the Normal factor and this damage type's `Factor` together.
3. If the actor has no type-specific or Normal factor defined, apply this damage type's `Factor` alone.
4. If no damage type definition exists for the damage type, apply the actor's Normal factor if defined, otherwise use `1.0`.

The final result is truncated to an integer (via simple multiplication, not rounded).

## Examples

### Damage type with zero default factor

```mapinfo
DamageType SpecialDamage
{
    Factor = 0
    // ReplaceFactor is automatically set since Factor = 0
}
```

In this example, actors take no damage from `SpecialDamage` unless they explicitly define a `DamageFactor` for it. An actor can override this by declaring `DamageFactor 'SpecialDamage', 1.0;` in its default properties.

### Damage type that ignores armor and uses a custom obituary

```mapinfo
DamageType GreenGoo
{
    Obituary = "%o got gooed."
    NoArmor
}
```

Damage from `GreenGoo` always bypasses armor, and players killed by it see the custom message "%o got gooed." (where `%o` is replaced with the victim's name).

### Redefining a predefined damage type

```mapinfo
DamageType Drowning
{
    NoArmor
    ReplaceFactor
}
```

This redefines the "Drowning" damage type (a predefined type) to bypass armor and to ignore the Normal fallback damage factor. Declaring a damage type with the same name as a predefined one resets all its properties to the values you specify (or to defaults if not specified).

## Engine-family divergence

### MAPINFO DamageType block: UZDoom-only

Zandronum does not support the `DamageType` block in MAPINFO lumps. Attempting to use it results in a fatal script error: "damagetype: Unknown top level keyword" (Zandronum source `src/g_mapinfo.cpp:1999`). Moving the block to ZMAPINFO does not hide it from Zandronum, as both lump types use identical parsing.

### DECORATE DamageType block: Both engines, with differences

Both UZDoom and Zandronum accept a top-level `damagetype` block in DECORATE lumps (UZDoom source `src/scripting/decorate/thingdef_parse.cpp:1207-1245`, Zandronum source `src/thingdef/thingdef_parse.cpp:1180-1217,1303-1306`). The two DECORATE parsers are the same shape, and both differ from the MAPINFO form:

- Only `Factor`, `ReplaceFactor` and `NoArmor` are accepted, on **both** engines. `Obituary` is an unknown key in either DECORATE parser and is a fatal "Unexpected data" error.
- `Factor` takes its value with **no `=`** (`Factor 0.5`), whereas the MAPINFO form requires `Factor = 0.5`.
- Zandronum stores the factor as fixed-point, so very small factors quantize; UZDoom stores a double.

```decorate
DamageType GreenGoo
{
    Factor 0.5
    NoArmor
}
```

For modders targeting both engines, the DECORATE form is the portable one, at the cost of `Obituary`. A MAPINFO/ZMAPINFO `DamageType` block can't be hidden from Zandronum: it reads both lump names with the same parser, and an unknown top-level keyword is fatal there.

## Wiki/engine divergence

**Factor = 0 automatically enables ReplaceFactor:** The wiki does not mention that setting `Factor = 0` automatically enables `ReplaceFactor`. This is an implementation detail confirmed in the UZDoom source (src/gamedata/info.cpp:990) and Zandronum's DECORATE parser (src/thingdef/thingdef_parse.cpp:1198): when the parser reads `Factor = 0`, it sets `ReplaceFactor` to true immediately, making the two flags redundant in practice when `Factor` is zero.

**Obituary only used when attacker is unknown:** The wiki's description of the `Obituary` property ("used if the source of damage is unknown or does not define an obituary of its own") is partially simplified. More precisely, the obituary is consulted only when `attacker == nullptr` (no actor caused the damage). When an attacker exists, even if it doesn't define a custom obituary, the engine first searches for actor-specific and weapon-specific strings before falling back to built-in damage-type messages. The damage-type obituary never takes precedence over an attacker's own obituary logic.

## Known gaps

The following claims were not independently re-verified and are flagged for future review:

- How the `DamageFactor` actor property parser maps `'Normal'` to the untyped damage slot, and whether the lookup actually uses `NAME_None` or a literal `Normal` name.
- Whether `NoArmor` applies uniformly across both `BasicArmor` and `HexenArmor` classes in armor absorption calculations, and the full armor-bypass logic in the playsim.
- The full implementation of `%o` and `%k` substitution in obituary strings (confirmed present at UZDoom source `src/playsim/p_interaction.cpp:275` but not fully traced).
