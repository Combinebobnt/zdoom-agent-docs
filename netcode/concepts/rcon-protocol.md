# The RCON protocol (remote administration)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `RCon protocol` (https://wiki.zandronum.com/w/index.php?title=RCon_protocol&oldid=2186, retrieved 2026-09-22) + verified against the Zandronum source's `src/sv_rcon.cpp` (whole file), `src/sv_rcon.h:62-104`, `rcon_utility/main.cpp` (`main_Loop`, `main_ParseCommands`, `main_AttemptConnection`, `main_SendPassword`), `src/sv_main.cpp` (`sv_rconpassword` at line 364, `SERVER_DetermineConnectionType` at 1828, `server_RequestRCON` at 6480, `server_RCONCommand` at 6548, `server_CheckForClientCommandFlood` at 5783), `src/cl_main.cpp` (`CCMD( rcon )`/`send_password`/`rcon_logout` at 9924-10012), `src/cl_commands.cpp:560-576`, `src/networkshared.cpp` (`QueryIPQueue`, `BYTESTREAM_s`), `src/network.cpp` (`NETWORK_LaunchPacket`, `CMD5Checksum::GetMD5`) and `src/c_console.cpp:1109-1116`. Line numbers are from a 3.3-alpha checkout; `sv_rcon.cpp` is within 2 lines of 3.2.1 and `sv_main.cpp`/`cl_main.cpp` are not, so search by function name. Every behavior below was confirmed present at 3.2.1 (`git merge-base --is-ancestor` on each introducing commit, and a `28f736fb3..HEAD` diff of `sv_rcon.cpp` that only adds the `useZStd=false` argument).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
(NonCommercial) — see [LICENSE](../../LICENSE) §2.

A Zandronum server accepts remote administration over two unrelated mechanisms. The **RCON
protocol** proper is an out-of-band UDP protocol spoken by external tools (the in-repo reference
client is `rcon_utility/`): salted-MD5 login, then a stream of console output and state updates,
and console commands in the other direction. The **in-game `rcon`** path (see its own section
below) is a game-protocol client command used by a player already connected to the server, and it
sends the password in plaintext. Both check the same `sv_rconpassword` cvar.

## Transport, briefly

Shared with the launcher and master-server protocols; [wire-basics.md](wire-basics.md) is the
full treatment, this is the RCON-relevant summary:

- UDP to the server's game port, Huffman-encoded, **one RCON message per datagram**. Huffman is
  compression only, not encryption: everything except the password digest is readable in transit.
- RCON never adds anything to the server's shared 10-second flood queue (see "Failed-login rate
  limiting" below), but an IP placed there by another subsystem (for example an unknown
  connection challenge) has its RCON packets, including an admin's `CLRC_PONG`s, silently dropped
  for that window.
- Sessions are keyed by full IP **and** port (`NETADDRESS_s::Compare` with its default
  `ignorePort=false`). A client must send from one stable source port for the whole session.

## Message codes

Protocol version: server `PROTOCOL_VERSION` 4, accepts clients reporting 3 or higher
(`MIN_PROTOCOL_VERSION`). The server's behavior does not otherwise branch on the client's version;
version 4 added tab completion.

Server to client (`SVRC_*`):

| Code | Name | Payload after the code byte |
|---|---|---|
| 32 | `SVRC_OLDPROTOCOL` | byte server protocol version, string server version (`DOTVERSIONSTR`) |
| 33 | `SVRC_BANNED` | none |
| 34 | `SVRC_SALT` | string: 32-character salt |
| 35 | `SVRC_LOGGEDIN` | see "Login payload" below |
| 36 | `SVRC_INVALIDPASSWORD` | none |
| 37 | `SVRC_MESSAGE` | string: one console line |
| 38 | `SVRC_UPDATE` | one update record (subtype byte + data, below) |
| 39 | `SVRC_TABCOMPLETE` | byte count N (< 50), then N strings |
| 40 | `SVRC_TOOMANYTABCOMPLETES` | **short** (16-bit LE) match count, 50 or more |

Client to server (`CLRC_*`):

| Code | Name | Payload | Accepted from |
|---|---|---|---|
| 52 | `CLRC_BEGINCONNECTION` | byte protocol version | anyone |
| 53 | `CLRC_PASSWORD` | string: hex MD5 digest | a pending candidate only |
| 54 | `CLRC_COMMAND` | string: console command | an authenticated client only |
| 55 | `CLRC_PONG` | none | an authenticated client only |
| 56 | `CLRC_DISCONNECT` | none | an authenticated client only |
| 57 | `CLRC_TABCOMPLETE` | string: partial command | an authenticated client only |

