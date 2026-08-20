# `CheckProximity(int tid, str classname, float distance [, int count [, int flags [, int ptr]]])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** wiki page `CheckProximity - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=CheckProximity&oldid=55206`) + source-verified against `p_acs.cpp:5899-9064` (no matching case statement,
falls through to `default: break;` returning 0), `zcommon.bcs:1729` (declared as extension
function -98), `zcommon.bcs:1162-1174` (flag constants defined). Wiki/fork divergence
(function compiled but not implemented, returns 0 silently) recorded rather than silently
trusted.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (negative index -98 in `zcommon.bcs:1729`).

Proximity check intended to find actors of a given class within a distance radius. **Implemented
on UZDoom** (`case ACSF_CheckProximity:` at `src/playsim/p_acs.cpp`, dispatching to
`P_Thing_CheckProximity` in `src/playsim/p_things.cpp:566`) but **not implemented on Zandronum**
(see below) — declared in `zcommon.bcs` as extension function -98 but has no corresponding `case`
in Zandronum's `CallFunction` switch in `p_acs.cpp:5899-9064`. On Zandronum it compiles without
error (the compiler honors the function signature and `CPXF_*` flag constants defined in
`zcommon.bcs:1162-1174`) but silently falls through to the switch's `default: break;` case and
returns `0` (false) at runtime, rendering every call a permanent failed check.

## Signature discrepancy — resolved for UZDoom, still open for Zandronum

The ZDoom wiki page describes the first parameter as `int tid` (the activator's TID, with 0 meaning
"the current activator"). **UZDoom's actual implementation confirms the wiki: the first parameter
is read via `Level->SingleActorFromTID(args[0], ...)`**, the standard int-TID resolution helper
used tree-wide — i.e. the wiki is correct for the engine that actually implements this function.
Zandronum's compiled signature in `zcommon.bcs:1729` declares it as `str` instead; since Zandronum
never implements the function at all, this divergence never reaches a point where the type
matters there, but it's no longer "unexplained" — it reads as Zandronum's own partial/abandoned
port rather than a documentation drift on the wiki's side.

## Parameters

Per the ZDoom wiki page, confirmed against UZDoom's `P_Thing_CheckProximity`
(`src/playsim/p_things.cpp:566`) and the `case ACSF_CheckProximity:` call site that invokes it:

- `tid` — the actor around which to perform the distance check (0 for the activator, via
  `SingleActorFromTID`'s standard tid-0-means-activator convention).
- `classname` — the actor class name to search for; resolved with `PClass::FindClass`.
- `distance` — the search radius in map units; must be greater than 0 (a `<= 0` distance short-
  circuits to a failed check).
- `count` — the minimum number of actors to find within `distance` for the check to succeed.
  Default `1` (confirmed: the ACSF case passes `argCount >= 4 ? args[3] : 1`).
- `flags` — bitwise flags modifying the check behavior, default `0`. `CPXF_ANCESTOR` (inheritance
  check via `IsKindOf` rather than exact class match), `CPXF_NOZ`, and `CPXF_CHECKSIGHT` (via
  `P_CheckSight`) are all confirmed implemented as their names describe, read directly from
  `P_Thing_CheckProximity`'s body. The remaining `CPXF_*` flags (`CPXF_SETTARGET`,
  `CPXF_SETMASTER`, `CPXF_SETTRACER`, `CPXF_COUNTDEAD`, `CPXF_DEADONLY`, `CPXF_LESSOREQUAL`,
  `CPXF_EXACT`, `CPXF_FARTHEST`, `CPXF_CLOSEST`, `CPXF_SETONPTR`) are referenced in the function
  body but their exact per-flag semantics weren't traced line-by-line for this pass — treat as
  present and wired up, not as independently re-verified against the wiki's per-flag claims.
- `ptr` — optional pointer selector for setting target/master/tracer on a different actor pointer
  than the caller itself, default `AAPTR_DEFAULT` (i.e. the calling actor) — confirmed via
  `COPY_AAPTREX(Level, self, ptr, clientSide)` resolving the reference actor.

## Return value

**On UZDoom:** an `int` (used as the ACS `bool` convention — 0/1 — for the non-counting call path
the ACSF case uses) reflecting whether the check succeeded, matching the wiki's documented bool
result. **On Zandronum:** always `0` (false), for the reasons above.

## Related (implemented on both engines)

- `GetActorProperty` and `SetActorProperty` (working) for reading/writing individual actor
  properties — different use case but similar actor-query pattern.
- `Thing_ProjectileHit`, `Thing_Explode`, and other actor-inspection action specials for
  collision/projectile checks (unrelated mechanism, working).
