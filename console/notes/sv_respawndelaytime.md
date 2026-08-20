# `sv_respawndelaytime`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes — UZDoom hardcodes a flat one-second (`TICRATE` tics) respawn delay with no configurable cvar equivalent; see divergence section below.
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) + verified against engine spawn logic.

Cooldown period (in seconds) that a player must wait after dying before they can respawn. Allows fractional (decimal) values, enabling sub-second delays if desired (e.g., `0.5` for half a second).

## Decimal values and sub-second respawning

Although `sv_respawndelaytime` is most commonly set to integer seconds (1, 2, 3, etc.), the cvar accepts floating-point values and defaults to `1.0f`. Setting it to `0.5` creates an approximately 0.5-second respawn delay; `0.1` an approximately 0.1-second one. This allows fine-tuning respawn dynamics in modes like deathmatch or survival where respawn timing affects gameplay balance.

The delay isn't applied as a continuous float, though: `AActor::Die` converts it with `static_cast<int>( sv_respawndelaytime * TICRATE )` (`src/p_interaction.cpp:758`, `TICRATE` is 35), which truncates to a whole number of tics rather than rounding. `0.1` (`0.1 * 35 = 3.5`) truncates to 3 tics (~85.7 ms, not 100 ms); `0.5` (`17.5`) truncates to 17 tics (~485.7 ms, not 500 ms) — sub-second values are quantized down to the nearest tic, not applied exactly.

The cvar's `CUSTOM_CVAR` callback (`src/sv_main.cpp:419-429`) separately clamps any value `<= 0.0` up to `1.0f / TICRATE` — one tic — rather than letting `0` or a negative value disable the delay outright, so the minimum effective delay is always at least a single tic long.

## Spawn-telefrag exemption

Players who are **spawn-telefragged** (killed immediately upon respawning because another actor occupies the spawn point, per `player->bSpawnTelefragged`) are exempt from the *configurable* `sv_respawndelaytime` value, but not from waiting outright — they still respawn after a flat, non-configurable delay rather than instantly.

The whole delay block in `AActor::Die` (`src/p_interaction.cpp:747-772`) only runs when the `ZACOMPATF_INSTANTRESPAWN` compat flag is off, the player was spawn-telefragged, or the player has no lives left. Within that block, `sv_respawndelaytime` is applied only when the player is *not* spawn-telefragged, has lives left, isn't in singleplayer, and isn't in a countdown sequence. In every other case — including the spawn-telefrag case — `player->respawn_time` is instead set to a flat `level.time + TICRATE` (one second), bypassing the configurable delay rather than skipping the delay entirely. This still prevents an exploitable death loop where a long `sv_respawndelaytime` compounds with spawn camping, just via a fixed floor rather than a zero-length respawn.

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, so the value persists to the config file and replicates to clients. It affects gameplay balance and is thus grouped with other gameplay-setting cvars.

## Related cvars

- **`sv_forcerespawn`** — a DMFlag that forces players to respawn automatically if alive for too long without manual respawn input.
- **`sv_forcerespawntime`** — complementary setting controlling how long a player can avoid respawning before being forced to respawn.

## Engine-family divergence: no configurable respawn delay on UZDoom

`sv_respawndelaytime` and its whole configurable-delay mechanism are Zandronum-only, checked against a UZDoom 5.0.0-pre `trunk` checkout @5a9b0ec511 (2026-08-15). UZDoom's equivalent code path (`AActor::Die`, `src/playsim/p_interaction.cpp:616`) unconditionally sets the player's `respawn_time` field to the current level time plus a fixed `TICRATE` (one second), with no cvar to adjust it, no spawn-telefrag special-casing (`respawn_time` is otherwise only read back in `wadsrc/static/zscript/actors/player/player.zs:805` to gate the respawn-key check, and exposed as a native field there — no ZScript-side override of the value exists either), and no `sv_forcerespawntime`-style companion setting (grepped the full checkout, including `wadsrc/`, for `respawndelaytime`/`forcerespawntime`; neither exists). `sv_forcerespawn` itself does still exist on UZDoom as the same `DF_FORCE_RESPAWN` DMFlag alias (`src/d_main.cpp:664`), so only the *delay-tuning* half of this file's "Related cvars" is Zandronum-specific, not the force-respawn toggle itself.
