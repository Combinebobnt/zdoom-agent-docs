# `sv_limitcommands`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02) for the debug-only-availability note; Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration with `CVAR_DEBUGONLY` flag), verified against client-command flood protection implementation in `src/cl_commands.cpp`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Enables client-command flood protection: when true, limits how frequently a single client can invoke certain commands (join, suicide, change team) to prevent rapid-fire command spam.

## Debug-only availability

This cvar is marked `CVAR_DEBUGONLY` in the engine source, meaning it **only exists in debug/testing builds**, not in release builds. The wiki's note "Only available for testing binaries" is accurate. Setting this cvar in a release binary will fail silently or produce an "unknown cvar" error.

## Flood protection behavior (when enabled)

When `sv_limitcommands` is true:
- **Join requests** are throttled to one per 3 seconds (`3 * TICRATE` gametic delay).
- **Suicide requests** are throttled to one per 10 seconds (`10 * TICRATE` delay).
- **Team-change requests** are throttled to one per 3 seconds.

If a client attempts to invoke a throttled command too soon, they receive a message indicating how many more seconds they must wait before retrying. Disabling this cvar removes all throttling, allowing clients to spam these commands without delay.

## Use case

This cvar exists in testing/debug builds to validate the server's command-flood protection works correctly and to allow testing without artificial throttling if needed. It should not appear in release-build configurations since the feature is compile-time gated.

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_NOSETBYACS | CVAR_SERVERINFO | CVAR_DEBUGONLY`. The `CVAR_NOSETBYACS` flag means ACS scripts cannot modify this cvar; `CVAR_NOSETBYACS` and `CVAR_DEBUGONLY` together ensure only human admins (in debug builds) can control it.

## Related cvars

- **`sv_useticbuffer`** — another debug-only cvar controlling a different flood/latency mitigation mechanism (command buffering).

## Engine-family divergence

`sv_limitcommands` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. UZDoom's administration surface has no equivalent per-client throttle for join/suicide/team-change command spam.

Attempting to set it under UZDoom (via the console, a config file, or ACS's `ConsoleCommand()`) prints `Unknown command "sv_limitcommands"` to console/log and does nothing else — the write silently fails to apply, so no throttling state changes. This is visible if someone's watching the console at the time, but easy to miss in an unattended server startup script or `autoexec.cfg` line. As a result, a UZDoom server has no built-in way to rate-limit rapid-fire join/suicide/team-change requests from a single client the way Zandronum's debug builds do.
