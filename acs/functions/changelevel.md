# `void ChangeLevel(str mapname, int position, int flags [, int skill])`

Ends the current map and starts another. Compiler builtin (`PCD_CHANGELEVEL`, declared in
`zt-bcc/src/builtin.c`'s `g_funcs[]` as `{ "changelevel", ";sii;i" }` — no return type, three
required params (`str`,`int`,`int`), one optional `int`), handled in
the Zandronum source's `src/p_acs.cpp:12694-12701` (`case PCD_CHANGELEVEL:`), which forwards straight
into `G_ChangeLevel()` (`g_level.cpp:678`).

**Bucket:** compiler builtin.

- `mapname` — lump name of the map to change to. **Passing `""` (empty string) does not error —
  it ends the game/cluster instead of changing maps**: `G_ChangeLevel` treats `levelname == NULL
  || *levelname == 0` as "end the game," picking up an existing end-sequence
  (`level.nextmap` starting `"enDSeQ"`) or synthesizing one from `gameinfo.DefaultEndSequence`
  (falling back to just re-loading the current map if running as a `NETSTATE_SERVER`, per the
  `// [BB]` comment). This wiki page never mentions the empty-string case at all — it's a
  source-verified addition, not a correction of anything the page claims.
- `position` — player start number, matched against the first argument of the corresponding
  player-start thing; `0` if there's only one start. Verified: stored as `static int startpos`
  (`g_level.cpp:665,736`) and consumed by `G_DoLoadLevel(startpos, ...)` on the next level setup.
- `flags` — bitfield. Verified against `g_level.h:530-540` (values match `zcommon.bcs:971-977`
  exactly, same bit positions):
  - `CHANGELEVEL_KEEPFACING` (`0x1`) — player's angle is preserved; checked at
    `g_level.cpp:1920` (`if (!(changeflags & CHANGELEVEL_KEEPFACING))`), which otherwise resets
    facing to the destination player-start's angle.
  - `CHANGELEVEL_RESETINVENTORY` (`0x2`) — checked at `g_game.cpp:2108`.
  - `CHANGELEVEL_NOMONSTERS` (`0x4`) — checked at `g_level.cpp:1471`.
  - `CHANGELEVEL_NOINTERMISSION` (`0x10`) — checked at `g_level.cpp:728`, sets `LEVEL_NOINTERMISSION`.
  - `CHANGELEVEL_RESETHEALTH` (`0x20`) — checked at `g_game.cpp:2094`, only applies
    `if (p->playerstate != PST_DEAD)`.
  - `CHANGELEVEL_PRERAISEWEAPON` (`0x40`) — checked at `g_level.cpp:1479`.
  - **`CHANGELEVEL_CHANGESKILL` (`0x8`) is dead in this fork.** It's declared in both
    `g_level.h:533` and `zcommon.bcs:974` (so it compiles and takes a real bit position), but
    grepping all of the Zandronum source's `src/*.cpp` for the symbol finds only its two declaration
    sites — no `if (flags & CHANGELEVEL_CHANGESKILL)` anywhere. Whether the `skill` argument
    actually takes effect is controlled purely by `skill != -1` (see below), **not** by this
    flag. Setting or omitting `CHANGELEVEL_CHANGESKILL` has zero observable effect. Not mentioned
    on this wiki page (it isn't a ZDoom/base-ACS flag), so there's nothing to contradict — this
    is a pure fork-internals addition.
  - `CHANGELEVEL_HIDENAME` (`1<<31`, `g_level.h:540`) exists engine-side ("prevents the next
    level's name from appearing in the console... only used for the `SetCurrentGameMode` ACS
    function," per the `// [AK]` comment) but **has no `zcommon.bcs` constant and cannot be set
    from `ChangeLevel`ACS/BCS at all** — `PCD_CHANGELEVEL`'s handler unconditionally clears it
    (`STACK(2) & ~CHANGELEVEL_HIDENAME`, `p_acs.cpp:12696-12698`) before calling `G_ChangeLevel`,
    regardless of what bits the caller passed. It's reachable only through the separate
    `SetCurrentGameMode` internal call site (`p_acs.cpp:7578`). Predates the 3.2.1 version-bump
    commit (`28f736fb3`), so this doesn't run afoul of the 3.2.1-vs-3.3-alpha gate.
- `skill` *(optional)* — 0-based skill index to switch to (e.g. `SKILL_NORMAL`). **`-1` keeps the
  current skill unchanged**; any other value (including `0`) sets it. Verified:
  `G_ChangeLevel`'s only skill-related line is `if (nextSkill != -1) NextSkill = nextSkill;`
  (`g_level.cpp:725-726`) — unconditional on any flag, matching the wiki's warning. **Omitting
  the argument compiles to a literal `0`, not `-1`:** `zt-bcc`'s `setup_default_value()`
  (`builtin.c:462-480`) only special-cases `PCD_MORPHACTOR`'s string params; every other optional
  int (including `ChangeLevel`'s `skill`) falls through to `param->default_value =
  setup->task->dummy_expr` — a zero-initialized literal expression also aliased as
  `task->raw0_expr` (`task.c:107-116`). So `ChangeLevel("MAP01", 0, 0)` silently resets skill to
  `SKILL_VERY_EASY` (index 0), exactly as the wiki's "Note that omitting this parameter..."
  warning says — confirmed here at the compiler level, not just taken on the wiki's word.

**Returns:** nothing (`void`) — matches the declared signature; there is no result to check for
success/failure.

**Provenance:** wiki page `ChangeLevel - ZDoom Wiki.html` (`_intake/`, `oldid=43453`) +
source-verified (`p_acs.cpp:12694-12701`, `g_level.cpp:678-737,1471,1479,1920`,
`g_game.cpp:2094,2108`, `g_level.h:530-541`, `zt-bcc/src/builtin.c:146,462-480`,
`zt-bcc/src/task.c:107-116`). All six flags the wiki documents (`KEEPFACING`,
`NOINTERMISSION`, `NOMONSTERS`, `PRERAISEWEAPON`, `RESETHEALTH`, `RESETINVENTORY`) check out
exactly as described; the empty-`mapname` end-game behavior, the dead `CHANGELEVEL_CHANGESKILL`
flag, the ACS-unreachable `CHANGELEVEL_HIDENAME` flag, and the omitted-`skill`-defaults-to-`0`
compiler mechanics are this doc's source-verified additions, not wiki-sourced. **Engine:**
Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in
`../../shared/AUTHORING.md`; the one flag with an `// [AK]` Zandronum-native tag, `CHANGELEVEL_HIDENAME`,
confirmed to predate the `28f736fb3` 3.2.1 version-bump commit). **Tier:** A.
