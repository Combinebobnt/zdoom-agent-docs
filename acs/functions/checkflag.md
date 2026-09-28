# `bool CheckFlag(int tid, str flag)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki page `CheckFlag` (retrieved 2026-07-29, https://zdoom.org/w/index.php?title=CheckFlag&oldid=44244) + verification against the Zandronum source's `src/p_acs.cpp:6804-6812` (ACSF_CheckFlag case), `thingdef/thingdef_properties.cpp` (CheckActorFlag implementation, flag lookup/error handling), `thingdef/thingdef_data.cpp:404-412,449-486` (`FlagLists[]` and the qualified-name `FindFlag`), and `p_acs.cpp` (SingleActorFromTID for TID 0 and shared-TID behavior). ZDoom wiki describes function correctly for Zandronum.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index −75 in `zcommon.bcs`'s `special` table; dispatched as `ACSF_CheckFlag` in `p_acs.cpp:6804-6812`).

Checks whether an actor with a given TID has a specified actor flag set.

## Parameters

- **`tid`**: thing ID of the target actor. If `0`, the check is performed on the script's activator (the map entity or player that triggered the script).
- **`flag`**: actor flag name as a string (e.g., `"FLOAT"`, `"FRIENDLY"`, `"AMBUSH"`). Names are case-insensitive and are resolved against the target actor's class, so a flag valid for one actor type may not exist for another (e.g. an `Inventory` flag on a monster). On Zandronum the lookup searches the engine's static flag lists (`Actor`, `Inventory`, `Weapon`, `PlayerPawn`, `PowerSpeed`), consulting each list only if the actor's class descends from that list's class.

## Return value

Returns **`true`** if the actor has the flag set, **`false`** otherwise.

### The false cases are not distinguished

`CheckFlag` returns `false` in three different scenarios:
1. **Actor not found**: no actor with the given TID exists (or activator is NULL when tid is 0).
2. **Flag name unknown**: the name matches no flag available to the target actor's class (including a flag that exists only for classes the actor doesn't descend from). Unknown flag names print a console error `Unknown flag '<name>' in '<classname>'` and return `false` — a typo'd flag triggers spam, not a compile error.
3. **Flag unset**: the actor has the flag, but it is currently not set (the flag bit is 0).

Calling code cannot distinguish case 2 from case 3 without checking the console, so care must be taken to spell flag names correctly.

## Shared TIDs and activator semantics

If multiple actors share the same TID, `CheckFlag` returns true/false **only for the first actor in the TID's iteration order** — it does not check all of them or gather their results. Give each actor its own TID if each one needs checking.

## Flag names: class scope and dot notation

Flag strings support both simple names and dot notation. A simple name (`"FLOAT"`) is searched among every flag set the actor's class has access to through its ancestry. In dot notation the prefix names the class that owns the flag, as in DECORATE (`"INVENTORY.AUTOACTIVATE"`, `"WEAPON.NOAUTOFIRE"`); only that class's flags are searched, and an actor not descended from that class gets the unknown-flag error. On Zandronum the valid prefixes are exactly the five flag-list classes `Actor`, `Inventory`, `Weapon`, `PlayerPawn` and `PowerSpeed`. See the DECORATE documentation and/or the engine's `FFlagDef` and `FindFlag` implementations for the full flag namespace.

## Zandronum-specific: SetActorFlag absence

This function **does work** on both engines — the implementation is present and verified as far back as Zandronum 3.2.1, and equivalently on UZDoom (`ACSF_CheckFlag` at `src/playsim/p_acs.cpp`, dispatching to the shared `CheckActorFlag` helper). However, the inverse function `SetActorFlag` (documented on the same ZDoom Wiki page) **does not exist in the Zandronum engine fork** — it is declared in the compiler's `zcommon.bcs` to match upstream ZDoom, but was never merged into Zandronum `master` (the 3.2.1 target); it does work on UZDoom, which implements `ACSF_SetActorFlag`. See `functions/setactorflag.md` for the full details and a DECORATE-based workaround. Effectively, on Zandronum `CheckFlag` is the only working named-flag reader; there is no working named-flag setter from ACS on that engine (though dedicated property setters and DECORATE-based workarounds exist — see that file for both).
