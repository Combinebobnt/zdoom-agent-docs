# What the bot A* pathfinder can actually reach

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/astar.cpp` (`ASTAR_Path`, `astar_ProcessNextPathNode`, the path-smoothing pass), `src/botpath.cpp` (`BOTPATH_TryWalk`, `BOTPATH_IsPositionBlocked`), `src/botcommands.cpp` (`botcmd_PathToGoal` and its siblings) and `src/p_user.cpp` (`APlayerPawn::CalcJumpHeight`, `APlayerPawn::CalcJumpVelz`), first at @bdd0f7beb (2026-09-18). The solid-goal-actor section was added 2026-09-23 from the same files at @bdd0f7beb (also reading `botpath_CheckThing` and `astar_PullNodeFromOpenList`); all four files are unchanged between the two revisions, so line numbers cited here hold for both. The node-grid, search-budget, walk-blocking and north-west-diagonal sections were added later on 2026-09-23 from the same revision, also reading `src/astar.h`, `src/botcommands.h`, `src/bots.cpp`, `src/p_setup.cpp` and `wadsrc/static/actors/shared/player.txt`; where a claim there postdates the 3.2.1 version bump it says so inline. The overlapping-actor section was added 2026-09-24 at @bdd0f7beb, also reading `src/p_local.h` (`MAXMOVE`), `src/botcommands.h` (the `PATH_*` values), `src/p_things.cpp` (`P_MoveThing`) and `src/p_map.cpp` (`P_TestMobjLocation`, `PIT_CheckThing`, `P_CheckUnblock`); `src/botpath.cpp`, `src/astar.cpp` and `src/botcommands.cpp` are unchanged since @bdd0f7beb, so earlier line numbers still hold. The node-index formula, the out-of-grid goal case and the grid-corner offset and floor-check bullets were added 2026-09-25 at @bdd0f7beb, also reading `astar_GetNodeFromPoint`, `ASTAR_BuildNodes` and `ASTAR_Path`'s NULL-goal-node branch in `src/astar.cpp`, and `src/p_acs.cpp` (`PCD_GETSECTORFLOORZ`); the grid formula and the `tag` 0 point lookup were also checked at the 3.2.1 version bump `28f736fb3`. The file's empirical figures come from logged `PathToGoal` results in a live game. The height-frame behavior was additionally confirmed empirically: a flood fill of a real map's per-cell floor heights under the rule derived here reproduced exactly the set of floor heights a bot was observed to occupy over a full session, where a relative-step rule predicted the whole map. The UZDoom=no claim is not re-verified here; it rests on the direct UZDoom-checkout check recorded in `botscript-lump-format.md`'s provenance, which established that UZDoom's bot implementation is an unrelated one. No wiki page covers the pathfinder.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## Engine-family divergence

The A\* pathfinder in `src/astar.cpp` exists only to serve Zandronum's bot commands, which live in
a bot-command dispatcher (`botcommands.cpp`) that UZDoom/GZDoom-family engines don't have at all.
UZDoom's `src/playsim/bots/` is an unrelated bot implementation and has no counterpart to this
search, so there is nothing to diverge from; see `../AGENTS.md`.

The bot pathing commands (`PathToGoal`, `PathToLastKnownEnemyPosition`, `Roam`) all dispatch into
the same A\* search in `src/astar.cpp`. It is a grid search over fixed 64-unit square nodes, not a
sector-adjacency or waypoint graph, and it decides whether one node connects to the next by calling
`BOTPATH_TryWalk` rather than by running the pawn's own movement code. That distinction is the
whole content of this page: **the reachable set is not "wherever the pawn could walk."**

## The reachable set is capped in an absolute Z frame, not a per-step one

`BOTPATH_TryWalk` takes a `StartZ` parameter, and `astar.cpp`'s node-expansion call site passes the
*current node's* floor height for it (`pSector->floorplane.ZatPoint( CurPos.x, CurPos.y )`) so that
each hop is measured from the height the search has climbed to. The floor-step test then does not
use it:

```c
lHeightChange = g_PathSectorFloorZ - pActor->z;
if ( lHeightChange > 0 )
{
    if ( lHeightChange <= stepheight )      ulFlags |= BOTPATH_STAIRS;
    else if ( lHeightChange <= jumpheight ) ulFlags |= BOTPATH_JUMPABLELEDGE;
    else { ulFlags |= BOTPATH_OBSTRUCTED; return ( ulFlags ); }
}
```

`pActor->z` is the pawn's live position, so every candidate node in the search is measured against
where the pawn is standing right now, not against the node the search arrived from. `StartZ` is
consumed only by the blocking-actor branch earlier in the same function. The ceiling-fit test just
above uses `pActor->z` the same way, and the path-smoothing pass in `astar.cpp` passes
`pPath->pActor->z` explicitly.

The consequence is a hard ceiling on the whole search:

> For the entire duration of one path search, no node whose floor is higher than
> `pawn_z + jumpheight` can be expanded, however gradual the staircase leading up to it.

A staircase of 16-unit steps climbing 400 units is fully walkable to the pawn and stops the search
dead at `pawn_z + jumpheight`. The ledge classification is not the limiter here: `BOTPATH_STAIRS`
and `BOTPATH_JUMPABLELEDGE` both let the node through, so the bot does not need to jump, and a
capture showing zero bot jumps is consistent with this rather than evidence against it.

The line-crossing loop lower in the same function is a separate test and *is* correctly relative
(back-sector floor minus front-sector floor across each crossed linedef), so a fix would be scoped
to the floor-step and ceiling-fit tests, not to `BOTPATH_TryWalk` as a whole.

## Computing `jumpheight` for a given pawn

`jumpheight` is `APlayerPawn::CalcJumpHeight()` for a player pawn and a flat `60 * FRACUNIT`
otherwise. `CalcJumpHeight` simulates the arc rather than reading a property:

- initial velocity is `JumpZ * 35 / TICRATE`, doubled under the high-jump power and halved on a
  spring pad;
- per-tic gravity is `level.gravity * Sector->gravity * FIXED2FLOAT(gravity) * 81.92`, where
  `gravity` is the actor's own `AActor::gravity` factor (default `FRACUNIT`). At stock
  `level.gravity` 800 in a sector with gravity 1.0 this works out to exactly 1.0 map unit per tic
  per tic, so the arc height for integer `JumpZ` is the triangular number `JumpZ*(JumpZ+1)/2`;
- `MaxStepHeight` is then added, unless the caller passes `bAddStepZ = false`.

So a pawn with `JumpZ 9` and `MaxStepHeight 32` under stock gravity gets `45 + 32 = 77`.

**`CalcJumpHeight` returns 0 outright when `level.IsJumpingAllowed()` is false.** On a no-jumping
map the cap collapses to `pawn_z + MaxStepHeight`, which for a stock pawn is 24 units of absolute
climb for an entire search. This is the single biggest cliff in the behavior and it is invisible
from the pathing code.

**On a 3.2.1 build the floor-step and blocking-actor tests do not use `jumpheight`.** The
`MaxStepHeight`/`jumpheight` thresholds in those two tests arrived after the 3.2.1 version bump
(commit `2c0a1ed57`, 2025-11-24). At 3.2.1 (`src/botpath.cpp:549-551` and `:483-487` in that
revision) the floor-step test grades any rise up to a flat 60 units as `BOTPATH_JUMPABLELEDGE` and
anything higher as obstructed, so the whole-search cap is `pawn_z + 60` whatever the pawn's
`JumpZ`, the gravity or the map's jumping setting. The blocking-actor test likewise uses 60 where
this page says `jumpheight` for non-player blockers. In both, and in the line-crossing test, the
`BOTPATH_STAIRS` branch compares against 0 rather than `MaxStepHeight`, so it never fires and every
passable rise is graded a jumpable ledge. The line-crossing test already used `jumpheight` at 3.2.1.

## Why a bot does not climb out of its region over time

The cap is relative to the pawn, so a bot that reaches higher ground genuinely gets a higher cap and
can then path further up. It usually will not, because the commands give it no reason to move:
`PathToGoal`, `PathToLastKnownEnemyPosition` and `Roam` all `return` on the `PATH_UNREACHABLE` and
`PATH_INCOMPLETE` branches *before* `forwardmove` is written. An unreachable goal applies zero
thrust, so the bot is not attempting the climb and failing, it is standing still. A bot spawned in a
low basin therefore stays in the connected set of nodes whose floors are within `jumpheight` of its
spawn floor, for as long as every goal it is handed lies outside that set.

The visible symptom is a bot that paces or fidgets in place instead of following a target, while a
same-map human moves freely across terrain the bot never enters.

## Diagnosing it without launching the game

Two signatures distinguish this from ordinary geometric obstruction, and both are readable from
logged positions plus a per-cell floor-height dump:

1. **The set of floor heights the bot occupies is bounded above by `spawn_floor + jumpheight`, with
   no other structure.** Geometry that merely blocks a bot produces an arbitrarily shaped region;
   this mechanism produces a region whose boundary lies exactly on a height contour.
2. **A flood fill under relative-step rules reaches far more of the map than the bot ever does,
   from the bot's own starting cell.** If ordinary movement rules say the whole map is connected and
   the bot occupies a height-bounded fraction of it, the limiter is the search, not the map.

A per-sample predicate of the form `goal_floor - bot_z > jumpheight` does **not** cleanly separate
reachable from unreachable results, and is not worth building a test around. The constraint binds on
every intermediate node, so a goal well inside the cap is still unreachable if the route to it
crosses a ridge above the cap. `PathToGoal` also snapshots its goal position rather than tracking
it, and an already-accumulated path keeps returning `PATH_COMPLETE` without re-running the test.

## The node grid

The search runs over square cells of 64 map units (`ASTAR_NODE_SHIFT` is 22, i.e. `64 << FRACBITS`;
the Zandronum source's `src/astar.h:61-63`). The grid origin is the blockmap origin floored to a
multiple of 64 (`( g_lMapXMin >> ASTAR_NODE_SHIFT ) << ASTAR_NODE_SHIFT` in
`ASTAR_GetPositionFromIndex`, `src/astar.cpp:517-518`, with the same floor in
`astar_GetNodeFromPoint`, `:777-778`). Cell edges therefore fall on absolute world multiples of 64,
and every node centre sits at `64k + 32` on both axes. Which cell a point falls in is just its
coordinates floored to a multiple of 64, with no map data needed.

Spelled out, the lookup index is `(p >> ASTAR_NODE_SHIFT) - (g_lMapXMin >> ASTAR_NODE_SHIFT)` per
axis (`g_lMapXMin`/`g_lMapYMin` are `bmaporgx`/`bmaporgy`, `:136-137`), and
`ASTAR_GetPositionFromIndex` adds the same shifted origin back before adding 32. The blockmap-origin
term cancels, so the centre of the node containing a point `p` is `floor(p / 64) * 64 + 32` per axis
(`ASTAR_NODE_SIZE` 64 in `src/astar.h`). `>>` on a signed `fixed_t` is an arithmetic shift here, so
this is a true floor for negative coordinates too, not a truncation toward zero. A script can
therefore compute the exact node centre the search will walk to for any goal point without reading
the map. The same formula is present at 3.2.1.

The grid spans from the blockmap origin to the largest vertex coordinate (`ASTAR_BuildNodes`,
`:128-142`). A goal point outside that range has no node: `ASTAR_Path` prints
`WARNING! Cannot path to location` and returns with no flags set (`:255-264`), which
`botcmd_PathToGoal` reports as `PATH_INCOMPLETE` with no thrust. The path type stays
`BOTPATHTYPE_ITEM`, so the same snapshotted point fails the same way on every call until `SetGoal`
is re-issued.

`ASTAR_BuildNodes` (`src/astar.cpp:119-209`) precomputes only each node's grid index and its
`Position`. It runs at map setup when bots are present, the machine is not a network client and the
level doesn't set `LEVEL_ZA_NOBOTNODES` (`src/p_setup.cpp:4362-4367`), and otherwise when the first bot is
constructed (`src/bots.cpp:1668-1669`). No connectivity is cached. Every hop the search considers is
a fresh `BOTPATH_TryWalk` against the live map (`src/astar.cpp:1025`), and a stored path re-tests
the walk from the pawn to its next node on every call (`:331`). When that comes back
`BOTPATH_OBSTRUCTED` the path is discarded and searched again, or for a `Roam` path dropped
outright (`:332-353`). A door, lift or floor that moves at runtime changes
reachability on the next search; the grid itself never goes stale.

`Position` also carries a floor z sampled once at build time (`:520-521`) and never refreshed. Its
only reader is the cost heuristic (`astar_GetCostToGoalEstimate`, `:793-796`), which folds the z
difference into the distance estimate. A floor that has since moved skews the order nodes are
searched in, never whether a node can be reached. The z sample and the 3D estimate postdate 3.2.1
(commit `ef3615c11`, 2025-11-24): on a 3.2.1 build `Position.z` is 0 and the estimate is 2D.

## The per-call search budget

A fresh search (the first `ASTAR_Path` call after the path was cleared) runs in this order
(`src/astar.cpp:395-451`):

1. Under `BOTPATHTYPE_ITEM` (`PathToGoal`), a goal point more than `36 + pawn height` above the
   floor beneath it ends the search at once as complete-without-success, i.e. `PATH_UNREACHABLE`
   (`:399-412`).
2. A straight-line shortcut: `BOTPATH_TryWalk` from the pawn to the exact goal point. Unless that
   returns `BOTPATH_OBSTRUCTED` or `BOTPATH_DAMAGINGSECTOR`, the path is marked complete and
   successful immediately and no A\* runs at all (`:438-450`).
3. Otherwise A\*, resumable across calls.

The A\* budget is `botdebug_maxsearchnodes` (archived Float cvar, default 1024, `src/bots.cpp:342`),
and despite its name it counts **steps, not nodes**. The counter is bumped on every
`astar_PathNextNode` call (`src/astar.cpp:661`), and each call does one step: pull one node off the
open list, or test one of the current node's 8 neighbours. Fully expanding a node costs 9 steps, so
the default budget covers about 113 node expansions per call. `Roam`'s give-up limit
(`botdebug_maxroamgiveupnodes`) counts the same steps, cumulatively over the path's lifetime. A
budget between 0 and 1 runs a single step every `1/budget` tics instead (`:453-457`).

The search ends in one of three ways:

- the open list drains: complete without success, so `PATH_UNREACHABLE` (`:844-847`);
- the goal node is popped: complete with success (`:865`). The start node enters the open list
  without any walk test (`:423-424`), so a pawn already standing in the goal's cell succeeds on the
  first pop;
- the budget runs out first: `PATH_INCOMPLETE`, and the next call resumes the same search.

`PATH_INCOMPLETE` therefore only shows up when the region reachable from the pawn is larger than
roughly 113 cells (about a 10x10-cell open area) and the goal isn't found early. A search confined
to a small enclosed area always resolves within one call. `PATH_UNREACHABLE` also resets the path
type to `BOTPATHTYPE_NONE` (`src/botcommands.cpp:1320`), so a caller that keeps asking for an
unreachable goal re-runs the whole sequence above, from step 1, on every call.

Once a path exists, a later call steers at the next stored node's cell centre, and at the exact
goal point only once the pawn is inside the goal node's cell (`src/astar.cpp:359-378`,
`src/botcommands.cpp:1324-1331`). A path found by the shortcut stores just the goal node, so after
its first call the pawn heads for the goal cell's centre until it enters that cell, and the
per-call re-test (`:331`) walks to that centre, not to the goal point.

## What blocks a single walk test

`BOTPATH_TryWalk` samples the segment in steps of at most `MAXMOVE` (30 units) and tests a box of
the pawn's own radius around each sample point (`BOTPATH_IsPositionBlocked`), so a point within one
pawn radius of a blocking line is itself blocked.

**Lines** (`botpath_CheckLine`, `src/botpath.cpp:863`): a one-sided line, or one flagged
`ML_BLOCKING`, `ML_BLOCKEVERYTHING` or `ML_BLOCK_PLAYERS`, always blocks. `ML_BLOCKMONSTERS` blocks
only when the pawn lacks `MF3_NOBLOCKMONST` (DECORATE `+NOBLOCKMONST`). The stock `PlayerPawn` sets
that flag (`wadsrc/static/actors/shared/player.txt:21`), so by default bots path straight through
monster-blocking lines, matching how players move; this check (commit `43040e6e2`) is already in
3.2.1. Any other two-sided line passes this test and is graded by the floor-step and ceiling tests
described above.

**Things** (`botpath_CheckThing`, `src/botpath.cpp:807-841`): only `MF_SOLID` actors count, so a
`-SOLID` actor never blocks. There is no health check; a corpse passes only because dying normally
clears `MF_SOLID` (`AActor::Die` for a player, `A_NoBlocking`/`A_Fall` in a monster's death
states), so a dead actor that keeps the flag still blocks. The pawn itself is skipped, and so is the current enemy on
`BOTPATHTYPE_ENEMYPOSITION` paths, but not the goal actor. See the next section for the full test
and how a blocking actor is graded. The test never consults `sv_unblockplayers`/`sv_unblockallies`,
and a solid actor stacked on the pawn itself blocks every walk out of its position: see
[A solid actor overlapping the pawn blocks every path](#a-solid-actor-overlapping-the-pawn-blocks-every-path).

**Damaging sectors** are flagged only inside the crossed-line loop: `BOTPATH_DAMAGINGSECTOR` is set
when the sector on the far side of a crossed two-sided line carries one of the Doom damage specials
or has `damage > 0` (`src/botpath.cpp:671-690`). A walk that starts inside a damaging sector and
stays there is never flagged. What the flag does depends on the caller:

- the straight-line shortcut (`src/astar.cpp:438`) and the path-smoothing pass (`:917`) reject it
  for every path type;
- A\* node expansion rejects it only for `Roam` paths (`:1026-1027`). For `PathToGoal` and
  `PathToLastKnownEnemyPosition` the hop is allowed, and a separate cost penalty (`:1030-1058`,
  +16 to +64) is added based on the *source* node's sector `special` from a hardcoded list, never on
  `damage`, so a sector that hurts only through its `damage` field adds no cost;
- the stored-path re-test (`:331`) checks `BOTPATH_OBSTRUCTED` only.

Put together: a goal point inside a separate area sealed off by blocking lines fails the shortcut,
the A\* open list drains over the pawn's own region, and `PathToGoal` returns `PATH_UNREACHABLE` on
every call, re-running the full search each time. A goal on open, flat ground with no solid actor on
it passes the shortcut and returns `PATH_COMPLETE` on the first call. Both were observed in a live
game: a bot inside a sealed 512x512 box, given a non-solid item goal inside the box, got
`PATH_COMPLETE` and reached the goal in about 75 tics; given a goal outside the box, it got
`PATH_UNREACHABLE` on every sampled call.

## Known defect: the north-west diagonal is never tried

`astar_PathNextNode` expands a node's 8 neighbours in a fixed sequence, one per step. The last two
steps both request the same cell: `ASTAR_NS_LOOKBELOWBACK` (`src/astar.cpp:719-721`) and
`ASTAR_NS_LOOKABOVEBACK` (`:737-739`) both call `astar_GetNode( x - 1, y - 1 )`. The eighth
neighbour, `( x - 1, y + 1 )` (north-west, since node `y` grows with world `y`), is never requested,
and the south-west cell is processed twice, the second time tagged with direction 7. This dates to
the original 2007 import and is present in 3.2.1.

The search can therefore never step diagonally north-west. That cell is still reachable through two
orthogonal hops (west then north, or north then west), at a cost of 128 plus the 1.5x turn penalty
instead of 91, so paths heading that way zigzag and are costed higher than their mirror images. A
gap only passable diagonally toward the north-west is unpathable in that direction, although the
reverse south-east diagonal is tested normally.

## A solid goal actor blocks its own goal point

`PathToGoal` snapshots the goal actor's own x/y/z as its goal point and sets the path type to
`BOTPATHTYPE_ITEM` (the Zandronum source's `src/botcommands.cpp:1300-1308`). When that actor is
`MF_SOLID`, for example a monster the bot is chasing, the path test treats the actor's body as an
obstacle sitting exactly on the goal point. The goal can then be unreachable on open, flat ground.

### The blocker test

`BOTPATH_IsPositionBlocked` runs `botpath_CheckThing` (`src/botpath.cpp:807-841`) against every
actor near each test point. An actor counts as a blocker only if all of these hold:

- it is not the pawn itself, and it has `MF_SOLID` (`:812-817`);
- `|thing.x - point.x|` and `|thing.y - point.y|` are *both* below
  `blockdist = thing.radius + pawn.radius` (`:819-824`). The blocked region is a square, not a
  circle: a point escapes once its Chebyshev distance `max(|dx|, |dy|)` reaches `blockdist`, and
  clearing one axis is enough;
- its vertical span overlaps the pawn's live `z` span (`:829-833`). An actor entirely above or
  below the pawn is exempt, unless `compat_nopassmobj` is on, which skips this exemption;
- it is not the bot's current enemy while the path type is `BOTPATHTYPE_ENEMYPOSITION`
  (`:836-837`). That enemy is always a player (`players[m_ulPlayerEnemy].mo`), so no monster is
  ever exempted this way, and `PathToGoal`'s `BOTPATHTYPE_ITEM` never qualifies at all.

A goal monster standing on the same floor as the bot fails every exemption.

### The blocker is graded like a ledge

`BOTPATH_TryWalk` then classifies a blocking actor by the height of its top above `StartZ`, the
same way it grades a floor step:

```c
if ((( g_pBlockingActor->z + g_pBlockingActor->height ) - StartZ ) > 0 )
{
    if ((( g_pBlockingActor->z + g_pBlockingActor->height ) - StartZ ) <= stepheight /*gameinfo.StepHeight*/ )
        ulFlags |= BOTPATH_STAIRS;
    else if ((( g_pBlockingActor->z + g_pBlockingActor->height ) - StartZ ) <= 36 * FRACUNIT )
        ulFlags |= BOTPATH_JUMPABLELEDGE;
    else if (( g_pBlockingActor->player == NULL ) && ((( g_pBlockingActor->z + g_pBlockingActor->height ) - StartZ ) <= jumpheight ))
        ulFlags |= BOTPATH_JUMPABLELEDGE;
    else
    {
        ulFlags |= BOTPATH_OBSTRUCTED;
        return ( ulFlags );
    }
}
```

(`src/botpath.cpp:482-494`.) So, for the blocker's top measured above `StartZ`:

- up to `MaxStepHeight`: `BOTPATH_STAIRS`, passable with no jump;
- up to a hardcoded 36 units: `BOTPATH_JUMPABLELEDGE`, for any blocker including a player;
- up to `jumpheight` (see [Computing `jumpheight` for a given pawn](#computing-jumpheight-for-a-given-pawn)):
  `BOTPATH_JUMPABLELEDGE`, for non-player blockers only;
- above that: `BOTPATH_OBSTRUCTED`, even when the blocker stands on the same floor as the pawn.

Any result short of `OBSTRUCTED` is still forced to `OBSTRUCTED` if the pawn lacks `MF2_PASSMOBJ`
(DECORATE `+CANPASS`, set on the stock `PlayerPawn`) or `compat_nopassmobj` is on (`:515-519`).

`StartZ` differs by call site: the pawn's live `z` for the initial straight-line check
(`src/astar.cpp:438`) and for `PathToGoal`'s per-tic look-ahead probe
(`src/botcommands.cpp:1352`), and the current node's floor for A\* node expansion
(`src/astar.cpp:1025`).

### Two outcomes, split at `jumpheight`

**A goal actor whose top is more than `jumpheight` above the pawn gives zero thrust.**

1. The straight-line check (`src/astar.cpp:438`) walks to the goal point itself, the actor's
   centre (`dx = dy = 0`), so it always hits the actor and comes back `OBSTRUCTED`.
2. A\* succeeds only by popping the goal node off its open list (`src/astar.cpp:865`), and a node
   enters the open list only if `BOTPATH_TryWalk` into its *centre* is not obstructed
   (`src/astar.cpp:1025-1027`). Node centres sit at cell origin + 32
   (`ASTAR_GetPositionFromIndex`, `src/astar.cpp:513-519`), so the actor is within 32 units per
   axis of its own cell's centre. When `thing.radius + pawn.radius > 32` (a radius-20 monster and a
   radius-16 pawn give 36) that centre is always inside the blocked square, the goal node is never
   opened, and the search cannot succeed. With a smaller sum it depends on where in its cell the
   actor stands. The exception is a bot already standing in the goal actor's own cell: the start
   node enters the open list untested (`src/astar.cpp:423-424`), is popped first, and *is* the goal
   node, so the search succeeds at once and `PathToGoal` returns `PATH_COMPLETE` with thrust.
3. `PathToGoal` passes a give-up limit of 0 (`src/botcommands.cpp:1310`), so the search runs
   `botdebug_maxsearchnodes` search steps per call (see
   [The per-call search budget](#the-per-call-search-budget)), returning `PATH_INCOMPLETE` each
   call, until the open
   list drains over the whole reachable region (`src/astar.cpp:844-847`). It then returns
   `PATH_UNREACHABLE`, which resets the path type to `BOTPATHTYPE_NONE`
   (`src/botcommands.cpp:1320`), so the next call re-snapshots the goal and starts the full search
   over. The cycle repeats for as long as the goal is the actor.
4. Both results return (`src/botcommands.cpp:1316-1321`, `:1335-1336`) before `forwardmove` is
   written at `:1345`. The bot gets no forward thrust for the whole cycle.

**A goal actor whose top is within `jumpheight` gives thrust plus jump presses.** The straight-line
check only fails on `OBSTRUCTED|DAMAGINGSECTOR`, so a `JUMPABLELEDGE` or `STAIRS` grade lets it
succeed: `PathToGoal` returns `PATH_COMPLETE` and writes `forwardmove`. Its look-ahead probe
(`src/botcommands.cpp:1349-1354`) then tests a point `USERANGE` (64 units) ahead along the bot's
heading. Once the actor is inside that reach, the probe grades it as a jumpable ledge and sets
`BT_JUMP`, so the bot jumps at its target on the approach.

### Workaround: aim at a point beside the actor

Hand `PathToGoal` a goal that is not the actor's centre: a non-solid helper actor, passed to
`SetGoal`, placed at an offset from the target on the side facing the bot.

- The goal *point* is clear once its Chebyshev distance from the target's centre is at least
  `thing.radius + pawn.radius`. That is enough whenever the straight-line check succeeds.
- When walls force the A\* search, the goal *node's centre* must clear too, and it can sit up to 32
  units per axis back toward the target. An offset of at least `thing.radius + pawn.radius + 32` on
  one axis clears both. Because the test is per axis, a diagonal offset needs about 1.41 times the
  length of a cardinal one.
- The worst case is a target standing exactly on a 64-unit grid corner. The four node centres
  around it are each exactly 32 units off on both axes, so whenever `thing.radius + pawn.radius`
  exceeds 32 all four are inside the blocked square (`botpath_CheckThing` clears a point only when
  `|dx| >= blockdist` or `|dy| >= blockdist`, `src/botpath.cpp:820`). An offset of just
  `thing.radius + pawn.radius` plus a small margin clears the goal point but can leave its node
  centre in one of those four cells, still blocked. On the offset axis the node centres around a
  corner sit at 32, 96, 160... units out, so for `32 < blockdist <= 96` the first clear one is 96
  units from the target, and the goal point that selects it is more than 64 units out.
- Because the goal point ends up that far from the target, it can land on different floor from
  the target's (a ledge, a pit, a raised platform). Node centres are computable without map data
  (see [The node grid](#the-node-grid)), so a script placing the helper can check both the
  candidate goal point and its node centre with the point-lookup form of
  [`GetSectorFloorZ`](../../acs/functions/getsectorfloorz.md) and
  [`GetSectorCeilingZ`](../../acs/functions/getsectorceilingz.md) (`tag` 0 resolves the sector
  containing `(x, y)`, in whole map units) and reject a candidate whose floor differs from the
  target's or whose floor-to-ceiling gap is too small for the pawn. The goal point's floor
  matters for the `36 + pawn height` rejection below and the final steer; the node centre's
  matters because it is what A\* must walk into.
- The helper must not have `MF_SOLID`, or it blocks its own goal point the same way. Keep it at
  floor level: under `BOTPATHTYPE_ITEM` a goal point more than `36 + pawn height` above the floor
  beneath it is rejected outright (`src/astar.cpp:399-413`).
- Picking up a moved helper means re-issuing `SetGoal`, which discards the accumulated path (see
  [PathToGoal](../notes/pathtogoal.md)'s goal-snapshot section). A caller that recomputes the
  offset every tic would reset the path every tic. Snapping the offset direction to the 8 compass
  octants keeps the helper still while the bearing to the target drifts within one octant.

### Empirical support

A same-floor chase of a stationary monster 78 units tall, by a pawn whose `jumpheight` is 77
(`JumpZ 9` plus `MaxStepHeight 32` under stock gravity), returned `PATH_COMPLETE` on 1 of 75
sampled `PathToGoal` calls. Chases whose goal was a non-actor point returned `PATH_COMPLETE` on
over 350 of 360 samples.

With an offset of `thing.radius + pawn.radius + 8` per axis, the straight-line case recovered
(29 of 31 calls `PATH_COMPLETE`, target reached). Where a wall forced the A\* search and the target
stood on a 64-unit node corner, the same offset failed (11 of 12 calls not `PATH_COMPLETE`): all
four surrounding node centres, the goal's included, sat inside the blocking box. Moving the target
32 units onto a node centre, with nothing else changed, gave 17 of 17 `PATH_COMPLETE`. Adding the
full 32 instead pushes the goal point further out, which is why the workaround above checks the
candidate's floor and ceiling before using it.

## A solid actor overlapping the pawn blocks every path

A solid actor stacked on (or almost on) the pawn's own position makes every walk out of that
position fail, so the search returns `PATH_UNREACHABLE` for any goal. This needs two conditions,
both of which hold for two stock player pawns (radius 16, height 56) on the same floor:
`thing.radius + pawn.radius` is more than 30, and the actor grades `BOTPATH_OBSTRUCTED` under
[The blocker is graded like a ledge](#the-blocker-is-graded-like-a-ledge) (a player blocker whose
top is more than 36 units above `StartZ`, as a 56-unit pawn's is).

### The path test ignores the unblock settings

`botpath_CheckThing` (the Zandronum source's `src/botpath.cpp:807-841`) treats every `MF_SOLID`
actor inside the per-axis `blockdist` square as a blocker, subject only to the exemptions listed in
[The blocker test](#the-blocker-test). It never calls `P_CheckUnblock`, so `sv_unblockplayers` and
`sv_unblockallies` have no effect on bot pathing. Two player pawns that real movement lets overlap
are still solid to each other in every path test.

### Why the first sample of every walk is blocked

`BOTPATH_TryWalk` never tests its start point. When the longer axis of a walk exceeds `MAXMOVE`
(30 units, `src/p_local.h:81`) it splits the walk into `1 + distance / MAXMOVE` equal sub-steps,
otherwise it uses one, and it tests from the end of the first sub-step onward
(`src/botpath.cpp:445-473`). The first sample point is therefore at most 30 units from the start on
each axis, in whatever direction the walk goes. A blocker whose centre is within
`blockdist - 30` of the pawn's on both axes contains that first sample for every direction. For two
stock pawns (`blockdist` 32) that is within 2 units, i.e. effectively the same point.

Every walk the search makes near the start begins at the pawn's own x/y:

- the straight-line check to the goal point (`src/astar.cpp:438`);
- the start node's neighbour expansions, which walk from the pawn's position, not from the start
  node's centre (`src/astar.cpp:978-983`, walk and rejection at `:1025-1027`);
- the stored-path re-test on later calls (`:331`), so an already-found path is discarded and
  searched again the next time it is used.

All of them come back `BOTPATH_OBSTRUCTED`. No neighbour enters the open list, the start node is
popped and expanded to nothing, and the list drains (`src/astar.cpp:844-847`): `PATH_UNREACHABLE`
(raw value -1, `src/botcommands.h:63`) on every call, whatever the goal. The one exception is a
goal inside the pawn's own 64-unit cell, where the untested start node is itself the goal node (see
[The per-call search budget](#the-per-call-search-budget)).

`PATH_UNREACHABLE` returns before `forwardmove` is written (`src/botcommands.cpp:1316-1321`), so the
bot gets no forward thrust from `PathToGoal`, and the same holds for `PathToLastKnownEnemyPosition`
and `Roam` (see [Why a bot does not climb out of its region over
time](#why-a-bot-does-not-climb-out-of-its-region-over-time)). The only exemption is the bot's
current enemy on a `BOTPATHTYPE_ENEMYPOSITION` path (`src/botpath.cpp:836-837`): if the overlapping
pawn is that enemy, `PathToLastKnownEnemyPosition` is not stranded by it.

### How two player pawns end up stacked

Real placement disagrees with the path test here. `SetActorPosition` validates its destination
through `P_MoveThing` (`src/p_things.cpp:175`), `P_TestMobjLocation` (`src/p_map.cpp:1640`),
`P_CheckPosition` and `PIT_CheckThing` (`src/p_map.cpp:902`), and `PIT_CheckThing` does consult
`P_CheckUnblock` (`src/p_map.cpp:923`). With `sv_unblockplayers` on (or `sv_unblockallies` for
teammates), a script can therefore move a player pawn onto exactly the point another one occupies,
and the move succeeds. Both bots' pathing then fails as above for as long as they stay stacked, and
since neither pathing command writes `forwardmove`, nothing in the pathing layer moves them apart.

A script that places player pawns should not rely on the unblock settings to keep them apart: keep
each pair at a Chebyshev distance of at least `blockdist + 30`, i.e. that far apart on at least one
axis (62 units for stock pawns). At that distance no first sample of either bot's walks can land in
the other's square, so only walks that actually pass through the other pawn are blocked. Closer
placements block progressively more directions, and inside `blockdist - 30` on both axes they block
all of them.

## Related

- [PathToGoal](../notes/pathtogoal.md) — the command most likely to surface this, and the
  no-thrust-on-`PATH_UNREACHABLE` behavior that keeps a confined bot confined.
- [PathToLastKnownEnemyPosition](../notes/pathtolastknownenemyposition.md) and
  [Roam](../notes/roam.md) — same A\* dispatch, same cap.
