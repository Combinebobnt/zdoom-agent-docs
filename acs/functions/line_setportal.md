# Line_SetPortal

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki (`_intake/Line_SetPortal - ZDoom Wiki.html`, retrieved from `https://zdoom.org/w/index.php?title=Line_SetPortal&oldid=45834`), verified against the Zandronum source.

Action special #156. The zt-bcc source's `lib/zcommon.bcs` does not expose a function named `Line_SetPortal` — this special is not callable by name from BCS.

## Status in Zandronum: Non-functional

**This feature is a ZDoom-only addition and is not implemented in this fork.** Special #156 maps to `LS_NOP` in the Zandronum source's `src/p_lnspec.cpp` (line 3756), a no-op placeholder. Any attempt to trigger this special (via `Line_SetLineSpecial` with a raw numeric call or other means) does nothing.

**Also checked for a static/map-editor escape hatch and found none.** Unlike [Sector_SetPortal](sector_setportal.md) (special #57), which is a genuine no-op via ACS/runtime triggering but *does* work when placed directly on a linedef and processed once at map load by `P_SpawnSpecials`/`P_SpawnPortal` in `p_spec.cpp`, `Line_SetPortal` has no such counterpart — `grep -rn "Line_SetPortal"` over the Zandronum source's `src/*.cpp` returns zero hits outside the `LS_NOP` table entry itself. This engine has no true line/wall portal rendering subsystem at all (no `r_portal.cpp`/`hw_portal.cpp`-equivalent file anywhere in the tree); the only portal-like feature that exists is `Sector_SetPortal`'s floor/ceiling-only "stacked sector" mechanism. A mapper cannot get any form of line-to-line portal working in this fork by any means.

The ZDoom wiki documents line-to-line portals with five portal type modes (`0`=visual-only, `1`=simple teleporter, `2`=interactive, `3`=static/Eternity-compatible, `4`=Eternity-compatibility wrapper). None of these are available in Zandronum. The related function `Line_SetPortalTarget` (special #107) is similarly non-functional — it also maps to `LS_NOP`.

## See also

- `Sector_SetPortal` (special #57, also `LS_NOP` in this fork) — another portal-related ZDoom-only feature.
