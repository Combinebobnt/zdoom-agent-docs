# Line_SetPortal

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki (`_intake/Line_SetPortal - ZDoom Wiki.html`, retrieved from `https://zdoom.org/w/index.php?title=Line_SetPortal&oldid=45834`), verified against the Zandronum source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Action special #156. The zt-bcc source's `lib/zcommon.bcs` does not expose a function named `Line_SetPortal` — this special is not callable by name from BCS. This is a compiler-tooling note about zt-bcc/bcc (the Zandronum-targeting BCS compiler), not an engine claim — it doesn't bear on whether either engine implements the special itself, since a raw numeric special call (`Line_SetLineSpecial`, a `LineSpecial` action, or a map-editor-assigned linedef special) reaches the same underlying dispatch regardless of whether a named wrapper function exists.

## Status on Zandronum: non-functional (re-confirmed this pass)

**This feature is a ZDoom-only addition and is not implemented in Zandronum.** Special #156 maps to `LS_NOP` in the Zandronum source's `src/p_lnspec.cpp` (line 3756), a no-op placeholder in the same table used both for ACS-triggered calls and for a player crossing/using/shooting a live line carrying this special. Any attempt to trigger this special (via `Line_SetLineSpecial` with a raw numeric call or other means) does nothing on Zandronum.

