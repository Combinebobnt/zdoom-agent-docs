# ACS_NamedTerminate

**Tier:** A
**Engine:** Zandronum 3.2.1 (feature predates the fork; verified against the `3.3-alpha` local checkout, no version-gap concern for this one).
**Provenance:** `ACS_NamedTerminate - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=ACS_NamedTerminate&oldid=33698`), verified 2026-07-29 against the Zandronum source's `src`.

`bool Acs_NamedTerminate(str script, int map)`

## Bucket

Extension function, `ACSF_ACS_NamedTerminate` (index `-41` in `zcommon.bcs`'s `special` table).
Its `case ACSF_ACS_NamedTerminate:` in `p_acs.cpp` (~line 6341) is shared with the other five
`ACS_Named*` extension functions (`NamedExecute`, `NamedSuspend`, `NamedLockedExecute`,
`NamedLockedExecuteDoor`, `NamedExecuteWithResult`, `NamedExecuteAlways`): it resolves the string
argument to a named-script number (`-FName(...)`), then dispatches through
`NamedACSToNormalACS[]` (`p_lnspec.cpp:86`) into the **action special** `LS_ACS_Terminate`
(`FUNC(LS_ACS_Terminate)`, `p_lnspec.cpp:1866`) — the same code path the numbered `ACS_Terminate`
special uses. So `Acs_NamedTerminate("Foo", 0)` and `Acs_Terminate(-"Foo", 0)` are the same call
by the time execution reaches `P_TerminateScript`.

## Parameters

- `script` — name of the script to terminate (a BCS string, resolved via `FName`/string-table
  lookup, not a script number).
- `map` — map containing the script. **Not optional in this fork's signature** (`zcommon.bcs`
  gives `Acs_NamedTerminate` no `;`-separated default, unlike `Acs_NamedExecute`'s trailing
  `raw,raw,raw`), even though the underlying C++ (`p_acs.cpp`) defensively falls back to `0` if
  `argCount <= 1`. `map == 0` means "the current map" (`level.mapname`), not "map number 0" —
  matches the older numbered `ACS_Terminate`/`ACS_Suspend` convention.

## Return value

Per the wiki: "Returns true in all cases." **This is accurate but is not a success signal** —
`LS_ACS_Terminate` (`p_lnspec.cpp:1866`) returns `true` unconditionally, before knowing whether
anything was actually terminated:

- If `map` names a level not found by `FindLevelByNum`, the function silently does nothing at
  all (no call into `P_TerminateScript`) and still returns `true`.
- If `map` resolves (or is `0`/current map) but no script with that name is currently *running*,
  `SetScriptState` (`p_acs.cpp:13143`) looks the script number up in the active `DACSThinker`'s
  `RunningScripts` map, finds nothing, and silently no-ops — again with `true` already returned
  by the caller.

So a script name typo, a script that already finished, or a bad map number are all
indistinguishable from a successful terminate by return value alone.

## Cross-map behavior

`P_TerminateScript` (`p_acs.cpp:13298`) compares `map` against `level.mapname`:
- **Same map:** terminates immediately — `SetScriptState(script, SCRIPT_PleaseRemove)`.
- **Different map:** does not terminate anything now. It queues a deferred action
  (`addDefered(..., acsdefered_t::defterminate, ...)`) that fires only if/when that target map is
  actually entered later (`P_DoDeferedScripts`) — same deferred-execution mechanism
  `ACS_Execute`/`ACS_Suspend` use for cross-map targets, not a special case unique to Terminate.

## Fork/wiki notes

The wiki page's mention of "both an ACS and a DECORATE version" refers to a DECORATE action
function counterpart outside ACS/BCS scope — not relevant when compiling with `bcc` for Zandronum
and not verified here.
