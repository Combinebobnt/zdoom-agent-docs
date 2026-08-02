# `SV_ForceRespawnTime`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) and `src/g_game.cpp` (respawn enforcement logic).

Cooldown period (in seconds) after which an idle player is forcibly respawned. Works in conjunction with the `SV_ForceRespawn` DMFlag to enforce automatic respawning in deathmatch and competitive modes.

## How SV_ForceRespawn flag and this cvar interact

The **`SV_ForceRespawn` DMFlag (dmflags bit 8)** enables automatic respawning. When this flag is set:
- Players who remain dead/spectating for longer than `sv_forcerespawntime` seconds are automatically forced to respawn.
- If the player is already in spectate mode (dead), they are respawned at the next valid spawn point.

Example workflow:
1. Set `dmflags` to include `SV_ForceRespawn` (add 256 to dmflags, or set `DF_FORCE_RESPAWN 1`).
2. Set `sv_forcerespawntime 15` (force respawn after 15 seconds of being dead).
3. Player dies and waits; after 15 seconds, the server automatically respawns them.

## Timing and related behavior

- The timer starts when a player dies or goes spectating.
- If a player manually respawns before the timeout, the timer resets.
- The precision depends on the server tick rate (typically 35 ticks/second).

## Storage and replication

Marked `CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`. The value persists to the config file and is replicated to clients.

## Related cvars and flags

- **`SV_ForceRespawn`** — the DMFlag (dmflags bit 8) that enables automatic respawning; this cvar only has effect when that flag is set.
- **`sv_respawndelaytime`** — separate cvar controlling the *minimum* wait before respawning after voluntary death (orthogonal to force-respawn).
- **`dmflags`** — contains the `SV_ForceRespawn` flag and other gameplay rules.
