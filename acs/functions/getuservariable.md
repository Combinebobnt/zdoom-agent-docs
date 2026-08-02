# `int GetUserVariable(int tid, str name)`

**Tier:** A
**Engine:** Zandronum 3.2.1 (verified against the `3.3-alpha` local checkout).
**Provenance:** `GetUserVariable - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=GetUserVariable&oldid=44988`), verified 2026-07-30 against the Zandronum source's `src/p_acs.cpp:5623-5652` (static helper) and `p_acs.cpp:6148-6157` (engine case handler); the `bUserVar`-gate finding below re-verified 2026-08-01 against the same helper's exact guard at `p_acs.cpp:5629-5633`.
**Bucket:** Extension function.

Retrieves the value of a user-defined actor variable. Extension function, index -25 in `zcommon.bcs`'s `special` table.

## Parameters

- `tid` — actor's thing ID. **`0` means "the activator"** (`SingleActorFromTID`, per the getter case at `p_acs.cpp:6153`).
- `name` — name of the variable to retrieve, as a string constant. Looked up by `FName` in the actor's class symbol table (Zandronum's `src/p_acs.cpp:5625`).

## Return value

Returns the value of the variable as a plain `int`. All return values are uninterpreted raw integer bits.

## Supported variable types and failure modes

**Critical ZDoom/Zandronum fork divergence:** the ZDoom wiki claims this function supports `double` (returned as fixed-point), `bool`, `string`, and `name` types, plus handling for arrays. **Zandronum supports only `int` and `int[]` arrays** — attempting to read any other type silently returns `0` (`src/p_acs.cpp:5634-5644`, the type check in the static `GetUserVariable` helper):

- **`int` variables:** return the int value directly.
- **`int[]` arrays:** returns the element at index 0 (the getter has no array-index parameter; use `GetUserArray` instead for explicit indexing).
- **Any other type** (`double`, `bool`, `string`, `name`, non-int arrays): return `0`. Indistinguishable from a genuinely-zero variable.

If the variable doesn't exist in the actor's class symbol table, returns `0`.

**A more fundamental gate runs before the type check, and it applies regardless of type:** the static helper's very first check is `sym == NULL || sym->SymbolType != SYM_Variable || !var->bUserVar` (`src/p_acs.cpp:5629-5633`) — it returns `0` immediately unless the resolved symbol carries the `bUserVar` flag, which is only set on fields declared through DECORATE's `var int user_<name>;` syntax (`src/thingdef/thingdef_parse.cpp`'s `ParseUserVariable`, `sym->bUserVar = true`). This means the wiki's claim that `GetUserVariable` "is capable of retrieving non-user variables including strings and names" does not hold in this fork at all: **a plain native or DECORATE-declared `int` member field that is not a `user_`-prefixed user variable also returns `0` here**, not because of the type mismatch documented above, but because it never has `bUserVar` set in the first place — there is no code path in this fork that reads an arbitrary non-user member by name via this function, of any type. `GetUserArray` (index -29) calls this exact same static helper (just with a nonzero `index` argument instead of `0` — see `src/p_acs.cpp:6187-6194`'s case handler), so this gate applies identically to both functions. `SetUserVariable`/`SetUserArray` (`src/p_acs.cpp:5593-5621`, the sibling static `SetUserVariable` helper) apply the identical `bUserVar` gate on the write side.

## Related functions

- `SetUserVariable` (index -24) — write a user variable (same type restrictions).
- `GetUserArray`/`SetUserArray` (indices -29/-28) — read/write individual array elements with explicit indexing.

## Example

```
script "ReadUserVar" (void)
{
    int val = GetUserVariable(0, "user_myvar");
    if (val != 0) {
        Print(s: "Value: ", d: val);
    }
}
```

Note: if `user_myvar` doesn't exist or is any type other than `int`, `val` will be `0` even if the variable is defined on the actor.
