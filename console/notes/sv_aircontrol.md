# `sv_aircontrol`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/p_user.cpp` (CUSTOM_CVAR declaration) and `src/g_level.cpp` (fixed-point conversion logic).

Controls the player's ability to steer/adjust direction while airborne (e.g., during jumps or falling). Higher values increase air-steer responsiveness; 0 disables mid-air steering entirely.

## Value encoding and units

The default value **`0.00390625`** equals `1/256` as a floating-point multiplier. Internally, the engine converts this to a fixed-point representation by multiplying by 65536 (`src/g_level.cpp`), which represents fractions with 16 bits of decimal precision.

This small default value provides very limited air control — it's roughly equivalent to classic Doom behavior, where players have minimal directional influence while airborne. The default of `1/256` is a legacy choice for gameplay balance; increasing it (e.g., to `0.01` or higher) makes players much more maneuverable in the air.

## Compatibility flag interaction

Setting `compat_limited_airmovement` (a compatibility flag) on a map restricts how much this cvar's value can actually affect air steering, even if `sv_aircontrol` is set high. This flag forces stricter, more Doom-like movement even when the cvar would normally permit it — used for maps or WADs that depend on classic air-movement physics.

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_NOSAVE | CVAR_GAMEPLAYSETTING`. The `CVAR_SERVERINFO` flag means the value is replicated to clients; `CVAR_NOSAVE` means it doesn't persist to the config file (it must be set per-game or per-server, not globally). `CVAR_GAMEPLAYSETTING` indicates it affects gameplay balance and is lumped with other gameplay-critical settings.

## Related cvars and flags

- **`compat_limited_airmovement`** — compatibility flag that overrides/restricts this cvar's effect per-map.
- **`sv_gravity`** — another physics cvar affecting vertical movement; works independently of air control.
