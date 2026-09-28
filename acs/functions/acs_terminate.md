# ACS_Terminate

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `ACS_Terminate - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=ACS_Terminate&oldid=35856`), verified 2026-07-29 against the Zandronum source's `src`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

`bool Acs_Terminate(int script, int map)`

## Bucket

Action special (index 82), `LS_ACS_Terminate` in `p_lnspec.cpp:1866`. This is the underlying numbered-script implementation; the named variant `ACS_NamedTerminate` (extension function `-41`) dispatches to this same code path after resolving the script name to a number (see `NamedACSToNormalACS[]` in `p_lnspec.cpp:86`).

## Parameters

- `script` — numeric script ID to terminate.
- `map` — map containing the script, passed to `FindLevelByNum` to resolve a map-info level number, **not a lump name**. `map == 0` means "the current map" (`level.mapname`).

## Return value

Per the wiki: "Returns true in all cases." **This is accurate but is not a success signal** — `LS_ACS_Terminate` returns `true` unconditionally, whether or not anything was actually terminated:

- If `map` names a level not found by `FindLevelByNum`, the function silently does nothing and still returns `true`.
- If `map` resolves (or is `0`/current map) but no script with that number is currently *running*, `SetScriptState` (`p_acs.cpp:13143`) looks the script up in the active `DACSThinker`'s `RunningScripts` map, finds nothing, and silently no-ops — again with `true` already returned.

So a script typo, a script that already finished, or a bad map number are all indistinguishable from a successful terminate by return value alone.

## Restriction on ExecuteAlways and ENTER scripts

The wiki states: "You may not terminate scripts that were executed using the `ACS_ExecuteAlways` special or ENTER scripts."

**Mechanism:** This restriction is enforced via `RunningScripts` map indexing, not an explicit guard. When a script is started:

- **Registered starts:** the `DLevelScript` constructor (`p_acs.cpp:13130-13131`) inserts the script into `DACSThinker::ActiveThinker->RunningScripts[script_number]` only when the start lacks the `ACS_ALWAYS` flag. That covers `ACS_Execute`, `ACS_LockedExecute`/`ACS_LockedExecuteDoor` (which call `LS_ACS_Execute`) and their named forms, plus the OPEN, UNLOADING and LIGHTNING script types. UZDoom also starts REOPEN scripts this way.
- **Unregistered starts:** `ACS_ExecuteAlways`, `ACS_ExecuteWithResult` (Zandronum `p_lnspec.cpp:1790`, `1840`) and most typed scripts carry `ACS_ALWAYS`, so the constructor skips the insertion. `StartTypedScripts` maps its `always` argument to `ACS_ALWAYS` (`p_acs.cpp:3413`), and ENTER (e.g. `g_game.cpp:4286`, `sv_main.cpp:1680`), RETURN, RESPAWN, DEATH, KILL and DISCONNECT scripts are all started with `always=true` on both engines. On Zandronum the EVENT, PICKUP and team-return script types are too. A `puke` with a negative script number is also an always-start.

So the wiki's restriction is narrower than the real one: only the registered starts above can be terminated.

`SetScriptState` (`p_acs.cpp:13143`) calls `RunningScripts.CheckKey(num)`, which returns NULL for scripts never inserted in the first place. The no-op is thus silent and harmless.

## Cross-map behavior

`P_TerminateScript` (`p_acs.cpp:13298`) compares `map` against `level.mapname`:

- **Same map:** acts immediately via `SetScriptState(script, SCRIPT_PleaseRemove)` (see the removal timing below).
- **Different map:** does not terminate anything now. It queues a deferred action (`addDefered(..., acsdefered_t::defterminate, ...)`) that fires only if/when that target map is actually entered later (`P_DoDeferedScripts`, `p_acs.cpp:13190`). This is the same deferred-execution mechanism `ACS_Execute`/`ACS_Suspend` use for cross-map targets.

## Zandronum-specific: CLIENTSIDE termination asymmetry

No server-side broadcast exists for script termination (no `SERVERCOMMANDS_ACSScriptTerminate`). On a server, the ACS execute specials (`LS_ACS_Execute`, `LS_ACS_ExecuteAlways`, `LS_ACS_ExecuteWithResult`) and `StartTypedScripts` never start a `CLIENTSIDE` script locally. They hand it to clients with `SERVERCOMMANDS_ACSScriptExecute` instead (e.g. `p_lnspec.cpp:1762-1767`, `p_acs.cpp:3404-3411`). A server-side terminate of a `CLIENTSIDE` script started through those paths therefore finds nothing in the server's `RunningScripts`, silently no-ops, and tells clients nothing. (A server-console `puke` does start one on the server, `c_cmds.cpp:794-797`.) The client's instance keeps running until it finishes or a terminate call runs on that client.

That client-side call only works for some starts. The client starts the broadcast script with the `always` flag the server sent (`cl_main.cpp:7192`), so a `CLIENTSIDE` script the server started via `ACS_ExecuteAlways`, `ACS_ExecuteWithResult` or a typed start (ENTER etc.) is unregistered on the client too and can't be terminated there either. Only one started via plain `ACS_Execute` or a locked variant is registered client-side. This asymmetry is undocumented on the ZDoom wiki and is a Zandronum multiplayer peculiarity.

## Removal timing

`SetScriptState` only marks the target `SCRIPT_PleaseRemove`; the script thinker does the removal. The target runs no further p-codes after the call, because the interpreter loop in `DLevelScript::RunScript` only runs while the state is `SCRIPT_Running`. It is unlinked the next time the thinker reaches it (`p_acs.cpp:13028-13037`), which is later in the same tic if it sits after the caller in the thinker list, otherwise the next tic.
