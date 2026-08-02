# `bool SetActivator(int tid [, int pointer_selector])`

Reassigns the *calling script's own* activator (the same `activator`/pointer the rest of the
script's execution — `ActivatorTID()`, `PlayerNumber()`, `Log`/`Print`'s activator-relative
delivery, etc. — reads from then on) to a different actor, or to no actor at all ("the world").
Extension function (`ACSF_SetActivator`, index `-12` in the zt-bcc source's `lib/zcommon.bcs:1640`),
implementation in `p_acs.cpp:5952-5961`.

**Bucket:** extension function (negative index → `ACSF_SetActivator` in `p_acs.cpp`).

```cpp
case ACSF_SetActivator:
    if (argCount > 1 && args[1] != AAPTR_DEFAULT) // condition (x != AAPTR_DEFAULT) is essentially condition (x).
    {
        activator = COPY_AAPTR(SingleActorFromTID(args[0], activator), args[1]);
    }
    else
    {
        activator = SingleActorFromTID(args[0], NULL);
    }
    return activator != NULL;
```

## Two genuinely different code paths depending on whether `pointer_selector` is passed

This is not "resolve `tid`, then optionally apply a selector" — omitting the selector (or passing
`AAPTR_DEFAULT` explicitly, which takes the *same* branch since the condition is
`args[1] != AAPTR_DEFAULT`) changes what `tid == 0` means:

- **Selector given (and not `AAPTR_DEFAULT`):** `tid` is resolved via
  `SingleActorFromTID(tid, activator)` — **`tid == 0` falls back to the *current* activator**
  (`SingleActorFromTID`'s `if (tid == 0) return defactor;`, `p_acs.cpp:4445-4456`), matching every
  other `tid`-taking builtin's "0 means the activator" convention. The resolved actor is then fed
  through `COPY_AAPTR` with the given selector — see
  [Actor pointer selectors](../concepts/actor-pointers.md) for the full `COPY_AAPTR` priority
  chain shared by every `AAPTR_*`-consuming function in this engine (`SetPointer`,
  `SetActivatorToTarget`, `IsPointerEqual`, etc.). Real-world callers use exactly this
  pattern throughout (e.g. `SetActivator(0, AAPTR_TRACER)`, `SetActivator(0, AAPTR_PLAYER_GETTARGET)`)
  — `tid=0` there means "start from my current activator, then walk to its tracer/aim-target."
- **No selector, or `AAPTR_DEFAULT` passed explicitly:** `tid` is resolved via
  `SingleActorFromTID(tid, NULL)` instead — **the fallback-for-`tid==0` is a hardcoded `NULL`, not
  the current activator.** This is the load-bearing trap: `SetActivator(0)` with no selector does
  **not** mean "leave the activator as it is" or "reset to the original activator" the way `tid=0`
  reads everywhere else in this engine — it unconditionally sets the activator to `NULL` (the
  world) and returns `0`, because there is no actor with TID literally `0`. Only a genuinely
  nonzero `tid` can succeed on this branch (e.g. `SetActivator(TID_SOME_TRIGGER)`,
  `SetActivator(1000 + p_num)`, both patterns seen in real-world scripts). The wiki's own
  example, `SetActivator(0, AAPTR_PLAYER1)`, sidesteps this entirely by always passing a selector.

## No self-pointer guard, unlike `SetPointer`

`ACSF_SetPointer` (`p_acs.cpp:5938-5950`) explicitly nulls out a resolved pointer that turns out to
equal the activator itself (`if (ptr == activator) ptr = NULL;`) before assigning. `SetActivator`
has **no equivalent check** — if the selector chain resolves back to the actor that was already
the activator, `activator` is simply reassigned to itself and the function returns `1`. Not a bug,
just an asymmetry worth knowing if code was ported from a `SetPointer` call site with the same
selector logic.

## Return value / failure behavior

`activator != NULL` after the assignment — matches the wiki's "1 if the activator exists, 0 (and
activator set to the world) if the TID doesn't resolve or the pointer is NULL." No fork divergence
found here: both branches funnel through the same "did we end up with a non-NULL actor" check, and
`COPY_AAPTR`/`SingleActorFromTID` are the same NULL-safe helpers used elsewhere in this engine (a
`NULL` origin into `COPY_AAPTR` falls through every tier and returns `NULL` unchanged — no crash,
verified in [Actor pointer selectors](../concepts/actor-pointers.md)).

## Scope of the change

The reassignment is a plain local-variable write to the running script instance's own `activator`
(no Zandronum server→client replication — this is server-side (or client-side, for a `CLIENTSIDE`
script) interpreter state, not something clients need to know about) and persists for the rest of
that script instance's execution, across function calls, until the script ends or calls
`SetActivator`/`SetActivatorToTarget`/`SetActivatorToPlayer` again.

**Provenance:** wiki page `SetActivator - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=35016`) + source-verified against `p_acs.cpp:5952-5961` (`ACSF_SetActivator` case),
`p_acs.cpp:4445-4456` (`SingleActorFromTID`), `p_acs.cpp:5938-5950` (`ACSF_SetPointer`, for the
self-pointer-guard contrast), and `zt-bcc/lib/zcommon.bcs:1640` (index `-12`, optional 2nd arg).
Selector resolution itself (`COPY_AAPTR`) is documented once in
[Actor pointer selectors](../concepts/actor-pointers.md) rather than re-derived here. **Engine:**
Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in
`../../shared/AUTHORING.md`). **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
