# `void ChangeLevel(str mapname, int position, int flags [, int skill])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes — the one flag with an `// [AK]` Zandronum-native tag,
`CHANGELEVEL_HIDENAME`, confirmed to predate the `28f736fb3` 3.2.1 version-bump commit; it does not
exist in UZDoom at all — see "Zandronum-specific: `CHANGELEVEL_HIDENAME` flag" below.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** wiki page `ChangeLevel - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=ChangeLevel&oldid=43453`) +
source-verified (`p_acs.cpp:12694-12701`, `g_level.cpp:678-737,1471,1479,1920`,
`g_game.cpp:2094,2108`, `g_level.h:530-541`, `zt-bcc/src/builtin.c:146,462-480`,
`zt-bcc/src/task.c:107-116`). All six flags the wiki documents (`KEEPFACING`,
`NOINTERMISSION`, `NOMONSTERS`, `PRERAISEWEAPON`, `RESETHEALTH`, `RESETINVENTORY`) check out
exactly as described; the empty-`mapname` end-game behavior, the dead `CHANGELEVEL_CHANGESKILL`
flag, the ACS-unreachable `CHANGELEVEL_HIDENAME` flag, and the omitted-`skill`-defaults-to-`0`
compiler mechanics are this doc's source-verified additions, not wiki-sourced.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Ends the current map and starts another. Compiler builtin (`PCD_CHANGELEVEL`, declared in
`zt-bcc/src/builtin.c`'s `g_funcs[]` as `{ "changelevel", ";sii;i" }` — no return type, three
required params (`str`,`int`,`int`), one optional `int`), handled in
the Zandronum source's `src/p_acs.cpp:12694-12701` (`case PCD_CHANGELEVEL:`), which forwards straight
into `G_ChangeLevel()` (`g_level.cpp:678`). Confirmed the same shape in the UZDoom source's
`src/playsim/p_acs.cpp:10101-10106` (`case PCD_CHANGELEVEL:`), which forwards straight into
`FLevelLocals::ChangeLevel()` (`src/g_level.cpp:719`) — same four-argument stack layout, but with no
flag-clearing at the dispatch site (UZDoom has no `CHANGELEVEL_HIDENAME` bit to strip; see below).

- `mapname` — lump name of the map to change to. **Passing `""` (empty string) does not error —
  it ends the game/cluster instead of changing maps**: `G_ChangeLevel` treats `levelname == NULL
  || *levelname == 0` as "end the game," picking up an existing end-sequence
  (`level.nextmap` starting `"enDSeQ"`) or synthesizing one from `gameinfo.DefaultEndSequence`
  (falling back to just re-loading the current map if running as a `NETSTATE_SERVER`, per the
  `// [BB]` comment). This wiki page never mentions the empty-string case at all — it's a
  source-verified addition, not a correction of anything the page claims. Confirmed the same
  end-game logic in UZDoom's `FLevelLocals::ChangeLevel` (`g_level.cpp:736-748`): the identical
  `levelname == NULL || *levelname == 0` check, the same "leave an existing end-sequence alone"
  short-circuit, and the same `enDSeQ%04x`-from-`DefaultEndSequence` synthesis. The
  `NETSTATE_SERVER` re-load fallback is Zandronum-only, though — see "Zandronum-specific:
  dedicated-server empty-mapname fallback" below.
- `position` — player start number, matched against the first argument of the corresponding
  player-start thing; `0` if there's only one start. Verified: stored as `static int startpos`
  (`g_level.cpp:665,736`) and consumed by `G_DoLoadLevel(startpos, ...)` on the next level setup.
  Confirmed identical in UZDoom, modulo storage class: `startpos` is a plain (non-`static`) global
  there (`g_level.cpp:104`), set the same way (`startpos = position;`, `g_level.cpp:784`) and
  consumed the same way (`G_DoLoadLevel(nextlevel, startpos, ...)`, `g_level.cpp:1115,1612`).
