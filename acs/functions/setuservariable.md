# SetUserVariable

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes — Zandronum source used is a 3.3-alpha checkout (see ../../shared/AUTHORING.md's "Engine scope" section for the 3.2.1-target-vs-checkout gap).
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Verified against Zandronum source (p_acs.cpp, case ACSF_SetUserVariable) from the ZDoom Wiki page, https://zdoom.org/w/index.php?title=page&oldid=45355.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

**Signature:** `void SetUserVariable(int tid, str name, raw value)` (extension function, index -24)

## Summary

Sets a user variable on one or more actors.

## Parameters

- `tid`: The thing ID(s) to target. If 0, targets the script's activator. If nonzero, the function iterates through all actors with that TID. Same on both engines.
- `name`: The name of the variable to set. **On Zandronum**, must be of the form `user_*` (enforced by the `bUserVar` gate — see "User variable restrictions" below). **On UZDoom, this restriction does not exist** — any non-native scalar field reachable by name in the class symbol table can be targeted, `user_`-prefixed or not. See "Engine-family divergence" below.
- `value`: The value to assign. Passed as a fixed-point ACS integer. **On Zandronum**, always stored as a raw 32-bit integer (the only supported field type). **On UZDoom**, the stored representation depends on the target field's actual type — see "Engine-family divergence" below.

## Behavior

The function attempts to set the named field on all matching actors. It returns an actor count as follows:
- If `tid` is 0: returns 1 (whether or not the activator exists; see Quirks below).
- If `tid` is nonzero: returns the count of actors it actually iterated through (0 if no actors match that TID).

This count logic is identical on both engines — confirmed by reading `ACSF_SetUserVariable`'s case handler in each (Zandronum `src/p_acs.cpp:6120-6146`; UZDoom `src/playsim/p_acs.cpp:5645-5672`), which have the same shape.

In practice, the return value is inaccessible from ACS/BCS code — the function is declared as `void` in `zcommon.bcs` so the compiler will not allow assigning its return value to a variable, even though the engine internally computes it. This is a compiler-side (`zt-bcc`) fact and applies regardless of engine.

### User variable restrictions (Zandronum)

- Only `int`-typed user variables can be set. Declarations of `double` or `bool` user variables in DECORATE are rejected at parse time (Zandronum's DECORATE parser enforces `user_*` variables to be `int` only, unlike the ZDoom wiki's claim of supporting `double` and `bool`).
- Native variables (declared with the `native` keyword in DECORATE) cannot be set.
- Both restrictions stem from the same gate: the static `SetUserVariable` helper (`src/p_acs.cpp:5593-5621`) requires the resolved symbol to carry the `bUserVar` flag, which DECORATE's `ParseUserVariable` only ever sets on `int`-typed, `var`-declared, non-native fields. See "Engine-family divergence" below — UZDoom does not have this gate at all, so neither restriction holds there in the same form.

### Failure behavior

If the named variable doesn't exist, isn't accessible to this function (see the engine-specific gates above/below), or the actor instance is NULL, the function silently does nothing — there is no error return or indication of failure. True on both engines, though the specific gate that produces the no-op differs (Zandronum's `bUserVar` check vs. UZDoom's `GetVarAddrType` field-type/native check).

## Engine-family divergence: UZDoom drops the `bUserVar` gate and broadens both name and type support

This mirrors the divergence already documented for the getter — see `getuservariable.md`'s "Engine-family divergence" section for the full mechanism trace; this section covers the write-side specifics.

UZDoom's `SetUserVariable` is built on the same shared helper as `GetUserVariable`, `GetVarAddrType` (`src/playsim/p_acs.cpp:4898-4936`), rather than a `bUserVar`-gated lookup. Consequences for the setter specifically:

- **No `user_` name restriction.** Any field resolvable by name via the class symbol table (parent classes included) is a candidate — not just fields declared with DECORATE's `var` keyword.
- **Native fields are still rejected, but by an explicit check, not by never having a flag set.** `GetVarAddrType` returns `false` for a write (`readonly=false`) when `var->Flags & VARF_Native` is set (`src/playsim/p_acs.cpp:4902`). Net effect matches Zandronum (native fields can't be set), but the mechanism is a dedicated write-only exclusion rather than a shared read/write gate — see `getuservariable.md`'s note that this makes native fields *readable* but not *writable* on UZDoom, an asymmetry Zandronum's single `bUserVar` gate doesn't have.
- **Type support is broader than `int`.** `DLevelScript::SetUserVariable` (`src/playsim/p_acs.cpp:4938-4959`) dispatches on the resolved field's type: a `string` field is set via `Level->Behaviors.LookupString(value)` into an `FString` (the ACS `value` argument is treated as a string-table index, not a raw int, when the target field is `string`-typed); a `float`/`double` field is set via `ACSToDouble(value)` (fixed-point-to-double conversion); everything else (`int`, `bool`) is set via a generic `SetValue(addr, value)`. `Name`-typed fields are excluded on the write side specifically — `GetVarAddrType`'s type-acceptance check only allows `TypeName` through when `readonly` is true (`src/playsim/p_acs.cpp:4926-4934`), so `SetUserVariable(tid, "some_name_field", ...)` fails silently even though `GetUserVariable` can read that same field.
- **Array-of-int writes still work identically to Zandronum's `int[]` support** via `SetUserArray`, which calls the same helper with a nonzero index; `GetVarAddrType` unwraps the array's element type and bounds-checks the index (`src/playsim/p_acs.cpp:4908-4919`).

## Quirks

- **NULL-activator bug (both engines):** When `tid` is 0, the return count (`1`) is incremented *outside* the check for `activator != NULL`. So calling `SetUserVariable(0, ...)` on a script with no activator (e.g., a clientside script with no valid activator) returns 1 but sets nothing — the count doesn't reflect actual writes. Confirmed identical in both engines' case handlers (Zandronum `src/p_acs.cpp:6126-6133`; UZDoom `src/playsim/p_acs.cpp:5652-5659`) — this was previously documented as if it were a Zandronum-specific bug, but it is shared behavior, not a fork divergence.

## See also

- `getuservariable.md` — retrieves a user variable value (returns 0 on failure, unlike the setter which has no error path); its "Engine-family divergence" section documents the same `bUserVar`-vs-`GetVarAddrType` split from the read side, including the `string`/`float`/`Name` type-support detail this file's divergence section builds on.
- `SetUserArray` / `GetUserArray` — array-indexed variants, sharing the same engine-specific gates.
- `../../decorate/concepts/user-variables.md` — DECORATE-side declaration rules and the parent-class-visibility/lookup-cost findings that apply to this function's name resolution on both engines.

---

**Note:** This function is half of a getter/setter pair with `GetUserVariable`. A future consolidation into a `families/user-variables.md` covering both (and the array variants) is a plausible refactoring candidate, since the pair has asymmetric behavior (the setter iterates *all* matching actors; the getter resolves a single actor).
