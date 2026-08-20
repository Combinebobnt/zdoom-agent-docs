# `sv_useticbuffer`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02) for the debug-only-availability note; Zandronum source `src/sv_main.cpp` (CVAR declaration with `CVAR_DEBUGONLY` flag), verified against server command-processing logic in `src/sv_commands.cpp`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Enables command buffering: when true, the server buffers incoming client movement and fire commands before processing them, spreading execution across multiple server ticks to smooth laggy-client behavior.

## Debug-only availability

This cvar is marked `CVAR_DEBUGONLY` in the engine source, meaning it **only exists in debug/testing builds**, not in release builds. The wiki's note "Only available for testing binaries" is accurate. Release builds do not expose this setting.

## Buffering mechanism and latency smoothing

When `sv_useticbuffer` is true:
- Client commands (movement, fire, jump) are not processed immediately on receipt.
- Instead, the server queues incoming commands into a "ticbuffer" — a per-client command queue.
- During each server tick, the server processes up to 2 sets of commands from each client's buffer (limiting laggy clients to at most 2 ticks' worth of input per tick).
- This prevents a single laggy client from causing sudden bursts of movement or weapon fire that would look jittery to other players.

**Impact on client perception:** Clients see their own movement as predicted/smooth regardless of this setting (client-side prediction hides the buffering). The primary effect is on *other players' perception* of a laggy client — instead of sudden position/fire jumps, they see gradual, interpolated movement.

When disabled (`sv_useticbuffer false`):
- Client commands are processed immediately upon receipt.
- Laggy clients can produce jittery or sudden-jump behavior visible to other players.
- Lower latency for responsive clients, but worse visibility of laggy clients.

## Tradeoff and use case

This cvar exists in testing/debug builds to measure and tune the latency-smoothing behavior. In typical usage, enabling buffering reduces visible jitter at the cost of slight response-delay perception on other clients (which is usually imperceptible at normal latency).

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_NOSETBYACS | CVAR_DEBUGONLY`. The `CVAR_NOSETBYACS` flag prevents ACS scripts from modifying it.

## Related cvars

- **`sv_limitcommands`** — another debug-only cvar controlling command-flood protection (separate from buffering).
- **`sv_maxpacketspertick`** — limits outbound packet transmission rate, another latency-mitigation mechanism (available in release builds).

## Engine-family divergence

`sv_useticbuffer` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. Attempting to set it under UZDoom (via the console, a config file, or ACS's `ConsoleCommand()`) prints `Unknown command "sv_useticbuffer"` to console/log and the write silently fails to apply — a visible failure if someone is watching the console at the time, but easy to miss in an unattended context such as a server startup script or an `autoexec.cfg` line.

UZDoom's netcode has no equivalent debug-build command-buffering knob for spreading a laggy client's queued movement/fire commands across multiple ticks, so the jitter-smoothing tradeoff this cvar exists to measure and tune simply cannot be toggled or tested on that engine.
