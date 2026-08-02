# `CheckProximity(int tid, str classname, float distance [, int count [, int flags [, int ptr]]])`

Proximity check intended to find actors of a given class within a distance radius.
**Not implemented in this fork** — declared in `zcommon.bcs` as extension function -98 but
has no corresponding `case` in the `CallFunction` switch in `p_acs.cpp:5899-9064`. Compiles
without error (the compiler honors the function signature and `CPXF_*` flag constants defined
in `zcommon.bcs:1162-1174`) but silently falls through to the switch's `default: break;` case
and returns `0` (false) at runtime, rendering every call a permanent failed check.

**Bucket:** extension function (negative index -98 in `zcommon.bcs:1729`).

## Signature discrepancy

The ZDoom wiki page describes the first parameter as `int tid` (the activator's TID, with 0 meaning
"the current activator"). The compiled signature in `zcommon.bcs:1729` declares it as `str` instead.
This mismatch is unexplained and raises questions about whether this is a partial port or a
documentation drift on one side; either way, the function is non-functional in this fork and
never reaches a point where the type matters.

## Parameters

Per the ZDoom wiki page (unverified in this fork due to lack of implementation):

- `tid` — the actor around which to perform the distance check (or 0 for the activator).
- `classname` — the actor class name to search for.
- `distance` — the search radius in map units; must be greater than 0.
- `count` — the minimum number of actors to find within `distance` for the check to succeed.
  Default is 1.
- `flags` — bitwise flags modifying the check behavior. Possible values (`CPXF_*` constants all
  defined in `zcommon.bcs:1162-1174`) include `CPXF_ANCESTOR`, `CPXF_NOZ`, `CPXF_CHECKSIGHT`,
  `CPXF_SETTARGET`, `CPXF_SETMASTER`, `CPXF_SETTRACER`, `CPXF_COUNTDEAD`, `CPXF_DEADONLY`,
  `CPXF_LESSOREQUAL`, `CPXF_EXACT`, `CPXF_FARTHEST`, `CPXF_CLOSEST`, `CPXF_SETONPTR`.
  **None of these behaviors are implemented or verifiable in this fork.**
- `ptr` — optional pointer selector for setting target/master/tracer on a different actor
  pointer than the caller itself. Default is 0 (the calling actor).

## Return value

Always returns `0` (false) in this fork due to lack of implementation. The wiki page documents
a bool result indicating whether the check succeeded.

## Related (implemented)

- `GetActorProperty` and `SetActorProperty` (working) for reading/writing individual actor
  properties — different use case but similar actor-query pattern.
- `Thing_ProjectileHit`, `Thing_Explode`, and other actor-inspection action specials for
  collision/projectile checks (unrelated mechanism, working).

**Provenance:** wiki page `CheckProximity - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=55206`) + source-verified against `p_acs.cpp:5899-9064` (no matching case statement,
falls through to `default: break;` returning 0), `zcommon.bcs:1729` (declared as extension
function -98), `zcommon.bcs:1162-1174` (flag constants defined). Wiki/fork divergence
(function compiled but not implemented, returns 0 silently) recorded rather than silently
trusted. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD,
which is `3.3-alpha` and similarly lacks this function — see "Engine scope" in `../../shared/AUTHORING.md`).
**Tier:** A.
