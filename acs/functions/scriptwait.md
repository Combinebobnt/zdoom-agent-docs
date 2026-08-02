# `void ScriptWait(int script)`

**Bucket:** compiler builtin (`zt-bcc/src/builtin.c:44`, `{ "scriptwait", ";i" }` — one required
int arg, matches the wiki's signature exactly; table-flagged `PCD_SCRIPTWAIT | F_LATENT` at
`builtin.c:192`, marking it a *latent* — i.e. potentially script-suspending — call. There's also a
`PCD_SCRIPTWAITDIRECT` opcode the compiler emits instead when the argument is a compile-time
constant — same runtime behavior, just skips a stack push). Implemented in `p_acs.cpp`. The
sibling `NamedScriptWait(str)` (`PCD_SCRIPTWAITNAMED`) shares the exact same state machine below —
see that function's own doc for name-specific details; not duplicated here.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `ScriptWait - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=ScriptWait&oldid=35861`), verified against
the Zandronum source's `src/p_acs.cpp` on 2026-07-29. The wiki's usage line is accurate as far as it
goes, but understates a real footgun (see "Can't tell 'never started' from 'already finished'"
below) that only shows up by reading `RunningScripts`' lifecycle in the engine source.

Suspends the calling script until the script numbered `script` is no longer running — waiting for
it to *start* first if it isn't already running when `ScriptWait` is called.

- **Mechanism — two-state wait:** `PCD_SCRIPTWAIT`/`PCD_SCRIPTWAITDIRECT` (`p_acs.cpp:10656-10670`)
  store `script` into the interpreter's `statedata` and pick the entry state via a single check:
  if `controller->RunningScripts.CheckKey(statedata) != NULL` (i.e. a script with that number is
  currently active), enter `SCRIPT_ScriptWait`; otherwise enter `SCRIPT_ScriptWaitPre`
  (`p_acs.cpp:9190-9203`):
  - `SCRIPT_ScriptWaitPre` — polled once per tic; as soon as `RunningScripts` gains an entry for
    `script`, transitions to `SCRIPT_ScriptWait`. Otherwise stays parked here indefinitely.
  - `SCRIPT_ScriptWait` — polled once per tic; as soon as `RunningScripts` *no longer* has an
    entry for `script` (the target finished, terminated, or errored out — anything that hits
    `SCRIPT_PleaseRemove`, `p_acs.cpp:13028-13037`, removes it from `RunningScripts`), transitions
    back to `SCRIPT_Running` and calls `PutFirst()` so the newly-woken script is scheduled ahead of
    everything else already in the tic's run list — it can execute its resumed bytecode in the
    same tic the target script finished, rather than waiting for the following tic.
- **`RunningScripts` only reflects "currently executing," with no history.** A script number is
  added to `RunningScripts` when it starts (`p_acs.cpp:13131`) and removed the moment it stops
  (`p_acs.cpp:13035`, on `SCRIPT_PleaseRemove` — natural completion, `Terminate`, or a runtime
  error alike). There is no separate "has this script ever run" flag.
- **Can't tell "never started" from "already finished" — the real gotcha.** Because
  `SCRIPT_ScriptWaitPre` only asks "is it running *right now*," calling `ScriptWait(N)` *after*
  script `N` has already run to completion looks identical, from the interpreter's point of view,
  to calling it *before* script `N` ever started: both see `RunningScripts.CheckKey(N) == NULL`
  and enter `SCRIPT_ScriptWaitPre`, which then waits for `N` to start. If `N` was a once-only
  script (the wiki's own motivating example — a script that unlocks a door and is never triggered
  again), a `ScriptWait(N)` issued too late — after `N` already fired and finished — will **block
  the caller forever**, since `N` is never going to start again. The wiki's phrasing ("If the
  specified script is not running, this command will wait until it has run") reads as if this case
  is handled; it isn't distinguished at all from the true "not started yet" case. Callers relying
  on this pattern need external ordering/state (e.g. a global bool flag, as the wiki's own example
  actually uses *in addition to* `ScriptWait`) to be safe against the target having already
  finished by the time the wait is issued.
- **Latent/blocking-function family:** `PCD_SCRIPTWAIT` is one of the opcodes (alongside
  `PCD_DELAY`/`PCD_TAGWAIT`/`PCD_POLYWAIT`/`PCD_SUSPEND`) that changes `state` away from
  `SCRIPT_Running` and exits `RunScript()`'s bytecode loop early — see
  [SetResultValue](setresultvalue.md) for why a synchronous `Acs_(Named)ExecuteWithResult` caller
  only ever observes the result value as of the *first* such block.
