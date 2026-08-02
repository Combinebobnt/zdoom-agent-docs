# `int GetMapPosition(int type)`

Returns the 1-based position of the current or next map in the server's map rotation. Extension
function (`ACSF_GetMapPosition`, index -151 in `zt-bcc/lib/zcommon.bcs:1781`), implementation at
the Zandronum source's `src/p_acs.cpp:7916-7948`.

**Bucket:** extension function.

```cpp
case ACSF_GetMapPosition:
{
	enum
	{
		MAPPOSITION_CURRENT,
		MAPPOSITION_NEXT,
	};

	// [AK] If there's no maplist, return zero.
	if ( MAPROTATION_GetNumEntries() == 0 )
		return 0;

	const int positionType = args[0];
	unsigned int position = 0;

	if ( positionType == MAPPOSITION_CURRENT )
		position = MAPROTATION_GetCurrentPosition( );
	else if ( positionType == MAPPOSITION_NEXT )
		position = MAPROTATION_GetNextPosition( );
	else
		return 0;

	// [AK] Make sure that the current map position is the current level being played.
	if ( positionType == MAPPOSITION_CURRENT )
	{
		level_info_t *rotationMap = MAPROTATION_GetMap( position );

		if (( rotationMap == nullptr ) || ( stricmp( level.mapname, rotationMap->mapname ) != 0 ))
			return 0;
	}

	return position + 1;
}
```

- **`type`** is `MAPPOSITION_CURRENT` (0) or `MAPPOSITION_NEXT` (1), both real named constants in
  `zt-bcc/lib/zcommon.bcs:1248-1251` matching the engine's internal (unexposed) enum order
  exactly — no divergence to flag here, unlike some other extension functions in this tree.
  Any other `type` value returns `0` (there's no "invalid argument" signal distinct from "no
  rotation").
- **Return value is 1-based** ("starting from 1" per the wiki, confirmed by the `position + 1`
  at the end) even though the underlying `MAPROTATION_GetCurrentPosition()`/
  `MAPROTATION_GetNextPosition()` helpers (`maprotation.cpp:134-144`) return plain 0-based
  indices into the rotation vector (`g_CurMapInList`/`g_NextMapInList`). Don't use this return
  value directly as an index into `GetMapRotationInfo`/other 0-based rotation APIs without
  subtracting 1 back off.
- **Two independent failure paths both silently return `0`**, matching the wiki's description:
  - No rotation at all (`MAPROTATION_GetNumEntries() == 0`) — e.g. a single fixed map with no
    `sv_maprotation` list configured.
  - For `MAPPOSITION_CURRENT` only: an extra sanity check re-resolves the rotation entry at the
    stored current-position index and compares its `mapname` (case-insensitively) against the
    actually-running map (`level.mapname`). If they don't match — e.g. the map was changed via
    `map`/`changemap`/RCON outside the rotation's own advancement — this returns `0` even though
    a rotation exists and the position variable is technically non-negative. **`MAPPOSITION_NEXT`
    has no equivalent cross-check** — it just reports `MAPROTATION_GetNextPosition() + 1`
    unconditionally once a non-empty rotation exists, since the "next" index is always an
    internally-consistent slot in that same rotation.
  - Both branches collapse to the same `0` result as "position 1" would look like if it existed —
    there is no separate "no rotation" vs. "map not in rotation" signal, exactly as the wiki
    states.
- **Related but not merged into one file:** this function's "See also" list on the wiki
  (`GetMapRotationSize`, `GetMapRotationInfo`) are the same map-rotation subsystem and read the
  same `g_MapRotationEntries`/`g_CurMapInList`/`g_NextMapInList` state. This doc was written
  standalone per this intake batch's per-function convention; a future pass may want to fold
  `GetMapPosition`/`GetMapRotationSize`/`GetMapRotationInfo` into a shared `families/` page the
  way `families/lump-io.md` groups its sequence — flagging that here rather than doing it
  unilaterally, since two sibling functions were being processed concurrently in the same intake
  batch.

**Example:**

```
int pos = GetMapPosition(MAPPOSITION_CURRENT);
if (pos == 0)
{
    Log(s: "Not running from the map rotation (or no rotation configured).");
}
```

**Returns:** `int` — 1-based position in the map rotation, or `0` if there is no rotation, `type`
is invalid, or (for `MAPPOSITION_CURRENT` specifically) the running map doesn't match the
rotation's recorded current-position entry.

**Provenance:** wiki page `GetMapPosition - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=2246`) + source-verified against the Zandronum source (`p_acs.cpp:7916-7948`,
`maprotation.cpp:127-144`) and `zt-bcc/lib/zcommon.bcs:1781,1248-1251`. The wiki's description
held up fully against source; this doc adds the 0-based-vs-1-based indexing detail and the
`MAPPOSITION_CURRENT`-only cross-check (both absent from the wiki page). Function was added as
`GetCurrentMapPosition` in commit `2ba3d3c975` (2022-02-13) and renamed to `GetMapPosition` (with
the current/next `type` parameter added) in commit `2d88efa44b` (2024-04-23) — confirmed via
`git merge-base --is-ancestor` that this rename commit predates the 3.2.1 version-bump commit
`28f736fb3` (2025-08-04), so the function under its current name and signature is present in the
3.2.1 target. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
