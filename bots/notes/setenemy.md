# SetEnemy

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_SetEnemy`) and `src/botcommands.h` (`SETENEMY_LASTSEEN`/`SETENEMY_LASTSHOTBY`); `GetPlayerDamagedBy` from `botcmd_GetPlayerDamagedBy` (`src/botcommands.cpp`) and its `m_ulLastPlayerDamagedBy` source (`src/p_interaction.cpp`). No wiki page covers this command.

## Engine-family divergence

`SetEnemy` is a bot command, not an ACS/BCS function — it lives in Zandronum's bot-command
dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all. There is no
UZDoom counterpart to diverge from; see `../AGENTS.md`.

Sets the bot's current enemy directly by **player index** (`0`..`MAXPLAYERS-1`), validated via
`botcmd_ValidatePlayerID`: an out-of-range index is fatal (`I_Error`, "Illegal player index"),
taking down the whole process/server, not just the bot — the same validation every other
player-index-taking command in this table shares (`GetPlayerName`, `LookForPlayerEnemies`, ...).

## The int argument is not `SETENEMY_LASTSEEN`/`SETENEMY_LASTSHOTBY`

`botcommands.h` declares `SETENEMY_LASTSEEN` (0) and `SETENEMY_LASTSHOTBY` (1), and their names
suggest they select *how* the enemy is determined — a natural reading of `SetEnemy`'s single int
argument once its name is known. They don't: `botcmd_SetEnemy`'s body never references either
define, and a tree-wide grep confirms neither name is referenced anywhere outside its own
declaration — the pair is dead code. The argument `SetEnemy` actually takes is a raw player index,
assigned straight to `pBot->m_ulPlayerEnemy`; passing `SETENEMY_LASTSEEN`/`SETENEMY_LASTSHOTBY` by
name (as their values, 0/1) just sets the enemy to player 0 or player 1, not to "whoever was last
seen/shot the bot" — do not write a call site assuming otherwise.

## Related

- `ClearEnemy` — resets the enemy to `MAXPLAYERS` (no validation, since that value is intentionally
  out of the valid-index range and used as the bot's own "no enemy" sentinel).
- `IsEnemyAlive`/`IsEnemyVisible`/`GetDistanceToEnemy`/`GetEnemyInvulnerabilityTicks` — read
  state about whichever player index the bot's enemy is currently set to.
- `GetPlayerDamagedBy` does not read the enemy. It returns the index of the last player who
  damaged the bot (`MAXPLAYERS` if none yet), which a script can pass to `SetEnemy` itself.
