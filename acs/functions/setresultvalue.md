# `void SetResultValue(int value)`

**Bucket:** compiler builtin (`zt-bcc/src/builtin.c:119`, `{ "setresultvalue", ";i" }` — one
required int arg, no optional args; matches the wiki's signature exactly). Implemented as
`PCD_SETRESULTVALUE` in `p_acs.cpp`.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

Sets the calling script's own "result value" — the `int` that a synchronous
`Acs_ExecuteWithResult`/`Acs_NamedExecuteWithResult` caller receives back, or that a switch-line
`ACS_ExecuteWithResult` special reads to decide whether to flip the texture/play the sound. See
the [Named script execution family](../families/script-execution.md) for the full mechanics of
the *reading* side (`Acs_NamedExecuteWithResult`) — this page only covers `SetResultValue` itself.

- **Bytecode-level detail:** `PCD_SETRESULTVALUE` (`p_acs.cpp:10461-10470`) stores `STACK(1)` into
  the interpreter-local `resultValue`, then **falls through into the `PCD_DROP` case** to pop the
  stack — i.e. it's implemented as "peek, save, drop," not a dedicated pop. No externally
  observable difference from a real pop; noted here only so a future reader grepping the switch
  isn't confused by the fallthrough.
- **The wiki's "must call before any blocking function" rule is exactly right, and here's why
  mechanically:** `DLevelScript::RunScript()` (`p_acs.cpp:9120-13051`) initializes a local
  `int resultValue = 1` on every invocation and runs the bytecode loop only `while (state ==
  SCRIPT_Running)`. The moment a blocking opcode (`PCD_DELAY`/`PCD_TAGWAIT`/`PCD_POLYWAIT`/
  `PCD_SCRIPTWAIT`/`PCD_SUSPEND`, etc.) changes `state` away from `SCRIPT_Running`, the loop exits
  and the function falls straight through to `return resultValue;` (`p_acs.cpp:13050`) —
  whatever `SetResultValue` last stored *before that point*, or the `1` default if it was never
  called. For a **synchronous** caller (`Acs_(Named)ExecuteWithResult`, which calls `RunScript()`
  directly rather than queueing the script), that returned value is final — the script keeps
  running in later tics after unblocking, but nothing re-reads `resultValue` for that already-
  completed call. A `SetResultValue` call issued after the script resumes from its first block
  has no way to reach the original caller.
- **Zandronum-only side effect: `SetResultValue` inside an `EVENT` script can silently mutate the
  shared event result, but only on the script's first tic.** (`p_acs.cpp:9150-9158,10464-10468`,
  tagged `[AK]` — not in ZDoom, which has no `EVENT` script type at all.) Mechanism:
  - `RunScript()` tracks `bIsFirstTic`, true only on entry via `case SCRIPT_Running:` (i.e. the
    very first tic a given script instance runs, before it has ever blocked) — see
    `p_acs.cpp:9150-9158`.
  - On that first tic, if `ACS_IsEventScript(script)` is true (`pScriptData->Type == SCRIPT_Event`,
    `p_acs.cpp:13662-13671`), `resultValue` is pre-seeded from `GAMEMODE_GetEventResult()` instead
    of the usual literal `1` — so an `EVENT` script's result value doesn't start at `1`, it starts
    at whatever the *previous* event script (or the event dispatcher itself) left in the shared
    slot.
  - Then, still gated on `bIsFirstTic`, every `PCD_SETRESULTVALUE` that differs from the current
    `GAMEMODE_GetEventResult()` calls `GAMEMODE_SetEventResult(resultValue)`
    (`p_acs.cpp:10467-10468`) — a plain global (`g_lEventResult`, `gamemode.cpp:1369-1379`) that
    `GAMEMODE_HandleEvent()` reads back to decide the event's outcome and that chains to the next
    `EVENT` script handling the same event (see the "Result-value chaining" note in
    [EVENT scripts](../concepts/event-scripts.md)).
  - **Once the script blocks and comes back on a later tic, `bIsFirstTic` is false for the rest of
    its life** (it's a local reset to `false` by default on every `RunScript()` call and only ever
    set `true` in the `SCRIPT_Running`-entry branch) — so a `SetResultValue` call made after an
    `EVENT` script's first `Delay`/wait still updates the *return value* mechanism described above,
    but **no longer propagates into the shared game-event result**, silently. This is a second,
    independent way `SetResultValue`'s effect can go stale after the first block — on top of the
    ordinary synchronous-caller case above, `EVENT` scripts have this extra gate.
  - `GetEventResult()` (extension function, `zcommon.bcs:1782`, ACSF -152) is the read side of this
    same global — already noted in passing in
    [EVENT scripts](../concepts/event-scripts.md), which is why that page's own mention of
    `SetResultValue` is kept short and defers here for the mechanism.
- **No range/type validation** — `value` is stored as a plain `int`/`LONG`; any value compiles and
  runs, including negative numbers or values outside a `bool`-like `0`/`1` range (relevant for the
  switch-special use case, which the wiki says only special-cases exactly `0`).

**Example** (from the wiki, unmodified):

```
script 1 (void)
{
    Print(d:ACS_ExecuteWithResult(2, 0, 0, 0)); //prints 667
}

script 2 (void)
{
    SetResultValue(667);
}
```

**Provenance:** wiki page `SetResultValue - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`oldid=48425`) + source-verified against `zt-bcc/src/builtin.c:119` and the Zandronum source
(`p_acs.cpp:9120-9158,10461-10470,13050,13662-13671`, `gamemode.cpp:1369-1379`,
`gamemode.h:249-250`).
