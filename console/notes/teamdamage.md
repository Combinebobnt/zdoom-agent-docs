# `teamdamage`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/doomstat.cpp` (CUSTOM_CVAR declaration showing `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, with no `CVAR_LATCH` flag).

Controls the damage multiplier for friendly fire (damage dealt by a player to a teammate or ally). Specified as a float representing a percentage of normal damage.

## Behavior and range

**Default:** 0.0 (friendly fire disabled — teammates cannot damage each other).

Valid values:
- **0.0** — friendly fire disabled entirely.
- **1.0** — full friendly fire (100% damage).
- **0.5** — half damage friendly fire.
- Other values scale linearly (e.g., 0.25 = 25% of normal damage).

**Critical netcode semantic:** This cvar is marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, but **NOT** `CVAR_LATCH`. This means changes to `teamdamage` take effect **immediately** during the current map, not at the next map change. This differs from the behavior of other gameplay-setting cvars like `instagib` and `buckshot`, which are latched.

## Server and client scope

Because this cvar is `CVAR_SERVERINFO`, the server's value is replicated to all clients. Clients cannot override it locally — the server's setting is authoritative.
