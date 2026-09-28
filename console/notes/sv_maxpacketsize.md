# `sv_maxpacketsize` and `sv_maxpacketspertick`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum source `src/sv_main.cpp:375` and `src/network/packetarchive.cpp:172` (CUSTOM_CVAR declarations) + verified against network transmission logic.

Two complementary cvars: one sets the size at which the server flushes a client's outgoing packet buffer, the other caps how many reliable packets it sends each client per tick.

## `sv_maxpacketsize` — UDP packet size limit

Target size (in bytes) of each packet the server sends to a client. Default is 1024 bytes; the engine clamps any value above `MAX_UDP_PACKET` (8192 bytes, `src/networkshared.h:69`) down to it at set-time, printing a warning (`src/sv_main.cpp:375`, the `sv_maxpacketsize` `CUSTOM_CVAR` handler). The handler has no lower-bound check.

It is a flush threshold, not a hard ceiling. Before appending a command to a client's reliable or unreliable packet buffer, the server sends the buffer early if the command would push it past this size (`SERVER_CheckClientBuffer`, `src/sv_main.cpp:1023`). A single command already larger than the limit is still written, with a server warning naming it (`src/network/netcommand.cpp:336`), so such a packet can exceed the value. Three list-style commands (userinfo cvars, medal counts, map rotation) avoid this by splitting themselves: when the next element would bring the command plus its 5-byte header to the limit, they send what they have and start a new command (`src/sv_commands.cpp:619`, `:1159`, `:5336`). The threshold is measured on the uncompressed buffer; `NETWORK_LaunchPacket` (`src/network.cpp:867`) Huffman- or ZStd-compresses it before sending.

For game packets the value is read once, at server startup: `SERVER_Construct` copies it into the cached limit (`src/sv_main.cpp:535`) and sizes each client's packet-loss archive from it. Changing it on a running server prints `The server must be restarted before this change will take effect.`, and game packets keep the old limit until restart. Segmented launcher-query replies are the exception: `SERVER_MASTER_SendServerInfo` reads the live cvar (`src/sv_master.cpp:879`), so a runtime change applies to them at once (see [`netcode/concepts/launcher-protocol.md`](../../netcode/concepts/launcher-protocol.md)'s "Segmented replies").

**Effect of the value:** a smaller value makes the server flush sooner, so the same data goes out as more, smaller packets (`src/sv_main.cpp:1023`). Each reliable packet carries a 5-byte header, `SVC_HEADER` plus a 4-byte sequence number (`OutgoingPacketBuffer::SendPacket`, `src/network/packetarchive.cpp:228`; `PACKET_HEADER_SIZE`, `src/network.h:264`), and each one counts against `sv_maxpacketspertick` (`OutgoingPacketBuffer::ScheduleUnsentPacket`, `src/network/packetarchive.cpp:198`).

## `sv_maxpacketspertick` — packet transmission limit per server tick

Maximum number of reliable packets the server will send **to each client per server tick** (normally 35 ticks per second). Default is 64 packets/tick. The counter lives in each client's own outgoing packet buffer (`OutgoingPacketBuffer`, `src/network/packetarchive.cpp`), so the server-wide total can reach this value times the number of connected clients. A value of 0 or below is rejected with `sv_maxpacketspertick must be positive.` and reset to 64 (`src/network/packetarchive.cpp:172`). Unlike `sv_maxpacketsize`, it is read live every tick.

Only reliable packets are paced. A reliable packet that would exceed the cap, or that arrives while older ones are still queued, waits in that client's queue. `OutgoingPacketBuffer::Tick`, called per client from `SERVER_Tick` (`src/sv_main.cpp:829`), drains the queue at up to the cap each tick. Resends of packets a client reports missing go through the same cap. Unreliable packets bypass it (`SERVER_SendClientPacket`, `src/sv_main.cpp:966`). When a client is kicked, its queue is flushed at once regardless of the cap (`src/sv_main.cpp:3932`). So a new client joining a server with many actors receives its reliable initial state-sync spread across multiple ticks instead of a single burst.

**Effect of the value:** each tick, `Tick` first sends queued resends, then queued new packets, stopping once the client's count for the tick reaches the cap (`src/network/packetarchive.cpp:300`). A backlog of N reliable packets therefore takes at least N divided by the cap, rounded up, ticks to drain.

## Engine-family divergence: packet-size and pacing tuning absent on UZDoom

Neither cvar exists on UZDoom (checked at UZDoom 5.0.0-pre @5a9b0ec511) — grepped absent tree-wide (no `CVAR`/`CUSTOM_CVAR` declaration and no
bare mention of either name anywhere in the source). This isn't a missing config knob so much as a
missing tunable *surface*: UZDoom's netcode is architecturally a ticcmd-lockstep peer exchange, not
Zandronum's server-authoritative continuous-snapshot model. Each side of a connection computes and
sends exactly one packet per tic-exchange to each peer — `GetNetBufferSize()` (`src/d_net.cpp:585`) derives that packet's exact byte length from its variable-length ticcmd payload —
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
packet flush size or per-tick send pacing; UZDoom's fixed one-packet-per-tic
model removes the tuning problem these two cvars exist to solve, rather than solving it differently.

## Network and storage

Both are marked `CVAR_ARCHIVE`, so they persist to the config file. `sv_maxpacketsize` is also `CVAR_SERVERINFO` (`src/sv_main.cpp:375`), so its value **is** replicated to connecting clients; `sv_maxpacketspertick` is `CVAR_ARCHIVE` alone and is not.

## Related cvars

- No `sv_bandwidth` cvar exists in the Zandronum source (grepped absent at `bdd0f7beb`). Neither cvar here caps total server bandwidth directly.
