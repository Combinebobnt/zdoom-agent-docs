# `cl_backupcommands`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki "Console variables" (https://wiki.zandronum.com/w/index.php?title=Console_variables&oldid=2468, verified 2026-08-02) for behavior guidance; Zandronum source `src/cl_main.cpp` (CUSTOM_CVAR declaration and validation logic) for range enforcement (0–3 clamping).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

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

## Engine-family divergence

`cl_backupcommands` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. UZDoom's networking model doesn't carry this cvar or any equivalent client-side redundant-command mechanism.

Attempting to set it under UZDoom (via the console, a config file, or ACS's `ConsoleCommand()`) prints `Unknown command "cl_backupcommands"` to console/log and does nothing else — the write silently fails to apply, so no clamping, no bandwidth change, nothing. This is visible if someone's watching the console at the time, but easy to miss in an unattended `autoexec.cfg` line or server-launch script. As a result, a UZDoom client has no way to trade extra bandwidth for packet-loss recovery on movement/weapon-selection commands the way a Zandronum client can.
