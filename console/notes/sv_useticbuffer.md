# `sv_useticbuffer`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02) for the debug-only-availability note; Zandronum source `src/sv_main.cpp` (CVAR declaration with `CVAR_DEBUGONLY` flag), verified against the client-command buffering in `src/sv_main.cpp` (`server_ParseBufferedCommand`) and the per-tick drain loop in `src/p_tick.cpp` (`P_Ticker`), plus `src/c_cvars.cpp`'s `FBaseCVar` constructor for release-build handling of `CVAR_DEBUGONLY`; drain-rate change is Zandronum commit `22313870d`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Enables server-side command buffering (default `true`): the server queues each client's incoming movement and weapon-select commands and executes them at a steady rate across server ticks, instead of executing each one the moment its packet arrives. This smooths out a laggy client whose commands arrive in bursts.

## Debug-only availability

This cvar is marked `CVAR_DEBUGONLY` in the engine source. In a release build, the cvar constructor strips the name of any `CVAR_DEBUGONLY` cvar and adds `CVAR_NOSET`, so it cannot be looked up, set or saved from the console or config; the wiki's note "Only available for testing binaries" is accurate in that sense. The variable itself is still compiled in and keeps its default, so **release builds always buffer** (the value is fixed at `true`). Only a debug/testing build can switch buffering off.

## Buffering mechanism and latency smoothing

When `sv_useticbuffer` is true:
- Movement commands and weapon-select commands (including the backup weapon-select command) are not executed on receipt. They are appended to a per-client command buffer. Fire, jump and other buttons travel inside the movement command, so they are buffered with it.
- Commands carrying a client gametic are inserted in client-tic order, so commands that arrived out of order are put back in sequence.
- Each server tick, the server executes buffered commands for each client up to and including one movement command (weapon-select commands ahead of it run in the same pass). A second pass in the same tick can execute a second movement command, but when the client has exactly one movement command left it only does so once the client's movement commands have arrived on consecutive ticks for at least `TICRATE` (35) ticks. The effect is roughly one movement command per tick, with a second only to drain a backlog.
- Duplicate-command filtering (dropping a command whose client gametic was already received) happens before this cvar is checked, so it applies whether or not buffering is on.

**Version note:** the drain rate above was introduced after 3.2.1, in Zandronum commit `22313870d`. A 3.2.1 server instead executed two movement commands on every third gametic and one otherwise, i.e. four movement commands per three ticks.

**Impact on client perception:** Clients see their own movement as predicted/smooth regardless of this setting (client-side prediction hides the buffering). The primary effect is on *other players' perception* of a laggy client: its queued commands are played out at a steady rate instead of in sudden bursts.

When disabled (`sv_useticbuffer false`, debug/testing builds only):
- Client movement and weapon-select commands are executed immediately upon receipt.
- Laggy clients can produce jittery or sudden-jump behavior visible to other players.
- No buffering delay is added, but a laggy client's movement is less smooth to others.

## Tradeoff and use case

Exposing this as a debug-only cvar lets testing builds compare buffered and unbuffered command handling. Buffering reduces visible jitter at the cost of a small added delay before a client's commands take effect on the server.

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_NOSETBYACS | CVAR_DEBUGONLY`. The `CVAR_NOSETBYACS` flag prevents ACS scripts from modifying it. `CVAR_ARCHIVE` only has an effect in debug/testing builds, since a release build's copy has no name to save under.

## Related cvars

- **`sv_limitcommands`** — another debug-only cvar controlling command-flood protection (separate from buffering).
- **`sv_maxpacketspertick`** — limits outbound packet transmission rate, another latency-mitigation mechanism (available in release builds).

## Engine-family divergence

`sv_useticbuffer` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. Attempting to set it under UZDoom via the console or a config file prints `Unknown command "sv_useticbuffer"` to console/log and the write silently fails to apply: a visible failure if someone is watching the console at the time, but easy to miss in an unattended context such as a server startup script or an `autoexec.cfg` line. ACS's `ConsoleCommand()` never reaches the console dispatcher on UZDoom; it only prints "UZDoom doesn't support execution of console commands from scripts" (`src/playsim/p_acs.cpp`) and does nothing else.

UZDoom's netcode has no equivalent debug-build command-buffering knob for spreading a laggy client's queued movement/fire commands across multiple ticks, so the jitter-smoothing tradeoff this cvar exists to measure and tune simply cannot be toggled or tested on that engine.
