# The engine is single-threaded: no two actors' script calls can interleave within a tic

**Tier:** B — source-derived, no wiki page (this is an engine-architecture fact, not a
documented ACS feature).
**Applies to:** UZDoom=unknown, Zandronum=yes — traced on Zandronum only. `DThinker::RunThinkers`
is shared ZDoom-family lineage, so this almost certainly holds on UZDoom too, but that has not
been separately confirmed by reading UZDoom's own `dthinker.cpp`.
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-08-27)
**Provenance:** Direct source trace, no wiki page — the question ("can two actors' `CallACS`
calls interleave in the same tic") arose from a mod project (Orc Slayer) needing to know whether
a shared scratch struct, written by one actor's script call and read later in the same call
chain, could be corrupted by a second actor's simultaneous call.

## The guarantee

Game logic runs on one thread, and `DThinker::RunThinkers()` (`src/dthinker.cpp:408-433`) ticks
every thinker strictly sequentially: it walks each statnum bucket in ascending order and calls
`Tick()` on one thinker at a time, `TickThinkers` at `dthinker.cpp:435+`. An actor's `Tick()`
(`AActor::Tick`, `src/p_mobj.cpp:3956`) always runs to completion before the next thinker's
`Tick()` begins — there is no async dispatch, no thread pool, nothing preempts a `Tick()` call
partway through.

Consequence: if actor A's `Tick()` calls a DECORATE action that runs an ACS script synchronously
(see below), that entire call — script execution included — happens inside actor A's `Tick()`
call frame. Actor B's `Tick()`, and therefore anything actor B's `Tick()` calls, cannot begin
until actor A's `Tick()` returns. **No two actors' script calls can interleave within one game
tic**, regardless of what either script does internally (including nested/recursive `CallACS`
calls, which just deepen the same C++ call stack rather than yielding to another actor).

## Which script calls this covers

This is the *general* engine-level guarantee. The *specific* case of `CallACS`/
`ACS_NamedExecuteWithResult`/`ACS_ExecuteWithResult` running synchronously in the caller's own tic
— i.e. that the called script's body executes in full, inline, before the calling DECORATE
expression evaluates — is already documented per-function in
[`acs_executewithresult.md`](../functions/acs_executewithresult.md)'s "Execution model" section
and in [`decorate/concepts/expressions.md`](../../decorate/concepts/expressions.md) (`CallACS` is
an alias for `ACS_NamedExecuteWithResult`). That existing coverage traces `FxActionSpecialCall::
EvalExpression` (`src/thingdef/thingdef_expression.cpp:2452-2481`) → `P_ExecuteSpecial`
(`src/p_lnspec.cpp:3923-3938`) → `LS_ACS_ExecuteWithResult` (`src/p_lnspec.cpp:1833-1851`) →
`P_StartScript` (`src/p_acs.cpp:13234-13288`) → `DLevelScript::RunScript`
(`src/p_acs.cpp:9120-13050`), and confirms the interpreter's `while (state == SCRIPT_Running)`
loop only exits via `PCD_TERMINATE` or a blocking opcode (`Delay`, `TagWait`, `PolyWait`,
`ScriptWait`, `Suspend`).

**What this file adds is the missing half:** that per-call synchronicity only guarantees a single
script call won't be interrupted by *itself*. It says nothing about whether a *different* actor's
simultaneous call could run concurrently and interleave. That's the single-threaded `RunThinkers`
fact above — a distinct claim, needed together with the per-call one to conclude that a shared
scratch variable written and read across a `CallACS` boundary is safe from cross-actor races
within one tic.

## What this does NOT cover

- **Across tics.** A script that blocks (`Delay`, `Suspend`, etc.) yields control back; a
  *different* actor's `Tick()` can and will run before the blocked script resumes on a later tic.
  The single-tic guarantee says nothing about state left in shared globals across a `Delay`.
- **`net`/`CLIENTSIDE` scripts on a dedicated server.** `LS_ACS_ExecuteWithResult` has a network
  carve-out (`p_lnspec.cpp:1842-1848`): a clientside-flagged script invoked server-side does not
  run synchronously server-side at all — it forwards a command to clients and returns `false`
  without executing anything locally. The single-threaded guarantee still holds for the *actual*
  execution (wherever it happens), but the caller on the server never observes it inline. This
  guarantee is therefore only useful as stated for ordinary (non-`net`) scripts.
- **Deferred/`ACS_Execute`-style dispatch.** Only the `*WithResult` variants (and any other path
  that calls `RunScript()` directly rather than merely scheduling a thinker) run inline. A plain
  `ACS_Execute`/`ACS_ExecuteAlways` call queues a new script thinker rather than running it in the
  caller's frame — that thinker still only ever runs during some actor's/the ACS thinker's own
  sequential `Tick()`, never concurrently with anything else, but it does not run *inside* the
  calling script's own call frame the way a `*WithResult` call does.

## Practical use

This is the fact that makes a pattern like "one shared `internal` scratch struct, populated by a
gatherer function and consumed by several short-lived pure predicates called later in the same
tic via `CallACS`" safe from cross-actor corruption — as long as every script in the chain is
non-`net` and contains no blocking statement. Two independent actors evaluating that same pattern
in the same tic will always do so strictly one-after-the-other, never interleaved, so a
`(actor, tic)` staleness check on the scratch (rather than a lock) is sufficient to guarantee
correctness.
