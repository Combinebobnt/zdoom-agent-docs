# `bool CheckFlag(int tid, str flag)`

**Tier:** A.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD; function introduced in commit `61c94648d`, confirmed as an ancestor of 3.2.1 version-bump commit `28f736fb3`).
**Provenance:** ZDoom Wiki page `CheckFlag` (retrieved 2026-07-29, oldid=44244) + verification against the Zandronum source's `src/p_acs.cpp:6802-6810` (ACSF_CheckFlag case), `thingdef/thingdef_properties.cpp` (CheckActorFlag implementation, flag lookup/error handling), and `p_acs.cpp` (SingleActorFromTID for TID 0 and shared-TID behavior). ZDoom wiki describes function correctly for this fork.
**Bucket:** extension function (index −75 in `zcommon.bcs`'s `special` table; dispatched as `ACSF_CheckFlag` in `p_acs.cpp:6802-6810`).

Checks whether an actor with a given TID has a specified actor flag set.

## Parameters

- **`tid`**: thing ID of the target actor. If `0`, the check is performed on the script's activator (the map entity or player that triggered the script).
- **`flag`**: actor flag name as a string (e.g., `"FLOAT"`, `"FRIENDLY"`, `"AMBUSH"`). Flag names are class-scoped and resolved through the target actor's `ActorInfo` lookup table — a flag valid for one actor type may not exist or resolve differently for another.

## Return value

Returns **`true`** if the actor has the flag set, **`false`** otherwise.

### The false cases are not distinguished

`CheckFlag` returns `false` in three different scenarios:
1. **Actor not found**: no actor with the given TID exists (or activator is NULL when tid is 0).
2. **Flag name unknown**: the flag does not exist in the target actor's class. Unknown flag names print a console error `Unknown flag '<name>' in '<classname>'` and return `false` — a typo'd flag triggers spam, not a compile error.
3. **Flag unset**: the actor has the flag, but it is currently not set (the flag bit is 0).

Calling code cannot distinguish case 2 from case 3 without checking the console, so care must be taken to spell flag names correctly.

## Shared TIDs and activator semantics

If multiple actors share the same TID, `CheckFlag` returns true/false **only for the first actor in the TID's iteration order** — it does not check all of them or gather their results. Use a `TagWait`/`ActorIterator`-style loop if you need to query multiple actors with the same TID.

## Flag names: class scope and dot notation

Flag strings support both simple names and dot notation. Simple lookup (`"FLOAT"`) searches in the actor's own class and its parent hierarchy. Dot notation (`"Parent.Subfield"`) allows qualification; typical patterns in ZDoom/Zandronum are flags like `"CountInvulnerable.Missile"`. See the DECORATE documentation and/or the engine's `FFlagDef` and `FindFlag` implementations for the full flag namespace.

## Fork-specific caveat: asymmetry with `SetActorFlag`

This function **does work** — the implementation is present and verified as far back as Zandronum 3.2.1. However, the inverse function `SetActorFlag` (documented on the same ZDoom Wiki page) **does not exist in this fork** — it is declared in the compiler's `zcommon.bcs` to match upstream ZDoom, but was never merged into Zandronum `master` (the 3.2.1 target). See `functions/setactorflag.md` for the full details and a DECORATE-based workaround. Effectively, `CheckFlag` is the only working named-flag reader in this fork; there is no working named-flag setter from ACS (though dedicated property setters and DECORATE-based workarounds exist — see that file for both).
