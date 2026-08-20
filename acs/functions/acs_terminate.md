# ACS_Terminate

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `ACS_Terminate - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=ACS_Terminate&oldid=35856`), verified 2026-07-29 against the Zandronum source's `src`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

`bool Acs_Terminate(int script, int map)`

## Bucket

Action special (index 82), `LS_ACS_Terminate` in `p_lnspec.cpp:1866`. This is the underlying numbered-script implementation; the named variant `ACS_NamedTerminate` (extension function `-41`) dispatches to this same code path after resolving the script name to a number (see `NamedACSToNormalACS[]` in `p_lnspec.cpp:86`).

## Parameters

- `script` — numeric script ID to terminate.
- `map` — map containing the script, passed to `FindLevelByNum` to resolve a map-info level number, **not a lump name**. `map == 0` means "the current map" (`level.mapname`).

## Return value

Per the wiki: "Returns true in all cases." **This is accurate but is not a success signal** — `LS_ACS_Terminate` returns `true` unconditionally, before knowing whether anything was actually terminated:

- If `map` names a level not found by `FindLevelByNum`, the function silently does nothing and still returns `true`.
- If `map` resolves (or is `0`/current map) but no script with that number is currently *running*, `SetScriptState` (`p_acs.cpp:13143`) looks the script up in the active `DACSThinker`'s `RunningScripts` map, finds nothing, and silently no-ops — again with `true` already returned.

So a script typo, a script that already finished, or a bad map number are all indistinguishable from a successful terminate by return value alone.

## Restriction on ExecuteAlways and ENTER scripts

The wiki correctly states: "You may not terminate scripts that were executed using the `ACS_ExecuteAlways` special or ENTER scripts."

**Mechanism:** This restriction is enforced via `RunningScripts` map indexing, not an explicit guard. When a script is started:

- **Normal execution** (`ACS_Execute`, non-ENTER scripts): inserted into `DACSThinker::ActiveThinker->RunningScripts[script_number]` by the `DLevelScript` constructor (`p_acs.cpp:13130-13131`).
- **ACS_ExecuteAlways or ENTER scripts**: started with the `ACS_ALWAYS` flag, which **skips the `RunningScripts` insertion** (`p_acs.cpp:13130: `if (!(flags & ACS_ALWAYS))`). ENTER scripts are dispatched via `FBehavior::StaticStartTypedScripts(SCRIPT_Enter, ...)` with `always=true` (e.g., `g_game.cpp:4286`, `sv_main.cpp:1680`).

`SetScriptState` (`p_acs.cpp:13143`) calls `RunningScripts.CheckKey(num)`, which returns NULL for scripts never inserted in the first place. The no-op is thus silent and harmless.

## Cross-map behavior

`P_TerminateScript` (`p_acs.cpp:13298`) compares `map` against `level.mapname`:

- **Same map:** terminates immediately — `SetScriptState(script, SCRIPT_PleaseRemove)`.
- **Different map:** does not terminate anything now. It queues a deferred action (`addDefered(..., acsdefered_t::defterminate, ...)`) that fires only if/when that target map is actually entered later (`P_DoDeferedScripts`, `p_acs.cpp:13190`). This is the same deferred-execution mechanism `ACS_Execute`/`ACS_Suspend` use for cross-map targets.

## Zandronum-specific: CLIENTSIDE termination asymmetry

No server-side broadcast exists for script termination (no `SERVERCOMMANDS_ACSScriptTerminate`). Terminating a `CLIENTSIDE` script server-side does **not** stop the client's running instance — only the server's state changes. Client termination requires the script to finish on its own or the client to execute its own termination call. This asymmetry is undocumented on the ZDoom wiki and is a Zandronum multiplayer peculiarity.

The `SCRIPT_PleaseRemove` state request is processed by the script thinker (not an instant kill) — termination is effectively "next tic" rather than synchronous.
