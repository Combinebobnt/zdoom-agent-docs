# DECORATE to ZScript migration: actor-definition differences

**Tier:** A
**Engine:** UZDoom 4.15pre / GZDoom-family (does not exist in Zandronum)
**Provenance:** ZDoom Wiki "Coding language differences" (retrieved 2026-07-31, oldid=52746) + verified against UZDoom engine source

When migrating actor definitions from DECORATE to ZScript, several syntax constraints tighten or change entirely. This documents the key differences that affect how an actor is declared in the `Default { }` block or via properties/flags.

## Actor instantiation: Spawn, not new()

In ZScript, the `new()` operator cannot instantiate classes descended from `Actor`. Actor creation requires the `Spawn` function instead, which is defined as a native static method on Actor:

```zscript
native static Actor Spawn(class<Actor> type, vector3 pos = (0,0,0), int replace = NO_REPLACE);
```

Attempting `new('SomeActor')` will fail to compile, even though `new` works fine for non-Actor classes.

## Properties requiring quotation: name, string, and class-name types

In DECORATE, many actor properties accept bare identifiers. In ZScript, properties with `name`, `string`, or class-name types require their values to be quoted.

### DECORATE example (accepts bare identifier):
```
DamageType Fire
```

### ZScript equivalent (requires quotes):
```zscript
DamageType "Fire";    // or single quotes: DamageType 'Fire';
```

The difference stems from ZScript's stricter type system: `DamageType` is internally a `name` type, and names must be explicitly quoted to distinguish them from identifiers.

**All actor properties that take a string, name, or class name must be enclosed in quotation marks** in ZScript's `Default { }` block.

## DoomEdNum: MAPINFO, not ZScript

In DECORATE, editor numbers (DoomEdNums) can be specified in the actor definition itself:

```
ACTOR MyThing 1234
{
  ...
}
```

In ZScript, `DoomEdNum` is not a valid actor property at all. Instead, editor numbers must be configured externally in a `MAPINFO` lump's `DoomEdNums` block:

```
DoomEdNums
{
    MyThing = 1234
}
```

## Class naming: no leading digits

ZScript class names cannot begin with a numeral. A class named `12Gauge` is invalid in ZScript. Use an identifier prefix instead, e.g., `ShotgunAmmo_12Gauge` or `Gauge12`.

This is a language-level constraint in the ZScript parser, not merely a convention.

## Multi-return assignments require brackets

ZScript supports functions that return multiple values, a feature borrowed from Lua. When assigning the results to multiple variables, the left-hand side **must** use square brackets:

```zscript
[amt, maxamt] = GetAmount("Clip");
```

Attempting `amt, maxamt = GetAmount("Clip");` without brackets will fail to parse.

## Named arguments: order and placement

ZScript functions support named arguments (also inspired by Lua), but with strict rules:

1. Named arguments must appear **after all required positional arguments**.
2. Named arguments must be passed **in the same order they appear in the function definition**.

For example, if a function is declared as `void SetThing(int a, int b = 10, int c = 20)`, this is valid:

```zscript
SetThing(5, c: 30);            // b uses default, c is named
```

But this is invalid:

```zscript
SetThing(5, b: 15, c: 30);     // b and c are out of definition order
```

Violating the order rule produces a compiler error: "Named argument X comes before current position in argument list."

## See also

- [`zscript-engine-availability.md`](zscript-engine-availability.md) — ZScript exists only in UZDoom/GZDoom-family, not Zandronum.
- [`../classes/`](../classes/) — individual ZScript class documentation.
