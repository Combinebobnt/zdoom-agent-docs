# `sv_limitcommands`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02) for the debug-only-availability note; Zandronum source `src/sv_main.cpp:391` (CUSTOM_CVAR declaration with `CVAR_DEBUGONLY` flag), verified against client-command flood protection implementation in `src/cl_commands.cpp:543`, `:582`, `:597`, `:738`; release-build handling of `CVAR_DEBUGONLY` from `src/c_cvars.cpp:106-113`; other gated sites `src/sv_main.cpp:5681`, `:5786`, `:5817`, `:6591`, `:6651`, `src/d_netinfo.cpp:1062`, `src/callvote.cpp:1135`; client sync `src/sv_commands.cpp:2560`, `src/cl_main.cpp:6259`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Enables client-command flood protection (default `true`): when true, limits how frequently a single client can invoke certain commands (join, suicide, change team, drop, name change, votes) and lets the server punish command floods.

## Debug-only availability

This cvar is marked `CVAR_DEBUGONLY` in the engine source, meaning it is **only settable in debug/testing builds**. The wiki's note "Only available for testing binaries" is accurate for the console name. In a release build the cvar object is still constructed, but unnamed and forced `CVAR_NOSET` (`src/c_cvars.cpp:106-113`). It keeps its default `true`, so **flood protection is always on in release builds and cannot be disabled**. Typing `sv_limitcommands` there gets `Unknown command` from the console, since no cvar by that name is registered.

## Flood protection behavior (when enabled)

When `sv_limitcommands` is true:
- **Join requests** are throttled to one per 3 seconds (`3 * TICRATE` gametic delay). Client-side check only.
- **Suicide requests** are throttled to one per 10 seconds (`10 * TICRATE` delay), checked on both client and server.
- **Team-change requests** are throttled to one per 3 seconds, checked on both ends. The limit is skipped during a last-man-standing countdown.
- **Drop** is throttled to once per second, and **name changes** to once per 30 seconds (`CLIENT_NAMECHANGE_WAITTIME`), both client-side.
- The server's **flood detection** runs: a client exceeding its command budget within 60 seconds is banned for 10 minutes, and minor-command, chat and userinfo floods are checked too.
- **Vote cooldown** (`sv_votecooldown`) applies; with this cvar false, voting is unlimited.

If a client attempts a throttled join, suicide, team change or name change too soon, they receive a message indicating how many more seconds they must wait before retrying. Disabling this cvar removes all of the above, allowing clients to spam these commands without delay.

## Use case

This cvar exists in testing/debug builds to allow testing without artificial throttling if needed. Only the switch is compile-time gated, not the protection itself. A release-build config line naming it does nothing, and the release server always throttles.

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_NOSETBYACS | CVAR_SERVERINFO | CVAR_DEBUGONLY`. The `CVAR_NOSETBYACS` flag means ACS scripts cannot modify this cvar. Together with `CVAR_DEBUGONLY`, only human admins in debug builds can change it; in release builds nobody can. Because the client enforces some limits itself, the server sends the value to clients with the game-mode limits and resends it whenever it changes.

## Related cvars

- **`sv_useticbuffer`** — another debug-only cvar controlling a different flood/latency mitigation mechanism (command buffering).

## Engine-family divergence

`sv_limitcommands` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. UZDoom's administration surface has no equivalent per-client throttle for join/suicide/team-change command spam.

Attempting to set it under UZDoom via the console or a config file prints `Unknown command "sv_limitcommands"` to console/log and does nothing else: the write silently fails to apply, so no throttling state changes. This is visible if someone's watching the console at the time, but easy to miss in an unattended server startup script or `autoexec.cfg` line. ACS's `ConsoleCommand()` never reaches the console dispatcher on UZDoom; it only prints "UZDoom doesn't support execution of console commands from scripts" (`src/playsim/p_acs.cpp`) and does nothing else. As a result, a UZDoom server has no built-in way to rate-limit rapid-fire join/suicide/team-change requests from a single client the way Zandronum does.
