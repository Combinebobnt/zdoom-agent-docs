# ACS_Suspend

**Tier:** A
**Engine:** Zandronum 3.2.1 (feature predates the fork; verified against the `3.3-alpha` local checkout, no version-gap concern for this one).
**Provenance:** `ACS_Suspend - ZDoom Wiki.html` (https://zdoom.org/w/index.php?title=ACS_Suspend&oldid=35857), verified 2026-07-29 against the Zandronum source's `src`.

`int Acs_Suspend(int script, int map)`

## Bucket

Action special, index 81 in `zcommon.bcs`'s `special` table — script-callable (the tail has no `:0`
restriction). Related to the extension function `Acs_NamedSuspend` (index `-40`), which resolves
a script name to a number and forwards through the same `LS_ACS_Suspend` action special (see
[ACS_NamedTerminate](acs_namedterminate.md)'s "Bucket" section for the dispatch path via
`NamedACSToNormalACS[]`).

## Parameters

- `script` — numeric ID of the script to suspend.
- `map` — numeric MAPINFO `levelnum` of the map containing the script. **Not optional in this
  fork** (`zcommon.bcs:1441` declares it as mandatory), even though the underlying C++ would
  tolerate omitting it. `map == 0` means "the current map" (`level.mapname`), not "map number 0"
  — matches the older numbered `ACS_Execute`/`ACS_Terminate` convention.

## Return value

Per the wiki: "Suspends execution of a script." **However, the return value is always `true`,
independent of whether anything was actually suspended** — the same unconditional-true polarity
as [ACS_NamedTerminate](acs_namedterminate.md) and for the same reason:

- If `map` names a level not found by `FindLevelByNum`, the function silently does nothing at all
  and still returns `true` (`p_lnspec.cpp:1858-1861`).
- If `map` resolves (or is `0`/current map) but no script with that name is currently *running*,
  `SetScriptState` (`p_acs.cpp:13143-13152`) looks the script number up in the active
  `DACSThinker`'s `RunningScripts` hash table, finds nothing, and silently no-ops — again with
  `true` already returned.

So a script number typo, a script that already finished, or a bad map number are all
indistinguishable from a successful suspend by return value alone. **This is a major fork/wiki
divergence:** the wiki states "If the specified script is not currently running, then it will be
immediately suspended the next time it is run" — but this fork has no "on next run" behavior.
`SetScriptState` only acts on currently-running instances; there is no latched "suspend on next
start" flag or deferred state.

## Cross-map behavior

`P_SuspendScript` (`p_acs.cpp:13290-13296`) compares `map` against `level.mapname`:

- **Same map:** suspends immediately — `SetScriptState(script, SCRIPT_Suspended)`.
- **Different map:** does not suspend anything now. It queues a deferred action
  (`addDefered(..., acsdefered_t::defsuspend, ...)`) that fires only if/when that target map is
  actually entered later (`P_DoDeferedScripts`, `p_acs.cpp:13154-13199`) — same
  deferred-execution mechanism `ACS_Execute`/`ACS_Terminate` use for cross-map targets. **Caveat:**
  a deferred suspend on a non-running script (the common case when a map first loads) is still a
  no-op, so deferred suspends are near-useless in practice.

## Resumption rules

A suspended script resumes only through a non-`ACS_ALWAYS` script-start path:

- `ACS_Execute` / `Acs_NamedExecute` — respects suspended instances; resumes the suspended script
  at its saved PC.
- `ACS_ExecuteAlways` / `Acs_NamedExecuteAlways` — always starts a fresh instance; a
  previously-suspended one is orphaned forever.
- `ACS_ExecuteWithResult` / `Acs_NamedExecuteWithResult` — always starts a fresh instance (these
  are flavored like `ACS_ExecuteAlways` internally).
- `ACS_LockedExecute` / `Acs_NamedLockedExecute` — respects suspended instances (these are
  `ACS_Execute` with a key check; see [suspend](suspend.md) for the full derivation).

**Fork/wiki alignment:** The wiki page doesn't explicitly state which start paths resume vs. orphan,
but its worked example uses `ACS_Execute` to resume a script suspended via the `suspend;`
statement — this pattern holds identically for `ACS_Suspend`-suspended scripts.

## Clientside behavior

Unlike `ACS_Execute` (which has a `CLIENTSIDE`-script carve-out in `p_lnspec.cpp:1761-1766`),
`LS_ACS_Suspend` has no server→client broadcast. A server-side call to suspend a `CLIENTSIDE`-flagged
script does not reach clients — the script continues running on clients even though suspended on
the server.

## Fork/wiki notes

**Wiki's "on next run" claim is false in this fork** (detailed above under "Return value"). The
source of confusion may be that the wiki was written for an earlier ZDoom version with different
semantics, or the author misread the deferred-suspend queueing as implying a "will suspend once
started" guarantee. Here, deferred-suspend still requires the script to already be running.
