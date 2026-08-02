# `sv_maxpacketsize` and `sv_maxpacketspertick`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/sv_main.cpp` and `src/network/packetarchive.cpp` (CUSTOM_CVAR declarations) + verified against network transmission logic.

Two complementary cvars controlling UDP packet size and transmission rate, affecting server bandwidth usage and client update responsiveness.

## `sv_maxpacketsize` — UDP packet size limit

Maximum size (in bytes) of a single UDP datagram that the server sends. Default is 1024 bytes.

**Tradeoff:** Small values (e.g., 512) reduce per-packet overhead but can cause the server to fragment large updates across multiple packets, potentially stalling clients if the server becomes saturated. Large values (e.g., 2048 or higher) cram more data into fewer packets, but newly connecting clients or clients on high-latency links may struggle to process large packets quickly enough, causing timeouts or connection loss.

The default of 1024 is a reasonable middle ground for typical network conditions, but can be tuned per-server based on client connectivity and bandwidth availability.

## `sv_maxpacketspertick` — packet transmission limit per server tick

Maximum number of packets the server will send **per server tick** (normally 35 ticks per second). Default is 64 packets/tick.

This cvar prevents the server from flooding the network with packets in a single tick, spreading the update load across multiple ticks. For large maps with many actors or high player counts, the server generates a large update; this cvar ensures that update is sent gradually (respecting the per-tick limit) rather than in a burst. A new client connecting to a server with many actors can receive its initial state-sync spread across multiple ticks instead of a single packet-flood that might overwhelm the client's buffer.

**Setting lower** (e.g., 32) spreads updates more gradually, reducing burst load but increasing total update latency. **Setting higher** (e.g., 128) accelerates state synchronization but increases per-tick network load.

## Network and storage

Both are marked `CVAR_ARCHIVE`, so they persist to the config file. Neither has `CVAR_SERVERINFO` — they are local server-side settings, not replicated to clients.

## Interaction and tuning

Tuning typically involves balancing:
- **Large maps with many actors:** lower `sv_maxpacketspertick` to avoid overwhelming the server's outbound buffer; raise `sv_maxpacketsize` slightly to avoid excessive fragmentation.
- **High player counts:** similar tuning — prioritize gradual updates over burst speed.
- **Low-bandwidth links:** lower both values to reduce peak bandwidth.
- **Fast, stable networks:** higher values reduce client-update latency.

## Related cvars

- **`sv_bandwidth`** (if present) — another network-tuning cvar controlling overall server bandwidth allocation.
