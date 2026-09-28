# ACS_Execute

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `ACS_Execute - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=ACS_Execute&oldid=38920`), verified 2026-07-29 against the Zandronum source's `src/p_lnspec.cpp` and `p_acs.cpp`; clientside path also checked against `src/cl_main.cpp:7163-7192` and `protocolspec/spec.misc.txt:1-12`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action special, index 80 in `zcommon.bcs`'s `special` table.

`int ACS_Execute(int script, int map [, int s_arg1, int s_arg2, int s_arg3])`

## Signature in this toolchain

`Acs_Execute(int,int;int,int,int):int` — in `zt-bcc`'s BCS signature, `map` is mandatory and the three script arguments are optional (after the `;`), unlike the ZDoom wiki's C-style prototype which shows all five as required. This means `ACS_Execute(5, 2)` compiles here, using the defaults `s_arg1=0, s_arg2=0, s_arg3=0`.

## Parameters

- `script` — script number to execute. To start a named script, use `ACS_NamedExecute` instead.
- `map` — map which contains the script, resolved via `FindLevelByNum` to a numeric MAPINFO `levelnum`. `0` means "the current map" and skips the lookup. **Non-zero and not found: returns `false` without deferring** (`p_lnspec.cpp:1773-1779`), silently indistinguishable from "script not found."
- `s_arg1, s_arg2, s_arg3` — three optional ints passed to the script as its own parameters; defaulting to `0` if omitted.

## Return value

Per `P_StartScript` and `P_GetScriptGoing` (`p_acs.cpp:13234-13288, 13055-13072`):

- **Same map, script found, not already running and not suspended:** returns `true`, starts a new instance.
- **Same map, script found, already suspended:** returns `true`, resumes the existing instance from the point immediately after where it suspended (via `PCD_SUSPEND` or `ACS_Suspend`/`Acs_NamedSuspend`). Locals, activator, and all state are preserved. The new call's `s_arg` values are ignored.
- **Same map, script found, already running (not suspended):** returns `false`. The call is silently rejected — only one instance of a script can run at a time when started with plain `ACS_Execute`. Use `ACS_ExecuteAlways` instead if you need multiple concurrent copies of the same script running. Only instances started without the "always" flag are tracked for this check (`p_acs.cpp:13130-13131`). A copy started by `ACS_ExecuteAlways` or `ACS_ExecuteWithResult` doesn't count, so plain `ACS_Execute` starts a fresh instance alongside it.
- **Same map, script not found:** returns `false` and prints `P_StartScript: Unknown script N` to the console (`script "name"` for a named script).
- **Different map:** returns `true` immediately and queues a deferred action (via `addDefered(..., defexecute, ...)`). The script will run once that map is actually entered, but there is no way to observe whether it ever actually succeeds or fails — the `true` return is not a success signal, only a queueing confirmation. The deferral only remembers a player activator. Any other activator becomes none (world), and the deferred script runs with no activation line (`p_acs.cpp:13219-13226`, `13172-13177`).
- **Unknown `map` number (non-zero, not found by `FindLevelByNum`):** returns `false` without deferring or printing a message. Indistinguishable by return value alone from "script not found on current map."

## Special behavior notes

- **Suspension/resume parity:** among the script-start specials, only `ACS_Execute` and the specials built on it resume a suspended instance. `ACS_LockedExecute` and `ACS_LockedExecuteDoor` call it after their key check (`p_lnspec.cpp:1815-1831`). The named variant `Acs_NamedExecute` uses the same mechanism (`p_acs.cpp:6339-6356` dispatches through `NamedACSToNormalACS[]` into this same action special), so the resume behavior is identical. In contrast, `ACS_ExecuteAlways` and `ACS_ExecuteWithResult` (and their named variants) always spawn a new instance and leave any previously-suspended script orphaned in `SCRIPT_Suspended` state, never to resume unless a later plain `ACS_Execute` call targets it directly. A copy started by one of those "always" calls that suspends itself can never be resumed, since it isn't tracked by script number.
- **Clientside carve-out (Zandronum-only, not on ZDoom wiki):** when running as a server, if the target script is clientside, the server doesn't run it at all. It broadcasts `SERVERCOMMANDS_ACSScriptExecute(...)` and returns `true` unconditionally (`p_lnspec.cpp:1762-1767`), regardless of whether any client has or loads the script. This differs from `ACS_ExecuteWithResult`, which returns `false` in the same scenario. Offline play and clients skip this branch and take the normal path above. "Clientside" means a `CLIENTSIDE` script, or a `NET` script when `ZACOMPATF_NETSCRIPTS_ARE_CLIENTSIDE` is set (`p_acs.cpp:13684-13697`). The test looks the script up on the current map before `map` is examined. Each client then resolves `map` itself (`cl_main.cpp:7163-7192`), but the command carries it as a `Byte` (`protocolspec/spec.misc.txt:5`), so map numbers above 255 reach clients truncated.
- **Cross-map does not guarantee execution:** maps must be reachable in the campaign for the deferred script to ever run. If the player never enters the target map, the script never executes. The wiki mentions this under "The two maps in question need to be part of the same cluster" but doesn't explain the underlying deferral mechanism.

## Contrast with related functions

- **vs. `ACS_ExecuteAlways`:** "Always" spawns a new instance even if one is already running; plain `ACS_Execute` is singleton (fails if already running, resumes if suspended).
- **vs. `ACS_ExecuteWithResult`:** result variant runs the script immediately in the caller's tic until it finishes or first waits. The caller doesn't block: it gets whatever result value was set at that point, and a waiting script carries on in the background. By contrast, plain `ACS_Execute` always returns immediately and the target script runs as a background task.
- **vs. `ACS_Suspend`/`Acs_NamedSuspend`:** suspend pauses a script without destroying it (places it in `SCRIPT_Suspended`), and can be called from outside the script; plain `suspend;` inside the script does the same thing. Plain `ACS_Execute` (and the locked and named variants built on it) is the only entry point that resumes a suspended instance.
- **vs. the named variants `Acs_NamedExecute`/`Acs_NamedExecuteWithResult`:** the named variants resolve the script name to a number first, then delegate to the same action special machinery. See [Named script execution family](../families/script-execution.md) for the Zandronum clientside/netcode carve-out's different return polarities across the named family.
