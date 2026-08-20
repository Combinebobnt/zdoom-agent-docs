# Plane-trigger family

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki pages `SetFloorTrigger - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SetFloorTrigger&oldid=22655`) and
`SetCeilingTrigger - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SetCeilingTrigger&oldid=22656`) (both `_intake/`, retrieved 2026-07-29) +
source-verified against the Zandronum source (`p_acs.cpp:1928-2022,12104-12114`,
`p_spec.cpp:270-277`, `r_defs.h:320-323`) and `zt-bcc/src/builtin.c:97-98,245-246,462-480`,
`zt-bcc/src/semantic/asm.c:359`, `zt-bcc/lib/zasm.bcs:208`. Cross-referenced against
`functions/lineside.md` for the no-line-context `activationline`/`backSide` default. Both wiki
pages are accurate as far as they go (signature, sign convention, basic trigger premise) but say
nothing about zero-tag/first-match-only resolution, the silent no-op on a bad tag, the one-time
threshold snapshot's non-monotonic-safety, the permanent `height == 0` dead case, or the frozen
activator/line/side context — all of those are this doc's source-verified additions.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** both compiler builtins. `PCD_SETFLOORTRIGGER` (the Zandronum source's `src/p_acs.cpp:12104`),
`PCD_SETCEILINGTRIGGER` (`p_acs.cpp:12110`), both inside `DLevelScript::RunScript`'s main switch,
both constructing a `DPlaneWatcher` thinker (`p_acs.cpp:1928-2022`). `zt-bcc/src/builtin.c`
`g_funcs[]` entries: `setfloortrigger` (line 97, format `";iii;rrrrr"`), `setceilingtrigger`
(line 98, same format) — 3 required ints (`tag`, `height`, `special`) plus 5 optional "raw" args
(`arg1`..`arg5`, `arg0`..`arg4` on the engine side) defaulting to a literal `0`
(`setup_default_value`, `builtin.c:462-480`).

`SetFloorTrigger`, `SetCeilingTrigger` — two compiler builtins that compile to opcodes sharing
one C++ implementation almost verbatim (`DPlaneWatcher`, differing only in a `ceiling` bool that
selects `sector->floorplane` vs `sector->ceilingplane`). Neither requires the other to be useful
— this isn't a mandatory-sequence family like [Lump I/O](lump-io.md) — but every non-trivial
behavior point below is identical prose for both, so one file avoids maintaining two
near-duplicate `functions/*.md` pages (same precedent as the [CVar family](cvar.md): independently
callable siblings that would otherwise duplicate the same source-verified mechanism twice).

---

## `void SetFloorTrigger(int tag, int height, int special [, int arg1 [, int arg2 [, int arg3 [, int arg4 [, int arg5]]]]])`
## `void SetCeilingTrigger(int tag, int height, int special [, int arg1 [, int arg2 [, int arg3 [, int arg4 [, int arg5]]]]])`

Arms a one-shot watcher on the (first) sector matching `tag`'s floor/ceiling: once that plane's
live height crosses a target computed from `height` at call time, runs `special(arg1..arg5)` and
self-destructs.

- **Not an instantaneous height comparison — arms a per-tic polling thinker.** At construction,
  `DPlaneWatcher` snapshots the target plane's current `d` constant as `LastD`, computes a target
  constant `WatchD` by applying `height` to a *copy* of that plane
  (`secplane_t::ChangeHeight(height << FRACBITS)`, `r_defs.h:320-323`; the real sector plane is
  untouched), then every tic (`Tick()`, `p_acs.cpp:1996-2020`) compares the plane's *current* live
  `d` against `LastD`/`WatchD`. It fires `P_ExecuteSpecial(...)` and `Destroy()`s itself the
  instant `(LastD < WatchD && current >= WatchD) || (LastD > WatchD && current <= WatchD)` holds —
  i.e. once the plane's height has moved from its original side of the target to the far side, by
  *any* means (a real mover special, a scripted z-set, another `SetFloorTrigger`/
  `SetCeilingTrigger`-driven change, or even repeated small nudges), not necessarily gradually —
  it only checks the current tic's height against the two fixed reference values, so an instant
  jump past the target in one tic still fires it. Each call arms exactly one watcher; firing
  self-destructs it, so watching again requires another call.
- `height` — a plain **map-unit int, not fixed-point** (the engine left-shifts by `FRACBITS`
  internally). Sign follows ordinary map convention and is identical for both functions: positive
  moves the watch point up, negative moves it down — confirmed via `ChangeHeight`'s internal sign
  compensation, which folds in each plane's own normal-direction coefficient automatically (opposite
  sign for floor vs. ceiling on a flat sector), so callers don't need to flip the sign themselves
  when switching between the two functions. Matches both wiki pages' own examples (`128` = up,
  `-64` = down).
- **`height == 0` is a permanent no-op, not "fires immediately."** `WatchD == LastD` in that case,
  and both branches of the OR require a *strict* `<`/`>`, so the crossing condition can never
  become true — the watcher sits inert, silently ticking with no effect, for the rest of the
  sector's existence (or the map, if the sector is never destroyed). Not documented on either wiki
  page; verified from `Tick()` directly.
