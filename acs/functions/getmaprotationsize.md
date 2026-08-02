# `int GetMapRotationSize(void)`

Zandronum-specific. Extension function, `zcommon.bcs:1779` declares it at index `-149`
(`ACSF_GetMapRotationSize`, the Zandronum source's `src/p_acs.cpp:5514`), implementation is the
one-line `case ACSF_GetMapRotationSize:` block at `p_acs.cpp:7869-7872`, which just returns
`MAPROTATION_GetNumEntries()` (the Zandronum source's `src/maprotation.cpp:127-130` —
`g_MapRotationEntries.size()`, no side effects, no invalid state).

**Bucket:** extension function (negative index, `p_acs.cpp`'s `ACSF_*` switch).

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

```
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

**Provenance:** wiki page `GetMapRotationSize - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=1370`) + source-verified against `p_acs.cpp:7869-7872,5514`,
`maprotation.cpp:127-137,301`, `maprotation.h:80-81`, `zt-bcc/lib/zcommon.bcs:1779-1781`. Wiki
page is accurate; the position-0/1-based-iteration relationship to `GetMapRotationInfo` isn't
spelled out on the wiki page itself but is confirmed by both the example code and the C++.
**Engine:** Zandronum 3.2.1 — the introducing commit (`4e38a84d7`, "Added ACS functions:
GetMapRotationSize and GetMapRotationInfo...", 2021-04-02) was confirmed via
`git merge-base --is-ancestor 4e38a84d7 28f736fb3` to predate the "changed the version string to
3.2.1" commit in the Zandronum source's checkout, i.e. it ships in 3.2.1, not just the
checkout's `3.3-alpha` HEAD. **Tier:** A.
