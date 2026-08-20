# `void A_SetUserArray(name varname, int index, int value)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_SetUserArray` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SetUserArray&oldid=42563) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5168-5194` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetUserArray)`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:5168` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetUserArray)`).

Sets an element of an integer array user variable on the calling actor to a specified value. Like `A_SetUserVar`, this function is part of the mechanism for storing actor-specific custom data via user variables.

## Parameters

- **`varname`** — the name of the user array variable to modify. The variable must have been declared with `var int <name>[size]` in the actor definition and its name must begin with the `user_` prefix. Required.
- **`index`** — the zero-based array index to set. Must be within the bounds of the declared array `[0, size)`. Required.
- **`value`** — the integer value to store at the specified array index. Required.

## Behavior and validation

When called, `A_SetUserArray` performs two validation checks:

**1. Variable lookup and type check** — the function looks up `varname` in the calling actor's class symbol table. If the variable is not found, is not marked as a user variable, or is not of type `int[]` (e.g., a scalar integer, float array, or non-user field), the function prints an error message to the console and returns without making any change:

```text
<varname> is not a user array in class <classname>
```

**2. Bounds check** — if the variable exists and is valid, the function checks whether `index` falls within the array bounds `[0, size)`. If the index is negative or >= the declared array size, the function prints an error message and returns:

```text
<index> is out of bounds in array <varname> in class <classname>
```

If both validations pass, the function updates the array element at the specified index.

## Weapon and CustomInventory caveats

- **Weapons with user array variables** must have those variables defined on the player actor itself (e.g., `PlayerPawn` or a player class inheriting from it), not on the weapon actor. User arrays defined only on the weapon will not be accessible or modifiable from weapon state code.
- **CustomInventory items modifying actor arrays** can update an actor's user arrays, but only after the CustomInventory item has legitimately entered its `Use` state. Before that point, modifications only affect the CustomInventory actor's own variables (if any). If an inventory item needs to modify itself once picked up, do so in the `Pickup` state rather than waiting for `Use`.

## See also

- `A_SetUserVar` — sets a scalar integer user variable (not an array).
- `A_SetUserVarFloat` — **UZDoom/GZDoom-family only** (does not exist in Zandronum); sets a floating-point user variable.
- `A_SetUserArrayFloat` — **UZDoom/GZDoom-family only** (does not exist in Zandronum); sets an element of a floating-point user array.
- `../concepts/user-variables.md` — declaration syntax, type restrictions, and the Weapon/CustomInventory calling convention for both scalar and array user variables.
- `../../acs/functions/getuservariable.md` — ACS-side equivalent functions (`SetUserArray`/`GetUserArray`) and the shared `bUserVar` validation gate.
