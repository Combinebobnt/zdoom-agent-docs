# `bool CheckScript(mixed script, bool named)`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-06-06)
**Provenance:** Zandronum Wiki `CheckScript` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=CheckScript&oldid=2510); verified against the Zandronum source's `src/p_acs.cpp:5553` (`EACSFunctions` enum) and `:9021` (dispatch `case ACSF_CheckScript`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (value 188 in the `EACSFunctions` enum; dispatched as `ACSF_CheckScript`).

Checks whether a script exists, identified by either its number or name.

## Parameters

- `script` — A `mixed` value (either an `int` script number or a `str` script name, depending on the `named` parameter).
- `named` — Whether to interpret `script` as a named script (`true`) or numbered script (`false`).

## Return value

Returns `true` if a script with the specified identifier exists, `false` otherwise.

## Zandronum-specific: uncallable from zt-bcc

This function exists in the Zandronum engine (`ACSF_CheckScript` in `src/p_acs.cpp:5553`, with a dispatch `case` at `:9021`, `EACSFunctions` value 188), but is not exposed by the zt-bcc compiler. The relevant namespace is the *negative* index (extension functions are negative indices in `zcommon.bcs`'s `special` table; positive indices are the unrelated action-special namespace, e.g. positive 188 there is `Sector_SetCeilingScale`, which says nothing about this function's callability). At the actual negative slot, `zcommon.bcs`'s sequential extension-function block jumps straight from `-185:IsPlayerContestingControlPoint` to the unrelated Q-Zandronum block starting at `-141` — no entry at `-186` through `-189` under any name, confirmed by direct inspection of that range. `src/builtin.c`'s `g_funcs[]` has no entry for this function either.

Scripts in Zandronum that need to check script existence must do so through this engine function directly, but **there is no way to call it from BCS source when targeting this engine via zt-bcc**. The Zandronum engine accepts the call at runtime (`PCD_CALLFUNC` dispatch), but the BCS compiler provides no way to generate the bytecode.

## Version note

This function was added after the Zandronum 3.2.1 release (confirmed by commit ancestry: the introducing commit `3ec151a78` "Added ACS function: CheckScript, to check if a particular script exists by searching for its name or number." postdates the 3.2.1 version-bump commit `28f736fb3`). It is only available in development builds of Zandronum 3.3-alpha and newer, not in 3.2.1.
