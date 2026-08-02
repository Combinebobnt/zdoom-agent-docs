# `str GetActorSectorLocation(int tid, bool point)`

**Tier:** A.
**Engine:** Zandronum 3.2.1 — introducing commit `1387a120e` ("Added ACS function: 'GetActorSectorLocation'.", 2022-02-20) confirmed via `git merge-base --is-ancestor` to predate the `28f736fb3` ("changed the version string to 3.2.1") version-bump commit in the local the Zandronum source checkout, i.e. it ships in 3.2.1, not just the checkout's `3.3-alpha` HEAD.
**Provenance:** wiki page `GetActorSectorLocation - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=2244`) + source-verified against `p_acs.cpp:5518,7955-7994`, `zcommon.bcs:1783`. Cross-checked against `functions/getcontrolpointinfo.md`'s documented `point`-index semantics, which the `point == true` branch here directly feeds. Wiki/fork divergence: wiki implies both modes return a name string; the `point == true` mode actually returns a raw control-point index (or `-1`), never a string.
**Bucket:** extension function (negative index, `p_acs.cpp`'s `ACSF_*` switch).

Extension function, `zcommon.bcs:1783` declares it at index `-153`
(`ACSF_GetActorSectorLocation`, the Zandronum source's `src/p_acs.cpp:5518`), implementation is the
`case ACSF_GetActorSectorLocation:` block at `p_acs.cpp:7955-7994`.

- `tid` — TID of the actor to look up, resolved via `SingleActorFromTID` (`p_acs.cpp:4445-4456`).
  **`tid == 0` uses the activator** (`defactor` param), matching the wiki.
- `point` — selects between two entirely different lookups and, contrary to the declared `str`
  return type and the wiki's description, **two different return *kinds***:
  - `point == false` (default sector lookup): looks up `pActor->Sector->sectornum` in
    `level.info->SectorInfo.Names` (parsed from the map's `SECTINFO` lump) and returns a real
    **string handle** (`GlobalACSStrings.AddString(...)`) — either the sector's SECTINFO-assigned
    name, or `""` if the actor is invalid, its sector has no entry in `Names`, or the entry is
    null. Safe to read as `str` in all cases, exactly as the wiki describes.
  - `point == true` (point-sector lookup): searches `level.info->SectorInfo.Points` for a point
    sector containing the actor's sector, and if found **returns the raw integer index `i` of the
    matching point** in that array — the *same* index `GetControlPointInfo(point, type)`
    (`functions/getcontrolpointinfo.md`) expects as its first argument — **not a string handle at
    all**. If the actor is invalid or no matching point sector is found, it returns the plain
    integer `-1`, not an empty string.

## Wiki/fork divergence: `point == true` does not return a string, despite the signature

The wiki page states the function "Returns a string containing the name of the (point) sector,"
implying `point == true` still gives back a name string (just derived from the point-sector table
instead of `Names`). The actual C++ (`p_acs.cpp:7969-7985,7993`) does nothing of the kind — it
returns a bare `unsigned int`/`-1` index value, never touching `GlobalACSStrings` in that branch.
A caller that does `str s = GetActorSectorLocation(tid, true); Log(s: s);` will not print a point
name — it will print whatever garbage the engine's string table happens to have at that raw index
position (or crash/misbehave, since the value was never registered as a string). The correct
usage for `point == true` is to treat the result as an `int` — typically to feed straight into
`GetControlPointInfo(result, POINTINFO_NAME)` to actually get a name back. This is corroborated by
an in-source comment right above the branch: `// [TRSR] We'd actually rather return the index of
the control point for GetControlPointInfo now.` — i.e. even the Zandronum maintainers describe
this branch as reusing (overloading) the function for a different, newer purpose than what its
name/wiki-declared signature suggest, rather than it being an oversight.

**Example — correct usage for both modes:**

```
// Get this map's SECTINFO name for the sector the activator is standing in.
str sectorName = GetActorSectorLocation(0, false);

// Get the *index* of the point sector the activator is standing in (Domination-style maps),
// then resolve that index to an actual name via GetControlPointInfo — do NOT read the
// GetActorSectorLocation(tid, true) result itself as a string.
int pointIndex = GetActorSectorLocation(0, true);
if (pointIndex != -1)
{
    str pointName = GetControlPointInfo(pointIndex, POINTINFO_NAME);
    Log(s: pointName);
}
```
