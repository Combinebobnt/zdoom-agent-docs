# Map rotation family

**Tier:** A for all four.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki `GetMapRotationSize` (https://wiki.zandronum.com/w/index.php?title=GetMapRotationSize&oldid=1370, retrieved 2026-07-29), `GetMapRotationInfo` (https://wiki.zandronum.com/w/index.php?title=GetMapRotationInfo&oldid=1369, retrieved 2026-07-29), `GetMapPosition` (https://wiki.zandronum.com/w/index.php?title=GetMapPosition&oldid=2246, retrieved 2026-07-29), `SetNextMapPosition` (https://wiki.zandronum.com/w/index.php?title=SetNextMapPosition&oldid=2476, retrieved 2026-08-18). Wiki-derived and source-verified against the Zandronum source's `src/p_acs.cpp:7869-7948` (the three getters) and `:8883-8897` (`SetNextMapPosition`), `src/maprotation.cpp:127-165`, `src/maprotation.h:80-81`, `src/g_level.cpp:218-219,1117-1131` (when the current position moves), and `zt-bcc/lib/zcommon.bcs:1242-1251,1779-1781,1806`. Consolidated from four standalone files 2026-09-22 with no change to any verified claim.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** all four are extension functions (`zcommon.bcs` negative indices), dispatched from
`DLevelScript::CallFunction` in `src/p_acs.cpp`: `GetMapRotationSize` -149
(`ACSF_GetMapRotationSize`, `:7869-7872`), `GetMapRotationInfo` -150 (`ACSF_GetMapRotationInfo`,
`:7874-7914`), `GetMapPosition` -151 (`ACSF_GetMapPosition`, `:7916-7948`), `SetNextMapPosition`
-178 (`ACSF_SetNextMapPosition`, `:8883-8897`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Grouped as one family under the **shared-implementation** rationale (`shared/AUTHORING.md`): all
four are thin wrappers over `maprotation.cpp`'s `MAPROTATION_*` helpers and the same three
globals, `g_MapRotationEntries` (the rotation list), `g_CurMapInList` and `g_NextMapInList` (0-based
indices into it). Map rotation is a Zandronum server feature (`sv_maprotation` plus the maplist);
none of these functions exists on UZDoom (see "Engine-family divergence" below).

The finding that only makes sense across all four is **position numbering**. Internally every index
is 0-based; every ACS-facing position is 1-based, and the members disagree about what `0` means:

| Member | ACS-facing position | What `0` means |
|---|---|---|
| `GetMapRotationSize` | returns the entry count; valid positions are `1..size` | an empty (or unconfigured) rotation, or UZDoom |
| `GetMapRotationInfo` | argument, `1..size` | argument `<= 0` is "the current map", **but only if** the running map matches the rotation's current-position entry |
| `GetMapPosition` | returns internal index `+ 1` | return value: no rotation, invalid `type`, or (for `MAPPOSITION_CURRENT`) the running map isn't the rotation's current entry |
| `SetNextMapPosition` | argument, `1..size` | argument `0` is plain out of range (unsigned underflow), **not** "current map" |

So a `GetMapPosition` result can be passed straight back into `GetMapRotationInfo` or
`SetNextMapPosition` as-is (all three speak 1-based), but not into anything indexing the internal
0-based list. The "current map" cross-check (`stricmp( level.mapname, rotationMap->mapname )`)
appears in both `GetMapRotationInfo`'s `position <= 0` branch and `GetMapPosition`'s
`MAPPOSITION_CURRENT` branch. With `sv_maprotation` on, `map` and `changemap` (typed, over RCON or
passed by a vote) move the current position to the loaded map when it is in the rotation
(`g_level.cpp:218-219,1120-1121`), so the check passes. Both report "nothing" when the running map
isn't the rotation's current entry: a map not in the rotation, or one reached by a level exit (e.g.
a secret exit) that isn't the next rotation entry, which leaves the current position unchanged
(`g_level.cpp:1123-1131`).

Iterating the rotation, from the wiki (semantics unchanged; the list starts at 1, position 0 is the
current map and is not counted in `size`):

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

**See also:** [SetMapUsedStatus](../functions/setmapusedstatus.md), the same subsystem's
used-flag setter (tier B, server-only, not callable from zt-bcc), kept as its own file.

## `int GetMapRotationSize(void)`

Returns `MAPROTATION_GetNumEntries()` (`maprotation.cpp:127-130`, `g_MapRotationEntries.size()`).
One-line `case` block, no side effects, no invalid state.

- The count is the raw size of the internal 0-based list. It is the **inclusive** upper bound for
  ACS-facing positions (`1..size`), not an exclusive bound over `0..size-1`, and it does not count
  the "current map" position `0` as an extra entry. Easy to get wrong if you assume a normal
  0-based range.
- No rotation configured (or not loaded yet) returns `0`: no error, no special sentinel.

**Returns:** `int` — number of rotation entries, `0` if there is no rotation.

## `raw GetMapRotationInfo(int position, int info)`

Reads one property of one rotation entry.

- **`position`** — 1-based; internally `ulPosition = args[0] - 1`. `position <= 0` instead takes
  `ulPosition = MAPROTATION_GetCurrentPosition()` and is subject to the current-map cross-check
  above.
- **`info`** — one of (values match `zcommon.bcs:1242-1246` and the wiki):
  - `MAPROTATION_NAME` = 0 — the map's display name (`level_info_t::LookupLevelName()`), e.g.
    `"Entryway"`.
  - `MAPROTATION_LUMPNAME` = 1 — the map lump name, e.g. `"MAP01"`.
  - `MAPROTATION_USED` = 2 — whether this entry has already been played this rotation cycle
    (`MAPROTATION_IsUsed`).
  - `MAPROTATION_MINPLAYERS` = 3 — minimum player count required to load the map; `0` = no
    minimum.
  - `MAPROTATION_MAXPLAYERS` = 4 — maximum player count allowed; `64` = no maximum.

**Returns:** declared `raw`; the real type depends on `info`. `MAPROTATION_NAME`/`LUMPNAME` return
a **string handle** (`GlobalACSStrings.AddString`), so print with `s:`; `USED`/`MINPLAYERS`/
`MAXPLAYERS` return a plain int. Any other `info` value falls through the `switch` (no `default`)
and returns `0` silently.

**Failure behavior (not on the wiki):** if `MAPROTATION_GetMap` returns `NULL` (out-of-range
position, or an empty rotation, which makes every position invalid including the `<= 0` branch),
or the `<= 0` current-map cross-check fails, the function returns `""` for the two string
properties and `0` for everything else (`p_acs.cpp:7888-7897`). So `GetMapRotationInfo(0, ...)`
is not "always describes the current map"; it describes it only when the rotation agrees the
running map is its current-position entry.

## `int GetMapPosition(int type)`

Returns the 1-based position of the current or next map in the rotation. Added as
`GetCurrentMapPosition` in commit `2ba3d3c975` (2022-02-13) and renamed to `GetMapPosition` (with the
`type` parameter) in `2d88efa44b` (2024-04-23); `git merge-base --is-ancestor` confirms the rename
predates the 3.2.1 version-bump commit `28f736fb3`, so this name and signature are in the 3.2.1
target.

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

- **`type`** — `MAPPOSITION_CURRENT` (0) or `MAPPOSITION_NEXT` (1), real named constants in
  `zcommon.bcs:1249-1252` matching the engine's internal enum order exactly. Any other value
  returns `0`, indistinguishable from "no rotation".
- The underlying `MAPROTATION_GetCurrentPosition()`/`GetNextPosition()` (`maprotation.cpp:134-144`)
  return 0-based indices; the `+ 1` makes the result 1-based.
- **Only `MAPPOSITION_CURRENT` has the current-map cross-check.** `MAPPOSITION_NEXT` reports
  `g_NextMapInList + 1` unconditionally once a non-empty rotation exists, since the next index is
  always a consistent slot in that same rotation.

**Example:**

```text
int pos = GetMapPosition(MAPPOSITION_CURRENT);
if (pos == 0)
{
    Log(s: "Not running from the map rotation (or no rotation configured).");
}
```

**Returns:** `int` — 1-based position, or `0` if there is no rotation, `type` is invalid, or (for
`MAPPOSITION_CURRENT` only) the running map doesn't match the rotation's current-position entry.
There is no separate "no rotation" vs. "map not in rotation" signal, as the wiki states.

## `int SetNextMapPosition(int position, bool ignoreLimits)`

**Provenance:** this member's wiki page was retrieved and source-verified 2026-08-18 (same
Zandronum 3.3-alpha @bdd0f7beb checkout), later than the other three.

Sets which rotation entry plays next.

- **`position`** — 1-based, valid `1..GetMapRotationSize()`. The engine computes
  `const unsigned int position = args[0] - 1`, so `0` underflows and fails the bound check: no
  "current map" meaning here, unlike `GetMapRotationInfo`.
- **`ignoreLimits`** — if `true`, the chosen next map ignores its configured min/max player limits
  when deciding whether it can load; if `false`, limits are enforced normally. Stored in
  `g_NextMapIgnoresLimits` by `MAPROTATION_SetNextPosition` (`maprotation.cpp:158-165`).

**Returns:** `1` on success, `0` on failure. Failure is either an out-of-range position
(`args[0] - 1 >= GetMapRotationSize()`) or a position that is **already** the next map, so
`SetNextMapPosition(GetMapPosition(MAPPOSITION_NEXT), ...)` always returns `0` (and does not update
`ignoreLimits` either).

**Clientside behavior and replication:** the call always mutates the local `g_NextMapInList`/
`g_NextMapIgnoresLimits`, wherever the script runs. The broadcast (`SERVERCOMMANDS_SetNextMapPosition()`)
is gated on `NETWORK_GetState() == NETSTATE_SERVER`, so a `CLIENTSIDE` call changes only that
client's own copy and replicates nowhere. To change the next map for everyone, call it from a
server-executed script.

## Engine-family divergence

All four sit in the ACSF (CALLFUNC) 100–199 range UZDoom's own ACSF enum reserves for Zandronum's
extensions and implements none of (indices 149, 150, 151, 178; `GetMapRotationInfo` confirmed via
`tools/engine_matrix.py GetMapRotationInfo`, bin `zandronum-only-silent`). UZDoom's `CallFunction`
dispatcher is a plain `switch` with `default: break;` falling through to `return 0`: no error, no
log line, the script keeps running. See
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general mechanism
(these four aren't individually listed there, but sit in the same block by construction). UZDoom
has no dedicated-server map-rotation concept for them to map onto.

How badly the silent `0` hides differs per member, because `0` already means something on
Zandronum:

- **`GetMapRotationSize`** — the sharpest case. `0` is the legitimate "no rotation" answer, so a
  caller can't tell "this server has no rotation" from "this engine doesn't implement the call". The
  wiki's `for (i = 1; i <= size; i++)` loop just never runs its body, which reads as an empty
  rotation during testing.
- **`GetMapPosition`** — equally invisible: `0` is its own "no rotation / not running from the
  rotation" sentinel.
- **`GetMapRotationInfo`** — for `USED`, `0` reads as "not yet played"; for `MINPLAYERS`, `0`
  collides with the "no minimum" sentinel; all three int properties match the Zandronum
  invalid-position fallback. Only `NAME`/`LUMPNAME` give it away: the caller gets plain integer `0`
  where Zandronum returns a string handle, which is more likely to surface as a type mismatch.
- **`SetNextMapPosition`** — least acute. `0` is already the documented failure return, and the
  call's intent is a mutation, so `0` reliably means "it didn't happen" on either engine, even
  though the reason differs.
