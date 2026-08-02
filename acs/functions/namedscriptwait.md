# `void NamedScriptWait(str script)`

**Bucket:** compiler builtin (`zt-bcc/src/builtin.c:166`, `{ "namedscriptwait", ";s" }` — one
required string arg, matches the wiki's signature exactly; table-flagged
`PCD_SCRIPTWAITNAMED | F_LATENT` at `builtin.c:314`, marking it latent/script-suspending).
Implemented as `PCD_SCRIPTWAITNAMED` in `p_acs.cpp` (`10672-10675`), which shares its state
machine entirely with `PCD_SCRIPTWAIT`/`PCD_SCRIPTWAITDIRECT` (the numbered-script variant) via a
shared `scriptwait:` label.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `NamedScriptWait - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=NamedScriptWait&oldid=36650`), verified against
the Zandronum source's `src/p_acs.cpp` on 2026-07-29. The wiki page is thin (one usage line, no
examples) and its wording — "if the specified script is not running, this command will wait
until it has run" — reads ambiguously (does "not running" mean "already finished, so return
immediately"?) but is in fact accurate once you read the implementation: everything below comes
from tracing `PCD_SCRIPTWAITNAMED` and the `SCRIPT_ScriptWaitPre`/`SCRIPT_ScriptWait` state
handlers, plus `P_GetScriptGoing`/`DLevelScript`'s constructor for the `ACS_ALWAYS` caveat, none
of which the wiki page mentions at all.

Delays the calling script until an instance of the *named* script has both started and finished
running, as tracked by the level's `RunningScripts` map. For numbered scripts, the equivalent is
`ScriptWait`.

- **Name resolution / shared keyspace:** `PCD_SCRIPTWAITNAMED` resolves the string to
  `-FName(...)` (`p_acs.cpp:10673`) — the same negative-`FName` numeric encoding used everywhere
  else in the engine to identify a *named* script (a named script's own `ScriptPtr::Number` is
  negative; a numbered script's is positive/non-negative — see `p_acs.cpp:3012`, `3466`,
  `13900`). Because of this, named and numbered scripts occupy disjoint sign ranges in
  `RunningScripts`, so `NamedScriptWait("Foo")` can never accidentally match a numbered script.
- **Two-phase wait, polled once per tic** (`p_acs.cpp:9190-9203`):
  - If no instance of the named script is present in `RunningScripts` at the moment the call
    executes, the caller enters `SCRIPT_ScriptWaitPre` and blocks — with no timeout — until *some*
    instance of that script appears in `RunningScripts` (i.e. starts running), then automatically
    advances to `SCRIPT_ScriptWait` to wait for that instance to finish.
  - If an instance is already running, the caller skips straight to `SCRIPT_ScriptWait`.
  - Either way, resumption requires the instance to be *removed* from `RunningScripts` (finishes
    normally, is terminated, or errors out) — not merely "has been called" or "has run once in the
    past." A script that already ran to completion *before* `NamedScriptWait` was called does not
    satisfy the wait; from the waiter's perspective that's indistinguishable from "not running,"
    so it will block for an entirely new future start+finish cycle.
- **No existence check — a wrong or never-triggered name deadlocks forever, silently.** There is
  no validation that `script` names any script that will ever actually run in the loaded modules.
  A typo, wrong module, or a script gated behind a condition that never fires leaves the caller
  stuck in `SCRIPT_ScriptWaitPre` permanently — no error, no console message, no timeout.
- **`ACS_(Named)ExecuteAlways`-started scripts are invisible to this wait and will deadlock it.**
  `DLevelScript`'s constructor only registers a script in `RunningScripts` `if (!(flags &
  ACS_ALWAYS))` (`p_acs.cpp:13130`), and `P_GetScriptGoing`'s already-running check is likewise
  skipped `if (!(flags & ACS_ALWAYS))` (`p_acs.cpp:13061`) — i.e. scripts launched via
  `ACS_ExecuteAlways`/`ACS_NamedExecuteAlways` (or the line special `LS_ACS_ExecuteAlways`) never
  enter `RunningScripts` at all, even while genuinely executing, and can have unlimited concurrent
  instances. `NamedScriptWait` on a script that is *only ever* started this way will sit in
  `SCRIPT_ScriptWaitPre` forever, even though the target script is running (repeatedly) the whole
  time. This is a real footgun for a project this scripted, if a named script's only launch site
  is ever changed to the `Always` variant (e.g. to allow re-triggering) without checking whether
  something elsewhere `NamedScriptWait`s on it.
- **Scheduling:** entering either wait state calls `PutLast()` (`p_acs.cpp:10664`), moving the
  waiting script to the end of this tic's script execution order — the same scheduling nudge
  `ScriptWait`/`PolyWait` use. On the tic the wait is satisfied, `SCRIPT_ScriptWait`'s handler
  calls `PutFirst()` instead (`p_acs.cpp:9202`) and falls straight into the bytecode loop that same
  `RunScript()` invocation (`p_acs.cpp:9226`, `while (state == SCRIPT_Running)`) — i.e. once
  unblocked, the waiter resumes executing on the very tic it detects completion, not the tic after.
- **Latent/blocking-function family:** like `Delay`/`TagWait`/`PolyWait`/`ScriptWait`/`Suspend`,
  this changes `state` away from `SCRIPT_Running` and exits `RunScript()`'s bytecode loop early —
  see [SetResultValue](setresultvalue.md) for why a synchronous `Acs_(Named)ExecuteWithResult`
  caller only ever observes the result value as of the *first* such block.
