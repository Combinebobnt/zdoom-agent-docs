# `int GetUserVariable(int tid, str name)`

**Tier:** A (original content); B (the `searchparents=true`/parent-class-visibility clause in
Parameters below, added from direct source reading — not on this file's wiki page)
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-30)
**Provenance:** `GetUserVariable - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=GetUserVariable&oldid=44988`), verified 2026-07-30 against the Zandronum source's `src/p_acs.cpp:5623-5652` (static helper) and `p_acs.cpp:6148-6157` (engine case handler); the `bUserVar`-gate finding below re-verified 2026-08-01 against the same helper's exact guard at `p_acs.cpp:5629-5633`. The `searchparents=true` clause is a further source-only reading of the same `p_acs.cpp:5623-5652` helper, with no wiki counterpart.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function.

Retrieves the value of a user-defined actor variable. Extension function, index -25 in `zcommon.bcs`'s `special` table.

## Parameters

- `tid` — actor's thing ID. **`0` means "the activator"** (`SingleActorFromTID`, per the getter case at `p_acs.cpp:6153`).
- `name` — name of the variable to retrieve, as a string constant. Looked up by `FName` in the actor's class symbol table (Zandronum's `src/p_acs.cpp:5625`), via `FindSymbol(varname, /*searchparents=*/true)` — **the search does walk parent classes**, so a `user_`-prefixed variable declared on a base class is reachable through this call on any subclass instance without redeclaring it there. See `../../decorate/concepts/user-variables.md#parent-class-visibility-and-lookup-cost-tier-b--source-verified-no-wiki-starting-point` for the full finding (tier B, source-only — not on this file's wiki page).

## Return value

Returns the value of the variable as a plain `int`. All return values are uninterpreted raw integer bits.

## Supported variable types and failure modes

**Critical ZDoom/Zandronum fork divergence:** the ZDoom wiki claims this function supports `double` (returned as fixed-point), `bool`, `string`, and `name` types, plus handling for arrays. **Zandronum supports only `int` and `int[]` arrays** — attempting to read any other type silently returns `0` (`src/p_acs.cpp:5634-5644`, the type check in the static `GetUserVariable` helper):

- **`int` variables:** return the int value directly.
- **`int[]` arrays:** returns the element at index 0 (the getter has no array-index parameter; use `GetUserArray` instead for explicit indexing).
- **Any other type** (`double`, `bool`, `string`, `name`, non-int arrays): return `0`. Indistinguishable from a genuinely-zero variable.

If the variable doesn't exist in the actor's class symbol table, returns `0`.

**A more fundamental gate runs before the type check, and it applies regardless of type:** the static helper's very first check is `sym == NULL || sym->SymbolType != SYM_Variable || !var->bUserVar` (`src/p_acs.cpp:5629-5633`) — it returns `0` immediately unless the resolved symbol carries the `bUserVar` flag, which is only set on fields declared through DECORATE's `var int user_<name>;` syntax (`src/thingdef/thingdef_parse.cpp`'s `ParseUserVariable`, `sym->bUserVar = true`). This means the wiki's claim that `GetUserVariable` "is capable of retrieving non-user variables including strings and names" does not hold in the Zandronum engine fork at all: **a plain native or DECORATE-declared `int` member field that is not a `user_`-prefixed user variable also returns `0` here**, not because of the type mismatch documented above, but because it never has `bUserVar` set in the first place — there is no code path in the Zandronum engine fork that reads an arbitrary non-user member by name via this function, of any type. `GetUserArray` (index -29) calls this exact same static helper (just with a nonzero `index` argument instead of `0` — see `src/p_acs.cpp:6187-6194`'s case handler), so this gate applies identically to both functions. `SetUserVariable`/`SetUserArray` (`src/p_acs.cpp:5593-5621`, the sibling static `SetUserVariable` helper) apply the identical `bUserVar` gate on the write side.

## Engine-family divergence: UZDoom drops the `bUserVar` gate and the type restriction

UZDoom's `GetUserVariable` is built on a different, more permissive lookup mechanism than Zandronum's — not just a different observable contract but a different mechanism underneath. It resolves the name the same way (a class-symbol-table lookup that walks parent classes, matching the `searchparents=true` finding above), but the resolved symbol is then treated as an arbitrary reflected field (`PField`) rather than being checked for a `bUserVar` flag. There is no `bUserVar` concept in UZDoom's implementation at all.

Practical effect: UZDoom's `GetUserVariable` can read **any** actor field reachable by name through the class symbol table — not just `user_`-prefixed DECORATE user variables — including plain native engine fields and ordinary DECORATE-declared members, for reading. (The sibling `SetUserVariable` is more restrictive on the write side: it rejects native fields specifically, so native properties are readable but not writable through this pair of functions in UZDoom — an asymmetry Zandronum's single shared `bUserVar` gate doesn't have, since it blocks native fields on both read and write alike.)

Type support is also much broader in UZDoom, matching the original ZDoom wiki description this doc's Zandronum section calls out as a "critical fork divergence" from that wiki: `int`, `bool`, and `float`/`double` fields (returned as fixed-point) are readable, `string` fields are readable (returned as a string-table index, like any other ACS string result), and `Name`-typed fields are additionally readable specifically through the get path (returned as a string-table index of the name's text) though not through the corresponding set path. Only a handful of "int-like subclass" types (e.g. `Color`) remain deliberately excluded, to avoid exposing those as raw ints. In short: on UZDoom, the wiki's original broader description of this function is largely accurate; it's specifically the Zandronum fork that narrowed it down to `user_`-prefixed `int`/`int[]` only.

Array-of-int reads through `GetUserVariable` itself (as opposed to `GetUserArray`) still return element 0 of an array field, same as Zandronum, since this function always passes an index of 0 to the shared lookup helper.

## Related functions

- `SetUserVariable` (index -24) — write a user variable (same type restrictions).
- `GetUserArray`/`SetUserArray` (indices -29/-28) — read/write individual array elements with explicit indexing.

## Example

```text
script "ReadUserVar" (void)
{
    int val = GetUserVariable(0, "user_myvar");
    if (val != 0) {
        Print(s: "Value: ", d: val);
    }
}
```

Note: if `user_myvar` doesn't exist or is any type other than `int`, `val` will be `0` even if the variable is defined on the actor.
