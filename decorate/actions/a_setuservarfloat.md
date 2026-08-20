# `A_SetUserVarFloat(string name, float value)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `A_SetUserVarFloat` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_SetUserVarFloat&oldid=46794) + verified against UZDoom source's `src/playsim/p_actionfunctions.cpp:3042-3062` and Zandronum absence confirmed in `src/thingdef/thingdef_codeptr.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

**Engine-family note:** This action and its array variant `A_SetUserArrayFloat` do not exist in Zandronum. User variables in Zandronum are restricted to `int` type only — the parser in `src/thingdef/thingdef_parse.cpp:361` requires `TK_Int` and rejects float declarations with the message "User variables must be of type int". The integer setter `A_SetUserVar` explicitly type-checks and prints an error message if passed a variable not of `VAL_Int` type. Float user variables are a UZDoom/GZDoom-family feature and Zandronum projects must use `int` variables or alternative storage mechanisms (actor properties, `args[]` array, `special1`/`special2` fields).

Sets a floating-point user variable on the calling actor. The variable name must begin with `user_` and must have been declared in the actor class definition (e.g., `var float user_angle;`).

## Parameters

- **`name`** — The name of the user variable (must begin with `user_`).
- **`value`** — The floating-point value to store.

## Notes

- **Zandronum incompatible** — this feature does not exist in Zandronum; use integer user variables (`A_SetUserVar`) or alternative storage instead.
- User variables declared in weapons will not work unless the variable is defined on the player actor itself, not just the weapon class.
- `CustomInventory` items can modify another actor's variables, but the variable must be declared in both the item and the target actor class. Until the inventory item's `Use` state is entered legitimately (not via state jumps), modifications affect only the item's own variables.

## See also

- `A_SetUserVar` — integer variant; available in Zandronum.
- `A_SetUserArrayFloat` — array variant (also GZDoom-family only).
- `A_SetUserArray` — integer array variant; available in Zandronum.
