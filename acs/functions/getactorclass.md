# GetActorClass

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `GetActorClass - ZDoom Wiki` (https://zdoom.org/w/index.php?title=GetActorClass&oldid=40905), verified against Zandronum source 2026-07-29
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function (`zcommon.bcs` index -68, dispatches to `case ACSF_GetActorClass` in `p_acs.cpp:6208`)

**Syntax:** `str GetActorClass(int tid)`

---

## Description

Returns the class name of an actor as a string.

### Parameters

- **`tid`**: Target actor's thing ID. Use `0` to refer to the activator.

### Return value

`str` — a string handle to the actor's class type name, or the literal four-character string `"None"` if the lookup fails.

The function returns `"None"` in three distinct but silent scenarios:
1. The actor's class type is genuinely named `None` (extremely rare/unverified in stock Doom; theoretically possible in a custom mod).
2. Nonzero `tid` matches no actor (null lookup result).
3. `tid == 0` and the activator is `NULL` (e.g., in `OPEN` scripts).

These cases cannot be distinguished by the return value alone.

### Behavior details

- **TID resolution:** Uses `SingleActorFromTID(tid, activator)`, which means only the **first actor** matching a nonzero `tid` is checked; if multiple actors share the same TID, the others are not tested. Iteration order is undefined (engine-internal). For `tid == 0`, returns the activator or NULL if there is no activator.

- **String handle:** The return value is a string handle obtained via `GlobalACSStrings.AddString(...)`, compatible with all `str`-type operations (`StrCmp`, `StrLen`, concatenation, HUD printing, etc.).

- **NULL lookup behavior:** Unlike `CheckActorClass` (the companion checker function), which returns `false` on a NULL result, `GetActorClass` returns the literal string `"None"`. There is no error return — the function always produces a valid string, never an invalid handle or empty string.

### Related functions

- **`CheckActorClass`** (index -27): Companion checker that tests whether an actor's class matches a provided string name. Returns `false` (instead of the string `"None"`) on the same NULL-actor paths. See [functions/checkactorclass.md](checkactorclass.md).

---

## Wiki notes

The ZDoom wiki page provides the correct basic description but omits the NULL-actor path behavior. The fork's C++ implementation returns `"None"` where the page makes no claim, verified via `p_acs.cpp:6210-6211`.

---

## Code references

- **Engine implementation:** the Zandronum source's `src/p_acs.cpp:6208-6212` (the case block)
- **Declaration:** the zt-bcc source's `lib/zcommon.bcs:1697`
- **TID resolution helper:** the Zandronum source's `src/p_acs.cpp:4445-4456` (`SingleActorFromTID`)
