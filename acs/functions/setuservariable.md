# SetUserVariable

**Tier:** A
**Engine:** Zandronum 3.2.1 (source is 3.3-alpha; see ../../shared/AUTHORING.md's "Engine scope" section).
**Provenance:** Verified against Zandronum source (p_acs.cpp, case ACSF_SetUserVariable) from the ZDoom Wiki page, revision 45355.

**Signature:** `void SetUserVariable(int tid, str name, raw value)` (extension function, index -24)

## Summary

Sets a user variable on one or more actors.

## Parameters

- `tid`: The thing ID(s) to target. If 0, targets the script's activator. If nonzero, the function iterates through all actors with that TID.
- `name`: The name of the variable to set (must be of the form `user_*`).
- `value`: The value to assign. Passed as a fixed-point value for mathematical operations, but stored as a 32-bit integer in the variable itself.

## Behavior

The function attempts to set the named user variable on all matching actors. It returns an actor count as follows:
- If `tid` is 0: returns 1 (whether or not the activator exists; see Quirks below).
- If `tid` is nonzero: returns the count of actors it actually iterated through (0 if no actors match that TID).

In practice, the return value is inaccessible from ACS/BCS code — the function is declared as `void` in `zcommon.bcs` so the compiler will not allow assigning its return value to a variable, even though the engine internally computes it.

### User variable restrictions

- Only `int`-typed user variables can be set. Declarations of `double` or `bool` user variables in DECORATE are rejected at parse time (the fork's DECORATE parser enforces `user_*` variables to be `int` only, unlike the ZDoom wiki's claim of supporting `double` and `bool`).
- Native variables (declared with the `native` keyword in DECORATE) cannot be set.

### Failure behavior

If the named variable doesn't exist, isn't a user variable, or the actor instance is NULL, the function silently does nothing — there is no error return or indication of failure.

## Quirks

- **NULL-activator bug:** When `tid` is 0, the return count (`1`) is incremented *outside* the check for `activator != NULL`. So calling `SetUserVariable(0, ...)` on a script with no activator (e.g., a clientside script with no valid activator) returns 1 but sets nothing — the count doesn't reflect actual writes.

## See also

- `GetUserVariable` — retrieves a user variable value (returns 0 on failure, unlike the setter which has no error path).
- `SetUserArray` / `GetUserArray` — array-indexed variants.

---

**Note:** This function is half of a getter/setter pair with `GetUserVariable`. A future consolidation into a `families/user-variables.md` covering both (and the array variants) is a plausible refactoring candidate, since the pair has asymmetric behavior (the setter iterates *all* matching actors; the getter resolves a single actor).
