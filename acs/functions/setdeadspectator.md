# `bool SetDeadSpectator(int playernumber, bool state)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** Zandronum Wiki `SetDeadSpectator` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=SetDeadSpectator&oldid=1328) + verified against Zandronum source (`src/p_acs.cpp:7428-7501`). Note: local Zandronum checkout carries applied ZandronumMCP integration patch (+170 lines to `src/p_acs.cpp`); line numbers may shift relative to a clean upstream checkout. UZDoom absence confirmed by repo-wide grep: no `deadspectator`/`ACSF_SetDeadSpectator` in `src/playsim/p_acs.cpp` or `src/playsim/actionspecials.h`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -130; dispatched as `ACSF_SetDeadSpectator`).

Turns a player that is alive into a dead spectator, or vice versa. Returns `1` (true) on success, `0` (false) on failure.

## Parameters

**`playernumber`** — the player number to affect (validated via `PLAYER_IsValidPlayer()`).

**`state`** — the desired state for the player:
  - `false` (0) — revive the dead spectator to alive.
  - `true` (1) — turn an alive player into a dead spectator.

## Behavior and scope

This function **only affects dead spectators or players who are alive**; true spectators cannot be forced to become dead spectators (checked via `PLAYER_IsTrueSpectator()`). The game mode must support dead spectators (checked via `GMF_DEADSPECTATORS` flag); if not, the function silently returns `0`.

**Server-only.** The function is a no-op when called from client code (`NETWORK_InClientMode()` returns `0`).

**Game state restrictions.**
  - **Turning players into dead spectators** (`state=true`) fails if the game is not in progress (i.e., is waiting for players, or is in the countdown or results sequence).
  - **Reviving dead spectators** (`state=false`) is allowed at any time *except* during the results sequence — they can be revived while waiting for players or during countdown, which is unrelated to the live-player restriction above.

Attempting to change a player's state when they are already in the target state (e.g., reviving a player who is already alive, or dead-spectating a player already a dead spectator) returns `0`.

## Resurrection behavior

When reviving a dead spectator (`state=false`), the function:
  1. Removes the dead spectator flag and the spectating flag.
  2. Sets the player's state to `PST_REBORN` (if `sv_deadplayerscankeepinventory` is set) or `PST_REBORNNOINVENTORY` (otherwise), matching the `ZADF_DEAD_PLAYERS_CAN_KEEP_INVENTORY` engine flag.
  3. Calls `GAMEMODE_SpawnPlayer()` to respawn the player.
  4. **If `sv_samespawnspot` is set**, the engine's respawn logic (in `src/p_mobj.cpp`) checks this flag during spawn and places the player at their death location (`spawn_x = mo->x; spawn_y = mo->y;`) rather than a designated spawn point. This is specific to co-op play and the `PST_REBORN`/`PST_REBORNNOINVENTORY` states, consistent with normal co-op respawning behavior.
  5. If the player is a bot, notifies the bot that the game was joined via `BOTEVENT_JOINEDGAME`.

## Example

```acs
script 29999 (int pnum)
{
  int spec_state = PlayerIsSpectator(pnum);
  
  // 0 = alive player, 1 = true spectator, 2 = dead spectator
  if (spec_state == 0) {
    SetDeadSpectator(pnum, 1);  // Alive → dead spectator
  } else if (spec_state == 2) {
    SetDeadSpectator(pnum, 0);  // Dead spectator → alive
  }
  // True spectators (spec_state == 1) are not affected
}
```

## See also

- `PlayerIsSpectator()` — check a player's spectator state (returns 0 = alive, 1 = true spectator, 2 = dead spectator).

## Zandronum-specific: dead spectator feature

This function and the dead spectator state are entirely Zandronum-specific; UZDoom has neither. Dead spectators are a cooperative multiplayer feature allowing players to spectate while dead without fully leaving the game. The feature is gamemode-dependent and requires the `GMF_DEADSPECTATORS` gamemode flag to be set.

### Related engine flags and cvars

- **`GMF_DEADSPECTATORS`** — gamemode flag; if not set, `SetDeadSpectator()` always returns `0` and dead spectators are not possible (checked in `src/p_acs.cpp:7438-7440`).
- **`sv_deadplayerscankeepinventory`** — if set, dead spectators keep their inventory when revived; if not set, they respawn with no inventory (checked in `src/p_acs.cpp:7485` as `ZADF_DEAD_PLAYERS_CAN_KEEP_INVENTORY`).
- **`sv_samespawnspot`** — if set (and in co-op), revived dead spectators respawn at their death location rather than a designated spawn point (checked during respawn in `src/p_mobj.cpp:5461-5473`).