A message from an address that isn't in the required state is dropped silently, with no reply.

Update subtypes (`SVRCU_*`), the byte after `SVRC_UPDATE` or inside the login payload:

| Value | Name | Data | Sent when |
|---|---|---|---|
| 0 | `SVRCU_PLAYERDATA` | byte count, then that many names | a client finishes connecting, a client disconnects, a player's color-stripped name changes (compared case-insensitively), a bot is added or removed, an admin force-renames a player |
| 1 | `SVRCU_ADMINCOUNT` | byte: number of **other** authenticated RCON clients | an RCON client logs in, disconnects, or times out |
| 2 | `SVRCU_MAP` | string: map lump name (`level.mapname`, e.g. `MAP01`) | a new level starts |

The player count and list include bots and spectators (`SERVER_CountPlayers( true )` and every
`playeringame` slot), and names have color codes removed. The admin count is the authenticated
list size minus one written as a byte; the list has no size cap, so past 256 admins the count
wraps.

## Login sequence

1. Client sends `CLRC_BEGINCONNECTION` + its protocol version byte. A missing version byte reads as
   -1 and counts as too old.
2. Server replies, in this order of checks:
   - IP banned (`SERVERBAN_IsIPBanned`): `SVRC_BANNED`.
   - Version below 3: `SVRC_OLDPROTOCOL`.
   - Otherwise: any existing candidate **and any existing authenticated session** at the same
     IP:port is deleted (no log line, no admin-count update), a new candidate slot is created, and
     `SVRC_SALT` is sent.
3. Client computes `MD5(salt + password)`: the salt string immediately followed by the password,
   no separator, no terminator, digested as bytes. It sends `CLRC_PASSWORD` + the 32-character hex
   digest as a NUL-terminated string.
4. Server computes the same digest (`CMD5Checksum::GetMD5` renders it as **lowercase** hex) and
   compares with `strcmp`, so an uppercase-hex digest fails. It replies `SVRC_INVALIDPASSWORD` on a
   mismatch **or whenever `sv_rconpassword` is empty**, else `SVRC_LOGGEDIN`.
5. **Either way the candidate slot is deleted.** A retry needs a fresh `CLRC_BEGINCONNECTION` and a
   new salt; a second `CLRC_PASSWORD` against the old salt is silently ignored.

The candidate must answer within 10 seconds of `CLRC_BEGINCONNECTION` (`RCON_CANDIDATE_TIMEOUT_TIME`);
the candidate's timer is never refreshed.

### `sv_rconpassword` values

- Empty (the default): the protocol is effectively disabled. Every login fails, and so does the
  in-game `send_password`.
- 1 to 4 characters: the cvar's change callback prints `sv_rconpassword must be greater than 4
  chars in length!` and resets it to empty, which disables RCON rather than keeping a previous
  value.
- 5 or more characters: accepted. The comparison is case-sensitive on both paths.

### Login payload (`SVRC_LOGGEDIN`)

```text
byte    35 (SVRC_LOGGEDIN)
byte    server protocol version (4)
string  sv_hostname, with color codes expanded then stripped
byte    3 (NUM_RCON_UPDATES)
        3 update records, in subtype order: PLAYERDATA, ADMINCOUNT, MAP
        (each is subtype byte + data; no SVRC_UPDATE byte in front)
