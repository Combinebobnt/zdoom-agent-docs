# Wire basics shared by the launcher, master-server and RCON protocols

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/network.cpp` (`NETWORK_LaunchPacket`, `network_ReadPacketsFromSocket`, the receive-buffer size), `src/huffman/huffman.cpp` (`HUFFMAN_Construct`, `HUFFMAN_Encode`/`HUFFMAN_Decode`), `src/networkshared.h`/`src/networkshared.cpp` (`BYTESTREAM_s` readers and writers, `QueryIPQueue`, the port and size constants) and `src/sv_main.cpp` (`SERVER_DetermineConnectionType`, `SERVER_IgnoreIP`, `SERVER_ClientError`), read at `bdd0f7beb` (3.3-alpha) and each fact below re-checked against `git show 28f736fb3:<file>` except where marked 3.3-alpha only. The UZDoom=no claim was checked against a UZDoom `98b16b78fc` checkout (`src/common/engine/i_net.cpp`, `src/d_net.cpp`). No wiki page covers this material as such; the three protocol pages' wiki sources each restate parts of it.

The three out-of-band protocols in this section ([launcher](launcher-protocol.md),
[master server](master-server-protocol.md), [RCON](rcon-protocol.md)) share one transport and
one encoding layer. This page is the one copy of those facts; the protocol pages link here
instead of restating them.

## Transport

Plain UDP, one request per datagram. A server answers launchers, RCON clients and the master
server on **the same socket as game traffic** (default port 10666, `-port` to change it). There
is no separate query port.

A datagram from an address that isn't a connected client (and isn't the auth server) goes to
`SERVER_DetermineConnectionType`, which reads **only the first command byte** of the packet and
dispatches on it. Anything after the first command's payload is ignored: the server deliberately
never loops over a non-client's packet, so one malformed datagram can't be used to trigger many
connection attempts.

## Encoding: Huffman, with a raw-copy escape

Every packet on these channels is Huffman-encoded, in both directions. The tree is a fixed,
compiled-in table inherited from the Skulltag launcher protocol (the codec is a 2009 MIT-licensed
rewrite that keeps the old table and bit order for compatibility). A launcher or RCON tool must
implement the same codec; there is no negotiation and no plain-text mode.

- **First byte of an encoded packet** is the padding signal: the count of unused bits in the
  final byte.
- **`0xFF` as the first byte** means "not encoded": the rest of the datagram is the raw payload.
  The encoder falls back to this whenever encoding would make the packet larger, and the decoder
  accepts it from any sender, so a tool can skip Huffman on its *outgoing* packets by prefixing
  `0xFF`. It still has to decode what the server sends back.
- **The auth server is the one exception**: traffic to and from the cached auth-server address
  is neither encoded nor decoded.

**ZStd is not used here.** 3.3-alpha adds Zstandard compression for game traffic (`useZStd`
argument to `NETWORK_LaunchPacket`), but every launcher, master-server and RCON send passes
`false`. The 3.3-alpha receive path does sniff the ZStd frame magic (`28 B5 2F FD`) on every
incoming datagram before falling back to Huffman, which a hand-built raw packet could collide
with only by accident. None of this exists at 3.2.1: the `useZStd` send path arrived in
`d09240b3c` and the receive-side magic sniff in `4a7242a77`, neither an ancestor of the 3.2.1
release commit.

## Field encoding

All multi-byte integers are **little-endian**, regardless of host byte order.

| Type | Wire form |
|---|---|
| Byte | 1 byte. Reading past the end of the packet yields `-1`, which is how parsers detect a missing trailing field. |
| Short | 2 bytes, little-endian. |
| Long | 4 bytes, little-endian. |
| Float | the float's raw 32-bit pattern written as a Long (no fixed-point conversion). |
| String | bytes up to and including a `0x00` terminator. A reader also stops at end of packet. Strings longer than 2047 characters (`MAX_NETWORK_STRING` 2048) are consumed in full but truncated on read. |

A "Long 199" in a protocol page therefore means the four bytes `C7 00 00 00` before Huffman
encoding. `SERVER_DetermineConnectionType` reads the first of those as the command byte and
skips the other three, which is why protocol commands and launcher challenges can share one
dispatch switch.

## Ports

| Port | Constant | Used for |
|---|---|---|
| 10666 | `DEFAULT_SERVER_PORT` | server socket: game traffic, launcher queries, RCON, master-server messages |
| 10667 | `DEFAULT_CLIENT_PORT` | client socket default |
| 15300 | `DEFAULT_MASTER_PORT` | the master server's listen port (servers heartbeat to it, launchers request lists from it) |
| 15101 | `DEFAULT_BROADCAST_PORT` | LAN: servers broadcast their info here, clients bind a LAN socket to it to list LAN servers |
| 15201 | `DEFAULT_STATS_PORT` | declared only, referenced nowhere in the server, client, master or RCON utility source |

## Size limits

- **`MAX_UDP_PACKET` is 8192 bytes**: the buffer size servers build outgoing packets in. The
  launcher protocol's segmented reply splits on `sv_maxpacketsize`, not on this constant; see
  [launcher-protocol.md](launcher-protocol.md).
- **Incoming datagrams of 21,846 bytes or more are dropped** before decoding (the decode buffer
  is sized `MAX_UDP_PACKET * 8 / 3 + 1`, the worst-case Huffman expansion).

## The shared 10-second flood queue

The server keeps one IP queue, `g_floodProtectionIPQueue`, checked at the top of
`SERVER_DetermineConnectionType`, so it gates **every** non-client packet: launcher queries, RCON
packets, master-server messages and connection attempts alike.

- An address is added by `SERVER_IgnoreIP` in two cases only: an unknown first command byte
  ("Unknown challenge ... Ignoring IP for 10 seconds", printed only with
  `sv_printconnectionmessages`; a byte in the in-game client-command range, or a master-server
  code from a non-master address, is dropped without this, `sv_main.cpp:1862,1908-1927`), and a connecting client being refused by `SERVER_ClientError`
  (wrong password or version, banned, failed authentication, rejected userinfo, and on 3.3-alpha
  only a mismatched Zstandard dictionary, added in `7435acc0b` after 3.2.1). An ordinary
  disconnect does not add to it. A successful or merely frequent
  launcher query does not add to it; the launcher protocol has its own, separate
  `sv_queryignoretime` throttle (see [launcher-protocol.md](launcher-protocol.md)).
- Entries last 10 seconds and match on **IP only, not port**, so an ignored address can't dodge
  it by changing source port.
- Packets from a queued address are dropped silently: no reply, no log line.
- The queue holds 512 slots. When it is full (one short of wrapping), the server drops every
  non-client packet from every address until entries expire, by design, as a DoS brake.

RCON keeps a second queue of its own that is written but never consulted; see
[rcon-protocol.md](rcon-protocol.md).

## Engine-family divergence

None of this exists on UZDoom. UZDoom's multiplayer is a peer-to-peer lockstep netgame: a
`-host`/`-join` lobby exchanging its own `PRE_*` pre-game packets (`src/common/engine/i_net.cpp`),
then ticcmd exchange (`src/d_net.cpp`), on port 5029 by default. There is no dedicated server, no
Huffman layer, no launcher query reply, no master-server registration and no RCON, so no tool
built against this page can talk to a UZDoom game.
