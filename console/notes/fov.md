# `fov`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/p_user.cpp` (CUSTOM_CVAR declaration) + verified against the implementation, which shows default 90.0 (not 100 as the wiki states).

Sets the player's field of vision in degrees. Valid range is **1° to 179°** (enforced by the renderer and server-side clamps `sv_minfov` and `sv_maxfov`, both of which can be adjusted by the server).

## Default and scope

**Default:** 90° (standard Doom field of view — not 100 as the wiki inventory row states; this is a wiki documentation error).

This cvar is marked `CVAR_ARCHIVE | CVAR_USERINFO | CVAR_UNSYNCED_USERINFO | CVAR_NOINITCALL`. The `CVAR_UNSYNCED_USERINFO` flag means it is **not** replicated to other players — each client's FOV setting is purely local and does not affect other players' view of the world.

## Server limits

Servers can enforce a narrower range via `sv_minfov` (default 5°) and `sv_maxfov` (default 179°), which clamp each connecting client's FOV to the server's allowed range.
