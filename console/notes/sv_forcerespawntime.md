# `SV_ForceRespawnTime`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes — no UZDoom/GZDoom-family equivalent cvar; the paired `SV_ForceRespawn` DMFlag does exist there but with different timing, see "Engine-family divergence" below.
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) and `src/g_game.cpp` (respawn enforcement logic).

Extra delay (in seconds) added to a dead player's respawn wait when the `SV_ForceRespawn` DMFlag is on, causing the server to respawn them automatically once that wait elapses. Works in conjunction with the `SV_ForceRespawn` DMFlag to enforce automatic respawning in deathmatch and competitive modes.

## Engine-family divergence: force-respawn timing without this cvar

`sv_forcerespawntime` itself does not exist on UZDoom — a full-tree search (`src/`, `wadsrc/static/zscript/`) turns up no such cvar anywhere. The DMFlag it's paired with, however, does: `SV_ForceRespawn`/`DF_FORCE_RESPAWN` (dmflags bit 8, same bit position as Zandronum, `src/doomdef.h:105`) is declared the same way (`CVAR (Flag, sv_forcerespawn, dmflags, DF_FORCE_RESPAWN)`, `src/d_main.cpp:664`) and is actively consumed in `wadsrc/static/zscript/actors/player/player.zs` (~line 800-812): once a dead player's `respawn_time` has elapsed, `sv_forcerespawn` being set is enough by itself (no button press needed) to transition them to `PST_REBORN`, mirroring Zandronum's own auto-respawn gate.

The difference is entirely in how long the wait is. UZDoom's death handling (`src/playsim/p_interaction.cpp:616`) sets `respawn_time` to a fixed `Level->time + TICRATE` — one second, unconditionally, with no cvar controlling it. There is no UZDoom equivalent of Zandronum's `sv_respawndelaytime` (the baseline wait) either. So enabling force-respawn on UZDoom always yields the same ~1-second wait; the same flag on Zandronum yields a wait that's tunable via both `sv_respawndelaytime` and this cvar (see below).

## How SV_ForceRespawn flag and this cvar interact

The **`SV_ForceRespawn` DMFlag (dmflags bit 8)** enables automatic respawning. On death (`src/p_interaction.cpp:747-778`), the engine first computes a baseline `respawn_time` from `sv_respawndelaytime` (or a flat 1-second fallback in singleplayer, on spawn-telefrag, or when the player has no lives left). *Then*, if `SV_ForceRespawn` is set and the player still has lives, `sv_forcerespawntime` is **added on top** of that baseline (`player->respawn_time += sv_forcerespawntime * TICRATE`) — the two cvars compose rather than acting independently. If `sv_forcerespawntime` is 0 (the default) the add-on still floors to half a second (`TICRATE/2`) rather than adding nothing.

There's one exception: when the `ZACOMPATF_INSTANTRESPAWN` compat flag is also active together with `SV_ForceRespawn`, `sv_forcerespawntime` **replaces** the baseline entirely instead of adding to it (`player->respawn_time = level.time + sv_forcerespawntime * TICRATE`, `src/p_interaction.cpp:782-785`) — `sv_respawndelaytime` is ignored in that combination.

Once `respawn_time` is reached, the automatic respawn itself happens in `src/p_user.cpp:3469-3473`: if `SV_ForceRespawn` is set (in deathmatch/teamgame, or with `alwaysapplydmflags`), the player is transitioned to `PST_REBORN` — and thus respawned at the next valid spawn point — with no button press required, distinct from the `BT_USE`/fire-to-respawn path also checked in the same condition.

Example workflow:
1. Set `dmflags` to include `SV_ForceRespawn` (add 256 to dmflags, or set `DF_FORCE_RESPAWN 1`).
2. Set `sv_forcerespawntime 15` (adds 15 seconds on top of `sv_respawndelaytime`'s baseline wait, or replaces it entirely under the instant-respawn compat flag).
3. Player dies and waits; once the combined delay elapses, the server automatically respawns them.

## Timing and related behavior

- The wait is established once, at death (`src/p_interaction.cpp:747-778`) — voluntarily entering spectator mode afterward (`PLAYER_SetSpectator`, `src/p_interaction.cpp:2441`) does not itself touch `respawn_time` or restart this timer; that's a separate mechanism from force-respawn. **Correction:** an earlier version of this note claimed the timer "starts when a player dies or goes spectating" as if these were two independent triggers for the same timer — only death starts it.
- A player who presses use (or fires, with `CLIENTFLAGS_RESPAWNONFIRE`) during the `sv_forcerespawntime`-added portion of the wait has `respawn_time` zeroed out immediately (`src/p_user.cpp:3419-3425`), letting them respawn on the very next check rather than counting down further. **Correction:** this is better described as "skips the remaining forced wait" than "resets the timer" — nothing restarts a countdown; `respawn_time` is simply cleared.
- **Correction:** the dead player waiting on this timer is not necessarily in "spectate mode." A plain deathmatch death leaves the player dead-with-a-corpse, not a spectator; the engine only puts a player into actual dead-spectator mode (`PLAYER_SetSpectator(..., bDeadSpectator=true)`) as a *separate* mechanism, when lives are limited (LMS/Survival-style modes, gated by `GAMEMODE_ShouldPlayerLoseLife()`) and the player has run out of lives — that path doesn't go through this cvar's add-on at all.
- The precision depends on the server tick rate (typically 35 ticks/second, `TICRATE`).

## Storage and replication

Marked `CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`. The value persists to the config file and is replicated to clients.

## Related cvars and flags

- **`SV_ForceRespawn`** — the DMFlag (dmflags bit 8) that enables automatic respawning; this cvar only has effect when that flag is set.
- **`sv_respawndelaytime`** — separate cvar controlling the baseline wait before respawning after death. **Correction:** not orthogonal to force-respawn — in the common case `sv_forcerespawntime` adds on top of `sv_respawndelaytime`'s baseline (see "How SV_ForceRespawn flag and this cvar interact" above); it's only fully independent of `sv_respawndelaytime` in the `ZACOMPATF_INSTANTRESPAWN` compat-flag combination, where it replaces the baseline outright instead.
- **`dmflags`** — contains the `SV_ForceRespawn` flag and other gameplay rules.
