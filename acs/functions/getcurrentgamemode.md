# `str GetCurrentGamemode(void)`

Returns the current game mode as a string constant name, with the `GAMEMODE_` prefix stripped.
Extension function, index `-133` in `zt-bcc/lib/zcommon.bcs:1766` (declared there as
`GetCurrentGamemode` — lowercase `m`; ACS/BCS name lookups are case-insensitive, so the wiki's
`GetCurrentGameMode` capitalization calls the same function). `ACSF_GetCurrentGamemode` in
`p_acs.cpp`, case body at `p_acs.cpp:7582-7586`:

```cpp
case ACSF_GetCurrentGamemode:
{
    // [AK] We need to leave the "GAMEMODE_" prefix out of the string, which is 9 characters long.
    return GlobalACSStrings.AddString( GetStringGAMEMODE_e( GAMEMODE_GetCurrentMode()) + 9 );
}
```

**Bucket:** extension function (negative index, `ACSF_GetCurrentGamemode`).

- Takes no arguments and cannot fail — it just stringifies whatever `GAMEMODE_GetCurrentMode()`
  (the server's live `GAMEMODE_e` state) currently is, via a fixed name table
  (`gamemode_enums.h`) and a hardcoded `+ 9` to skip the `"GAMEMODE_"` prefix. There is no
  "unknown"/error string case.
- The wiki's return-value list is exactly the `GAMEMODE_e` enum in
  the Zandronum source's `src/gamemode_enums.h:82-104`, in the same order, each with `GAMEMODE_`
  stripped: `Cooperative`, `Survival`, `Invasion`, `Deathmatch`, `Teamplay`, `Duel`, `Terminator`,
  `LastManStanding`, `TeamLMS`, `Possession`, `TeamPossession`, `TeamGame`, `CTF`, `OneFlagCTF`,
  `Skulltag`, `Domination` — confirmed 1:1, nothing added or missing.
- Pairs with `SetCurrentGamemode(str)` (`-132`, `p_acs.cpp:7516-7580`), which does the reverse
  lookup (`GetValueGAMEMODE_e` on `"GAMEMODE_" + name`, case-insensitive via `ToUpper()`) and has
  several failure/refusal conditions of its own (client-mode call, mid-result-sequence, no
  matching starts for the target mode, etc.) — not covered here since this file is scoped to the
  getter; see that function's own doc if/when written.
- This function and its `Set` counterpart were both added in the same commit, `c487ff0a5`
  ("Added new ACS functions: SetGamemodeLimit()... SetCurrentGamemode()... GetCurrentGamemode()
  ..."), which **is an ancestor of** the 3.2.1 version-bump commit `28f736fb3` (verified via
  `git merge-base --is-ancestor c487ff0a5 28f736fb3`) — so it did exist in Zandronum 3.2.1, not
  just in the `master`/`3.3-alpha` checkout.

**Example:**

```
str mode = GetCurrentGamemode();
if (mode == "Invasion")
{
    Log(s:"Playing Invasion");
}
```

**Returns:** `str` — one of the 16 `GAMEMODE_e` names above (prefix stripped), always a valid
value; never fails or returns an empty/error string.

**Provenance:** wiki page `GetCurrentGameMode - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=2308`) + source-verified (`p_acs.cpp:7582-7586`, `gamemode_enums.h:82-104`,
`zt-bcc/lib/zcommon.bcs:1766`) and version-gated against `28f736fb3` per this repo's 3.2.1 check.
**Engine:** Zandronum 3.2.1. **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
