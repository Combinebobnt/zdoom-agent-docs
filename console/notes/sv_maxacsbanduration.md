# `sv_maxacsbanduration`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), whose version-availability claim this file corrects; Zandronum source `src/p_acs.cpp:104-109` (CUSTOM_CVAR declaration) and ACS BanFromGame function implementation (`src/p_acs.cpp:8694-8711`), verified against server ban enforcement (`src/sv_ban.cpp:198-219`, `src/sv_ban.cpp:498-507`, `src/sv_ban.cpp:553-560`), cvar flag handling (`src/c_cvars.cpp:291-325`, `src/c_cvars.cpp:348-350`) and version ancestry against the 3.2.1 version-bump commit (`28f736fb3`) and `docs/zandronum-history.txt:141` (3.2 changelog).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Sets the maximum duration (in minutes) that a mod can ban a player for using the ACS `BanFromGame()` function. The default is 0, which **forbids mods entirely from banning players**, disabling the ACS ban mechanism server-wide. A negative value is reset to 0 by the cvar's change callback.

## Prohibition mode (value 0)

When `sv_maxacsbanduration 0` (the default):
- `BanFromGame()` does nothing and returns 0. The server checks the cvar before touching the player at all.
- Mods cannot ban players through `BanFromGame()`, whatever arguments they pass.

## Duration limiting (values > 0)

When set to a positive integer, the requested duration is clamped to the range `[1, sv_maxacsbanduration]` minutes. A request of 0 or a negative duration therefore still produces a 1-minute ban, not a no-op. The ban only happens on a server (`NETSTATE_SERVER`); in single player or on a client the function returns 0 regardless of this cvar.

The ban is an address ban: the player's address is added to the server's ban list and the player is kicked immediately. Targeting a bot prints an error and bans nobody, but `BanFromGame()` still returns 1 in that case.

Example:
- `sv_maxacsbanduration 30`: mods can ban for at most 30 minutes.
- `sv_maxacsbanduration 0`: mods cannot use `BanFromGame()` at all.

## Security and server control

This cvar is a security/policy boundary: it prevents a malicious mod from permanently banning a player (or for an unreasonably long time) through ACS scripting. A server admin sets this to enforce a maximum ban duration, ensuring mods comply with server policy even if the mod author's code doesn't self-limit.

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_NOSETBYACS`, so ACS cannot change it (a mod cannot raise its own cap). In Zandronum `CVAR_SERVERINFO` alone does not broadcast the value to ordinary clients (only `CVAR_MOD` server-info cvars are sent that way). A change on the server is synced to RCON-connected admins, an RCON admin's client-side set is forwarded to the server, and a plain connected client cannot set it locally. It has no `CVAR_ARCHIVE` flag, so it is not saved to the config file; set it on the command line or in a server config each launch. The wiki notes this is "development version 3.2-alpha and above only," but the cvar shipped in released Zandronum 3.2 (listed in the 3.2 changelog) and is present at the 3.2.1 version-bump commit.

## Related functions and cvars

- **`BanFromGame(int player, int duration[, str reason])`**: ACS function to ban a player; its duration is clamped by this cvar. See [`acs/functions/banfromgame.md`](../../acs/functions/banfromgame.md).
- **`sv_banfile`**: ACS bans are added to the first ban list loaded from this cvar, the same list a manual `addban` uses by default.
- **`sv_enforcebans`**: whether that ban list is checked when a player connects. ACS bans are ordinary entries in it, so with `sv_enforcebans false` an ACS-banned player is still kicked immediately but can reconnect.
- **`sv_banexemptionfile`**: an address on the exemption (whitelist) list can reconnect despite an ACS ban.

## Engine-family divergence

`sv_maxacsbanduration` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. UZDoom's ACS implementation and administration surface carry no equivalent policy cap on ACS-triggered ban duration.

Attempting to set it under UZDoom via the console or a config file prints `Unknown command "sv_maxacsbanduration"` to console/log and does nothing else: the write silently fails to apply, so no cap is ever enforced. This is visible if someone's watching the console at the time, but easy to miss in an unattended server startup script or `autoexec.cfg` line. ACS's `ConsoleCommand()` never reaches the console dispatcher on UZDoom; it only prints "UZDoom doesn't support execution of console commands from scripts" (`src/playsim/p_acs.cpp`) and does nothing else. As a result, a UZDoom server admin has no way to cap or prohibit how long a mod's ACS-triggered ban logic can ban a player for — this specific policy boundary is simply unavailable on UZDoom.
