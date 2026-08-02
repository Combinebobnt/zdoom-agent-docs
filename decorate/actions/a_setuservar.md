# `void A_SetUserVar(string name, int value)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_SetUserVar` (retrieved 2026-07-31, oldid=46793) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5149-5168` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetUserVar)`).
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:5149` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetUserVar)`).

Sets a user variable on the calling actor to an integer value. User variables are a feature for storing actor-specific data that the engine does not use internally — they exist solely for modders' custom data storage.

## Parameters

- **`name`** — the name of the user variable to set. The variable must have been declared with `var int <name>` in the actor definition and its name must begin with the `user_` prefix. Required.
- **`value`** — the integer value to set the variable to. Required.

## Behavior and validation

When called, `A_SetUserVar` looks up the named variable in the calling actor's class symbol table. If the variable is not found, is not marked as a user variable, or is not of type `int` (e.g., a float or array user variable), the function prints an error message to the console and returns without making any change:

```
<name> is not a user variable in class <classname>
```

If the variable exists and is valid, the function updates its value at the actor's memory address offset stored in the symbol table.

## Weapon and CustomInventory caveats

- **Weapons with user variables** must have those variables defined on the player actor itself (e.g., `PlayerPawn` or a player class inheriting from it), not on the weapon actor. User variables defined only on the weapon will not be accessible or modifiable from weapon state code.
- **CustomInventory items modifying monster variables** can update a monster actor's user variables, but only after the CustomInventory item has legitimately entered its `Use` state (via the engine's internal triggering, not via `Goto` or other state jumps). Before that point, modifications only affect the CustomInventory actor's own variables. If an inventory item needs to modify itself once picked up, do so in the `Pickup` state rather than waiting for `Use`.

## See also

- `A_SetUserArray` — sets an integer array user variable at a specified array index.
- `GetUserVariable` — retrieves the value of a user variable.
