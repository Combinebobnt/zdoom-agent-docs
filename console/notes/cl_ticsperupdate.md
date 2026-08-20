# `cl_ticsperupdate`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/d_netinfo.cpp:99` and `zandronum/docs/commands.txt` + verified against the implementation's clamping logic.

Controls how frequently the server sends updated player positions to the client. Valid values are clamped to **1, 2, or 3 tics** — attempting to set this cvar outside that range will silently clamp to the nearest boundary (1 if below, 3 if above).

## Units and interpretation

The value represents tics (game frames); Zandronum's tic rate is 35 Hz, so 1 tic ≈ 28.6 ms. A higher value reduces bandwidth consumption by extrapolating other players' positions between server updates, but increases latency in position tracking. A lower value increases bandwidth but provides more accurate real-time positioning.

**Default:** 1 (most frequent updates; highest bandwidth).

## Network impact

This cvar is marked `CVAR_USERINFO | CVAR_ARCHIVE`, so it's transmitted as part of the player's network userinfo and persists across sessions. Servers can see and query each connected client's setting. Server-side, the send loop in `src/sv_main.cpp:3087` skips a given player's position update on ticks where `gametic` isn't an even multiple of that player's stored tics-per-update value — this is the actual mechanism the cvar tunes, not just a hint.

## Engine-family divergence

`cl_ticsperupdate` does not exist on UZDoom at all — confirmed absent from the entire checkout (not just `d_netinfo.cpp`), not merely undocumented. This isn't a missing knob so much as a mismatch of netcode models: Zandronum uses a client/server-authoritative architecture where the server periodically broadcasts each player's actual position and clients extrapolate between updates, so "how often the server sends a position update" is a meaningful, tunable rate. UZDoom/GZDoom-family netcode (`NetUpdate()`, `src/d_net.cpp:1309`) is a ticcmd-lockstep peer model instead — every peer exchanges input commands (with consistency checks and a duplication factor for lag compensation) and independently simulates every tic from those commands, rather than one side broadcasting authoritative positions at a throttled rate. There is no equivalent "position-update frequency" to throttle in that model, so the concept `cl_ticsperupdate` controls doesn't carry over, not just its specific cvar name.

Attempting to set `cl_ticsperupdate` under UZDoom (console, config file, or ACS's `ConsoleCommand()`) prints `Unknown command "cl_ticsperupdate"` and the write silently fails to apply.
