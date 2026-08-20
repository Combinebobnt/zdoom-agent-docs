# `str GetCurrentGamemode(void)`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `GetCurrentGameMode - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `https://wiki.zandronum.com/w/index.php?title=GetCurrentGameMode&oldid=2308`) + source-verified (`p_acs.cpp:7582-7586`, `gamemode_enums.h:82-104`,
`zt-bcc/lib/zcommon.bcs:1766`) and version-gated against `28f736fb3` per this repo's 3.2.1 check.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (negative index, `ACSF_GetCurrentGamemode`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

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

```text
str mode = GetCurrentGamemode();
if (mode == "Invasion")
{
    Log(s:"Playing Invasion");
}
```

**Returns:** `str` — one of the 16 `GAMEMODE_e` names above (prefix stripped), always a valid
value; never fails or returns an empty/error string.

## Engine-family divergence

`GetCurrentGamemode` is bound as ACSF (CALLFUNC) index 133 — inside the 100–199 range UZDoom's own
ACSF enum reserves for Zandronum's extensions and implements none of (confirmed via
`tools/engine_matrix.py GetCurrentGamemode`, bin `zandronum-only-silent`). UZDoom's `CallFunction`
dispatcher is a plain `switch` over the ACSF index with `default: break;` falling through to
`return 0` — no error, no log line, execution just continues. A Zandronum-compiled object calling
`GetCurrentGamemode()` under UZDoom silently gets `0` back in place of the real gamemode name. See
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general mechanism
— this function is one of the confirmed instances it names directly.

That `0` doesn't land the way it does for the compat doc's plain int/bool-returning examples,
where the substituted `0` is directly the coincidentally-correct payload. This function's declared
return type is `str`, which ACS implements as an index into a string pool, not a raw value — a
genuine call encodes its result through `GlobalACSStrings.AddString`, which tags the index with
the pool's reserved library-id bits so the VM resolves it against the dynamic string table. The
substituted `0` carries none of those bits: it decodes as library ID 0, string index 0 — whatever
compiled string constant happens to sit at that slot in the calling object's own string table, if
any, unrelated to any `GAMEMODE_e` name. So although `GAMEMODE_COOPERATIVE` is numerically 0 in
the enum this file documents above, the UZDoom-side failure does not stringify to `"Cooperative"`
and isn't the "looks fine in a quick SP test" case the compat doc warns about for int-returning
extensions — a script comparing the result against a gamemode name is far more likely to see
garbage or an unrelated string than a plausible-looking default.
