# `fixed GetSectorFloorZ(int tag, int x, int y)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `GetSectorFloorZ - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=GetSectorFloorZ&oldid=44122`) + source-verified (`p_acs.cpp:12057-12089`, `p_spec.cpp:270-277`
`P_FindSectorFromTag`, `p_setup.cpp:3463-3474` `P_InitTagLists`, `r_defs.h:267` `ZatPoint`). The
wiki page's description of `tag`/`x`/`y`, the `tag == 0` behavior, the flat-vs-sloped-plane
distinction, and the "lowest sector number" tiebreak all check out against the Zandronum engine fork's source —
no divergence found for this particular function. The one addition beyond the wiki is the silent
`0` return on total failure (no matching tag / point outside any sector), which the wiki doesn't
mention.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Returns the floor height of a tagged sector (or the sector at a point) at a given `(x, y)`
location, as a fixed-point value. Compiler builtin (`zt-bcc/src/builtin.c` `g_funcs[]` entry
`{ "getsectorfloorz", "f;iii" }`, opcode `PCD_GETSECTORFLOORZ`), semantics in
the Zandronum source's `src/p_acs.cpp`, `case PCD_GETSECTORFLOORZ:` (line 12057) — a single shared
`case` block with `PCD_GETSECTORCEILINGZ` that differs only in which plane (`floorplane` vs
`ceilingplane`) is sampled at the end.

- `x`, `y` — **plain map-unit integers, not fixed-point**, despite the fixed-point return value.
  The engine itself converts them (`x = STACK(2) << FRACBITS`) before evaluating the plane
  equation. This matches the wiki's own parenthetical ("not fixed point value!").
- `tag` — if non-zero, resolved via `P_FindSectorFromTag(tag, -1)`. **The "sector with the lowest
  sector number and matching tag wins" claim is verified**, not just asserted by the wiki: the
  tag hash chains are built in `P_InitTagLists` (`p_setup.cpp:3463-3474`) by iterating sectors
  from last to first and prepending each to its tag's chain — the code comment there literally
  says "Proceed from last to first sector so that lower sectors appear first" — so `start=-1`
  always yields the lowest-numbered matching sector first.
  - If `tag == 0`, the sector is instead resolved via `P_PointInSector(x, y)` — whatever sector
    geometrically contains `(x, y)`, ignoring tags entirely. This matches the wiki's "if tag is 0,
    returns the floor height of whatever sector is found at [x, y]."
  - **If `tag != 0` but no sector has that tag, or `tag == 0` and `(x, y)` isn't inside any sector,
    the function silently returns `0` (i.e. `0.0` fixed)** — indistinguishable from a real sector
    floor genuinely sitting at height 0. Not mentioned on the wiki page.
- Height computation is `sectors[secnum].floorplane.ZatPoint(x, y)` — a linear plane-equation
  evaluation (`r_defs.h:267`, `FixedMul(ic, -d - DMulScale16(a, x, b, y))`) with **no bounds check
  against the sector's actual shape**. For a flat (unsloped) plane, `a == b == 0`, so the result
  is a true constant regardless of `(x, y)` — confirming the wiki's "so [0, 0] is as good as
  anywhere" claim. For a sloped plane, `(x, y)` outside the sector's own area still evaluates the
  same infinite-plane formula, i.e. a genuine linear projection as the wiki describes, not a
  clamped/error value.

**Example — read the floor height at the tagged sector's own origin (works for flat sectors):**

```text
fixed z = GetSectorFloorZ(sectorTag, 0, 0);
```

**Returns:** `fixed`, the floor height at `(x, y)` in the resolved sector, or `0.0` if no matching
sector could be resolved (see the silent-failure note above).
