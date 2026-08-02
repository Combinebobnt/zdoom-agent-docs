# `cl_ticsperupdate`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/d_netinfo.cpp:99` and `zandronum/docs/commands.txt` + verified against the implementation's clamping logic.

Controls how frequently the server sends updated player positions to the client. Valid values are clamped to **1, 2, or 3 tics** — attempting to set this cvar outside that range will silently clamp to the nearest boundary (1 if below, 3 if above).

## Units and interpretation

The value represents tics (game frames); Zandronum's tic rate is 35 Hz, so 1 tic ≈ 28.6 ms. A higher value reduces bandwidth consumption by extrapolating other players' positions between server updates, but increases latency in position tracking. A lower value increases bandwidth but provides more accurate real-time positioning.

**Default:** 1 (most frequent updates; highest bandwidth).

## Network impact

This cvar is marked `CVAR_USERINFO | CVAR_ARCHIVE`, so it's transmitted as part of the player's network userinfo and persists across sessions. Servers can see and query each connected client's setting.
