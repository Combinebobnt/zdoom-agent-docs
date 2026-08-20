# DECORATE to ZScript migration: syntax and language differences

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "Coding language differences" (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Coding_language_differences&oldid=52746) + verified against UZDoom engine source; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

When migrating from DECORATE to ZScript, several syntax constraints tighten or change entirely, and ZScript adds general-purpose language features DECORATE never had. This documents both: actor-definition-specific differences (how an actor is declared in the `Default { }` block or via properties/flags) and broader language-level additions (access control, `readonly`, `let` type inference, reference semantics).

## Actor instantiation: Spawn, not new()

In ZScript, the `new()` operator cannot be used to instantiate classes descended from `Actor`. Actor creation requires the `Spawn` function instead, which is defined as a native static method on Actor:

```zscript
native static Actor Spawn(class<Actor> type, vector3 pos = (0,0,0), int replace = NO_REPLACE);
```

The Actor-descent check is not a compile-time restriction: `new('SomeActor')` compiles cleanly (the compiler always lowers `new` to a call into a native constructor helper, regardless of whether the class is a compile-time constant) and only fails **at run time**, when that native helper inspects the class's inheritance chain, finds it descends from `Actor`, and aborts script execution with a runtime error directing you to use `Actor.Spawn` instead. In other words, a `new('SomeActor')` call can sit uncaught in an otherwise-clean compile and only surface when that code path actually executes.

## Properties requiring quotation: name, string, and class-name types

In DECORATE, many actor properties accept bare identifiers. In ZScript, properties with `name`, `string`, or class-name types require their values to be quoted.

### DECORATE example (accepts bare identifier):
```text
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

```text
ACTOR MyThing 1234
{
  ...
}
```

In ZScript, `DoomEdNum` is not a valid actor property at all. Instead, editor numbers must be configured externally in a `MAPINFO` lump's `DoomEdNums` block:

```text
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

ZScript functions support named arguments (also inspired by Lua). **Note:** the constraints documented here apply to pre-4.13.0 versions; GZDoom 4.13.0 and later provide significantly relaxed rules. See [named-arguments.md](named-arguments.md) for the full version-specific behavior and the 4.13.0+ changes.

In pre-4.13.0, the rules are strict:

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

## No address-of or dereference operators

C and C++ use `&` for address-of (taking a reference) and `*` for dereferencing. ZScript does not support these unary operators at all. Instead, all complex objects (Actors and other classes) are inherently reference types, passed by reference implicitly. You access members and methods directly without any pointer syntax:

```zscript
Actor thing = ...;
int health = thing.health;      // Direct member access, no ->, no *
thing.Damage(10, ..., ...);     // Method call directly, no pointer notation
```

This is fundamentally different from C++, where you'd write `thing->health` or `(*thing).health` depending on whether `thing` is a pointer or reference.

## The `readonly` qualifier

Class and struct members can be declared `readonly` to prevent modification after initialization:

```zscript
class MyActor : Actor
{
    readonly int MyConstantValue;
}
```

Once set, a `readonly` member cannot be changed, providing a form of data immutability at the language level.

## Access control: public by default

Unlike Java (which requires explicit `public` for public members), ZScript makes everything public by default. Only members explicitly marked `private` or `protected` are restricted:

```zscript
class MyActor : Actor
{
    int publicMember;                // implicitly public
    private int hiddenFromOutside;   // not accessible outside the class
    protected int subclassOnly;      // accessible by subclasses
}
```

This is a key difference from DECORATE, which has no access control at all.

## Variable inference: `let` for auto-typed declarations

ZScript's `let` keyword is equivalent to C++'s `auto` — it infers the variable's type from its initializer:

```zscript
let myVariable = 42;      // inferred as int
let actor = level.SpawnActor(...);  // inferred as the return type
```

This is purely syntactic sugar; `let` and `auto` are equivalent. Unlike C++, where `auto` is primarily a storage class, ZScript's `let` is the standard way to declare locally-scoped variables with inferred types.

## See also

- [`zscript-engine-availability.md`](zscript-engine-availability.md) — ZScript exists only in UZDoom/GZDoom-family, not Zandronum.
- [`../classes/`](../classes/) — individual ZScript class documentation.