**Also checked for a static/map-editor escape hatch and found none.** Unlike [Sector_SetPortal](sector_setportal.md) (special #57), which is a genuine no-op via ACS/runtime triggering but *does* work when placed directly on a linedef and processed once at map load by `P_SpawnSpecials`/`P_SpawnPortal` in `p_spec.cpp`, `Line_SetPortal` has no such counterpart on Zandronum — `grep -rn "Line_SetPortal"` over the entire Zandronum source tree (not just `src/*.cpp`) returns **zero hits anywhere**, not even a comment on the `LS_NOP` table entry. Zandronum has no line-to-line portal *concept* in its own engine model at all — no `FLinePortal`-equivalent struct, no line-portal array, nothing a map-load scan could dispatch into even if it wanted to.

**Correction to an earlier pass on this file:** the previous claim that "this engine has no true line/wall portal rendering subsystem at all (no `r_portal.cpp`/`hw_portal.cpp`-equivalent file anywhere in the tree)" overstated the case. `src/gl/scene/gl_portal.cpp`/`gl_portal.h` and `src/gl/data/gl_portaldata.cpp` do exist and do implement a `GLPortal` base class with several subclasses. None of them render a `Line_SetPortal`-style line-to-line portal, though: `GLMirrorPortal` is wired to `RENDERWALL_MIRROR`/`Line_Mirror` lines (`src/gl/scene/gl_walls.cpp:232-236`) — a visually-reflective special, not a teleporting/interactive one — and the rest (`GLSkyboxPortal`, `GLSkyPortal`, `GLHorizonPortal`, `GLPlaneMirrorPortal`, `GLSectorStackPortal`) back skybox/horizon/mirror effects or [Sector_SetPortal](sector_setportal.md)'s stacked-sector mechanism. The substance of the old claim (no working line-to-line portal exists on Zandronum) holds; its literal "no portal-rendering file exists" framing did not.

The ZDoom wiki documents line-to-line portals with five portal type modes (`0`=visual-only, `1`=simple teleporter, `2`=interactive, `3`=static/Eternity-compatible, `4`=Eternity-compatibility wrapper). None of these are available on Zandronum. The related function `Line_SetPortalTarget` (special #107) is similarly non-functional on Zandronum — it also maps to `LS_NOP` (`p_lnspec.cpp:3707`).

## Engine-family divergence: fully functional on UZDoom

UZDoom implements this special for real, contradicting the Zandronum-only assumption the rest of this file was originally built around. It's declared at `src/playsim/actionspecials.h:169` (`DEFINE_SPECIAL(Line_SetPortal, 156, -1, -1, 4)`) and, like `Sector_SetPortal`, is handled only as a **static, map-editor-placed, load-time** special — not an ACS/BCS-callable one. UZDoom's own runtime dispatch table (`src/playsim/p_lnspec.cpp:3703`) also carries `LS_NOP` at special #156, so `Line_SetLineSpecial` or a live-triggered line still does nothing at runtime, on both engines equally. The actual work happens in `MapLoader::SpawnLinePortal` (`src/maploader/specials.cpp:86-162`), called once per matching line from the per-line map-load scan's `case Line_SetPortal: case Line_QuickPortal:` (`src/maploader/specials.cpp:753-755`).

`args[2]` selects the portal type, matching the wiki's five modes exactly against the engine's `PORTT_*` enum (`src/playsim/portal.h:173-177`):

- `0` = `PORTT_VISUAL` — visual-only (see-through, not passable).
- `1` = `PORTT_TELEPORT` — a simple teleporter (passable, without true visual continuity through the wall).
- `2` = `PORTT_INTERACTIVE` — full visual continuity plus actor passage; downgraded to `PORTT_TELEPORT` with a console warning if `args[3]` requests anything other than absolute z-alignment, since interactive portals can't support a z-offset.
- `3` = `PORTT_LINKED` — the "static"/linked-portal form; always uses absolute alignment regardless of `args[3]`.
- `4` = `PORTT_LINKEDEE` — the Eternity-compatible one-line-ID wrapper (see below).

For types `0`-`2`, `args[0]` is the destination line's tag: `FLevelLocals::FindPortalDestination` (`src/playsim/portal.cpp:178-194`) looks up a line whose own line ID equals `args[0]` via `GetLineIdIterator`, and pairs the two lines into one `FLinePortal`. On a Hexen-format map, that "own line ID" comes from `MapLoader::SetLineID` (`src/maploader/maploader.cpp:1501-1503`): for a line carrying the `Line_SetPortal` special, its line ID is drawn from `args[1]`, not the ordinary tag field — so a paired portal's two lines cross-reference each other through `args[0]`/`args[1]` rather than sharing one tag the way most tagged specials do. `args[3]` selects z-alignment for the non-`PORTT_LINKED` types via `PORG_ABSOLUTE`/`PORG_FLOOR`/`PORG_CEILING` (`src/playsim/portal.h:182-184`).

Type `4` (`PORTT_LINKEDEE`) uses a different pairing convention entirely, matching the wiki's "Eternity-compatibility wrapper" description: it requires `args[0] == 0` on the line acting as the portal's "target," and searches for another `Line_SetPortal` line sharing the same first line ID with `args[0] == 1` (the "anchor"); once matched, both directions of an interactive linked portal are spawned as a pair. This is the shape the engine's own built-in Doom-format Eternity translation uses to reconstruct Eternity's two specials (`wadsrc/static/xlat/eternity.txt:156-157`: Doom-format specials 376/377 map to `Line_SetPortal(0, tag, 4)` and `Line_SetPortal(1, tag, 4)` respectively — i.e. Eternity's `Portal_LinkedLineToLine`/`Portal_LinkedLineToLineAnchor` pair).

`Line_SetPortalTarget` (special #107) is also implemented on UZDoom — unlike Zandronum, where it's `LS_NOP` alongside `Line_SetPortal` itself (see above). On UZDoom it *is* runtime/ACS-callable (`FUNC(LS_Line_SetPortalTarget)`, `src/playsim/p_lnspec.cpp:3413-3417`, `Line_SetPortalTarget(thisid, destid)`), calling `FLevelLocals::ChangePortal` to re-point an already-spawned line portal's `thisid` end at a new `destid` destination at runtime — a genuinely different capability from `Line_SetPortal` itself, which only ever builds portals once, at map load.

## See also

- [Sector_SetPortal](sector_setportal.md) (special #57) — the older, floor/ceiling-only "stacked sector" portal mechanism. Correction to the old bullet here: it is not Zandronum-`LS_NOP`-only — it has its own functional static/map-load path on Zandronum too (see that file), so it isn't purely a "ZDoom-only feature" the way `Line_SetPortal` is on Zandronum.
