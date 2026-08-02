# ACS_ExecuteAlways

**Tier:** A
**Engine:** Zandronum 3.2.1 (feature predates the fork; verified against the `3.3-alpha` local checkout).
**Provenance:** `ACS_ExecuteAlways - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=ACS_ExecuteAlways&oldid=42554`), verified 2026-07-30 against the Zandronum source's `src/p_lnspec.cpp:1784-1813` and `p_acs.cpp:13234-13288`.
**Bucket:** Action special, index 226 in `zcommon.bcs`'s `special` table.

`int ACS_ExecuteAlways(int script, int map [, int s_arg1, int s_arg2, int s_arg3])`

## Signature in this toolchain

`Acs_ExecuteAlways(int,int;int,int,int):int` — in zt-bcc's BCS signature, `map` is mandatory and the three script arguments are optional (after the `;`), unlike the ZDoom wiki's C-style prototype which shows all five as required. This means `ACS_ExecuteAlways(5, 0)` compiles here, using the defaults `s_arg1=0, s_arg2=0, s_arg3=0`.

## Parameters

- `script` — script number to execute (numeric, not a name; use the numbered `ACS_ExecuteAlways` special, not `Acs_NamedExecuteAlways`, if you need a script's string-based selection via `arg0str`).
- `map` — map which contains the script, resolved via `FindLevelByNum` to a numeric MAPINFO `levelnum`. `0` means "the current map" and skips the lookup. **Non-zero and not found: returns `false` without deferring** (`p_lnspec.cpp:1808-1810`), silently indistinguishable from "script not found." **Caveat:** the CLIENTSIDE carve-out (see below) runs *before* this map resolution, so a `CLIENTSIDE` target with a bogus `map` returns `true` on the server; a non-CLIENTSIDE target with the same bogus `map` returns `false`.
- `s_arg1, s_arg2, s_arg3` — three optional ints passed to the script as its own parameters; defaulting to `0` if omitted.

## Return value

Per `P_StartScript` and `P_GetScriptGoing` (`p_acs.cpp:13234-13288, 13055-13072`):

- **Same map, script found:** returns `true`, always spawns a new instance of the script, even if one is already running. Unlike plain `ACS_Execute`, there is no singleton/resume behavior.
- **Same map, script not found:** returns `false` plus a console message `"P_StartScript: Unknown script %d"`.
- **Different map:** returns `true` immediately and queues a deferred action (via `addDefered(..., defexealways, ...)`). The script will run once that map is actually entered, but there is no way to observe whether it ever actually succeeds or fails — the `true` return is not a success signal, only a queueing confirmation.
- **Unknown `map` number (non-zero, not found by `FindLevelByNum`):** returns `false` without deferring or printing a message. Indistinguishable by return value alone from "script not found on current map."

## Special behavior notes

- **Multiple concurrent instances:** unlike plain `ACS_Execute` (which is singleton — fails if already running, resumes if suspended), `ACS_ExecuteAlways` always spawns a fresh instance. The underlying mechanism is the `ACS_ALWAYS` flag passed to `P_StartScript`, which causes `P_GetScriptGoing` to skip the singleton check and always return a new script object (`p_acs.cpp:13055-13072`).

- **Scripts started with ExecuteAlways are not registered in `RunningScripts`:** as a side effect of the `ACS_ALWAYS` flag, the script instance is not added to the `RunningScripts` map (`p_acs.cpp:13130-13131`). This is the source-level fact behind the wiki's claim that "any scripts started with this special cannot be suspended or terminated with ACS_Suspend or ACS_Terminate." An attempt to suspend or terminate one by number silently fails because `P_SuspendScript`/`P_TerminateScript` lookup the script by number in that map and find nothing. Similarly, `NamedScriptWait` waits by checking for script registration in the same map — so waiting on a script that was started only with `ACS_ExecuteAlways` deadlocks forever (the script is genuinely running, but the wait sees it as "never started"). See [acs_terminate.md](acs_terminate.md), [namedscriptwait.md](namedscriptwait.md), and [suspend.md](suspend.md) for downstream consequences.

- **Clientside carve-out (Zandronum-only, not on ZDoom wiki):** on the server, if the target script is flagged `CLIENTSIDE` (e.g. a `CLIENTSIDE` script-type declaration), the server doesn't run it at all — instead it broadcasts `SERVERCOMMANDS_ACSScriptExecute(...)` and returns `true` unconditionally (`p_lnspec.cpp:1792-1798`), regardless of whether any client has or loads the script. This is the *same* polarity as plain `ACS_Execute` (both return `true`), but differs from `ACS_ExecuteWithResult`, which returns `false` in the same scenario.

## Contrast with related functions

- **vs. `ACS_Execute` (index 80):** `Execute` is singleton (fails if already running, resumes if suspended) and registers the script in `RunningScripts`, making it suspendable/terminable and waitable. `ExecuteAlways` always spawns a new instance, never resumes, and does not register in `RunningScripts`, making it immune to suspend/terminate/wait. Both support deferred cross-map execution and take a mandatory `map` parameter.
- **vs. `ACS_ExecuteWithResult` (index 84):** result variant runs synchronously in the caller's tic (blocking on any `Delay`/`Wait`, returning an intermediate value if the script blocks) and always executes on the current map, whereas `ExecuteAlways` runs asynchronously as a background task and supports deferred cross-map execution. Result variant also differs in clientside carve-out polarity (returns `false`/`0` instead of `true`) and takes only 4 arguments instead of 3.
- **vs. `Acs_NamedExecuteAlways` (extension function):** the named variant resolves the script name to a number first, then delegates to this action special machinery. See [Named script execution family](../families/script-execution.md) for the full comparison and shared traits, including the Zandronum clientside/netcode carve-out's consistent return polarity across the named family (all return `true` when handed off to clients, except for `ExecuteWithResult` which returns `false`/`0`).
- **vs. `ACS_Suspend`/`Acs_NamedSuspend` (action specials):** these are external suspend callsites — they reach the same `P_SuspendScript` machinery as the `suspend;` statement inside a script, but they can only affect scripts that are registered in `RunningScripts`, so they silently fail on `ExecuteAlways`-started scripts by design.

## Example

From the wiki: a health regeneration script in a sector that runs independently for each player because `ACS_ExecuteAlways` spawns separate instances.

```acs
int InSector[8];

script 10 (void)
{
    InSector[PlayerNumber()] = TRUE;

    while (InSector[PlayerNumber()]) {
        GiveInventory("HealthBonus", 1);
        ThingSound(0, "special/regen", 127);
        delay(15);
    }
}

script 11 (void)
{
    InSector[PlayerNumber()] = FALSE;
}
```

Script 10 is called by an "Actor Enters Sector" thing using `ACS_ExecuteAlways`. It sets a flag variable to true and loops until the flag is false. Script 11 is called by an "Actor Leaves Sector" thing using `ACS_ExecuteAlways`, and unsets the flag variable. Because this script is using `ACS_ExecuteAlways` instead of `ACS_Execute`, it is possible for multiple copies of the script to be active at once — one for each player in the game — each maintaining its own `InSector[player]` flag.
