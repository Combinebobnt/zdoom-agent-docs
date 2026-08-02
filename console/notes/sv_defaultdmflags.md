# `sv_defaultdmflags`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) and game-mode initialization logic in `src/*.cpp` (mode-specific dmflags preset).

When enabled, automatically sets certain dmflags appropriate to the current game mode, without requiring manual cvar configuration.

## Automatic dmflags per game mode

When `sv_defaultdmflags` is true:

- **Deathmatch and team games** (CTF, Skulltag, one-flag CTF, etc.):
  - Weapons stay enabled (weapons remain after pickup)
  - Items respawn
  - Monsters disabled
  - Crouching disabled
  - Double ammo

- **Cooperative modes:**
  - Flags are **cleared** — default cooperative rules apply (monsters spawn, normal item spawning, etc.).

- **Duel mode:**
  - Same settings as deathmatch (above) **plus:**
    - Players spawn farthest from other players

When false, dmflags are not automatically adjusted; the server uses whatever values are explicitly set via `dmflags`/`dmflags2` or map-specific MAPINFO settings.

## Rationale and convenience

This cvar simplifies game-mode setup: a server operator can enable deathmatch by setting a gametype cvar (e.g., `sv_gametype deathmatch`) and let `sv_defaultdmflags` automatically configure standard weapons-stay, respawn-items, and no-monsters behavior, rather than manually setting dmflags each time.

Map-specific MAPINFO flags still take precedence where they exist (depending on other cvar settings like `sv_usemapsettingswavelimit`).

## Storage and replication

Marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, so the setting persists and is replicated to clients. Affects gameplay rules, thus the `CVAR_GAMEPLAYSETTING` flag.

## Related cvars and flags

- **`dmflags`** / **`dmflags2`** / **`zadmflags`** — the actual gameplay-rule bitfields that this cvar may populate automatically.
- **`sv_usemapsettingswavelimit`** — similar "use map settings" control for wave limits in invasion/survival modes.
- **`sv_usemapsettingspossessionholdtime`** — similar "use map settings" control for possession-mode hold time.

See `console/concepts/dmflags.md` for detailed explanation of individual dmflags, 2-bit fields, and engine-family divergence.
