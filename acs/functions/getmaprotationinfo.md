# `raw GetMapRotationInfo(int position, int info)`

**Tier:** A
**Engine:** Zandronum 3.2.1 — added in `4e38a84d7` ("Added ACS functions: GetMapRotationSize and GetMapRotationInfo..."), confirmed an ancestor of `28f736fb3` (the "changed the version string to 3.2.1" commit), so this predates and is included in the 3.2.1 target, not just the local 3.3-alpha checkout.
**Provenance:** `GetMapRotationInfo - Zandronum Wiki.html` (wiki `oldid=1369`), verified against the Zandronum source 2026-07-29.
**Bucket:** extension function.

Reads one property of one entry in the server's map rotation list. Extension function
(`ACSF_GetMapRotationInfo`, index `-150` in the zt-bcc source's `lib/zcommon.bcs:1780`), implementation
in `DLevelScript::CallFunction`, the Zandronum source's `src/p_acs.cpp:7874-7914`.

## Parameters

- `position` — index into the map rotation, **1-based** for actual entries. `0` (or, per the
  code, anything `<= 0`) means "the current map" and is handled specially — see below.
  Otherwise must be between `1` and `GetMapRotationSize()`; internally the engine does
  `ulPosition = args[0] - 1` to convert to the 0-based `g_MapRotationEntries` index.
- `info` — one of (values match the zt-bcc source's `lib/zcommon.bcs:1242-1246` and the wiki):
  - `MAPROTATION_NAME` = 0 — the map's display name (`level_info_t::LookupLevelName()`), e.g.
    `"Entryway"`.
  - `MAPROTATION_LUMPNAME` = 1 — the map lump name, e.g. `"MAP01"`.
  - `MAPROTATION_USED` = 2 — whether this entry has already been played this rotation cycle
    (`MAPROTATION_IsUsed`).
  - `MAPROTATION_MINPLAYERS` = 3 — minimum player count required to load the map; `0` = no
    minimum.
  - `MAPROTATION_MAXPLAYERS` = 4 — maximum player count allowed; `64` = no maximum.

## Return value

The declared type is `raw`, and which real type comes back depends on `info`:

- `MAPROTATION_NAME` / `MAPROTATION_LUMPNAME` → a **string handle** (`GlobalACSStrings.AddString`),
  not a plain int — must be printed with `s:` / treated as a string, matching the wiki's example.
- `MAPROTATION_USED` / `MAPROTATION_MINPLAYERS` / `MAPROTATION_MAXPLAYERS` → a plain int.
- Any other `info` value falls through the `switch` with no `default`, and the function returns
  `0` after the switch (`p_acs.cpp:7913`) — silently, same as an out-of-range property in
  `GetActorProperty`.

## Failure behavior (undocumented by the wiki)

The wiki does not mention this, and it's the main reason this page earns a doc file:

- If `position` resolves to an out-of-range rotation index (`MAPROTATION_GetMap` returns `NULL`
  for `position >= g_MapRotationEntries.size()`), the function returns `""` for
  `MAPROTATION_NAME`/`MAPROTATION_LUMPNAME` and `0` for every other `info` value
  (`p_acs.cpp:7888-7897`).
- **`position <= 0` (the "current map" case) has an extra validity check the wiki omits:** the
  engine takes `ulPosition = MAPROTATION_GetCurrentPosition()`, looks up that rotation entry, and
  then additionally requires `level.mapname` (the map actually running right now) to
  case-insensitively match that entry's `mapname`. If they don't match — e.g. the server is
  running a map that isn't the rotation's current-position entry at all (loaded manually, via
  `map`/`changemap`, votes, etc.) — the function falls into the same "invalid" branch as an
  out-of-range `position` and returns `""`/`0`, *not* information about whatever the rotation
  object thinks the current position is. So `GetMapRotationInfo(0, ...)` is not simply "always
  describes the current map"; it's "describes the current map only if the rotation agrees the
  current map is also its current-position entry."
- There is no maplist / empty rotation: `g_MapRotationEntries` is empty, so
  `MAPROTATION_GetMap` returns `NULL` for every position (including the `position <= 0` branch,
  since `MAPROTATION_GetCurrentPosition()` on an empty list is still an invalid index) → same
  `""`/`0` fallback.

## Example (from the wiki, semantics unchanged)

```
Script 1 OPEN {
	int size = GetMapRotationSize();
	Log(d: size, s: " maps are in the rotation.");

	// Note: the list starts at 1; position 0 is the current map.
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

## See also

- `GetMapRotationSize()` — returns `g_MapRotationEntries.size()` (`MAPROTATION_GetNumEntries`),
  the valid upper bound for `position`. Documented separately (being processed alongside this
  file in the same intake batch).
- `GetMapPosition` — a related extension function (`ACSF_GetMapPosition`,
  `p_acs.cpp:7916` onward) for querying the rotation's current/next *position* rather than a
  given entry's info; also being processed alongside this file in the same intake batch. **Not
  merged into a shared family file here** — this page only covers `GetMapRotationInfo`. If a
  future pass decides `GetMapRotationInfo`/`GetMapRotationSize`/`GetMapPosition` belong together
  as a `families/map-rotation.md`, that consolidation should happen as a deliberate follow-up,
  not as a side effect of processing one intake file.
