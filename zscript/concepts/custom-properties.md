# Custom properties

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `ZScript custom properties` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_custom_properties&oldid=54696) + verified against the UZDoom source's `src/common/scripting/frontend/zcc-parse.lemon` and `wadsrc/static/zscript/actors/` property definitions; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found. This pass also traced the array-field restriction to its exact compile-time error site and confirmed the `Default`-block value syntax has no parenthesized form (see inline citations below).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

A ZScript custom property allows you to initialize multiple actor fields in a single `Default` block declaration, mapping a custom property name to one or more underlying fields. This eliminates repetitive boilerplate when the same group of variables needs initialization across a class hierarchy.

## Declaring a custom property

Inside a class body, declare a property with the `property` keyword:

```zscript
class Widget : Inventory
{
	meta int LowCharge;
	meta String LowChargeMessage;
	
	property ChargeInfo: LowCharge, LowChargeMessage;
	
	// ...
}
```

The `property` keyword is followed by the property's name, a colon, and a comma-separated list of the variable names it maps to. The mapped variables can be instance fields (declared with `int`, `String`, etc.) or metadata fields (declared with `meta` — a prefix that marks fields as class-level configuration rather than per-instance state).

**Restrictions:** Fields in a property list cannot be arrays — they must be single-value types (int, double, String, Name, color, etc.). This isn't rejected at property-declaration time (the grammar and the class-body pass that builds the property's field list accept any field regardless of type); the check happens later, when a `Default` block actually assigns a value to the property. The per-field dispatch that applies default values (`ZCCDoomCompiler::DispatchScriptProperty` in `src/scripting/zscript/zcc_compile_doom.cpp`) has explicit handling for bool/int/float/String/Name/Sound/color/vector/class-pointer/function-pointer field types; any field type without a matching branch — including arrays — falls through to a final `else` that reports `"unhandled property type %s"` as a compile error.

## Using a custom property in a `Default` block

Inside a `Default` block, reference the property by class name and property name, followed by the values in the same order as the property declaration:

```zscript
class SmallWidget : Widget
{
	Default
	{
		Inventory.Amount 10;
		Widget.ChargeInfo 4, "$WIDGET_LOWCHARGE";  // Maps to LowCharge, LowChargeMessage
	}
}
```

The syntax is `<BaseClassName>.<PropertyName> <value1>, <value2>, ...;` — the property name and the value list are separated by whitespace (no operator or punctuation between them), and multiple values within the list are comma-separated. The grammar rule for this (`property_statement` in `zcc-parse.lemon`) is exactly `dottable_id expr_list SEMICOLON` (or `dottable_id SEMICOLON` with no values) — there is no alternate form that wraps the value list in parentheses. For the class that defines the property itself, `self` can be used instead of the class name. Inheriting classes must always use the base class name, even when overriding defaults.

## The `prefix` modifier (internal classes only)

For classes internal to the ZScript standard library, a short prefix can be defined to shorten property references in `Default` blocks. The syntax is `property prefix: <ShortName>;` declared in the class body; every subsequent property in that class is then reachable in a `Default` block as `<ShortName>.<PropertyName>` in addition to `<ClassName>.<PropertyName>`. The engine's own `PlayerPawn` class (`wadsrc/static/zscript/actors/player/player.zs`) uses this to declare `property prefix: Player;`, which is why player-related `Default` block entries elsewhere in the engine are written as `Player.AttackZOffset 8;` rather than `PlayerPawn.AttackZOffset 8;`.

This feature is **limited to internal ZScript library classes** (those in `wadsrc/static/zscript/`) and cannot be used in user code. Concretely, the compiler only honors a `property prefix:` declaration as a prefix when the class body's lump is loaded from the engine's own base resource file (container index 0); the same declaration written in a mod's own `.zs` file instead falls through to the ordinary property-building path, which tries to resolve the prefix's target name (e.g. `Player`) as a field of the class and reports a compile error (`Variable Player not found in ...`) unless a field with that exact name happens to exist.

## Accessing default values at runtime

Inside a method or function, you can read the class's default (unmodified-by-instance) field value using the `Default` keyword:

```zscript
int speed = Default.Speed;
String message = Default.LowChargeMessage;
```

Note that the `Default` accessor uses the *field* name, not the property name. If a property maps `ChargeInfo` to `LowCharge, LowChargeMessage`, you still access them as `Default.LowCharge` and `Default.LowChargeMessage`, not via the property name.

## Multiple inheriting classes

When multiple classes inherit from a base that defines a custom property, each can override the property's default values independently:

```zscript
class QuizItem : Inventory
{
	int QuizItemNumber;
	String QuizFailMessage;
	
	property ItemNumber: QuizItemNumber;
	property FailMessage: QuizFailMessage;
	
	// ...
}

class SpecificQuizItem1 : QuizItem
{
	Default
	{
		QuizItem.ItemNumber 5;
		QuizItem.FailMessage "You can't use that yet.";
	}
}

class SpecificQuizItem2 : QuizItem
{
	Default
	{
		QuizItem.ItemNumber 10;
		QuizItem.FailMessage "Wrong combination.";
	}
}
```

Each inheriting class still uses the base class name (`QuizItem.ItemNumber`, not `SpecificQuizItem1.ItemNumber`) in its own `Default` block.

## Notes on scope and type checking

- Custom properties are **class-local scope** — a property defined in one class is not visible or callable from another, and inheriting classes cannot redefine them.
- The property name and the mapped field names occupy separate symbol-table spaces — a property named `Speed` mapping to a field also named `Speed` does not create a collision; both can coexist in the same class.
- Type checking is strict: if a property maps to an `int` field, the corresponding value in the `Default` block must be an `int` or coercible to one.

## See also

- [DECORATE to ZScript migration: actor-definition differences](decorate-to-zscript-differences.md) — discusses strict property-type quotation rules when migrating from DECORATE.
- [ZScript load order and compile sequence](zscript-load-and-compile-order.md) — ZScript compile-phase semantics.
