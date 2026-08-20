# `teamdamage`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/doomstat.cpp` (CUSTOM_CVAR declaration showing `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, with no `CVAR_LATCH` flag).

Controls the damage multiplier for friendly fire (damage dealt by a player to a teammate or ally). Specified as a float representing a percentage of normal damage. The cvar exists under the same name on both engine families: UZDoom declares it at `src/g_cvars.cpp:131` as a `CUSTOM_CVAR` of type `Float` defaulting to `0.f` with the `CVAR_SERVERINFO | CVAR_NOINITCALL` flags, and both engines copy it into a per-level `teamdamage` field (`FLevelLocals::teamdamage` on UZDoom, `level.teamdamage` on Zandronum) that a map's MAPINFO `teamdamage` option can override — so the value actually applied to damage can be map-specific, not just whatever the cvar currently reads.

## Behavior and range

**Default:** 0.0 (friendly fire disabled — teammates cannot damage each other).

Valid values:
- **0.0** — friendly fire disabled entirely.
- **1.0** — full friendly fire (100% damage).
- **0.5** — half damage friendly fire.
- Other values scale linearly (e.g., 0.25 = 25% of normal damage).

Confirmed identical on both engines: the multiplier is applied as `damage = (int)(damage * teamdamage)` against the target's teammate/ally check (UZDoom `src/playsim/p_interaction.cpp:1321`, via `AActor::IsTeammate`; Zandronum `src/p_interaction.cpp:1488`, same formula against `level.teamdamage`), so any value in between scales linearly as described, and a non-zero product that rounds down to 0 still suppresses the hit exactly like the true-zero case.

**Critical netcode semantic:** On Zandronum this cvar is marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, but **NOT** `CVAR_LATCH`. This means changes to `teamdamage` take effect **immediately** during the current map, not at the next map change. This differs from the behavior of other gameplay-setting cvars like `instagib` and `buckshot`, which are latched (both declared `CVAR_SERVERINFO | CVAR_LATCH | CVAR_CAMPAIGNLOCK | CVAR_GAMEPLAYSETTING` in `src/gamemode.cpp`).

UZDoom's declaration agrees on the part that matters — `CVAR_SERVERINFO` without `CVAR_LATCH`, so the same "takes effect immediately" behavior holds there too — but it is not a byte-for-byte match: UZDoom's flags are `CVAR_SERVERINFO | CVAR_NOINITCALL` instead, and `CVAR_GAMEPLAYSETTING` isn't part of UZDoom's cvar-flag set at all (`src/common/console/c_cvars.h` has no such bit). On Zandronum, `CVAR_GAMEPLAYSETTING` (`src/c_cvars.h`, comment `[AK] The CVar is gameplay-related and can be configured in the GAMEMODE lump`) marks a cvar as configurable from a GAMEMODE lump and lockable via `GAMEMODE_IsGameplaySettingLocked` — unrelated to the latch/immediate-effect question. `CVAR_NOINITCALL` just suppresses the callback firing once at startup and has no bearing on in-map latching either.

## Server and client scope

Because this cvar is `CVAR_SERVERINFO` on both engines, the server's value is replicated to all clients. Clients cannot override it locally — the server's setting is authoritative. This applies equally to UZDoom and Zandronum.
