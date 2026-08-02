# `sv_limitcommands`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02) for the debug-only-availability note; Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration with `CVAR_DEBUGONLY` flag), verified against client-command flood protection implementation in `src/cl_commands.cpp`.

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
