# `int SetGameplaySetting(str cvar, int value)`

Zandronum-specific ACS function that changes the value of an engine CVar at runtime, but
**only** if that CVar has been marked as a "gameplay setting" (i.e. eligible for the
`GAMEMODE` lump's game-settings block). Extension function, index `-155` in
`zt-bcc/lib/zcommon.bcs:1785` (`SetGameplaySetting(str, int):bool`). `ACSF_SetGameplaySetting`
in `p_acs.cpp`, case body at `p_acs.cpp:8129-8174`:

```cpp
case ACSF_SetGameplaySetting:
{
    const char *pszName = FBehavior::StaticLookupString( args[0] );
    FBaseCVar *pCVar = FindCVar( pszName, NULL );

    // [AK] Ignore invalid CVars, especially those which are latched (e.g. sv_maxlives and sv_maxteams).
    if (( pCVar == NULL ) || ( pCVar->GetFlags() & ( CVAR_IGNORE | CVAR_NOSET | CVAR_LATCH )))
        return 0;

    // [AK] Make sure that the CVar can be used in a game settings block.
    if (( pCVar->GetFlags() & CVAR_GAMEPLAYSETTING ) || (( pCVar->IsFlagCVar() ) && ( static_cast<FFlagCVar *>( pCVar )->GetValueVar()->GetFlags() & CVAR_GAMEPLAYFLAGSET )))
    {
        UCVarValue Val;
        ECVarType Type;

        switch ( pCVar->GetRealType() )
        {
            case CVAR_Bool:
            case CVAR_Dummy:
                Val.Bool = !!args[1]; Type = CVAR_Bool; break;
            case CVAR_Float:
                Val.Float = FIXED2FLOAT( args[1] ); Type = CVAR_Float; break;
            default:
                Val.Int = args[1]; Type = CVAR_Int; break;
        }

        GAMEMODE_SetGameplaySetting( pCVar, Val, Type );
        return 1;
    }

    return 0;
}
```

**Bucket:** extension function (negative index, `ACSF_SetGameplaySetting`).

## Behavior beyond the wiki page

- **The wiki's "any engine-built CVar or flag that's allowed in the GAMEMODE lump" is a hard
  gate, not a description of typical use** — the function looks up the CVar by name via
  `FindCVar`, then requires it to carry the `CVAR_GAMEPLAYSETTING` flag directly, or (for a
  flag/bitfield CVar backed by an underlying value CVar, i.e. `dmflags`-style booleans) requires
  the *value* CVar behind it to carry `CVAR_GAMEPLAYFLAGSET`. A CVar without one of these two
  flags set in its `CUSTOM_CVAR`/`CVAR` declaration is silently rejected (return `0`), regardless
  of whether it's a real, settable CVar. This is a fixed, source-level allowlist — not something
  a mod can extend from ACS.
- **Unknown/invalid CVar name, or a `CVAR_IGNORE`/`CVAR_NOSET`/`CVAR_LATCH` CVar, also returns
  `0`** before the gameplay-setting check even runs. This is exactly the mechanism behind the
  wiki's claim that `sv_maxlives` and `sv_maxteams` can't be changed this way — both are declared
  with `CVAR_GAMEPLAYSETTING` (`gamemode.cpp:80`, `team.cpp:2169`) but *also* `CVAR_LATCH`, and
  the latch check is evaluated first and short-circuits before the gameplay-setting flag is ever
  consulted. Verified by grep: every other `CVAR_GAMEPLAYSETTING` CVar found in
  the Zandronum source's `src` (e.g. `timelimit`, `fraglimit`, `winlimit`, `wavelimit`,
  `sv_dominationscorerate`, `sv_maprotation`, `alwaysapplydmflags`, `teamdamage`,
  `sv_fastweapons`, `instagib`, `buckshot`) is a real, working example, but several of those
  (`instagib`, `buckshot`, `sv_suddendeath`, `sv_maxlives`, `fraglimit`, `timelimit`, `winlimit`,
  `wavelimit`) are *also* `CVAR_LATCH` and therefore equally un-settable via this function at
  runtime, on top of `sv_maxlives`/`sv_maxteams` — the wiki names those two only as examples, the
  actual exclusion is "any latched CVar," which is a larger set than the two named.
- **Type coercion is driven by the CVar's own declared type** (`pCVar->GetRealType()`), not by
  anything the caller specifies: `CVAR_Bool`/`CVAR_Dummy` CVars get `!!args[1]` (any nonzero ACS
  int becomes `true`), `CVAR_Float` CVars get `FIXED2FLOAT(args[1])` (confirms the wiki's note
  that float CVars like `sv_aircontrol`/`sv_gravity` must be passed as ACS fixed-point, e.g.
  `1.0` written as `1.0` in BCS source, not the raw float bit pattern), and everything else
  (`CVAR_Int`, `CVAR_String` is not handled specially and falls into `default`, effectively
  treated as int) gets the raw arg as an int.
- **Locking interaction:** if the CVar is currently one of the mode's configured `GameplaySettings`
  entries and is flagged locked (`GAMEMODE_IsGameplaySettingLocked`), `GAMEMODE_SetGameplaySetting`
  (the internal helper, not this ACS function) temporarily clears the lock, applies the value via
  `pCVar->ForceSet`, updates the saved `Val` for that setting, then restores the lock flag
  unchanged — so calling this from ACS **bypasses** a game-mode lock for that one write (the
  value takes effect), but the setting reports itself locked again immediately afterward and a
  future `GAMEMODE_ResetGameplaySettings` call will still reset it back to the locked value.
- Returns `1` on success, `0` on any rejection (unknown CVar, `IGNORE`/`NOSET`/`LATCH` flag, or
  missing `CVAR_GAMEPLAYSETTING`/`CVAR_GAMEPLAYFLAGSET`) — matches the wiki's stated return
  values, just with a wider failure surface than the wiki spells out.

## Version gate (3.2.1 check)

Added in commit `a02891d4e` ("Added ACS function: \"SetGameplaySetting\", allowing modders to
change gameplay-related CVars on the fly."), dated 2022-09-25. Verified via
`git merge-base --is-ancestor a02891d4e 28f736fb3` (the 3.2.1 version-string-bump commit) →
true, i.e. `a02891d4e` is an ancestor of `28f736fb3`. This function existed well before the
3.2.1 tag, not just in the `master`/`3.3-alpha` checkout.

**Family note:** this function is closely related to `SetGameModeLimit`/`GetGameModeLimit` (both
also gate CVar access through the game-mode system) and could arguably share a family page with
them, but this file covers only `SetGameplaySetting` per this batch's per-function scoping — a
sibling intake task is processing `SetGameModeLimit` independently in the same batch. Flagging
here in case the coordinating session wants to consolidate into a `families/gamemode-settings.md`
later.

**Provenance:** wiki page `SetGameplaySetting - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=2522`) + source-verified (`p_acs.cpp:8129-8174`, `gamemode.cpp:1619-1657`,
`c_cvars.h:88,91`) and version-gated against `28f736fb3` per this repo's 3.2.1 check.
**Engine:** Zandronum 3.2.1. **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
