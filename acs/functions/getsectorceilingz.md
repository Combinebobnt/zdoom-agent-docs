# `fixed GetSectorCeilingZ(int tag, int x, int y)`

Returns the ceiling height of a tagged sector (or the sector at a point) at a given `(x, y)`
location, as a fixed-point value. Compiler builtin (`zt-bcc/src/builtin.c` `g_funcs[]` entry
`{ "getsectorceilingz", "f;iii" }`, opcode `PCD_GETSECTORCEILINGZ`), semantics in
the Zandronum source's `src/p_acs.cpp`, `case PCD_GETSECTORCEILINGZ:` (line 12058) — a single shared
`case` block with `PCD_GETSECTORFLOORZ` that differs only in which plane (`floorplane` vs
`ceilingplane`) is sampled at the end. See `functions/getsectorfloorz.md` for the floor-side
sibling; the two share every mechanic below except the plane sampled.

**Bucket:** compiler builtin.

- `x`, `y` — **plain map-unit integers, not fixed-point**, despite the fixed-point return value.
  The engine converts them (`x = STACK(2) << FRACBITS`) before evaluating the plane equation.
  This matches the wiki's own parenthetical ("not fixed point value!").
- `tag` — if non-zero, resolved via `P_FindSectorFromTag(tag, -1)`, which (per the verification
  done for `GetSectorFloorZ`, `p_setup.cpp:3463-3474` `P_InitTagLists`) always yields the
  lowest-numbered sector with a matching tag, confirming the wiki's "sector with the lowest
  sector number and matching tag wins" claim.
  - If `tag == 0`, the sector is instead resolved via `P_PointInSector(x, y)` — whatever sector
    geometrically contains `(x, y)`, ignoring tags entirely. Matches the wiki's "if tag is 0,
    returns the ceiling height of whatever sector is found at [x, y]."
  - **If `tag != 0` but no sector has that tag, or `tag == 0` and `(x, y)` isn't inside any
    sector, the function silently returns `0` (i.e. `0.0` fixed)** — indistinguishable from a
    real sector ceiling genuinely sitting at height 0. Not mentioned on the wiki page.
- Height computation is `sectors[secnum].ceilingplane.ZatPoint(x, y)` — confirmed independently
  for this function (not just inherited from the floor sibling): line 12083 dispatches to
  `ceilingplane` specifically when `pcd != PCD_GETSECTORFLOORZ`, i.e. for
  `PCD_GETSECTORCEILINGZ`. Same linear plane-equation evaluation as the floor case
  (`r_defs.h:267`, `FixedMul(ic, -d - DMulScale16(a, x, b, y))`), no bounds check against the
  sector's actual shape. For a flat (unsloped) ceiling, `a == b == 0`, so the result is a true
  constant regardless of `(x, y)`, confirming the wiki's "so [0, 0] is as good as anywhere"
  claim. For a sloped ceiling, `(x, y)` outside the sector's own area still evaluates the same
  infinite-plane formula — a genuine linear projection, not a clamped/error value.
- `tag`/point-resolution logic is byte-for-byte identical to `GetSectorFloorZ`'s — both branches
  of the shared `case` block (lines 12064–12074) run before the `pcd` check that picks the plane,
  so there is no floor/ceiling divergence in how `tag`, `x`, or `y` are interpreted.

**Example — read the ceiling height at the tagged sector's own origin (works for flat sectors):**

```
fixed z = GetSectorCeilingZ(sectorTag, 0, 0);
```

**Returns:** `fixed`, the ceiling height at `(x, y)` in the resolved sector, or `0.0` if no
matching sector could be resolved (see the silent-failure note above).

**Provenance:** wiki page `GetSectorCeilingZ - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=44121`) + source-verified (`p_acs.cpp:12057-12089`, shared block with
`PCD_GETSECTORFLOORZ`; `p_spec.cpp:270-277` `P_FindSectorFromTag`; `p_setup.cpp:3463-3474`
`P_InitTagLists`; `r_defs.h:267` `ZatPoint`). The wiki page's description of `tag`/`x`/`y`, the
`tag == 0` behavior, the flat-vs-sloped-plane distinction, and the "lowest sector number"
tiebreak all check out against this fork's source — no divergence found for this particular
function, and none expected given it shares its implementation block with the already-verified
`GetSectorFloorZ`. The one addition beyond the wiki is the silent `0` return on total failure (no
matching tag / point outside any sector), which the wiki doesn't mention. **Engine:** Zandronum
3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`).
**Tier:** A.
