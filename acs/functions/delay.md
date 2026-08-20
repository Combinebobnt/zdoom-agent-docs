# `void Delay(int tics)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** `Delay - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Delay&oldid=35788`),
verified against the Zandronum source's `src/p_acs.cpp` on 2026-07-28. The wiki page itself is thin —
signature, one line of usage, and two examples — and everything below the "Units" bullet is *not*
in the wiki; it comes from reading `PCD_DELAY`'s implementation and the `SCRIPT_Delayed` state
handler directly, because the wiki's own runaway-script example is subtly wrong about how `Delay`
actually behaves at the boundary (see "Delay(0) is not a safe no-op" below).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin (`zt-bcc/src/builtin.c:36`, `{ "delay", ";i" }` — one required int
arg, no optional args, matches the wiki's signature exactly; table-flagged `PCD_DELAY | F_LATENT`
at `builtin.c:184`, marking it a *latent* — i.e. potentially script-suspending — call).
Implemented as `PCD_DELAY` in `p_acs.cpp`.

Suspends the calling script for the given number of tics, then resumes it.

- **Units:** `tics`, at `TICRATE` = 35 per second (`doomdef.h:60`) — matches the wiki's own
  `35*seconds` idiom.
- **Mechanism:** `PCD_DELAY` (`p_acs.cpp:10474-10481`) sets the interpreter's `statedata` to the
  argument and, **only if that value is `> 0`**, sets `state = SCRIPT_Delayed`. On every
  subsequent tic, `DLevelScript::RunScript()`'s `SCRIPT_Delayed` case (`p_acs.cpp:9160-9165`)
  decrements `statedata` and flips `state` back to `SCRIPT_Running` once it hits `0` — at which
  point execution **falls straight through into the same `RunScript()` invocation's bytecode
  loop** (`p_acs.cpp:9226`, `while (state == SCRIPT_Running)`), i.e. the script resumes running
  starting on the very tic the counter reaches zero, not the tic after.
- **`Delay(0)` (or a negative argument) is not a safe no-op — it does not block at all.** Because
  the `state = SCRIPT_Delayed` assignment is gated on `statedata > 0`, calling `Delay(0)` leaves
  `state` at `SCRIPT_Running` and the bytecode loop simply continues on the same tic without ever
  yielding. This matters because the wiki's own second example motivates `Delay` specifically as
  the fix for a "Runaway script terminated" error in a tight `while (TRUE)` loop — but that fix
  only works for `Delay(N)` with `N >= 1`. A loop that accidentally computes a delay of `0` (e.g.
  from a variable that can be zero) will still runaway-terminate; `Delay` gives no protection in
  that case despite superficially "being called every iteration."
  See `p_acs.cpp:9228-9233` for the runaway-script counter (`runaway > 2000000` per
  `RunScript()` call) this interacts with.
- **Legacy Hexen-format quirk (not relevant when compiling with `bcc`/`zt-bcc`, noted for
  completeness):** on the original Hexen ACS bytecode format (`fmt == ACS_Old`) running under
  `GAME_Hexen`, `PCD_DELAY` silently adds one extra tic to the delay (`p_acs.cpp:10475`, `+ (fmt
  == ACS_Old && gameinfo.gametype == GAME_Hexen)`). Scripts compiled by `bcc`/`zt-bcc` use the
  modern enhanced format, not `ACS_Old`, so this hack never applies — but it's the same opcode a
  future reader might grep into, so it's worth knowing it's dead weight in that toolchain rather
  than an active off-by-one.
- **Latent/blocking-function family:** `PCD_DELAY` is one of the opcodes (alongside
  `PCD_TAGWAIT`/`PCD_POLYWAIT`/`PCD_SCRIPTWAIT`/`PCD_SUSPEND`) that changes `state` away from
  `SCRIPT_Running` and exits `RunScript()`'s bytecode loop early — see
  [SetResultValue](setresultvalue.md) for why a synchronous `Acs_(Named)ExecuteWithResult` caller
  only ever observes the result value as of the *first* such block, which is the mechanical reason
  behind the common "call SetResultValue before your first Delay" advice.