byte    history line count (0-32)
string  x count  recent console lines, oldest first
```

The history holds the last 32 console lines the server printed, each prefixed with the server's
local time as `[hh:mm:ss am] ` or `[hh:mm:ss pm] ` (12-hour clock). Lines printed before midday
carry one extra trailing space after the text. The server logs `RCON client at <addr> connected.`
before building this packet, so the new client's own connect line is the last history entry. The
whole payload must fit in one 8192-byte datagram; 32 long lines can exceed that, and an overflow
makes the writer print an error through the console, which (see below) clears the shared RCON send
buffer mid-build. Treat a malformed login packet as possible when history lines are long.

Immediately after, every authenticated client, **including the one that just logged in**, receives
a separate `SVRC_UPDATE`/`SVRCU_ADMINCOUNT` datagram (the new client is already on the list), so a
client should expect that second packet right behind `SVRC_LOGGEDIN`.

## After login

- **Console output.** Every console line the server prints (except `PRINT_LOW` messages, and only
  on a `-host` server) is sent to every authenticated client as `SVRC_MESSAGE`, with no timestamp
  prefix, and appended to the 32-line history.
- **Commands.** `CLRC_COMMAND`'s string is logged as `-> <cmd> (RCON by <addr>)` and handed to
  `SERVER_AddCommand`, i.e. run like a line typed at the server console (`AddCommandString`, so
  `;`-separated commands and `wait` work). On a headless build (`NO_SERVER_GUI`) it runs
  immediately; on a build with the Windows server GUI it is queued and run later. There is no reply
  packet; any output comes back as ordinary `SVRC_MESSAGE` lines.
- **Tab completion** (protocol 4). `CLRC_TABCOMPLETE` + partial string returns `SVRC_TABCOMPLETE`
  (byte count, then each candidate) when there are fewer than 50 matches, and
  `SVRC_TOOMANYTABCOMPLETES` with a 16-bit count when there are 50 or more. The reference client in
  `rcon_utility/` never sends it.
- **Keepalive.** An authenticated client is dropped 40 seconds (`RCON_CLIENT_TIMEOUT_TIME`) after
  its last `CLRC_PONG` or `CLRC_COMMAND`, logged as `RCON client at <addr> timed out.`
  `CLRC_TABCOMPLETE` does **not** refresh the timer. The reference client sends `CLRC_PONG` when it
  has sent nothing for more than 10 seconds (a quarter of the timeout).
- **Disconnect.** `CLRC_DISCONNECT` removes the session, logs `RCON client at <addr>
  disconnected.`, and updates the remaining admins' count. There is no reply.

## Zandronum-specific: quirks for client authors

- **`SVRC_BANNED` and `SVRC_OLDPROTOCOL` replies can carry stale data in front of them.**
  `server_rcon_HandleNewConnection` writes these two replies into the module's shared send buffer
  without clearing it first, and `NETWORK_LaunchPacket` doesn't reset the buffer after sending.
  Every other RCON reply clears first. So once the RCON module has sent anything since server
  start, these two replies are appended to whatever RCON packet the server last sent to anyone (a
  console line, another client's salt, an update, even a full login payload), and repeated
  rejections keep appending to each other until the next normal RCON send clears the buffer. The
  stale packet's first byte is what a client sees first. A client that reads only
  the first byte (as `rcon_utility/` does) will misread a ban or version rejection as whatever that
  byte was. Scanning the datagram for a trailing `33`/`32` is not reliable either; the robust signal
  for "rejected" is not receiving a well-formed `SVRC_SALT`. A consequence of the same bug: any
  sender, banned or not, who sends `CLRC_BEGINCONNECTION` with a version below 3 gets the server's
  last RCON packet echoed back to it, which can include admin-visible console output.
- **Console printing clears the send buffer.** Every server `Printf` reaches `SERVER_RCON_Print`,
  which reuses the same buffer. Source comments warn to finish and send a packet before printing;
  the code follows that on its normal paths, but an overflow error printed while a packet is being
  built (while at least one client is authenticated) clears the partly built packet and leaves the
  error line's own `SVRC_MESSAGE` in its place, so the rest of the build is appended to that and
  the recipient gets a malformed packet.
- **Salt is not cryptographically random.** `server_rcon_CreateSalt` picks each of the 32
  characters from an 85-character alphabet using the current `gametic` plus three draws from the
  engine's game PRNG (`M_Random`), modulo 85. That generator is a game RNG, not a secure one, so
  the salt is predictable rather than secret, and it is sent in the clear anyway. Its job is to stop replaying a captured digest across sessions, not to resist
  an attacker; an observer of one `SVRC_SALT`/`CLRC_PASSWORD` pair can brute-force the password
  offline against plain MD5.
- **Unbounded lists.** Neither the candidate list nor the authenticated list has a size cap.
  Candidates expire after 10 seconds; authenticated sessions persist as long as they keep ponging.

## Failed-login rate limiting does not exist on this path

The source clearly intends one: a failed login, a banned request, and a too-old version request
each add the sender to `g_BadRequestFloodQueue`, and a failed login logs `Failed RCON login from
<addr>. Ignoring IP for 10 seconds...`. **Nothing ever checks that queue.** `addressInQueue` is
called only on `sv_main.cpp`'s separate shared flood queue, which RCON never writes to. The queue's
own numbers don't match the log either: it is constructed with 4 (`BAD_QUERY_IGNORE_TIME`), and is
fed `gametic / 1000`, which advances once per roughly 28.6 seconds, not once per second. None of
that matters, because the queue is write-only. The practical result: **a client can make password
attempts as fast as it can do the salt round trip**, and the "Ignoring IP" log line is false. The
4-second "Connect [n]" countdown in `rcon_utility/` after a bad password is purely client-side.

## The in-game `rcon` path (plaintext)

A player who is connected to the server as a game client can use console commands instead of an
external tool. This is a separate mechanism with no salt and no hashing:

| Console command | Sends (game-protocol client command) | Server handler |
|---|---|---|
| `send_password <password>` | `CLC_CHANGERCONSTATUS`, byte 1, **password as a plain string** | `server_RequestRCON` |
| `rcon_logout` | `CLC_CHANGERCONSTATUS`, byte 0 | `server_RequestRCON` |
| `rcon <command ...>` | `CLC_RCONCOMMAND`, command string | `server_RCONCommand` |

- **The password crosses the network in plaintext**, inside an ordinary game packet. Huffman (and,
  after 3.2.1, optional Zstandard, added in `d09240b3c`) compression is reversible by anyone with
  the public tables, so anyone who can observe the player's traffic learns `sv_rconpassword`
  itself, not a one-session digest. Prefer the salted UDP protocol when the network path isn't trusted.
- Only `send_password` uses the first argument; extra words are dropped, so a password containing
  spaces has to be quoted. The server grants access if the password is non-empty and matches by
  `strcmp`, replying `RCON access granted.` to the player and logging `RCON access for <name> is
  granted!`. After granting, it pushes every non-default server cvar to that client. A wrong
  password logs `Incorrect RCON password attempt from <name>.` (player name, not address).
- `send_password` **is** rate-limited, unlike the UDP path: it goes through the per-client
  command-flood check, which (while `sv_limitcommands` is on, the default) bans the client for 10
  minutes after more than 8 flood-checked commands within 60 seconds. `rcon` commands themselves
  are not flood-checked. A repeat `send_password` while the slot already has access is answered
  `You already have RCON access.` without checking the password again.
- `rcon` joins its arguments with spaces, re-quoting any argument that contains a space, and sends
  the result. The server silently ignores it unless that client has access; otherwise it logs
  `-> <cmd> (RCON by <name> - <addr>)` and runs the command inline with `C_DoCommand` (a single
  command, unlike the UDP path's `SERVER_AddCommand`/`AddCommandString`), routing console output to
  that player for the duration.
- All three console commands do nothing unless the client is fully connected, and none can be run
  from ACS `ConsoleCommand`.
- Access is per game-client slot: `rcon_logout` clears it, and it is reset whenever a new
  connection takes the slot, so it never survives a reconnect.
- The server pushes the access state to the client (`SVC2_RCONACCESS`). While it is set, the
  client's own local `map` command is refused with a message telling the player to `rcon_logout`
  first (`src/g_level.cpp:209-213`), since running it would otherwise leave the server and start a
  local game. This does not affect `rcon map`, which runs on the server.

## Wiki/engine divergence

The wiki page (oldid 2186) disagrees with the source on these points; the source is authoritative:

- **Timeout.** The wiki says RCON clients not heard from within 10 seconds are timed out and
  suggests a `CLRC_PONG` every 5 seconds. 10 seconds is the unauthenticated candidate's timeout;
  an authenticated client is dropped after 40 seconds, and only `CLRC_PONG`/`CLRC_COMMAND` reset
  it. A 5-second pong is safe, just more frequent than needed.
- **`SVRC_TOOMANYTABCOMPLETES` count width.** The wiki says the count is a byte; the server writes
  a 16-bit little-endian short. A client reading one byte will misparse.
- **Tab-complete boundary.** The wiki says "less than 50" gets the list and "more than 50" gets the
  refusal, leaving exactly 50 undefined. Exactly 50 matches gets `SVRC_TOOMANYTABCOMPLETES`.
- **"All traffic is Huffman".** True for RCON. The post-3.2.1 Zstandard option applies to game
  traffic only.
- Not contradicted but absent from the wiki: the empty and 1-4 character password rules, lowercase
  hex and case-sensitive compare, candidate deletion on every attempt, color stripping of the
  hostname and player names, bots and spectators in the player list, the history timestamp prefix,
  the stale-buffer reply bug, the missing rate limit, and the entire in-game plaintext path.

## Engine-family divergence

None of this exists on UZDoom or other GZDoom-family engines. Their multiplayer is a peer-to-peer
lockstep netgame joined through a `-host`/`-join` lobby, with no dedicated server process to
administer. The UZDoom source contains no RCON protocol, command or cvar (the string `rcon` appears
only inside unrelated identifiers). Its only password is a lobby join password (`net_password`)
checked when a peer joins the game; it grants no remote console access.