- `flags` — bitfield. Verified against the Zandronum source's `g_level.h:530-540` (values match
  `zcommon.bcs:971-977` exactly, same bit positions). UZDoom's `CHANGELEVEL_*` enum
  (`g_level.h:46-52`) carries the same six bit values for the six flags below, plus
  `CHANGELEVEL_CHANGESKILL`'s `0x8` (see below) — it just has no `CHANGELEVEL_HIDENAME` entry:
  - `CHANGELEVEL_KEEPFACING` (`0x1`) — player's angle is preserved; checked at
    `g_level.cpp:1920` (`if (!(changeflags & CHANGELEVEL_KEEPFACING))`), which otherwise resets
    facing to the destination player-start's angle. Confirmed identical in UZDoom: same guard,
    same bit value, same "reset facing otherwise" fallback (`g_level.cpp:1815`).
  - `CHANGELEVEL_RESETINVENTORY` (`0x2`) — checked at `g_game.cpp:2108`, unconditionally (no
    player-state gate). **This is a genuine cross-engine behavioral difference** — UZDoom gates
    this flag on the player not being dead, the same way it gates `RESETHEALTH` (see below); see
    "Engine-family divergence: `RESETINVENTORY` dead-player gating" below.
  - `CHANGELEVEL_NOMONSTERS` (`0x4`) — checked at `g_level.cpp:1471`. Confirmed identical in
    UZDoom (`g_level.cpp:1445`).
  - `CHANGELEVEL_NOINTERMISSION` (`0x10`) — checked at `g_level.cpp:728`, sets `LEVEL_NOINTERMISSION`.
    Confirmed identical in UZDoom (`g_level.cpp:776`, same flag).
  - `CHANGELEVEL_RESETHEALTH` (`0x20`) — checked at `g_game.cpp:2094`, only applies
    `if (p->playerstate != PST_DEAD)`. Confirmed identical in UZDoom, though the check has moved:
    UZDoom's `G_PlayerFinishLevel` (`g_game.cpp:1402`) is a thin dispatcher into a ZScript virtual
    function, `PlayerPawn.PlayerFinishLevel()` (`wadsrc/static/zscript/actors/player/player.zs:2187`),
    where the same flag-and-not-dead condition gates the health reset (`player.zs:2283`) — same
    behavior, different layer (native C++ in Zandronum vs. ZScript in UZDoom).
  - `CHANGELEVEL_PRERAISEWEAPON` (`0x40`) — checked at `g_level.cpp:1479`. Confirmed identical in
    UZDoom (`g_level.cpp:1453`).
  - **`CHANGELEVEL_CHANGESKILL` (`0x8`) is dead in both Zandronum and UZDoom.** In Zandronum, it's
    declared in both `g_level.h:533` and `zcommon.bcs:974` (so it compiles and takes a real bit
    position), but grepping all of the Zandronum source's `src/*.cpp` for the symbol finds only its
    two declaration sites — no `if (flags & CHANGELEVEL_CHANGESKILL)` anywhere. Whether the `skill`
    argument actually takes effect is controlled purely by `skill != -1` (see below), **not** by
    this flag. Setting or omitting `CHANGELEVEL_CHANGESKILL` has zero observable effect. Not
    mentioned on this wiki page (it isn't a ZDoom/base-ACS flag), so there's nothing to contradict —
    this is a pure fork-internals addition. UZDoom's copy of the flag is equally dead: declared at
    `g_level.h:49` and `wadsrc/static/zscript/constants.zs:1330`, checked nowhere in `src/` or
    `wadsrc/` — the same "declared, never gated" pattern, independently confirmed rather than
    assumed to carry over.
  - `CHANGELEVEL_HIDENAME` (`1<<31`, `g_level.h:540`) exists engine-side ("prevents the next
    level's name from appearing in the console... only used for the `SetCurrentGameMode` ACS
    function," per the `// [AK]` comment) but **has no `zcommon.bcs` constant and cannot be set
    from `ChangeLevel`ACS/BCS at all** — `PCD_CHANGELEVEL`'s handler unconditionally clears it
    (`STACK(2) & ~CHANGELEVEL_HIDENAME`, `p_acs.cpp:12696-12698`) before calling `G_ChangeLevel`,
    regardless of what bits the caller passed. It's reachable only through the separate
    `SetCurrentGameMode` internal call site (`p_acs.cpp:7578`). Predates the 3.2.1 version-bump
    commit (`28f736fb3`), so this doesn't run afoul of the 3.2.1-vs-3.3-alpha gate. **`CHANGELEVEL_HIDENAME`
    does not exist in UZDoom at all** — it's absent from UZDoom's `CHANGELEVEL_*` enum (`g_level.h:46-52`,
    which stops at `PRERAISEWEAPON = 64`) and from `constants.zs`'s copy of the same enum; a
    tree-wide grep of the UZDoom source and its `wadsrc/` ZScript stdlib for `HIDENAME` finds
    nothing. See "Zandronum-specific: `CHANGELEVEL_HIDENAME` flag" below.
- `skill` *(optional)* — 0-based skill index to switch to (e.g. `SKILL_NORMAL`). **`-1` keeps the
  current skill unchanged**; any other value (including `0`) sets it. Verified:
  `G_ChangeLevel`'s only skill-related line is `if (nextSkill != -1) NextSkill = nextSkill;`
  (`g_level.cpp:725-726`) — unconditional on any flag, matching the wiki's warning, and **with no
  bounds check on the value** — any `nextSkill != -1`, however out-of-range, is stored as-is.
  UZDoom differs here: see "Engine-family divergence: skill-index bounds checking" below. **Omitting
  the argument compiles to a literal `0`, not `-1`:** `zt-bcc`'s `setup_default_value()`
  (`builtin.c:462-480`) only special-cases `PCD_MORPHACTOR`'s string params; every other optional
  int (including `ChangeLevel`'s `skill`) falls through to `param->default_value =
  setup->task->dummy_expr` — a zero-initialized literal expression also aliased as
  `task->raw0_expr` (`task.c:107-116`). So `ChangeLevel("MAP01", 0, 0)` silently resets skill to
  `SKILL_VERY_EASY` (index 0), exactly as the wiki's "Note that omitting this parameter..."
  warning says — confirmed here at the compiler level, not just taken on the wiki's word.

**Returns:** nothing (`void`) — matches the declared signature; there is no result to check for
success/failure.

## Engine-family divergence: skill-index bounds checking

Zandronum's skill-index assignment is unconditional: `G_ChangeLevel`'s only relevant line is
`if (nextSkill != -1) NextSkill = nextSkill;` (`g_level.cpp:725-726`) — any value other than `-1`
is stored into the module-level `NextSkill` as-is, with no check against how many skills actually
exist. UZDoom's equivalent line bounds-checks it against the live skill count before storing
(`src/g_level.cpp:774`): an out-of-range index is discarded and `NextSkill` is set to `-1` instead
of the caller's value.

Both engines consume `NextSkill` identically at the next level load, confirmed by reading the
consumer on each side (Zandronum's `g_level.cpp:1337-1342`; UZDoom's `g_level.cpp:1394-1399`, same
shape): if `NextSkill` is non-negative, the `gameskill` cvar is force-set to it and `NextSkill` is
reset to `-1`; otherwise nothing happens. Because of that shared consumer, the two assignment
behaviors produce genuinely different outcomes for an
out-of-range **positive** `skill` argument (a negative value other than `-1` is already a no-op on
both, since the consumer's `>= 0` check rejects it either way): UZDoom's clamp-to-`-1` means the
consumer sees `NextSkill < 0` and skips the cvar force-set entirely — a true no-op, current skill
unchanged. Zandronum stores the out-of-range value unmodified, the consumer's `>= 0` check passes,
and `gameskill` gets force-set to that invalid index — an actual invalid-skill state, not merely a
theoretical one.

## Engine-family divergence: `RESETINVENTORY` dead-player gating

Zandronum applies `CHANGELEVEL_RESETINVENTORY` unconditionally: `G_PlayerFinishLevel`'s check is a
bare `if (flags & CHANGELEVEL_RESETINVENTORY)` (`g_game.cpp:2108-2112`), with no `playerstate`
condition — inventory is cleared and defaults re-given even for a dead player carrying the flag
into the level change. UZDoom gates `RESETINVENTORY` the same way it gates `RESETHEALTH`: the same
flag-set-and-not-dead condition (the UZDoom source's
`wadsrc/static/zscript/actors/player/player.zs:2289`) — a dead player's inventory is left alone on
UZDoom even with the flag set. `RESETHEALTH` itself has no such gap: both engines apply the same
not-dead condition to it (see the `flags` parameter notes above).

## Zandronum-specific: `CHANGELEVEL_HIDENAME` flag

`CHANGELEVEL_HIDENAME` (`1<<31`) is a Zandronum-only addition per the `// [AK]` comment at
`g_level.h:540` — it exists purely to suppress the next level's name from appearing in the console
for the separate `SetCurrentGameMode` ACS function, predates the 3.2.1 version-bump commit, and (as
noted above) can't even be set through `ChangeLevel` itself since `PCD_CHANGELEVEL`'s handler
unconditionally strips it before calling `G_ChangeLevel`. UZDoom carries no equivalent: the bit is
absent from its `CHANGELEVEL_*` enum (`g_level.h:46-52`, which only goes up to `PRERAISEWEAPON =
64`) and from `constants.zs`'s copy of the same enum, and a tree-wide grep of the UZDoom source and
its `wadsrc/` ZScript stdlib for `HIDENAME` turns up nothing. There is no `SetCurrentGameMode`-style
internal call site on UZDoom to reach it through either.

## Zandronum-specific: dedicated-server empty-mapname fallback

Zandronum's empty-`mapname` end-game path has a server-only special case: `G_ChangeLevel`, when
there's no existing end-sequence to reuse, checks `NETWORK_GetState() == NETSTATE_SERVER` and — per
the `// [BB]` comment "the server doesn't support end sequences, so just return to the current
map" — re-loads the current map instead of synthesizing an `enDSeQ`-prefixed end-sequence
(`g_level.cpp:701-706`). UZDoom's equivalent path (`g_level.cpp:736-748`) has no such branch — it
always synthesizes the `enDSeQ%04x`-from-`DefaultEndSequence` end-sequence name when no existing one
is being reused, with no dedicated-server case to divert around it. This tracks Zandronum's
dedicated-server architecture (`NETSTATE_SERVER`), which has no UZDoom analogue.
