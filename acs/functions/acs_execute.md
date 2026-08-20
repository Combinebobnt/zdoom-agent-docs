# ACS_Execute

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `ACS_Execute - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=ACS_Execute&oldid=38920`), verified 2026-07-29 against the Zandronum source's `src/p_lnspec.cpp` and `p_acs.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action special, index 80 in `zcommon.bcs`'s `special` table.

`int ACS_Execute(int script, int map [, int s_arg1, int s_arg2, int s_arg3])`

## Signature in this toolchain

`Acs_Execute(int,int;int,int,int):int` — in `zt-bcc`'s BCS signature, `map` is mandatory and the three script arguments are optional (after the `;`), unlike the ZDoom wiki's C-style prototype which shows all five as required. This means `ACS_Execute(5, 2)` compiles here, using the defaults `s_arg1=0, s_arg2=0, s_arg3=0`.

## Parameters

- `script` — script number to execute (numeric, not a name; use the numbered `ACS_Execute` special, not `Acs_NamedExecute`, if you need a script's TID-based selection via `arg0str`).
- `map` — map which contains the script, resolved via `FindLevelByNum` to a numeric MAPINFO `levelnum`. `0` means "the current map" and skips the lookup. **Non-zero and not found: returns `false` without deferring** (`p_lnspec.cpp:1773-1779`), silently indistinguishable from "script not found."
- `s_arg1, s_arg2, s_arg3` — three optional ints passed to the script as its own parameters; defaulting to `0` if omitted.

## Return value

Per `P_StartScript` and `P_GetScriptGoing` (`p_acs.cpp:13234-13288, 13055-13072`):

- **Same map, script found, not already running and not suspended:** returns `true`, starts a new instance.
- **Same map, script found, already suspended:** returns `true`, resumes the existing instance from the point immediately after where it suspended (via `PCD_SUSPEND` or `ACS_Suspend`/`Acs_NamedSuspend`). Locals, activator, and all state are preserved.
- **Same map, script found, already running (not suspended):** returns `false`. The call is silently rejected — only one instance of a script can run at a time when started with plain `ACS_Execute`. Use `ACS_ExecuteAlways` instead if you need multiple concurrent copies of the same script running.
- **Same map, script not found:** returns `false` plus a console message `"P_StartScript: Unknown script %d"`.
- **Different map:** returns `true` immediately and queues a deferred action (via `addDefered(..., defexecute, ...)`). The script will run once that map is actually entered, but there is no way to observe whether it ever actually succeeds or fails — the `true` return is not a success signal, only a queueing confirmation.
- **Unknown `map` number (non-zero, not found by `FindLevelByNum`):** returns `false` without deferring or printing a message. Indistinguishable by return value alone from "script not found on current map."

## Special behavior notes

- **Suspension/resume parity:** the plain non-"always" `ACS_Execute` is the only script-start function that resumes a suspended instance. The named variant `Acs_NamedExecute` uses the same mechanism (`p_acs.cpp:6339-6356` dispatches through `NamedACSToNormalACS[]` into this same action special), so the resume behavior is identical. In contrast, `ACS_ExecuteAlways` and `ACS_ExecuteWithResult` (and their named variants) always spawn a new instance and leave any previously-suspended script orphaned in `SCRIPT_Suspended` state, never to resume unless an older plain `ACS_Execute` call targets it directly.
- **Clientside carve-out (Zandronum-only, not on ZDoom wiki):** on the server, if the target script is flagged `CLIENTSIDE` (e.g. a `CLIENTSIDE` script-type declaration), the server doesn't run it at all — instead it broadcasts `SERVERCOMMANDS_ACSScriptExecute(...)` and returns `true` unconditionally (`p_lnspec.cpp:1762-1767`), regardless of whether any client has or loads the script. This differs from `ACS_ExecuteWithResult`, which returns `false` in the same scenario.
- **Cross-map does not guarantee execution:** maps must be reachable in the campaign for the deferred script to ever run. If the player never enters the target map, the script never executes. The wiki mentions this under "The two maps in question need to be part of the same cluster" but doesn't explain the underlying deferral mechanism.

## Contrast with related functions

- **vs. `ACS_ExecuteAlways`:** "Always" spawns a new instance even if one is already running; plain `ACS_Execute` is singleton (fails if already running, resumes if suspended).
- **vs. `ACS_ExecuteWithResult`:** result variant runs synchronously in the caller's tic (blocking on any `Delay`/`Wait`, returning an intermediate value if the script blocks), whereas plain `ACS_Execute` always returns immediately and the target script runs as a background task.
- **vs. `ACS_Suspend`/`Acs_NamedSuspend`:** suspend *terminates* a script without destroying it (places it in `SCRIPT_Suspended`), and can be called from outside the script; plain `suspend;` inside the script does the same thing. Plain `ACS_Execute` is the only entry point that resumes a suspended instance.
- **vs. the named variants `Acs_NamedExecute`/`Acs_NamedExecuteWithResult`:** the named variants resolve the script name to a number first, then delegate to the same action special machinery. See [Named script execution family](families/script-execution.md) for the Zandronum clientside/netcode carve-out's different return polarities across the named family.
