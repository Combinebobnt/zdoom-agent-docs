# `instagib`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/gamemode.cpp` (CVAR declaration showing `CVAR_SERVERINFO | CVAR_LATCH | CVAR_CAMPAIGNLOCK | CVAR_GAMEPLAYSETTING`).

Enables or disables the Instagib game mode modifier, where weapons and items are replaced with instant-kill weapons (typically rocket launcher or similar).

**Default:** false (disabled).

## Critical netcode semantic: CVAR_LATCH

This cvar is marked `CVAR_LATCH`, which means **changes to this setting do not take effect until the next map is loaded**. Setting `instagib` to true on a running map does not immediately enable Instagib mode; the change is queued and applies when the server advances to the next map.

This is a server-enforced semantic — if a client or admin changes `instagib` mid-map, the change will be broadcast to all connected clients, but the active game state remains unchanged until the map changes.

## Server and campaign scope

As `CVAR_SERVERINFO | CVAR_CAMPAIGNLOCK | CVAR_GAMEPLAYSETTING`:
- **`CVAR_SERVERINFO`**: the server's value is replicated to all clients.
- **`CVAR_CAMPAIGNLOCK`**: the setting is locked for the duration of a campaign, preventing mid-campaign mode changes.
- **`CVAR_GAMEPLAYSETTING`**: the setting is visible in gameplay configuration menus.

Clients cannot change this cvar locally — the server is authoritative.
