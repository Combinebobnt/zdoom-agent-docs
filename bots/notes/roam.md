# Roam

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_Roam`; the failed-search branch that drops the roam target is `src/botcommands.cpp:1553-1559`). No wiki page covers this command.

## Engine-family divergence

`Roam` is a bot command, not an ACS/BCS function — it lives in Zandronum's bot-command dispatcher
(`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all. There is no UZDoom
counterpart to diverge from; see `../AGENTS.md`.

Paths the bot one tic toward a randomly chosen map location, at a speed given as a 0-100 percentage
(the int argument, clamped into that range). Same A* dispatch shape as `PathToGoal` and
`PathToLastKnownEnemyPosition`. On the first call (or any call after the prior roam target was
reached, a failed search, or another pathing command taking over), picks a fresh random location via
`ASTAR_SelectRandomMapLocation` and clears the previous path — so `Roam` is self-perpetuating: the
bot always has somewhere to go, unlike `PathToGoal` (which needs an explicit `SetGoal` first, or
`SetGoalTID` on builds after 3.2.1, added in `86e33a32d`).

## Return values: only two of the four `PATH_*` constants

Unlike `PathToLastKnownEnemyPosition` (which can return all four) or `PathToGoal` (three of four,
missing `PATH_REACHEDGOAL`), `Roam` only ever returns:

- **`PATH_INCOMPLETE`** — the search hasn't finished this tic, or finished without a usable/
  successful node (both cases return this, not `PATH_UNREACHABLE` — `Roam` never rejects a
  destination as unreachable the way its siblings can, since it always picks a new random one it
  hasn't already validated). A failed search also drops the roam target, so the next call picks a
  new random destination rather than retrying the same one.
- **`PATH_COMPLETE`** — a valid step was taken. When the bot is now within its own radius of the
  target on both axes, the internal path-type state resets to "none" so the *next* call picks a
  fresh random destination — but the return value for that same tic is still `PATH_COMPLETE`, not
  `PATH_REACHEDGOAL`; there is no way for a caller to distinguish "still en route" from "just
  arrived, next call starts a new roam" from the return value alone.

## Related

- `PathToGoal` — same A* dispatch, targets the `SetGoal` actor, returns `PATH_UNREACHABLE`/
  `PATH_INCOMPLETE`/`PATH_COMPLETE` but never `PATH_REACHEDGOAL`.
- `PathToLastKnownEnemyPosition` — same A* dispatch, the only sibling that can return
  `PATH_REACHEDGOAL`.
- `PathToLastHeardSound` — despite the name suggesting a sibling in this family, always returns
  `PATH_UNREACHABLE`; see its own note.
