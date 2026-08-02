# `bool SetPointer(int assign_slot, int tid [, int pointer_selector [, int flags]])`

Sets one of the *activator's* own `target`/`master`/`tracer` fields. Extension function
(`ACSF_SetPointer`, index `-38` in the zt-bcc source's `lib/zcommon.bcs:1666`), implementation in
`p_acs.cpp:5938-5950`, field write in `actorptrselect.cpp:177-194` (`ASSIGN_AAPTR`).

**Bucket:** extension function (negative index → `ACSF_SetPointer` in `p_acs.cpp`).

- `assign_slot` — must be `AAPTR_TARGET` (`0x2`), `AAPTR_MASTER` (`0x4`), or `AAPTR_TRACER`
  (`0x8`) (`actorptrselect.h:22-24`). **`ASSIGN_AAPTR`'s `switch (toSlot)` has no `default` case**
  — any other value (including `0`/`AAPTR_DEFAULT`, or one of the read-only selectors like
  `AAPTR_PLAYER_GETTARGET`) silently writes nothing to the activator, yet the function still
  returns whatever `ptr != NULL` evaluates to from the *resolution* step below. A bad `assign_slot`
  is therefore indistinguishable from a successful assignment by return value alone.
- `tid` — resolved via `SingleActorFromTID(tid, activator)` (`p_acs.cpp:4445`): `0` means "the
  activator itself." This matters because of the next check — see "Self-reference" below.
- `pointer_selector` (optional) — if present, the actor found via `tid` becomes the *origin* for
  `COPY_AAPTR(ptr, pointer_selector)`, i.e. an `AAPTR_*` selector resolved relative to that
  intermediate actor rather than the activator (see
  [Actor pointers](../concepts/actor-pointers.md) for `COPY_AAPTR`'s resolution order). Without
  it, `ptr` is just the actor found by `tid`.
- `flags` (optional, default `0`) — `PTROP_UNSAFETARGET` (`0x1`) / `PTROP_UNSAFEMASTER` (`0x2`),
  passed straight through to `ASSIGN_AAPTR`; see "Loop guard" below.

## Self-reference is always nulled, which makes bare `tid=0` useless

`p_acs.cpp:5946`: `if (ptr == activator) ptr = NULL;` runs unconditionally, *after* the
`pointer_selector` intermediate step, on whatever actor was finally resolved. Concretely:

- `SetPointer(slot, 0)` (no `pointer_selector`) resolves `ptr` to the activator itself via
  `SingleActorFromTID(0, activator)`, then immediately nulls it back out — this call **always**
  ends up assigning `NULL` and returning `0`, regardless of `assign_slot`. This is what the wiki
  means by "`0` selects the activator, but the caller can only be an intermediate selection" — a
  bare `tid=0` can never be used to make the activator point at itself; it's only useful as the
  *origin* for a `pointer_selector` lookup (e.g. `SetPointer(AAPTR_TARGET, 0, AAPTR_PLAYER_GETTARGET)`
  to copy the activator's own current target-of-target).
- The same nulling applies if `tid`/`pointer_selector` resolve to the activator through any other
  path (e.g. a `pointer_selector` chain that loops back), not just the literal `tid=0` case.

## Loop guard only covers `target`/`master`, and `target`'s check is missile-gated

`ASSIGN_AAPTR` (`actorptrselect.cpp:177-194`) writes the field unconditionally, then:

- `AAPTR_TARGET`: calls `VerifyTargetChain(toActor)` unless `PTROP_UNSAFETARGET` is set — but
  `VerifyTargetChain(self, preciseMissileCheck=true)` (`actorptrselect.cpp:109-140`) opens with
  `if (!self || !self->isMissile(preciseMissileCheck)) return;` — **the cycle check is skipped
  entirely unless the activator itself is a missile.** A non-missile actor (e.g. a player, or a
  monster) can be given a `target` that creates a cycle and it will never be detected or nulled;
  the loop guard only protects the missile-chases-missile case the comment above the function
  describes ("many released DECORATE monsters rely on this bug").
- `AAPTR_MASTER`: calls `VerifyMasterChain(toActor)` unless `PTROP_UNSAFEMASTER` is set, with **no
  missile gate** — it always walks the master chain regardless of actor type.
- `AAPTR_TRACER`: no verification function is called at all, matching the wiki's note that the
  circular-reference test "does not occur when assigning to the tracer field" — `flags` has no
  effect on a `tracer` assignment either way.

See [Actor pointers](../concepts/actor-pointers.md#aaptr_masteraaptr_targetaaptr_tracer-assignment-loop-guard)
for the general loop-guard writeup this refines; the missile-gating detail on the target side is
new here and not previously recorded there.

## Return value

`ptr != NULL` after the self-reference nulling above (`p_acs.cpp:5948`) — **not** whether a field
was actually written. `0`/`false` covers three distinct cases the caller can't tell apart from the
return value alone: no activator at all, the resolved actor was the activator itself (nulled), and
`tid`/`pointer_selector` failed to resolve to any actor.

**Provenance:** wiki page `SetPointer - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=38756`) + source-verified against `p_acs.cpp:5938-5950` (`ACSF_SetPointer` case),
`actorptrselect.cpp:109-194` (`VerifyTargetChain`/`VerifyMasterChain`/`ASSIGN_AAPTR`),
`actorptrselect.h:20-24` (`AAPTR_TARGET`/`MASTER`/`TRACER` values, `VerifyTargetChain`'s
`preciseMissileCheck=true` default), and `zt-bcc/lib/zcommon.bcs:1666` (index `-38`),
`:778-780` (`PTROP_*` constants). **Engine:** Zandronum 3.2.1 (verified against
the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
