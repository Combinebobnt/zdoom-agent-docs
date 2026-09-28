# PathToGoal

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_PathToGoal`). The speed and goal-snapshot sections were added 2026-09-11 from the same revision, also reading `src/p_user.cpp` (`P_MovePlayer`, `APlayerPawn::TweakSpeeds`), `src/bots.cpp` and `src/astar.cpp`. The numeric `PATH_*` values, the `botdebug_showgoal` section and the search-budget correction were added 2026-09-23 at @bdd0f7beb, also reading `src/botcommands.h`; `botcmd_PathToGoal`'s body and the A\* budget loop are unchanged from @28f736fb3, but line numbers cited here are @bdd0f7beb's. No wiki page covers this command.

## Engine-family divergence

`PathToGoal` is a bot command, not an ACS/BCS function — it lives in Zandronum's bot-command
dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all. There is no
UZDoom counterpart to diverge from; see `../AGENTS.md`.

Paths the bot one tic toward the actor last set by `SetGoal`, at a speed given as a 0-100 percentage
(the int argument, clamped into that range before use — an out-of-range value is silently clamped,
not rejected).

## Return values: three of the four `PATH_*` constants, never `PATH_REACHEDGOAL`

`botcommands.h` declares four path-result constants (`PATH_UNREACHABLE`/`PATH_INCOMPLETE`/
`PATH_COMPLETE`/`PATH_REACHEDGOAL`, numerically -1/0/1/2; the Zandronum source's
`src/botcommands.h:63-66`), but `PathToGoal` only ever returns three of them:

- **`PATH_UNREACHABLE`** — the A* search finished (`PF_COMPLETE`) but found no valid node or failed
  (`PF_SUCCESS` unset).
- **`PATH_INCOMPLETE`** — the search hasn't finished this tic; try again next tic.
- **`PATH_COMPLETE`** — the search produced a usable step, whether or not the goal itself was
  reached this tic.

Unlike `PathToLastKnownEnemyPosition` (which shares this same three-way A* dispatch but adds a
fourth branch), `PathToGoal` never checks whether the bot has actually arrived at the goal actor's
position — reaching it just keeps producing `PATH_COMPLETE` calls, tic after tic, until the caller's
own ACS/botscript logic decides to stop calling `PathToGoal` (e.g. on `IsItemVisible`/a distance
check against the goal item). **Also silently does nothing** (no state change, no return value
set) if no goal actor has been set via `SetGoal` yet.

## Speed argument: what 100 actually means in map units

The percentage becomes a forward command of `(0x32 << 8) * pct / 100`, so 100 is the stock "run"
forward value and everything below scales linearly. That command then goes through the ordinary
player-movement path (`P_MovePlayer`), not a bot-specific one:

- `TweakSpeeds` multiplies it by the pawn's first `Player.ForwardMove` value for any command below
  the run threshold, and by the second value only at exactly 100.
- It is then multiplied by the pawn's `Speed` actor property, and by the ground/air movement factor.

With stock friction (`0xE800`, i.e. velocity keeps 0.90625 of itself per tic) a stock pawn at 100
settles at about 16.7 map units/tic. Terminal velocity is roughly 10.7x the per-tic thrust, and the
approach is exponential: the first 6 tics from rest cover under 30% of what 6 tics at terminal
velocity would. So progress per tic is about `pct/100 x 16.7 x ForwardMove x Speed` once up to
speed, and much less right after starting or reversing direction. A pawn with `Speed 0.5` at 50%
moves about 4 units/tic. Any "is the bot stuck" test calibrated as a fixed distance per interval
needs to account for all three factors, or it will flag a bot that is moving freely.

The command lasts one tic. The bot's ticcmd is zeroed every tic (`src/bots.cpp`), and the
`PATH_INCOMPLETE`/`PATH_UNREACHABLE` returns both exit before `forwardmove` is written. So a tic
with no call, or with one of those results, applies no thrust and the bot just coasts on friction.

## The goal position is snapshotted, not tracked

On a call where the bot's path type is not already the goal-item type (the first call after
`SetGoal`, or `SetGoalTID` on post-3.2.1 engines, both of which reset it, or after an unreachable result), the command
clears the A\* path and copies the goal actor's current x/y/z into a stored goal position. Every
later call paths to that stored point. If the goal actor moves afterward, the bot doesn't notice
until the path is reset again.

Following a moving actor therefore means re-issuing `SetGoal` (or `SetGoalTID` where it exists), and each re-issue
discards the accumulated path. The next call first tries a straight-line walk to the goal and
finishes at once if nothing blocks it. Otherwise A\* runs over 64-unit nodes, at most
`botdebug_maxsearchnodes` search steps per call (archived cvar, default 1024). Despite the name
that is steps, not nodes: expanding one node costs 9 steps, so the default is about 113 node
expansions per call (see
[The per-call search budget](../concepts/bot-pathing-reachability.md#the-per-call-search-budget)).
Any call that ends before the search completes returns `PATH_INCOMPLETE` with no thrust. Re-issuing the goal every few
tics around corners is a real cost to how far the bot actually gets, not just to CPU time.

## `PATH_UNREACHABLE` is often the search's own height cap, not the map

A goal the pawn could plainly walk to can still return `PATH_UNREACHABLE`. The A\* search measures
every candidate node's floor against the pawn's *live* `z`, so nothing higher than
`pawn_z + jumpheight` is expandable for the whole duration of one search, however gradual the
staircase. Combined with the no-thrust behavior above, a bot that spawns in a low basin never moves
toward a goal outside it and so never climbs out. See
[What the bot A\* pathfinder can actually reach](../concepts/bot-pathing-reachability.md) for the
derivation, the per-pawn `jumpheight` formula, and how to recognise the pattern from logged
positions without launching.

## Debugging with `botdebug_showgoal`

With the archived Int cvar `botdebug_showgoal` nonzero, every `PathToGoal` call that has a goal
actor set prints `<goal class> (<x>, <y>)` to the console (`src/botcommands.cpp:1296-1297`). It
prints only when the local player's camera is that bot's body (`AActor::CheckLocalView`, e.g.
after switching the view to the bot with spy/coop view cycling), and never on a server, so on a
dedicated server it is silent. The
coordinates are the goal actor's *current* position in whole map units, not the snapshotted point
the path is actually aimed at (see the goal-snapshot section above), so after the goal actor moves
the printed point and the pathed point differ.

## Related

- [What the bot A\* pathfinder can actually reach](../concepts/bot-pathing-reachability.md) — why
  this command's `PATH_UNREACHABLE` frequently reports a search limit rather than a map one.
- [A solid goal actor blocks its own goal point](../concepts/bot-pathing-reachability.md#a-solid-goal-actor-blocks-its-own-goal-point) - why a `SetGoal` on a solid monster taller than the pawn's `jumpheight` yields endless `PATH_INCOMPLETE`/`PATH_UNREACHABLE` with no thrust, and the offset-goal workaround.
- `SetGoal` — sets the actor this command paths toward; must be called first.
- `PathToLastKnownEnemyPosition` — the same A* dispatch shape, but with a real "arrived" branch
  (`PATH_REACHEDGOAL`) this command lacks.
- `Roam` — the same A* dispatch shape again, targeting a randomly chosen map location instead of a
  set actor.
- `PathToLastHeardSound` — despite the name implying a fourth sibling in this family, always
  returns `PATH_UNREACHABLE` regardless of input; see its own note.
