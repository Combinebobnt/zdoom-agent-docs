# `int GetMapRotationSize(void)`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `GetMapRotationSize - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `https://wiki.zandronum.com/w/index.php?title=GetMapRotationSize&oldid=1370`) + source-verified against `p_acs.cpp:7869-7872,5514`,
`maprotation.cpp:127-137,301`, `maprotation.h:80-81`, `zt-bcc/lib/zcommon.bcs:1779-1781`. Wiki
page is accurate; the position-0/1-based-iteration relationship to `GetMapRotationInfo` isn't
spelled out on the wiki page itself but is confirmed by both the example code and the C++.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (negative index, `p_acs.cpp`'s `ACSF_*` switch).

Zandronum-specific. Extension function, `zcommon.bcs:1779` declares it at index `-149`
(`ACSF_GetMapRotationSize`, the Zandronum source's `src/p_acs.cpp:5514`), implementation is the
one-line `case ACSF_GetMapRotationSize:` block at `p_acs.cpp:7869-7872`, which just returns
`MAPROTATION_GetNumEntries()` (the Zandronum source's `src/maprotation.cpp:127-130` —
`g_MapRotationEntries.size()`, no side effects, no invalid state).

## What the returned count actually covers — worth stating explicitly

The count is the raw size of the server's internal map-rotation list, indexed `0..size-1`
server-side. The companion function `GetMapRotationInfo(position, type)` does not use that
internal indexing directly: it treats ACS-facing `position <= 0` as "the current map"
(`MAPROTATION_GetCurrentPosition()`) and only for `position > 0` maps it back to the internal
list via `ulPosition = position - 1` (`p_acs.cpp:7885`). So from ACS, valid rotation-entry
positions to iterate are `1..GetMapRotationSize()` inclusive, with position `0` reserved for
"current map" and *not* included in the count `GetMapRotationSize()` returns. This matches the
wiki's own example exactly (`for (i = 1; i <= size; i++)`), but is easy to get wrong if you
assume the return value is an exclusive upper bound over a normal 0-based range, or that it
includes the current map as one of its entries.

If `sv_maprotation` has no rotation configured at all (or hasn't loaded one yet),
`GetMapRotationSize()` simply returns `0` — no error, no special sentinel.

**Example — from the wiki, iterate every rotation entry (position 0 is the current map, not counted in `size`):**

```text
Script 1 OPEN {
	int size = GetMapRotationSize();
	Log(d: size, s: " maps are in the rotation.");

	for (int i = 1; i <= size; i++)
	{
		Log(
			d: i, s: ". ",
			s: GetMapRotationInfo(i, MAPROTATION_LumpName), s: " - ",
			s: GetMapRotationInfo(i, MAPROTATION_Name)
		);
	}
}
```

**Note:** this function is tightly coupled to `GetMapRotationInfo` (and arguably `GetMapPosition`)
— they only make sense read together. It's documented here as a standalone file per this intake
batch's file-collision guard (both `GetMapRotationInfo` and `GetMapPosition` were being processed
concurrently by sibling agents); a future pass may want to fold these into a single
`families/map-rotation.md` instead of three separate function files.

## Engine-family divergence

`GetMapRotationSize` is bound as ACSF (CALLFUNC) index 149, inside the 100–199 range UZDoom
reserves for Zandronum's extensions and implements none of. A Zandronum-compiled object calling
it under UZDoom hits the `default: break;` case of UZDoom's `CallFunction` switch, which returns
`0` with no error and no log line — the interpreter's stack stays balanced and the script keeps
running as if the call had succeeded. See
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general mechanism
and its full reserved-range function list (`GetMapRotationSize`/`GetMapRotationInfo`/`GetMapPosition`
aren't individually confirmed there, but sit in the same 100–199 block by construction).

This is a particularly sharp instance of the trap that file's "silent-0 can be coincidentally
correct" section warns about: this file's own body already documents that a genuinely empty or
unconfigured `sv_maprotation` makes `GetMapRotationSize()` legitimately return `0` on Zandronum
itself, "no error, no special sentinel." Under UZDoom, every call returns that same `0` regardless
of what the (nonexistent, on that engine) rotation list actually contains — so a caller has no way
to distinguish "this server has no map rotation" from "this server is running an engine that
doesn't implement this function at all." A loop written against the wiki's own example
(`for (i = 1; i <= size; i++)`) simply never executes its body under UZDoom instead of failing
loudly, which is easy to misread as "empty rotation" during testing.
