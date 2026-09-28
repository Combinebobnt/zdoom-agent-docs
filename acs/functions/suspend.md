# `suspend;`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `Suspend - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=Suspend&oldid=55228`), verified against
the Zandronum source's `src/p_acs.cpp` and the zt-bcc source's `src` on 2026-07-29. The wiki's core claim
("picks up where it left off... only works properly with `ACS_Execute`... `ACS_ExecuteWithResult`
and `ACS_ExecuteAlways` restart from the beginning instead") checks out exactly against the C++,
traced below. Corrections backed by Zandronum `p_lnspec.cpp:1762-1767, 1815-1831, 1853-1864`,
`p_acs.cpp:13130-13131` and `cl_main.cpp:7192`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** none of the three — this is a **compiler statement/keyword**, not a callable function
at all. `suspend` never appears in `zt-bcc/src/builtin.c`'s `g_funcs[]` (compiler-builtin bucket)
or `zcommon.bcs`'s `special` table (action-special/extension-function buckets); it's tokenized as
`TK_SUSPEND` and parsed directly by the statement grammar (`read_script_jump()` in
`zt-bcc/src/parse/stmt.c:567-583`, alongside `terminate`/`restart` — `semantic/stmt.c:869`'s
`SCRIPT_JUMP_TOTAL` triple). No parentheses, no arguments, bare `suspend;`. Compiles straight to
the zero-operand opcode `PCD_SUSPEND` (`zt-bcc/src/codegen/pcode.h:7`, emitted at
`zt-bcc/src/codegen/stmt.c:1146-1148`).

Unlike `restart;` (a `goto` back to the top of the same script instance) or `terminate;`
(destroys the script instance), `suspend;` just parks the *same* running `DLevelScript` C++
object: `PCD_SUSPEND` (`p_acs.cpp:9262-9264`) sets `state = SCRIPT_Suspended`, which drops out of
`RunScript()`'s `while (state == SCRIPT_Running)` loop. Because `state` is not
`SCRIPT_PleaseRemove`, the object is *not* unlinked or destroyed (`p_acs.cpp:13038-13042`):
`this->pc = pc;` saves the exact resume point, and the object — with its `localvars`, `activator`,
`activationline`, `backSide`, everything — simply sits alive and idle. This is the mechanism
behind the wiki's "leaves a marker in memory": there is no separate marker, the entire suspended
script instance itself is the marker.

- **Compile-time restriction (not on the wiki):** legal only directly inside a script body, never
  inside a function and never inside a string message-building block
  (`test_script_jump()`, `zt-bcc/src/semantic/stmt.c:867-880`) — `bcc` rejects it with `"suspend
  statement outside script"` otherwise, same restriction as bare `terminate;`/`restart;`.
- **Resuming only happens through the plain, non-"always" script-start path, and this is a hard
  fork-level branch, not a convention:** every script-start entry point (`ACS_Execute` the action
  special, `Acs_NamedExecute` the extension function, etc.) funnels into
  `P_GetScriptGoing` (`p_acs.cpp:13055-13072`), usually via `P_StartScript`. That function's very first
  check is `!(flags & ACS_ALWAYS)` — only when the `ACS_ALWAYS` flag is *absent* does it look the
  script number up in `DACSThinker::RunningScripts`, find the still-alive suspended instance, flip
  its state back to `SCRIPT_Running`, and return *that same object* (so it resumes at the saved
  `pc` with all locals/activator intact). If `ACS_ALWAYS` is set, that lookup is skipped
  unconditionally and a brand-new `DLevelScript` is constructed instead — fresh `localvars`
  (zeroed then re-populated from the new call's `args[]`, `p_acs.cpp:13084-13089`), fresh
  `activator`, `pc` reset to the script's start.
- **Confirms exactly which entry points set `ACS_ALWAYS`, verified by grep, not assumption:**
  - `LS_ACS_Execute` (`p_lnspec.cpp:1753`, the plain numbered `ACS_Execute` special) — flags
    `= (backSide ? ACS_BACKSIDE : 0)`, **no** `ACS_ALWAYS`. Of the three specials here, this is
    the only one that resumes a suspended instance. `ACS_LockedExecute`/`ACS_LockedExecuteDoor`
    (`p_lnspec.cpp:1815-1831`) call it after their key check, so they resume too.
  - `LS_ACS_ExecuteAlways` (`p_lnspec.cpp:1784`) — flags include `ACS_ALWAYS` explicitly. Always
    starts a new instance; a previously-suspended one is simply ignored (it stays parked until
    something else resumes or terminates it). The new instance doesn't displace it: the
    constructor registers an instance in `RunningScripts` only when `ACS_ALWAYS` is absent
    (`p_acs.cpp:13130-13131`), so a later plain `ACS_Execute` still finds and resumes the old one.
    The flip side is what makes the wiki's "only works properly with `ACS_Execute`" true. An
    instance started with `ACS_ExecuteAlways`/`ACS_ExecuteWithResult` that hits its own
    `suspend;` is never findable by number, so no `ACS_Execute` resumes it and no
    `ACS_Terminate`/`ACS_Suspend` reaches it. It never runs again.
  - `LS_ACS_ExecuteWithResult` (`p_lnspec.cpp:1833`) — flags include `ACS_ALWAYS | ACS_WANTRESULT`
    (the comment there literally says "This is like `ACS_ExecuteAlways`, except..."). Same
    always-fresh-instance behavior.
  - `Acs_NamedExecute`/`Acs_NamedExecuteWithResult`/`Acs_NamedExecuteAlways` (the `ACSF_ACS_Named*`
    extension functions, `p_acs.cpp:6339-6356`) all dispatch through `NamedACSToNormalACS[]` into
    the *same* `LS_ACS_Execute`/`LS_ACS_ExecuteAlways`/`LS_ACS_ExecuteWithResult` action specials
    above — no separate code path, so the same `ACS_ALWAYS` split applies identically to the named
    variants. `Acs_NamedLockedExecute`/`Acs_NamedLockedExecuteDoor` map the same way onto the
    locked specials, so they resume too.
  - On a Zandronum server, the three specials hand a `CLIENTSIDE` script to clients with
    `SERVERCOMMANDS_ACSScriptExecute` instead of starting it (`p_lnspec.cpp:1762-1767`,
    `1793-1798`, `1843-1848`). The client rebuilds `ACS_ALWAYS` from the command's always flag
    (`cl_main.cpp:7192`), so the resume split holds there too.
- **`ACS_Suspend`/`Acs_NamedSuspend` (the standalone functions, action special 81 /
  extension function `-40` in `zcommon.bcs` — separate from this bare `suspend;` statement) reach
  the identical state transition from outside the script:** `LS_ACS_Suspend`
  (`p_lnspec.cpp:1853`) calls `P_SuspendScript` → `SetScriptState(script, SCRIPT_Suspended)`
  (`p_acs.cpp:13290-13296, 13143-13152`) — the same `state = SCRIPT_Suspended` assignment
  `PCD_SUSPEND` makes internally. A script can be suspended either by hitting its own `suspend;`
  statement or by another script calling `ACS_Suspend`/`Acs_NamedSuspend` on it; both are resumed
  the same way (a non-`ACS_ALWAYS` `ACS_Execute`/`Acs_NamedExecute` call). On Zandronum,
  `LS_ACS_Suspend` (`p_lnspec.cpp:1853-1864`) forwards nothing to clients, so a suspend issued on
  the server only affects server-run instances. A `CLIENTSIDE` script can only be suspended by
  code running on the client.
- **Cross-map suspend is deferred, not applied immediately, if the target map isn't current:**
  `P_SuspendScript` (`p_acs.cpp:13290-13296`) checks `map` against `level.mapname` — a different
  map queues a `defsuspend` deferred action (`addDefered`, `p_acs.cpp:13201-13230`) that only
  actually calls `SetScriptState` once that map is entered (`P_DoDeferedScripts`,
  `p_acs.cpp:13154-13199`). This mirrors `ACS_Execute`/`ACS_Terminate`'s cross-map deferral (see
  [ACS_NamedTerminate](acs_namedterminate.md)) — not a special case unique to `Suspend`.
- **Runaway-loop interaction:** like `Delay`/`TagWait`/`ScriptWait`/`PolyWait`, `PCD_SUSPEND`
  moves `state` away from `SCRIPT_Running`, which exits `RunScript()`'s instruction-counting
  `while` loop and yields control back to the caller. Unlike those, which resume on a later tic
  by themselves, a suspended instance stays idle every tic until something resumes it. It does *not* burn toward the
  2,000,000-instruction runaway budget the way `restart;`'s in-place jump can (see
  [restart](restart.md)).
- **Cross-reference for a future family consolidation:** `restart`/`terminate`/`suspend` are
  literally the same grammar production in `bcc` (`SCRIPT_JUMP_*`, `semantic/stmt.c:869`) and
  share the identical "outside script" / "inside msgbuild block" restrictions — a natural
  `families/script-jump.md` candidate now that all three (`restart.md`, `acs_namedterminate.md`,
  this file) exist. Not created here per this batch's family-collision guard — left for the
  coordinating session to consolidate if warranted.
