# `sv_coop_damagefactor`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/p_interaction.cpp` (CUSTOM_CVAR declaration and ApplyCoopDamagefactor implementation), verified against engine behavior.

Damage multiplier applied to all damage **dealt to players by monsters** in cooperative game modes. Higher values increase monster damage; lower values reduce it. Default 1.0 leaves monster damage unchanged.

## Application and direction

This cvar only affects damage **from monsters to players**, not player-to-player or player-to-monster damage. It is applied via the `ApplyCoopDamagefactor()` function: `damage = int(damage * sv_coop_damagefactor)`.

For example:
- `sv_coop_damagefactor 2.0` doubles all damage dealt to players by monsters.
- `sv_coop_damagefactor 0.5` halves monster damage to players.
- `sv_coop_damagefactor 0.0` prevents all monster-to-player damage.

The multiplier applies only when the damage source (`source`) is flagged with `MF3_ISMONSTER`.

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, so the value is replicated to clients and affects gameplay balance.

## Related cvars and flags

- **`sv_forcerespawn`** / **`sv_forcerespawntime`** — control respawn behavior independently of damage scaling.
- **`sv_defaultdmflags`** — sets baseline deathmatch/cooperative flags, affecting monster spawning and other gameplay.
