# `instagib`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes — a Zandronum/Skulltag-lineage server game-mode modifier; UZDoom/GZDoom has no `instagib` cvar or built-in Instagib mode (see "Zandronum-specific" below).
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/gamemode.cpp` (CVAR declaration showing `CVAR_SERVERINFO | CVAR_LATCH | CVAR_CAMPAIGNLOCK | CVAR_GAMEPLAYSETTING`).

Enables or disables the Instagib game mode modifier. When enabled, a `DoomPlayer` in deathmatch or team-game modes is given the **`Railgun`** weapon as its starting weapon instead of the normal loadout — `Railgun` is a class defined outside this source tree (in the `skulltag_actors` content package; the engine errors out at spawn if it can't find the class) rather than a base-engine actor (`src/p_user.cpp:1679-1694`). Separately, while `instagib` is true, any hitscan attack's damage is forced to a lethal fixed value: `999` for a generic hitscan puff (`src/p_map.cpp:4956-4958`), and `1000` for the railgun's own attack specifically (vs. `75` in ordinary deathmatch and `200` otherwise; `src/g_doom/a_doomweaps.cpp:882-889`). *(Corrected: the previous "typically rocket launcher or similar" description was inaccurate — the weapon is specifically the Railgun, and the instant-kill effect is a global hitscan-damage override, not merely an item swap.)*

**Default:** false (disabled).

## Critical netcode semantic: CVAR_LATCH

This cvar is marked `CVAR_LATCH`, which means **changes to this setting do not take effect until the next map is loaded**. Setting `instagib` to true on a running map does not immediately enable Instagib mode; the change is queued and applies when the server advances to the next map.

This is a server-enforced semantic — if a client or admin changes `instagib` mid-map, the change will be broadcast to all connected clients, but the active game state remains unchanged until the map changes.

(The `CVAR_LATCH` flag's own source comment — identical in both Zandronum's and UZDoom's `c_cvars.h`, "save changes until server restart" — is misleading taken literally: the actual unlatch point is the two `UnlatchCVars()` calls inside `G_InitNew()` (Zandronum `src/g_level.cpp:441,447`; UZDoom `src/g_level.cpp:572,591`), which run on every new map load, not only on a literal process restart. This doc's "next map is loaded" wording reflects the verified applied behavior, which is identical between the two engines even though `instagib` itself only exists on Zandronum.)

## Server and campaign scope

As `CVAR_SERVERINFO | CVAR_CAMPAIGNLOCK | CVAR_GAMEPLAYSETTING`:
- **`CVAR_SERVERINFO`**: the server's value is replicated to all clients.
- **`CVAR_CAMPAIGNLOCK`**: the setting is locked for the duration of a campaign, preventing mid-campaign mode changes.
- **`CVAR_GAMEPLAYSETTING`**: the cvar is eligible to be set (and locked) from a map's `GAMEMODE` lump "game settings" block (`src/gamemode.cpp:309-319`) — cvars without this flag are rejected there with a script error. *(Corrected: this is not a menu-visibility flag as the previous wording implied.)*

Clients cannot change this cvar locally — the server is authoritative.

## Zandronum-specific: Instagib game mode

UZDoom/GZDoom has no `instagib` cvar, no `MODIFIER_INSTAGIB` concept, and none of the surrounding server game-mode-modifier infrastructure this cvar depends on — `CVAR_CAMPAIGNLOCK` and `CVAR_GAMEPLAYSETTING` (both grepped for across the full UZDoom source tree with zero hits) and the `GAMEMODE` lump don't exist there at all. This is Zandronum/Skulltag-lineage server functionality with no UZDoom counterpart, not merely a differently-implemented equivalent. A UZDoom-based mod wanting instagib-style play would need to build it itself (e.g. a ZScript event handler forcing hitscan damage, gated on a mod-defined cvar) rather than relying on an engine cvar.
