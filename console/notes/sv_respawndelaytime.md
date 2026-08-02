# `sv_respawndelaytime`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) + verified against engine spawn logic.

Cooldown period (in seconds) that a player must wait after dying before they can respawn. Allows fractional (decimal) values, enabling sub-second delays if desired (e.g., `0.5` for half a second).

## Decimal values and sub-second respawning

Although `sv_respawndelaytime` is most commonly set to integer seconds (1, 2, 3, etc.), the cvar accepts floating-point values. Setting it to `0.5` creates a 0.5-second respawn delay; `0.1` is 0.1 seconds. This allows fine-tuning respawn dynamics in modes like deathmatch or survival where respawn timing affects gameplay balance.

## Spawn-telefrag exemption

Players who are **spawn-telefragged** (killed immediately upon respawning because another actor occupies the spawn point or a projectile hits during spawn invulnerability) are **exempt from this delay** — they respawn again immediately without waiting. This prevents exploitable death loops where spawn camping causes infinite respawn delays.

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, so the value persists to the config file and replicates to clients. It affects gameplay balance and is thus grouped with other gameplay-setting cvars.

## Related cvars

- **`sv_forcerespawn`** — a DMFlag that forces players to respawn automatically if alive for too long without manual respawn input.
- **`sv_forcerespawntime`** — complementary setting controlling how long a player can avoid respawning before being forced to respawn.
