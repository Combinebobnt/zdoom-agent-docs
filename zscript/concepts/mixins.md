# Mixins

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "ZScript mixins" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_mixins&oldid=47180) + verified against UZDoom's ZScript parser and compiler in `src/common/scripting/frontend/zcc-parse.lemon` and `zcc_compile.cpp`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** ZScript language parser/compiler frontend.

ZScript mixins are a code-reuse mechanism similar to D's template mixins. A mixin is a named container of class members — variables, methods, enums, structs, states, properties, flag definitions, and constants — that can be included in multiple classes without duplication.

## Definition and scope

Mixins must be defined at global scope (outside any class or struct), using the `mixin class` keyword:

```zscript
mixin class FancyProperties
{
    int myCounter;
    
    void IncrementCounter()
    {
        myCounter++;
    }
    
    enum MyValues
    {
        VALUE_A,
        VALUE_B,
    };
}
```

A mixin definition is a compile-time construct: the compiler does not create an object or class when the mixin is defined. Instead, when a class uses a mixin via the `mixin` statement (see below), the compiler performs a deep copy of the mixin's body and inserts it at that point in the class member list.

## Usage

A class uses a mixin by declaring a `mixin` statement within its body:

```zscript
class MyActor : Actor
{
    mixin FancyProperties;
    
    // ... other members
}
```

Multiple mixins can be used in a single class:

```zscript
class AnotherActor : Actor
{
    mixin FancyProperties;
    mixin OtherMixin;
}
```

The mixin statement can appear anywhere among the class's members (before or after other declarations); the inserted members appear at the statement's location.

## Restrictions

**Classes only.** Only class definitions can use mixins — structs and other mixin definitions cannot. A mixin's body cannot contain another `mixin` statement (mixins cannot be nested).

**Translation-unit scope.** Mixins can only be used within the same translation unit they are defined in. In practice, a "translation unit" is a single ZSCRIPT lump; a mixin defined in one ZSCRIPT archive file cannot be used in another. However, files included via `#include` within the same ZSCRIPT lump are part of the same translation unit, so an included file can define or use mixins alongside the file that includes it.

**What mixins can contain.** A mixin body can hold variables, methods, enums, structs, states, default blocks, property definitions, flag definitions, static array declarations, and constant definitions. It cannot contain another mixin statement.

## Flag definition gotcha

If a mixin defines a `Flagdef`, the flag's name is namespaced to the *class that uses the mixin*, not to the mixin itself: the compiler deep-copies the mixin's body into the using class before any flag names are registered, so the flag ends up registered exactly as if it had been declared directly in the using class, under the using class's own name.

1. The flag can be used as `+ClassName.FLAGNAME` in the using class's Default block (`ClassName` being the class that wrote the `mixin` statement, not the mixin's own name).
2. The mixin's own Default block (if present) **cannot** set the flag at all — not via the bare `+FLAGNAME` form, and not via a qualified form either, since the mixin body has no way to know which class will eventually use it.

This bare-`+FLAGNAME`-fails behavior isn't actually mixin-specific: ZScript's own flag lookup always requires the qualified `ClassName.FLAGNAME` form for a custom `Flagdef`-declared flag, even when the flag is declared directly in a class's own (non-mixin) body — the unqualified spelling is registered only so the legacy DECORATE property parser can find it, and is deliberately excluded from ZScript's own strict lookup. Mixins just make this easy to trip over, since a flag defined inside a mixin can look like it ought to be locally usable within that same mixin's own Default block, and there it cannot be set by any spelling at all.

Example:

```zscript
mixin class HasAFlag
{
    int flagBits;
    Flagdef SPECIAL: flagBits, 0;
    
    Default
    {
        // WRONG: +SPECIAL won't work here because the flag is namespaced to the class that uses this mixin
        // +SPECIAL
    }
}

class MyMonster : Actor
{
    mixin HasAFlag;
    
    Default
    {
        // CORRECT: use the class name + flag name
        +MyMonster.SPECIAL
    }
}
```

## Engine-scope note

ZScript does not exist in Zandronum and mixins are a UZDoom/GZDoom-family feature only. See `concepts/zscript-engine-availability.md` for details.