- **`tag` resolution has no zero-tag special case, unlike sibling sector functions in the engine (both Zandronum and UZDoom).**
  Both opcodes call `P_FindSectorFromTag(tag, -1)` unconditionally (`p_acs.cpp:1962`) — unlike
  `GetSectorFloorZ`/`GetSectorCeilingZ` (see `functions/getsectorfloorz.md`), which treat `tag == 0`
  as "resolve by point-in-sector," or `Floor_MoveToValue`, which treats `tag == 0` as "use the
  triggering line's back sector." Here `tag = 0` searches for sectors literally tagged `0` — since
  most sectors in a typical map default to tag `0` (untagged), this watches whichever untagged
  sector's hash bucket resolves first (lowest sector number, the same `P_FindSectorFromTag`
  tie-break already verified for `GetSectorFloorZ`/`TagWait`), **not** "watch nothing" and **not**
  "watch a point." Neither wiki page mentions `tag == 0` at all — a source-only addition, not a
  wiki/fork divergence. Only the *first* matching sector is watched even if `tag` matches several —
  a shared tag does not arm watchers on all of them.
- **Bad/unmatched tag is a silent no-op, not a crash, undocumented by either wiki page.** If
  `P_FindSectorFromTag` finds nothing, the constructor sets `Sector = NULL` and `WatchD = LastD =
  0` (`p_acs.cpp:1980-1984`); the thinker still spawns, but its very first `Tick()` sees
  `Sector == NULL` and immediately `Destroy()`s (`p_acs.cpp:1998-2002`) without ever running
  `special` — one tic of the watcher's existence is burned, but nothing executes and nothing
  crashes. Indistinguishable from a call that "worked" but whose plane never happened to cross the
  threshold.
- **`special(arg1..arg5)` runs with the activator/line/side captured when `SetFloorTrigger`/
  `SetCeilingTrigger` was called, not re-resolved at trigger time.**
  `P_ExecuteSpecial(Special, Line, Activator, LineSide, Arg0..Arg4)` (`p_acs.cpp:2018`) uses the
  `activator`/`activationline`/`backSide` that were live for the *calling* script, held by the
  thinker for however many tics elapse until it fires. For a script with no line context at all
  (`OPEN`/`ENTER`/`RESPAWN`/etc., or an `ACS_Execute`-family start with no line), `activationline`
  is `NULL` and `backSide` is `false` — see `functions/lineside.md`'s already-verified breakdown of
  exactly which script-start paths leave these at that default — so `special` ends up executing
  with no line context / front-side, deterministically, regardless of what triggered the actual
  height change.
- The 5 optional trailing args are declared `"raw"` (`r`) params in `zt-bcc`, the same convention
  used for `SetLineSpecial`'s trailing args (see `functions/setlinespecial.md`) — they accept plain
  ints (or the compiler's named line-special constants) rather than a fixed type, matching how
  `special` itself is just an int index into the line-special table.
- Argument count/order and the basic "fires once the plane moves by `height`" premise both match
  each function's wiki page; no outright wiki/fork divergence was found for either (nothing either
  wiki claims turned out to be false) — every point above is a **material gap** in what the wiki
  says, not a correction of it.

## Engine-family divergence: unmatched-tag disposal never spawns a thinker; height uses native double math, not a fixed-point shift

Two internal-mechanism differences, neither changing what a calling script can observe.

**Unmatched tag.** Where the section above describes a bad/unmatched `tag` as spawning a thinker
that immediately `Destroy()`s itself on its very first `Tick()` — because the Zandronum
constructor unconditionally builds a `DPlaneWatcher` and only checks the found sector number
internally, leaving `Sector = NULL` when nothing matched — UZDoom's opcode handler
(`PCD_SETFLOORTRIGGER`/`PCD_SETCEILINGTRIGGER` in `src/playsim/p_acs.cpp`) checks
`Level->FindFirstSectorFromTag(tag) >= 0` *before* calling
`Level->CreateThinker<DPlaneWatcher>(...)` at all. If the tag doesn't resolve, no thinker is ever
created, so the `Sector == NULL` check inside UZDoom's `DPlaneWatcher::Tick()` is unreachable dead
code in this engine. The externally observable result is identical either way — `special` never
runs, nothing crashes, and there's no way for the calling script to detect the failure — only the
underlying mechanism (and whether one tic's worth of an inert thinker briefly exists) differs.

**Height units.** Where the section above describes `height` as internally left-shifted by
`FRACBITS` before being applied via `secplane_t::ChangeHeight`, UZDoom's sector planes are natively
double-precision map units (`secplane_t::ChangeHeight(double hdiff)` in `src/gamedata/r_defs.h`,
computing the new plane constant as the old constant minus `hdiff * normal.Z` directly) — there is
no fixed-point conversion step at all, because this engine's plane math was never fixed-point to
begin with. The sign convention and the "plain map-unit int, not fixed-point" contract from the
calling script's point of view are unchanged; only the fork-specific internal representation the
earlier prose called out differs.

**Returns:** nothing (`void`) for both — there is no way to detect from the calling script whether
`tag` resolved to a real sector; see the silent-no-op note above.

**Examples:**

```text
SetFloorTrigger(12, 128, ACS_Execute, 18, 0);
SetCeilingTrigger(12, 128, ACS_Execute, 18, 0);
```
