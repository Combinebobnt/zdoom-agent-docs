# Master-server protocol

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `Master Server` (retrieved 2026-09-22, https://wiki.zandronum.com/w/index.php?title=Master_Server&oldid=67), which covers only the hosting side (the `sv_updatemaster`/`sv_enforcemasterbanlist`/`masterhostname` cvars and the official master's address); every protocol claim below was written from the Zandronum source: `src/sv_master.cpp` (`SERVER_MASTER_Construct`/`SERVER_MASTER_Tick` 544-636, `SERVER_MASTER_HandleVerificationRequest` 953-964, `SERVER_MASTER_SendBanlistReceipt` 968-976, cvars 987 and 1058), `src/sv_main.cpp` (verification string 560-567, connectionless dispatch 1828-1927), `src/sv_ban.cpp` (`sv_enforcemasterbanlist` 101, `SERVERBAN_IsIPMasterBanned` 237-240, ban-list receipt 312-395), `src/networkshared.h` 83-173, `src/d_main.cpp` 3270-3278, and the in-repo reference master `masterserver/main.cpp` (whole file). Line numbers are from the 3.3-alpha checkout @bdd0f7beb; within the cited code, the diff from 28f736fb3 to it adds an explicit `useZStd=false` argument to the server's `NETWORK_LaunchPacket` calls and refactors and fixes the master's packet I/O (`6e1563a0d`, `b588af9d1`), all wire-neutral.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

The master server keeps the list of public Zandronum servers. Game servers register with it by
sending a heartbeat, prove they own their address through a one-round verification handshake,
and then receive the master's ban list. Launchers (server browsers) ask the master for the list of
server addresses and then query each server directly with the launcher protocol.

Tier B rather than A because the wiki page this was taken in from is hosting-shaped: it
corroborates the three cvars and the address, nothing about the wire format.

**Which master this describes.** The game-server half below is read from the engine and is what
every Zandronum server does. The master half describes `masterserver/`, the reference
implementation that ships in the Zandronum repository. The live `master.zandronum.com` may run a
different build or policy (timeouts, limits, hiding rules), so treat master-side numbers as the
reference behavior, not a guarantee about the official service.

## Wire basics, briefly

UDP, Huffman-encoded in both directions (the reference master uses the same codec), little-endian
Byte/Short/Long, NUL-terminated strings. The master listens on 15300; a game server talks to it
from its ordinary game socket (10666 by default). Full details, including the server's shared
10-second flood queue, are in [wire-basics.md](wire-basics.md). One addition specific to this
protocol: an IPv4 address is written as its 4 raw octets in network order, and a port as a Short.

**Command width is not uniform.** The game server reads the first **Byte** of an unsolicited
packet as the command, so master-to-server commands (205/206/207) are single bytes. The master
reads the first **Long**, so server-to-master and launcher-to-master commands are Longs.

## Command codes

From `src/networkshared.h`.

| Value | Name | Direction | Width |
|---|---|---|---|
| 5660020 | `SERVER_MASTER_CHALLENGE` | server to master (heartbeat) | Long |
| 5660021 | `SERVER_MASTER_CHALLENGE_OVERRIDE` | commented out, unused | |
| 5660022 | `SERVER_MASTER_STATISTICS` | declared; the reference master does not handle it | Long |
| 5660028 | `LAUNCHER_MASTER_CHALLENGE` | launcher to master (list request, v2) | Long |
| 5660029 | `SERVER_MASTER_VERIFICATION` | server to master (verification reply) | Long |
| 5660030 | `SERVER_MASTER_BANLIST_RECEIPT` | server to master | Long |
| 199 | `LAUNCHER_SERVER_CHALLENGE` | launcher to master (legacy list request); same code a launcher sends a game server | Long |
| 205 | `MASTER_SERVER_BANLIST` | master to server (legacy single-packet ban list) | Byte |
| 206 | `MASTER_SERVER_VERIFICATION` | master to server (verification request) | Byte |
| 207 | `MASTER_SERVER_BANLISTPART` | master to server (one part of a split ban list) | Byte |

`MASTER_SERVER_VERSION` is `2`. The 5660023 to 5660027 codes in the same enum belong to the
launcher protocol and to long-dead account commands, not to this exchange.

Master replies to launchers use the `MSC_*` enum:

| Value | Name | Width when sent |
|---|---|---|
| 0 | `MSC_BEGINSERVERLIST` | Long |
| 1 | `MSC_SERVER` | Byte |
| 2 | `MSC_ENDSERVERLIST` | Byte |
| 3 | `MSC_IPISBANNED` | Long |
| 4 | `MSC_REQUESTIGNORED` | Long |
| 5 | `MSC_WRONGVERSION` | Long |
| 6 | `MSC_BEGINSERVERLISTPART` | Long |
| 7 | `MSC_ENDSERVERLISTPART` | Byte |
| 8 | `MSC_SERVERBLOCK` | Byte |

Ban-list parts use `MSB_BAN` 0, `MSB_BANEXEMPTION` 1, `MSB_ENDBANLISTPART` 2, `MSB_ENDBANLIST` 3,
each a Byte.

## Server side: the heartbeat

`SERVER_MASTER_Tick` runs once per game tic on a server, and once at startup
(`src/d_main.cpp`, right after the `-private` check). It sends only when `gametic` is a multiple of
`TICRATE * 30`, so every **30 seconds** of game time, starting with the startup call.

- Nothing is sent if `sv_updatemaster` is false. The `-private` command-line switch just sets
  `sv_updatemaster` to false at startup. Players can still connect by address; the server is only
  missing from the master's list.
- `masterhostname` (default `master.zandronum.com`, stored in the global config section, also read
  by the client-side browser) is resolved **on every heartbeat**. If it does not resolve, the
  server prints a warning and skips that heartbeat.
- The destination port is 15300 unless the server was started with `-masterport <n>`.

Heartbeat payload:

```text
Long    5660020                 SERVER_MASTER_CHALLENGE
String  verification string     32 hex chars, see below
Byte    sv_enforcemasterbanlist 0 or 1
Long    revision number         GetRevisionNumber(): the source revision's Unix date on modern builds
```

**The verification string** is generated once when the server starts: 100 bytes from the game's
`M_Random` generator, MD5-hashed, kept as the hex digest. It never changes for the life of the
process. It is the only thing tying later master packets to this server, and it is not
cryptographically strong: `M_Random` is seeded from a 32-bit value, and a `-rngseed` on the command
line makes that seed, and therefore the string, predictable.

## Master side: registration and verification

On a heartbeat from an address not yet on the list:

1. **Ban/block check first.** An address in `banlist.txt` (and not in `whitelist.txt`) gets a Long
   `MSC_IPISBANNED` back for any command. An address in `blocklist.txt` gets the same reply to a
   heartbeat only; it can still fetch the server list, except that the refusal also puts it in
   the 10-second list-request queue described under "Launcher side".
2. **Per-IP limit.** If **10 or more** verified servers from the same IP (any port) are already
   listed, the heartbeat is dropped silently, unless the IP is in `multiserver_whitelist.txt`. So
   at most 10 servers per IP.
3. **Old-server filter.** If the enforcement Byte is missing (the read returns `-1`), the server
   is treated as old-format and refused. Revision `3021` (Skulltag 98d) is also refused. A refused
   IP goes into the same 10-second list-request queue. The revision is read as a Long if at least
   4 bytes remain, else as a Short.
4. **Verification request.** The server goes onto a separate unverified list, and the master sends
   it Byte `206` (`MASTER_SERVER_VERIFICATION`), the server's own verification string, and a Long
   nonce. The nonce comes from `srand(time)` plus arithmetic on `rand()`, so it is guessable; it
   only proves the server can receive at its claimed address.
5. **Verification reply.** The server checks that the packet came from the resolved master address
   (IP and port) and that the string matches its own exactly, then answers Long `5660029`
   (`SERVER_MASTER_VERIFICATION`), its string, and the nonce echoed back. A mismatch is logged
   ("Master server message with wrong verification string received") and ignored.
6. **Listed.** If the string (compared case-insensitively on the master) and nonce match, the
   master moves the server to the public list and immediately sends it the ban list.

A heartbeat from an address already listed only refreshes its last-seen time, and only if its
verification string matches the stored one. The enforcement Byte is re-read each time, so toggling
`sv_enforcemasterbanlist` takes effect on the next heartbeat.

**Timeouts.** Any entry, verified or not, is dropped once **60 seconds** pass without an accepted
heartbeat. Two practical consequences:

- A server restarted on the same address has a new verification string, so its heartbeats are
  ignored until the old entry times out (up to 60 seconds after the old process's last
  heartbeat). Until then the address stays listed through the stale entry, which still reaches the
  new server but carries the old `sv_enforcemasterbanlist` value. After the timeout the address is
  absent until the next heartbeat plus one verification round trip, so at most about 30 seconds.
- A lost verification request or reply is not retried directly. The unverified entry times out
  and the next heartbeat after that starts the handshake again.

**The official address.** The wiki lists `master.zandronum.com:15300`, which matches the engine's
default `masterhostname` and `DEFAULT_MASTER_PORT`. The reference master always binds 15300; an
optional `-useip <addr>` picks the interface, but it is only recognized as the second and third
command-line arguments (after one other argument), a positional quirk of `main`.

## Master side: ban-list push

The master's list comes from `banlist.txt` (bans) and `whitelist.txt` (exemptions). It is sent to
a server when the server is first listed, and again whenever the server is flagged as not having
the latest copy. The format depends on the server's reported revision:

- **Revision 2907 or newer** (any build whose revision stamp is a date, which is every normal
  build; a build made without the revision generator reports `0` and falls to the legacy form): one or more `MASTER_SERVER_BANLISTPART`
  packets, each holding up to about 1 KB of entries (the master's own cap, far below the
  8192-byte `MAX_UDP_PACKET`).
- **Older:** one `MASTER_SERVER_BANLIST` packet with the whole list.

```text
Split form, one packet:
Byte    207                     MASTER_SERVER_BANLISTPART
String  verification string
Byte    part number             0, 1, 2, ...
repeat:
  Byte    MSB_BAN (0) or MSB_BANEXEMPTION (1)
  String  IP pattern
Byte    MSB_ENDBANLISTPART (2) on every part but the last, MSB_ENDBANLIST (3) on the last

Legacy form:
Byte    205                     MASTER_SERVER_BANLIST
String  verification string
Long    ban count,       then that many Strings
Long    exemption count, then that many Strings
```

**Server-side receipt** (`src/sv_ban.cpp`). Both forms are accepted only from the master's address
with the correct verification string. Part number 0 clears the stored master bans and exemptions;
later parts append. The code assumes parts arrive in order and does not track gaps. On the final
part (or the legacy packet), a server with `sv_enforcemasterbanlist` on kicks any connected player
who now matches, then sends Long `5660030` (`SERVER_MASTER_BANLIST_RECEIPT`) with its verification
string.

**Resend.** Every 10 seconds the master marks any listed server that has not acknowledged the
current list as needing it, and the next timeout pass resends the whole list. A lost part therefore
costs a full resend, not a retransmit of that part. The master re-reads its ban files every 15
minutes; if either list changed, every server is marked stale and re-sent.

**Enforcement.** An address counts as master-banned on the server only while
`sv_enforcemasterbanlist` is true (the default), it matches a master ban, and it does not match a
master exemption. Turning the cvar back on kicks matching players immediately. The received lists
can be inspected with the `viewmasterbanlist` and `viewmasterexemptionbanlist` console commands.

**Banned from hosting.** The server reacts to an `MSC_IPISBANNED` from the master by printing
"You are banned from hosting on the master server!", but only during its first 20 seconds of
uptime, so effectively only for the startup heartbeat. After that the same reply is dropped
silently, and the server keeps sending heartbeats that the master keeps refusing.

## Launcher side: fetching the list

**Rate limits on the reference master.** After a list is sent, the requesting IP is remembered for
**10 seconds**. Another request in that window gets a Long `MSC_REQUESTIGNORED`, and the IP is then
ignored completely for 3 seconds. An unrecognized command gets the sender ignored for 10 seconds.
Banned IPs get `MSC_IPISBANNED` for everything.

**Current request (v2):** Long `5660028` (`LAUNCHER_MASTER_CHALLENGE`) followed by Short `2`
(`MASTER_SERVER_VERSION`). Any other version gets a Long `MSC_WRONGVERSION`. The reply is split
into packets of about 1 KB:

```text
Long    MSC_BEGINSERVERLISTPART (6)
Byte    packet number           0, 1, 2, ...
Byte    MSC_SERVERBLOCK (8)
repeat, one block per IP:
  Byte    port count N          never 0 inside the list
  4 bytes IPv4 address
  N x Short port
Byte    0                       port count 0 ends the block list
Byte    MSC_ENDSERVERLISTPART (7) if more packets follow, MSC_ENDSERVERLIST (2) on the last
```

Servers sharing an IP are grouped into one block, and a block is never split across packets. The
master does not send a packet count up front; a launcher knows it has everything when it has seen
`MSC_ENDSERVERLIST` and every lower packet number.

**Legacy request:** Long `199` (the same code a launcher sends a game server). The reply is a
single packet with no splitting, so it cannot scale to a large list:

```text
Long    MSC_BEGINSERVERLIST (0)
repeat:
  Byte    MSC_SERVER (1)
  4 bytes IPv4 address
  Short   port
Byte    MSC_ENDSERVERLIST (2)
```

**Hidden servers.** In both forms the reference master leaves out every server whose heartbeat said
`sv_enforcemasterbanlist` is false, unless it was started with `-DontHideBanIgnoringServers` (only
recognized as the first argument). Hiding is the default. This matches the wiki's statement that
such servers are hidden "according to current policy"; for the live master that is a policy claim,
not something the engine enforces. The server still sends heartbeats either way, so it stays
registered, just unlisted.

The list gives addresses only. Names, maps and player counts come from querying each server with
the launcher protocol.

## Engine-family divergence

None of this exists in UZDoom or the wider GZDoom family. Multiplayer there is a peer-to-peer
lockstep mesh (`src/d_net.cpp`) where one player starts a game with `-host` and the others connect
with `-join` (`src/common/engine/i_net.cpp`). There is no dedicated server to register, no
`masterhostname` or master address, no heartbeat or verification handshake, and no ban-list push:
a search of UZDoom's `src/` for the master constants and cvar names turns up nothing. A UZDoom
game is found by being told the host's address directly.
