# `void TagWait(int tag)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `TagWait - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=TagWait&oldid=35806`), verified against
the Zandronum source's `src/p_acs.cpp` and the Zandronum source's `src/p_spec.cpp` on 2026-07-29. The wiki
page is thin — signature, one paragraph of usage, one example, one lift-specific note — and its
"will always wait 1 tic" claim is stated as a bare fact with no mechanism given; the explanation
below (and the tag-matching/busy-definition details) comes from reading the engine directly.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin (`zt-bcc/src/builtin.c:39`, `{ "tagwait", ";i" }` — one required int
arg, no optional args, matches the wiki's signature exactly; table-flagged `PCD_TAGWAIT |
F_LATENT` at `builtin.c:187`, marking it a *latent* — i.e. potentially script-suspending — call,
in the same `g_deds[]` family as `Delay`/`PolyWait`/`ScriptWait`/`Suspend`). Implemented as
`PCD_TAGWAIT` in `p_acs.cpp`; there's also a `PCD_TAGWAITDIRECT` opcode the compiler emits instead
when the argument is a compile-time constant — same runtime behavior, just skips a stack push
(same pattern as `ScriptWait`/`ScriptWaitDirect` — see [ScriptWait](scriptwait.md)).

Suspends the calling script until every sector matching `tag` has stopped moving.

- **Mechanism:** `PCD_TAGWAIT`/`PCD_TAGWAITDIRECT` (`p_acs.cpp:10541-10551`) store `tag` into the
  interpreter's `statedata` and set `state = SCRIPT_TagWait`, then `break` out of the bytecode
  loop for the rest of that tic (`p_acs.cpp:9226`'s `while (state == SCRIPT_Running)` stops
  iterating the instant `state` changes). On every subsequent call to `RunScript()` (i.e. once per
  following tic), the `SCRIPT_TagWait` case (`p_acs.cpp:9167-9180`) walks every sector matching
  `statedata` via `P_FindSectorFromTag`; if **any** of them has a non-null `floordata` or
  `ceilingdata` pointer, it `return`s immediately without touching `state` — i.e. it re-enters
  this same case again next tic. Once none of the matching sectors are busy, `state` flips to
  `SCRIPT_Running` and execution falls straight through into that same tic's bytecode loop,
  matching `PolyWait`'s "resumes on the tic the wait ends, not the tic after" behavior — see
  [PolyWait](polywait.md).
- **Why it always waits at least 1 tic, confirmed:** the `SCRIPT_TagWait` busy check only runs
  once per `RunScript()` invocation, and `RunScript()` is called once per tic. Because
  `PCD_TAGWAIT` itself sets `state` and immediately exits the bytecode loop *within the tic it was
  called*, the earliest the busy check can run is the *next* tic — even if `tag` matches zero
  sectors, or matches only already-idle ones. This confirms the wiki's bare claim ("`TagWait` will
  always wait 1 tic even if the sector is not moving") down to the mechanism, and is the same
  shape of gotcha `Delay`'s doc already covers for a different opcode — see [Delay](delay.md).
- **"Busy" means floor/ceiling mover thinker attached, not "any thinker on the sector."** The
  check is specifically `sectors[secnum].floordata || sectors[secnum].ceilingdata`
  (`p_acs.cpp:9174`) — these fields point at the sector's active floor- or ceiling-mover thinker
  (set by `Floor_*`/`Ceiling_*`/`Plat_*`/`Door_*`/`Elevator_*`-family specials' `EV_Do*` calls,
  cleared when that thinker calls `Destroy()` on completion). A sector whose only activity is a
  lighting effect, a texture scroller, or a 3D-floor-linked mover on a *different* sector's
  `floordata`/`ceilingdata` is **not** busy by this check and won't hold `TagWait` — only an
  actual floor or ceiling mover on the matched sector(s) counts. This is why a "waggling" or
  perpetually-repeating mover (the wiki's own warning) blocks forever: its thinker never calls
  `Destroy()`, so `floordata`/`ceilingdata` never goes null.
- **Lift/plat semantics fall out of the same check, not special-cased.** The wiki notes that with
  a lift, `TagWait` waits until the lift "has successfully returned to its starting position" —
  this isn't a lift-specific rule, it's just that a repeating plat's mover thinker
  (`DPlat`/similar) stays alive and keeps `floordata` non-null for the entire up-down-return
  cycle, and only destroys itself once the sequence completes (or the plat is a `PLAT_*` type that
  removes itself after one full cycle). A plat set to loop forever (e.g. `PLAT_TOGGLE`-driven
  ping-pong with no stop condition) has the same "waits forever" hazard as a waggling floor.
- **`tag` is matched literally via `P_FindSectorFromTag`, with no zero-tag special case.**
  `P_FindSectorFromTag` (`p_spec.cpp:270-277`) is a plain hashed lookup by tag value with no
  `tag==0` branch — unlike some action specials (e.g. [Floor_MoveToValue](floor_movetovalue.md)),
  where `tag==0` is special-cased by the special's own handler to mean "the back sector of the
  triggering line." `TagWait(0)` waits on sectors literally tagged `0`; if none exist, the busy
  loop finds nothing and the call behaves as a plain 1-tic delay (see above) rather than resolving
  to any kind of "current sector" fallback. A tag matching zero sectors is not an error and prints
  nothing.
- **Latent/blocking-function family:** `PCD_TAGWAIT` is one of the opcodes (alongside
  `PCD_DELAY`/`PCD_POLYWAIT`/`PCD_SCRIPTWAIT`/`PCD_SUSPEND`) that changes `state` away from
  `SCRIPT_Running` and exits `RunScript()`'s bytecode loop early — see
  [SetResultValue](setresultvalue.md) for why a synchronous `Acs_(Named)ExecuteWithResult` caller
  only ever observes the result value as of the *first* such block.
