# Named arguments

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "ZScript named arguments" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_named_arguments&oldid=54697) + verified against UZDoom engine source `src/common/scripting/backend/codegen.cpp:9836-9943`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found (gate still 4.13, enforcement logic unchanged, the flag's misspelled identifier not fixed upstream). The block shifted -12 lines since the last pass (the declaration sat at 9848 at commit 515ea869f4); the prior citation's `9935` endpoint also stopped one branch short of the last gated check, hence 9943.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ZScript supports named arguments for function and method calls, allowing callers to use argument names to clarify intent and to conditionally skip optional parameters. The feature's behavior is version-gated: pre-4.13.0 and 4.13.0+ have significantly different constraints.

## Basic syntax

To pass an argument by name, use the syntax `name: value`:

```zscript
A_SpawnItemEx('Rocket', flags: SXF_NOCHECKPOSITION);
```

## Pre-4.13.0: Strict ordering with required-parameter restrictions

In versions of ZScript before GZDoom 4.13.0, named arguments have severe limitations:

- **Required parameters cannot be named at all.** If a parameter is required (has no default value), you must pass it positionally, before any named arguments.
- **Named arguments must follow definition order.** If a function is declared as `void Foo(int a, int b = 10, int c = 20)`, you cannot pass `c:` before `b:`. The parameter ordering constraint exists to avoid ambiguity during parsing.

Example (Pre-4.13.0):

```zscript
// INVALID - required parameter 'a' cannot be named
Foo(a: 5, b: 15);

// INVALID - named arg 'c' comes before 'b' in definition
Foo(5, c: 30, b: 15);

// VALID - 'a' is passed positionally, named args in definition order
Foo(5, b: 15, c: 30);
```

## 4.13.0 onward: Arbitrary ordering and required-parameter naming

As of GZDoom 4.13.0, the named-argument restrictions were relaxed:

- **Required parameters may now be named.** You can use the parameter name for a required argument, provided all required arguments are still provided (either positionally or by name).
- **Named arguments can be in any order.** The constraint requiring definition-order sequencing was removed, allowing much more flexible function call signatures.

To use these relaxed rules, the ZScript version must be explicitly set to 4.13.0 or later in the root ZScript file:

```zscript
version "4.13.0"
```

Example (4.13.0+):

```zscript
// All of these are now VALID:
A_SpawnItemEx(missile: 'Rocket', flags: SXF_NOCHECKPOSITION, zofs: 32);
A_SpawnItemEx(flags: SXF_NOCHECKPOSITION, missile: 'Rocket');
A_SpawnItemEx('Rocket', zofs: 32, flags: SXF_NOCHECKPOSITION);
```

The implementation in the UZDoom source (`src/common/scripting/backend/codegen.cpp`) gates this behavior on `ctx.Version >= MakeVersion(4, 13)`, stored in a boolean flag (still misspelled "arugments" in the identifier as of UZDoom 5.0.0-pre), controlling whether the parser enforces the ordering and required-parameter restrictions.

## Varargs and function pointers

Named arguments are not supported for:

- Function pointer calls
- Arguments in the varargs portion of a variadic function's parameter list

## See also

- [DECORATE to ZScript migration: actor-definition differences](decorate-to-zscript-differences.md) — includes a section on named arguments from the pre-4.13.0 perspective
- [ZScript load order and compile sequence](zscript-load-and-compile-order.md) — explains the version directive's role in the compile pipeline
