# `sv_maxpacketsize` and `sv_maxpacketspertick`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/sv_main.cpp` and `src/network/packetarchive.cpp` (CUSTOM_CVAR declarations) + verified against network transmission logic.

Two complementary cvars controlling UDP packet size and transmission rate, affecting server bandwidth usage and client update responsiveness.

## `sv_maxpacketsize` — UDP packet size limit

Maximum size (in bytes) of a single UDP datagram that the server sends. Default is 1024 bytes; the engine clamps any higher value down to `MAX_UDP_PACKET` (8192 bytes) at set-time, printing a warning (`src/sv_main.cpp`'s `sv_maxpacketsize` `CUSTOM_CVAR` handler).

**Tradeoff:** Small values (e.g., 512) reduce per-packet overhead but can cause the server to fragment large updates across multiple packets, potentially stalling clients if the server becomes saturated. Large values (e.g., 2048 or higher) cram more data into fewer packets, but newly connecting clients or clients on high-latency links may struggle to process large packets quickly enough, causing timeouts or connection loss.

The default of 1024 is a reasonable middle ground for typical network conditions, but can be tuned per-server based on client connectivity and bandwidth availability.

## `sv_maxpacketspertick` — packet transmission limit per server tick

Maximum number of packets the server will send **per server tick** (normally 35 ticks per second). Default is 64 packets/tick.

This cvar prevents the server from flooding the network with packets in a single tick, spreading the update load across multiple ticks. For large maps with many actors or high player counts, the server generates a large update; this cvar ensures that update is sent gradually (respecting the per-tick limit) rather than in a burst. A new client connecting to a server with many actors can receive its initial state-sync spread across multiple ticks instead of a single packet-flood that might overwhelm the client's buffer.

**Setting lower** (e.g., 32) spreads updates more gradually, reducing burst load but increasing total update latency. **Setting higher** (e.g., 128) accelerates state synchronization but increases per-tick network load.

## Engine-family divergence: packet-size and pacing tuning absent on UZDoom

Neither cvar exists on UZDoom — grepped absent tree-wide (no `CVAR`/`CUSTOM_CVAR` declaration and no
bare mention of either name anywhere in the source). This isn't a missing config knob so much as a
missing tunable *surface*: UZDoom's netcode is architecturally a ticcmd-lockstep peer exchange, not
Zandronum's server-authoritative continuous-snapshot model. Each side of a connection computes and
sends exactly one packet per tic-exchange to each peer — `GetNetBufferSize()` (`src/d_net.cpp`,
around line 583) derives that packet's exact byte length from its variable-length ticcmd payload —
bounded only by the fixed `MAX_MSGLEN` buffer constant (`14000` bytes, `src/common/engine/i_net.h`).
There is no per-tick multi-packet burst to pace (Zandronum's `sv_maxpacketspertick` concept) and no
runtime-adjustable ceiling on a single packet's size (Zandronum's `sv_maxpacketsize` concept) — the
buffer cap is a compile-time constant, not a cvar, and packet count per tic-exchange is architecturally
fixed at one per peer rather than a variable burst that needs pacing.

Attempting to set either name on UZDoom (console, `set`, or a config/autoexec line) hits the console
dispatcher's command/cvar-name lookup and, finding no match, prints `Unknown command "sv_maxpacketsize"`
(or `sv_maxpacketspertick`) to console/log (`src/common/console/c_dispatch.cpp:324`) — a visible
failure at the console, but easy to miss from an unattended context like a server startup script.

As a result, a server operator moving a Zandronum config to UZDoom has no equivalent knobs for
trading packet-fragmentation risk against per-tick send-burst size; UZDoom's fixed one-packet-per-tic
model removes the tuning problem these two cvars exist to solve, rather than solving it differently.

## Network and storage

Both are marked `CVAR_ARCHIVE`, so they persist to the config file. This was previously documented as neither carrying `CVAR_SERVERINFO`, which is only true for `sv_maxpacketspertick` (`CVAR_ARCHIVE` alone) — `sv_maxpacketsize` is declared `CVAR_ARCHIVE | CVAR_SERVERINFO` (`src/sv_main.cpp`), so its value **is** replicated to connecting clients, unlike `sv_maxpacketspertick`.

## Interaction and tuning

Tuning typically involves balancing:
- **Large maps with many actors:** lower `sv_maxpacketspertick` to avoid overwhelming the server's outbound buffer; raise `sv_maxpacketsize` slightly to avoid excessive fragmentation.
- **High player counts:** similar tuning — prioritize gradual updates over burst speed.
- **Low-bandwidth links:** lower both values to reduce peak bandwidth.
- **Fast, stable networks:** higher values reduce client-update latency.

## Related cvars

- **`sv_bandwidth`** (if present) — another network-tuning cvar controlling overall server bandwidth allocation.
