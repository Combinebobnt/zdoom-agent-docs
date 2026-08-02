# `void SetGameModeLimit(int limit, int value)`

Sets one of the six game-mode "limit" CVars (`fraglimit`, `timelimit`, `pointlimit`,
`duellimit`, `winlimit`, `wavelimit`) directly from ACS, bypassing console/rcon access checks.
Extension function, index `-134` in `zt-bcc/lib/zcommon.bcs:1767` (declared there as
`SetGamemodeLimit` — lowercase `m`; case-insensitive, same function as the wiki's
`SetGameModeLimit`). Declared to return `int`, but `ACSF_SetGamemodeLimit`'s case body in
`p_acs.cpp:7588-7592` just `break`s without an explicit `return` — falls through to the switch's
default `return 0;`, so calling it as an expression always yields `0`, not documented on the
wiki (which lists it as `void`).

```cpp
case ACSF_SetGamemodeLimit:
{
    GAMEMODE_SetLimit( static_cast<GAMELIMIT_e>( args[0] ), args[1] );
    break;
}
```

**Bucket:** extension function (negative index, `ACSF_SetGamemodeLimit`).

**Parameters:**

- `limit` — one of `GAMELIMIT_e` (`gamemode.h:134-140`), confirmed 1:1 with the wiki's list, same
  values: `GAMELIMIT_FRAGS = 0`, `GAMELIMIT_TIME = 1`, `GAMELIMIT_POINTS = 2`,
  `GAMELIMIT_DUELS = 3`, `GAMELIMIT_WINS = 4`, `GAMELIMIT_WAVES = 5`. Passing anything else
  hits `GAMEMODE_SetLimit`'s `default: I_Error(...)` case (`gamemode.cpp:1608-1610`) — an
  **engine fatal error**, not a silent no-op or ACS error return. This isn't mentioned on the
  wiki.
- `value` — for `GAMELIMIT_TIME` this is a **fixed-point number of minutes**
  (`GAMEMODE_SetLimit` does `FIXED2FLOAT(value)` and assigns it straight to the `timelimit`
  CVar, which every mode's exit check multiplies by `TICRATE * 60` — confirmed via
  `gamemode.cpp:742`, `duel.cpp:331`, `lastmanstanding.cpp:526`, `team.cpp:707`,
  `possession.cpp:582`, `p_spec.cpp:897-912` — all treat `timelimit` as minutes). For every
  other limit it's a plain integer count, matching the wiki.

**Per-limit silent clamping (not on the wiki at all):** each target CVar is a `CUSTOM_CVAR`
whose own callback clamps out-of-range values *after* `SetGameModeLimit` sets them — there is no
error path, the value is just silently rewritten:

| `limit` | CVar | Clamp range | Source |
|---|---|---|---|
| `GAMELIMIT_FRAGS` | `fraglimit` | `0 .. SHRT_MAX` (32767) | `deathmatch.cpp:302-336` |
| `GAMELIMIT_TIME` | `timelimit` | `0 .. SHRT_MAX` minutes | `deathmatch.cpp:344-360` |
| `GAMELIMIT_POINTS` | `pointlimit` | `0 .. 65535` | `team.cpp:2149-2157` |
| `GAMELIMIT_DUELS` | `duellimit` | `0 .. 255` | `duel.cpp:524-532` |
| `GAMELIMIT_WINS` | `winlimit` | `0 .. 255` | `lastmanstanding.cpp:695-703` |
| `GAMELIMIT_WAVES` | `wavelimit` | `0 .. 255` | `invasion.cpp:108-116` |

(`GAMELIMIT_WAVES`/`wavelimit` controls the wave count in Zandronum's invasion gamemode — a wave
count above 255 passed to `SetGameModeLimit(GAMELIMIT_WAVES, ...)` is silently truncated to 255,
not rejected.)

**Bypasses gameplay-setting locks.** All six CVars carry `CVAR_GAMEPLAYSETTING`, meaning a
GAMEMODE lump can mark them locked so players/rcon can't change them
(`GAMEMODE_IsGameplaySettingLocked`). `GAMEMODE_SetLimit` routes every write through
`GAMEMODE_SetGameplaySetting` (`gamemode.cpp:1619-1657`), which explicitly clears
`bIsLocked` before calling `pCVar->ForceSet(...)` and restores it afterward
(`gamemode.cpp:1640-1654`) — so `SetGameModeLimit` from ACS **always succeeds even on a
GAMEMODE-locked limit**, unlike a player/rcon attempt to change the same CVar. This same
lock-bypassing `GAMEMODE_SetGameplaySetting` path is shared with `SetGameplaySetting()` (a
sibling ACS function, documented separately) — the two functions plausibly belong in one
`families/` write-up together with `GAMEMODE_IsGameplaySettingLocked`, but per this batch's
collision guard this file only covers `SetGameModeLimit` itself.

**Client/server sync:** all six CVars are `CVAR_SERVERINFO` except `duellimit` (which is
missing that flag — an inconsistency in the fork, not verified further here). Their
`CUSTOM_CVAR` callbacks call `SERVER_SettingChanged(self, true[, ...])` to push the new value to
clients and the server console; this happens on the server's own clamped/final value, so
clients always see the post-clamp number, never a value that would have violated the range
above.

**Example:**

```
// Cap the current invasion round at 10 waves.
SetGameModeLimit(GAMELIMIT_WAVES, 10);

// Set a 15-minute time limit.
SetGameModeLimit(GAMELIMIT_TIME, 15.0);
```

**Returns:** nothing meaningful — always compiles to `0` if used as an expression (see above),
per the wiki's own `void` signature this isn't intended to be used as one.

**Provenance:** wiki page `SetGameModeLimit - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=1329`) + source-verified (`p_acs.cpp:7588-7592`, `gamemode.cpp:1572-1657`,
`gamemode.h:134-140`, plus the six CVar definitions in `deathmatch.cpp`, `team.cpp`,
`duel.cpp`, `lastmanstanding.cpp`, `invasion.cpp` listed above) and version-gated: added in
commit `c487ff0a5` ("Added new ACS functions: SetGamemodeLimit()... SetCurrentGamemode()...
GetCurrentGamemode()..."), confirmed via `git merge-base --is-ancestor c487ff0a5 28f736fb3` to
be an ancestor of the 3.2.1 version-bump commit `28f736fb3` — existed in Zandronum 3.2.1, not
just the `master`/`3.3-alpha` checkout.
**Engine:** Zandronum 3.2.1. **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
