# PathToLastKnownEnemyPosition

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_PathToLastKnownEnemyPosition`). No wiki page covers this command.

## Engine-family divergence

`PathToLastKnownEnemyPosition` is a bot command, not an ACS/BCS function — it lives in Zandronum's
bot-command dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all.
There is no UZDoom counterpart to diverge from; see `../AGENTS.md`.

Paths the bot one tic toward `pBot->GetLastEnemyPosition()`, at a speed given as a 0-100 percentage
(the int argument, clamped into that range). Same A* dispatch shape as `PathToGoal` and `Roam`, but
is the only one of the three that can return all four `PATH_*` constants:

- **`PATH_UNREACHABLE`** — the search completed but found no valid/successful node.
- **`PATH_INCOMPLETE`** — the search hasn't finished this tic.
- **`PATH_REACHEDGOAL`** — the bot is now within its own radius of the target position on both axes
  (checked *before* it moves this tic, against the position from the previous tic's step); also
  resets the internal path-type state back to "none" so the next call starts a fresh search.
- **`PATH_COMPLETE`** — a valid step was taken but the radius check above didn't pass.

Contrast `PathToGoal`, which shares this exact A* shape but has no equivalent "arrived" check at
all and can never return `PATH_REACHEDGOAL`.

## Related

- `PathToGoal` — same A* dispatch, targets the `SetGoal` actor instead, never returns
  `PATH_REACHEDGOAL`.
- `Roam` — same A* dispatch, targets a random map location instead.
- `PathToLastHeardSound` — despite the name suggesting a sibling in this family, always returns
  `PATH_UNREACHABLE`; see its own note.
- `GetDistanceToEnemy`, `IsEnemyVisible` — other ways to query the bot's current enemy relationship
  without moving toward it.
