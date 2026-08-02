# `cl_backupcommands`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki "Console variables" (https://wiki.zandronum.com/w/index.php?title=Console_variables&oldid=2468, verified 2026-08-02) for behavior guidance; Zandronum source `src/cl_main.cpp` (CUSTOM_CVAR declaration and validation logic) for range enforcement (0–3 clamping).

Specifies how many backup copies of old movement and weapon-selection commands the client should send to the server per tic, to recover from packet loss. This is a bandwidth/reliability tradeoff.

## Valid range and clamping

The cvar is clamped to **0 to 3** (i.e., up to three backup copies):
- **0** — send only the current command (no backups; minimal bandwidth, no packet-loss recovery).
- **1–3** — send 1–3 copies of previous commands in addition to the current command.

Attempting to set a value outside [0, 3] silently clamps to the nearest boundary.

**Default:** 0 (no backup commands).

## When to use

Per the wiki source, this cvar is useful when the client experiences **noticeable packet loss**, but should be disabled under normal network conditions because each backup command increases outbound network traffic. The backup mechanism allows the server to reconstruct a client's intended movement even if intermediate packets are dropped.

## Scope

This cvar is marked `CVAR_ARCHIVE` only — it's not part of `CVAR_USERINFO`, so it's purely a client-side setting that the server does not see or replicate. Each client independently controls how many backup commands it sends.
