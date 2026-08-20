# `void PolyWait(int polyid)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `PolyWait - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=PolyWait&oldid=35807`), verified against
the Zandronum source's `src/p_acs.cpp` and the Zandronum source's `src/po_man.cpp` on 2026-07-29. The wiki
page is thin — signature, one paragraph of usage, one example — and states only the happy path
("delays the script ... until it has finished its movement"); everything below the "Mechanism"
bullet comes from reading the engine directly, because the wiki doesn't mention either of the two
edge cases below.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin (`zt-bcc/src/builtin.c:40`, `{ "polywait", ";i" }` — one required int
arg, no optional args, matches the wiki's signature exactly; table-flagged `PCD_POLYWAIT |
F_LATENT` at `builtin.c:188`, marking it a *latent* — i.e. potentially script-suspending — call,
in the same `g_deds[]` family as `Delay`/`TagWait`/`ScriptWait`). Implemented as `PCD_POLYWAIT` in
`p_acs.cpp`.

Suspends the calling script until the polyobject identified by `polyid` stops moving.

- **Mechanism:** `PCD_POLYWAIT` (`p_acs.cpp:10553-10557`) sets `state = SCRIPT_PolyWait` and
  `statedata = polyid`. On every subsequent tic, `DLevelScript::RunScript()`'s `SCRIPT_PolyWait`
  case (`p_acs.cpp:9182-9188`) calls `PO_Busy(statedata)`; once it returns `false`, `state` flips
  back to `SCRIPT_Running` and execution falls straight through into the same tic's bytecode loop
  (`p_acs.cpp:9226`), matching `Delay`'s "resumes on the tic the wait ends, not the tic after"
  behavior — see [Delay](delay.md).
- **What "busy" means:** `PO_Busy` (`po_man.cpp:2207-2213`) is `poly != NULL && poly->specialdata
  != NULL`. `specialdata` on an `FPolyObj` points at its active `DPolyAction` mover thinker
  (`DRotatePoly`/`DMovePoly`/`DMovePolyTo`/`DPolyDoor`, all set it in their `EV_*Poly` constructor
  paths, e.g. `po_man.cpp:605`/`715`/`802`/`1064`) and is cleared only when that thinker calls
  `Destroy()` (`DPolyAction::Destroy`, `po_man.cpp:275-286`) — i.e. "finished moving" specifically
  means "the mover thinker destroyed itself," not merely "reached its target distance/angle this
  tic."
- **Nonexistent `polyid` does not block at all.** `PO_GetPolyobj` returns `NULL` for a `polyid`
  with no matching polyobject, so `PO_Busy` short-circuits to `false` on the very first check —
  `PolyWait` for a bad/typo'd id returns immediately rather than waiting or erroring, silently
  behaving as a no-op wait. Same shape of gotcha as `TagWait` waiting on a tag matching zero
  sectors.
- **A permanently obstructed polyobject waits forever, with no timeout.** `DMovePoly::Tick`
  (`po_man.cpp:638-686`) only calls `Destroy()` when `poly->MovePolyobj(...)` actually succeeds in
  moving the full remaining distance; if the move is blocked (an obstruction the polyobject can't
  push through), the `else` branch is taken, the thinker is left alive to retry next tic, and
  `specialdata` stays non-`NULL` — so `PO_Busy` keeps reporting `true` indefinitely. A `PolyWait`
  on a polyobject that gets permanently wedged (e.g. against unmovable geometry, or by something
  that can never be cleared) suspends the waiting script forever; this isn't caught by the
  runaway-script counter either, since `SCRIPT_PolyWait` exits `RunScript()`'s bytecode loop each
  tic rather than looping within one invocation (same mechanism note as `Delay`'s "latent function
  family" — see [Delay](delay.md)).
