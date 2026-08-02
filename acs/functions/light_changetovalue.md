# `int Light_ChangeToValue(int tag, int value)`

Sets the light level in sector(s) matching `tag` to a specified value. Action special (positive
index 112 in `zcommon.bcs`'s `special` table), semantics in the Zandronum source's `src/p_lnspec.cpp`,
`FUNC(LS_Light_ChangeToValue)` (line 1945), which forwards into `EV_LightTurnOn`
(`p_lights.cpp:503`).

**Bucket:** action special.

- `tag` — sector tag to affect. **No special handling for `tag == 0`** — it matches literal tag-0
  sectors only, same as any other tag (verified against `P_FindSectorFromTag`, which always
  compares `sectors[start].tag != tag` with no zero-tag fallback). Unlike `Floor_MoveToValue`
  (which uses the triggering line's back sector when `tag == 0`), this special has no activator
  dependency at all — see below.
- `value` — light level to assign to each tagged sector. **Clamped to `[SHRT_MIN, SHRT_MAX]`**
  (`-32768` to `32767`, verified via `SetLightLevel → ClampLight`), though valid visual light
  levels are `[0, 255]`. **If `value < 0`, instead of setting all sectors to a negative level, the
  function searches for the maximum light level among each sector's *adjacent* (line-connected)
  neighbors and sets that sector to that max** — i.e., `Light_ChangeToValue(tag, -1)` is a
  hidden "set each sector to its brightest neighbor's level" operation (a sibling special
  `Light_MaxNeighbor`, action special 234, deliberately uses `value == -1`). The per-sector
  independent-vs-cumulative scope is controlled by the `COMPATF_LIGHT` flag, which is only
  meaningful when `value < 0` — in normal use (`value >= 0`), the flag is a no-op.

**Return:** `int`, always `true`/`1` unconditionally, regardless of whether any sector matched `tag`.
This is not a success signal; it is identical to the "always returns true" pattern documented for
`ACS_Terminate`/`ACS_Suspend`/`ACS_NamedTerminate` — a failed tag match is silent.

**Activator-independent:** No activator or line reference in the implementation
(`EV_LightTurnOn` never touches `ln` or `it` parameters), so this special is safe in `OPEN`
scripts and other contexts where an activator is absent or unknown.

**Zandronum netcode:** On the server, each affected sector's light level change is broadcast to
clients via `SERVERCOMMANDS_SetSectorLightLevel`, and the sector is marked `bLightChange = true` so
clients can sync when they join later. This Zandronum-specific replication is not mentioned by the
ZDoom wiki page.

**Provenance:** wiki page `Light_ChangeToValue - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=44599`) + source-verified (`p_lnspec.cpp:1945-1950`, `p_lights.cpp:503-548`,
`P_FindSectorFromTag` in `p_spec.cpp:270-277`). The ZDoom wiki page is **incomplete, not wrong** —
it correctly describes the `value >= 0` path ("Sets the light level in a sector to value") but
omits the `value < 0` neighbor-max-search behavior entirely. The `tag == 0` fallback documented
for other sector specials does not apply here. The Zandronum netcode and clamping behavior are
additions verified against source. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source
`master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
