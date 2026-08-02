# `sv_maxacsbanduration`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), whose version-availability claim this file corrects; Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) and ACS BanFromGame function implementation, verified against server ban enforcement and version ancestry against the 3.2.1 version-bump commit (`28f736fb3`).

Sets the maximum duration (in minutes) that a mod can ban a player using the ACS `BanFromGame()` function. A value of 0 **forbids mods entirely from banning players**, effectively disabling the ACS ban mechanism server-wide.

## Prohibition mode (value 0)

When `sv_maxacsbanduration 0`:
- The `BanFromGame()` ACS function is effectively disabled — any call to it is ignored or rejected by the server.
- Mods cannot ban players through ACS, regardless of how they invoke the function.
- Players can continue to rejoin after being kicked by a mod (if the mod uses other means like map restart).

## Duration limiting (values > 0)

When set to a positive integer, mods can ban players through ACS for up to `sv_maxacsbanduration` minutes. This enforces a server-side maximum that the `BanFromGame()` ACS function must respect.

Example:
- `sv_maxacsbanduration 30` — mods can ban for at most 30 minutes.
- `sv_maxacsbanduration 0` — mods cannot use `BanFromGame()` at all.

## Security and server control

This cvar is a security/policy boundary: it prevents a malicious mod from permanently banning a player (or for an unreasonably long time) through ACS scripting. A server admin sets this to enforce a maximum ban duration, ensuring mods comply with server policy even if the mod author's code doesn't self-limit.

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, so the value is replicated to clients and treated as a gameplay/policy setting. The wiki notes this is "development version 3.2-alpha and above only," but this cvar exists in released Zandronum 3.2.1.

## Related functions and cvars

- **`BanFromGame(int minutes, str message)`** — ACS function to ban a player; respects this cvar's limit.
- **`sv_enforcebans`** — controls whether the ban list is actually enforced (independent of ACS bans).
- **`sv_banfile`** / **`sv_banexemptionfile`** — ban and whitelist file lists (for manual/admin bans, not ACS-triggered).
