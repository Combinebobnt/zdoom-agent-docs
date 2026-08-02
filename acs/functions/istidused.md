# `bool IsTidUsed(int tid)`

Returns whether any actor with the given TID currently exists, dead or alive. Extension function
(`ACSF_IsTIDUsed`, index -47 in `zcommon.bcs`), implementation at
the Zandronum source's `src/p_mobj.cpp:3626-3638` (called from `p_acs.cpp:6361-6362`).

**Bucket:** extension function. Note the case mismatch between layers: BCS-side name in
`zt-bcc/lib/zcommon.bcs:1675` is `IsTidUsed` (mixed case, matching the existing tier-C `INDEX.md`
entry), the engine's enum/wrapper spell it `ACSF_IsTIDUsed`/`P_IsTIDUsed` (all-caps TID) — same
function, just inconsistent capitalization across the compiler table and the C++ side. Use
`IsTidUsed` in BCS source; ACS is case-insensitive for identifiers anyway so either spelling
compiles, but `IsTidUsed` is what's actually declared.

```cpp
bool P_IsTIDUsed(int tid)
{
	AActor *probe = AActor::TIDHash[tid & 127];
	while (probe != NULL)
	{
		if (probe->tid == tid)
		{
			return true;
		}
		probe = probe->inext;
	}
	return false;
}
```

- **Checks existence only, alive or dead** — the walk over the `tid & 127` hash bucket has no
  `health` check at all, unlike `ThingCount`'s `tid`-only path (`p_acs.cpp:3923-3934`), which
  explicitly requires `actor->health > 0` to count a match. This is exactly the wiki's claimed
  distinction, confirmed by reading both implementations side by side: `IsTidUsed` will return
  `true` for a corpse still holding its TID, where `ThingCount(0, tid)` would return `0` for the
  same actor.
- **Why it's cheaper than `ThingCount(T_NONE, tid)` for a pure existence check** — `IsTidUsed`
  returns on the *first* hash-bucket entry whose `tid` matches. `ThingCount`'s `tid`-set path
  iterates every actor with that TID via `FActorIterator` to produce an exact count, doing more
  work than an existence check needs whenever more than one actor shares the TID (a real
  possibility — TIDs are not guaranteed unique). For the common "does at least one still exist"
  question, `IsTidUsed` avoids that extra iteration.
- **No validation of `tid`** — `0` is a valid argument like any other; since no actor is ever
  assigned TID `0` (it means "no TID" throughout the engine, e.g. `SingleActorFromTID`'s
  activator-fallback convention), `IsTidUsed(0)` always returns `false`. There is no separate
  error path for an out-of-range or unused `tid` — a TID nothing was ever assigned to just falls
  through the bucket walk and returns `false`, indistinguishable from "used to exist, now
  destroyed."

**Example:**

```
if (!IsTidUsed(TID_BOSS))
{
    Log(s: "The boss is gone (dead or removed).");
}
```

**Returns:** `bool` — `true` if any actor (alive or dead) currently holds `tid`, `false`
otherwise (including `tid == 0`, which no actor can hold).

**Provenance:** wiki page `IsTIDUsed - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`oldid=40891`) + source-verified against the Zandronum source (`p_mobj.cpp:3626-3638`,
`p_acs.cpp:6361-6362`, `ThingCount`'s `health > 0` filter at `p_acs.cpp:3923-3934`) and
`zt-bcc/lib/zcommon.bcs:1675`. The wiki's dead-or-alive and ThingCount-efficiency claims both hold
exactly against this fork's source; the `tid == 0` behavior is this doc's source-verified
addition (not mentioned on the wiki page). **Engine:** Zandronum 3.2.1 (verified against
the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
