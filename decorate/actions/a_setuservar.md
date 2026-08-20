# `void A_SetUserVar(string name, int value)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_SetUserVar` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_SetUserVar&oldid=46793) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5149-5168` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetUserVar)`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:5149` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetUserVar)`).

Sets a user variable on the calling actor to an integer value. User variables are a feature for storing actor-specific data that the engine does not use internally — they exist solely for modders' custom data storage.

## Parameters

- **`name`** — the name of the user variable to set. The variable must have been declared with `var int <name>` in the actor definition and its name must begin with the `user_` prefix. Required.
- **`value`** — the integer value to set the variable to. Required.

## Behavior and validation

When called, `A_SetUserVar` looks up the named variable in the calling actor's class symbol table. If the variable is not found, is not marked as a user variable, or is not of type `int` (e.g., a float or array user variable), the function prints an error message to the console and returns without making any change:

```text
<name> is not a user variable in class <classname>
```

If the variable exists and is valid, the function updates its value at the actor's memory address offset stored in the symbol table.

## Engine-family divergence: variable type check

On the Zandronum engine fork, DECORATE's `var` declaration only ever produces `int`-typed user variables — its parser rejects any other declared type with a `User variables must be of type int` script error — and `A_SetUserVar`'s own lookup independently rejects a match whose type isn't exactly int, so the two checks are redundant in practice.

On the UZDoom engine fork, DECORATE's `var` declaration accepts either `int` or `float` (`user_` prefix still required either way), and `A_SetUserVar`'s lookup only requires the matched class member to be non-native, non-private, non-protected, non-static, and of a scalar type — it does not require the type to be exactly `int`. Calling `A_SetUserVar` against a `float` user variable therefore succeeds on UZDoom instead of failing with the "is not a user variable" error: the integer argument is converted to a double and stored, with no error printed. A caller relying on the "not of type int" failure mode to guard against a misdeclared `float` user variable will not see that failure on UZDoom.

Separately, on UZDoom `A_SetUserVar` is also declared as a `native` function usable from ZScript (`wadsrc/static/zscript/actors/actor.zs`), where it is marked deprecated since version 2.3 in favor of direct field access; calling it from ZScript source (as opposed to DECORATE) emits a compile-time deprecation warning. Zandronum has no ZScript at all, so this has no equivalent there.

## Weapon and CustomInventory caveats

- **Weapons with user variables** must have those variables defined on the player actor itself (e.g., `PlayerPawn` or a player class inheriting from it), not on the weapon actor. User variables defined only on the weapon will not be accessible or modifiable from weapon state code.
- **CustomInventory items modifying monster variables** can update a monster actor's user variables, but only after the CustomInventory item has legitimately entered its `Use` state (via the engine's internal triggering, not via `Goto` or other state jumps). Before that point, modifications only affect the CustomInventory actor's own variables. If an inventory item needs to modify itself once picked up, do so in the `Pickup` state rather than waiting for `Use`.

## See also

- `A_SetUserArray` — sets an integer array user variable at a specified array index.
- `GetUserVariable` — retrieves the value of a user variable.
