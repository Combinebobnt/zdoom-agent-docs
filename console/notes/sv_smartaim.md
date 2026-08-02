# `sv_smartaim`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/p_map.cpp` (CVAR declaration) + verified against engine auto-aim logic.

Controls how the engine's automatic aiming system selects targets, with four modes that trade off between ease-of-use and avoid-friendly-fire safety.

## Value meanings

- **0 (default):** Auto-aim targets the **nearest shootable actor**, regardless of whether it's a friend, ally, or monster. Classic behavior with no filtering.
- **1:** Tries to **avoid targeting allies and non-monster actors** (e.g., players on friendly fire, breakables), but still aims at them if no pure monsters are available. Moderate friendly-fire avoidance.
- **2:** Auto-aim **never targets friends** (teammates in team mode), only monsters and enemies. Still may target non-monster hazards.
- **3:** Auto-aim **only targets hostile monsters**, avoiding all players and non-hostile actors. Maximum friendly-fire safety.

## Per-actor friendliness determination

The engine uses `AActor::IsFriend()` to determine friendliness; in team modes, teammates are considered friends. The actual filtering logic in `src/p_map.cpp` respects the `sv_smartaim` value and applies it per-shot during line-attack and hitscan tracing.

## Interaction with other aiming cvars

- **`autoaim` (client cvar)** — separate cvar controlling vertical auto-aim distance; orthogonal to `sv_smartaim`.
- **`cl_doautoaim` (client cvar)** — boolean toggle that disables auto-aim entirely on the client side, regardless of `sv_smartaim`'s value.
- **`sv_noautoaim` (server DMFlag)** — server-side flag that disables auto-aiming server-wide, overriding any `sv_smartaim` setting.

When `sv_noautoaim` is set or `cl_doautoaim` is false, `sv_smartaim` has no effect (auto-aiming doesn't occur at all).

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_SERVERINFO`, so it persists to the config file and replicates to clients. Server-side enforcement: the value is applied during server-side weapon fire calculations.

## Related cvars

- **`autoaim`** — client-side cvar controlling vertical targeting distance.
- **`cl_doautoaim`** — client-side boolean enabling/disabling auto-aim entirely.
