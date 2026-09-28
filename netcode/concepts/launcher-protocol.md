# Launcher query protocol

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki `Launcher protocol` (https://wiki.zandronum.com/w/index.php?title=Launcher_protocol&oldid=2289, retrieved 2026-09-22) + verified against the Zandronum source's `src/sv_main.cpp` (`SERVER_DetermineConnectionType` at line 1828, `SERVER_IgnoreIP` at line 4628), `src/network_enums.h:419-472` (the `CLC_*` range dropped without a flood-queue entry), `src/sv_master.cpp` (the field writers from line 119, the `ResponseFunctions` table at line 497, `SERVER_MASTER_Broadcast` at line 640, `SERVER_MASTER_SendServerInfo` at line 697, `SERVER_MASTER_GetGameName` at line 918), `src/sv_main.h:110-155` (`SQF_*`/`SQF2_*`), `src/networkshared.h:69-172` (response codes, `LAUNCHER_SERVER_CHALLENGE`, ports, `MAX_UDP_PACKET`) and `src/networkshared.cpp` (`QueryIPQueue`); line numbers are at bdd0f7beb. Secondary source: the first-party `docs/zandronum-launcher-protocol.txt` (v0.61), which is stale (see "Wiki/engine divergence").
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
(NonCommercial) — see [LICENSE](../../LICENSE) §2.

The launcher query protocol is how a server browser (Doomseeker and similar, or Zandronum's own
built-in browser) asks one Zandronum server for its name, map, WADs, players and settings. One UDP
request, one reply (or several segments of one reply). It is served on the server's game port
(default 10666), dispatched from the same entry point that handles new client connections and
RCON. Getting the *list* of servers from the master server is a different exchange, covered in
[master-server-protocol.md](master-server-protocol.md).

Transport, Huffman encoding, field types (`Byte`/`Short`/`Long`/`Float`/`String`) and the
8192-byte build buffer are shared with the other two protocols: see [wire-basics.md](wire-basics.md).

## Request

```text
Long   199      LAUNCHER_SERVER_CHALLENGE
Long   Flags    SQF_* bits wanted
Long   Time     any value; echoed back verbatim (use it to measure ping)
Long   Flags2   SQF2_* bits wanted - present only if Flags has SQF_EXTENDED_INFO
Byte   2        optional - exactly 2 requests a segmented reply
```

How the server actually parses it, which matters when a launcher gets the layout slightly wrong:

- **Only the first byte identifies the command.** The dispatcher reads one byte (199), then skips
  the next three without checking them. Only the first command in a packet from a non-client
  address is handled.
- **`Flags2` is read only when `Flags` carries `SQF_EXTENDED_INFO`** (`0x80000000`). A launcher
  that sends `Flags2` without setting that bit gets its `Flags2`'s low byte read as the
  segmentation byte instead; if that byte happens to be `2`, the reply comes back segmented.
- **Short reads return `-1`.** The byte-stream reader returns `-1` (all bits set) for a field past
  the end of the datagram. So `Flags` with `SQF_EXTENDED_INFO` but no `Flags2` behaves as a
  request for every `SQF2_*` field, and a missing `Time` is echoed as `0xFFFFFFFF`.
- **Segmentation byte:** any trailing byte is read; only the value `2` selects segmented mode.
  Anything else, or no byte at all, means a single unsegmented reply.

## Reply codes

Every reply datagram starts with a `Long`:

| Code | Name | Meaning |
|---|---|---|
| 5660023 | `SERVER_LAUNCHER_CHALLENGE` | Accepted, unsegmented; the reply body follows |
| 5660024 | `SERVER_LAUNCHER_IGNORING` | Denied: this IP already queried within `sv_queryignoretime` |
| 5660025 | `SERVER_LAUNCHER_BANNED` | Denied: this IP is on the server's ban list |
| 5660032 | `SERVER_LAUNCHER_CHALLENGE_SEGMENTED` | Accepted, segmented; a segment header follows |

The two denial replies are not bare codes: each is followed by the request's `Time` echoed as a
`Long`, and nothing else. 5660031 is deliberately skipped (an older, incompatible segmented design
used it).

## Rate limiting and ban checks, in order

Two separate per-IP mechanisms apply, and they fail differently:

1. **Shared flood queue: silent drop.** Before even reading the command byte, the server drops the
   datagram with no reply if the source IP is in the shared 10-second flood queue, or that queue
   is full ([wire-basics.md](wire-basics.md#the-shared-10-second-flood-queue)). A query whose
   first byte matches no known command puts the IP there, so a launcher that sends garbage once
   goes silent for 10 seconds rather than receiving IGNORING. Two exceptions are dropped silently
   with no queue entry: a first byte in the in-game client-command range (3 through 51), and a
   master-server ban-list code (205-207) from any address other than the master.
2. **Launcher ignore list: IGNORING reply.** If the IP (compared without port) made an accepted
   query within the last `sv_queryignoretime` seconds (default 10, measured in game tics), the
   reply is `SERVER_LAUNCHER_IGNORING` + `Time`. Being ignored does not extend the window. This
   check runs **before** the ban check, so an IP banned (for example with `addban`) just after an
   accepted query keeps getting IGNORING until its window lapses, and only then BANNED.
3. **Ban check: BANNED reply.** `SERVER_LAUNCHER_BANNED` + `Time`. A banned IP is not added to the
   ignore list, so it gets BANNED on every query.
4. Otherwise the IP is added to the ignore list (a 512-entry ring, separate from the flood queue)
   and the full reply is sent.

Because the ignore list keys on IP alone, several launchers behind one NAT address share one
query per `sv_queryignoretime`. `sv_showlauncherqueries` logs each accepted, ignored and banned
query to the server console.

## Reply body

For an unsegmented reply the body follows the 5660023 code directly. For a segmented reply the
reassembled buffer is the same body **without** the leading 5660023: it begins at `Time`.

```text
Long    Time      echoed from the request
String  Version   e.g. "<version with revision> on Linux 6.1.0-amd64" / "... on Windows ..."
Long    Flags     the corrected flags (see below); parse using these, not the requested ones
...     fields    one group per set bit of Flags, in ascending bit order
                  (SQF_EXTENDED_INFO, bit 31, writes Flags2 and then the SQF2_* fields follow,
                   also in ascending bit order)
```

### Flag correction

The server rewrites the requested flags before answering, and echoes the result. A parser must
drive field decoding from the echoed `Flags`/`Flags2`:

- Unknown bits are dropped (`Flags &= SQF_ALL`, `Flags2 &= SQF2_ALL`). Bit 15 (`0x8000`) is unused.
- `SQF_TEAMDAMAGE` is dropped unless the game is a team mode (`teamplay`, `teamgame`, `teamlms`,
  `teampossession`) **or** not a deathmatch mode at all. Cooperative-family servers do report it;
  plain deathmatch, duel, LMS and similar do not.
- `SQF_TEAMSCORES` and all four `SQF_TEAMINFO_*` flags are dropped unless the current game mode
  has the `PLAYERSONTEAMS` flag (see
  [`zandronum-lumps/concepts/gamemode.md`](../../zandronum-lumps/concepts/gamemode.md); a
  `GAMEMODE` lump can change which modes carry it).
- `SQF_PLAYERDATA` forces `SQF_NUMPLAYERS` on, since the player loop needs the count.
- `SQF_OPTIONAL_WADS` is dropped when no loaded WAD is optional; `SQF_DEH` when no DeHackEd patch
  is loaded.
- If `Flags2` masks to zero, `SQF_EXTENDED_INFO` is dropped too, so no `Flags2` field is written.

### Fields (`Flags`)

| Bit | Flag | Wire data |
|---|---|---|
| `0x00000001` | `SQF_NAME` | String `sv_hostname`, with color codes stripped |
| `0x00000002` | `SQF_URL` | String `sv_website` |
| `0x00000004` | `SQF_EMAIL` | String `sv_hostemail` |
| `0x00000008` | `SQF_MAPNAME` | String current map lump name |
| `0x00000010` | `SQF_MAXCLIENTS` | Byte `sv_maxclients` |
| `0x00000020` | `SQF_MAXPLAYERS` | Byte `sv_maxplayers` |
| `0x00000040` | `SQF_PWADS` | Byte count, then one String name per PWAD |
| `0x00000080` | `SQF_GAMETYPE` | Byte game-mode code (table below), Byte `instagib`, Byte `buckshot` |
| `0x00000100` | `SQF_GAMENAME` | String: `DOOM`, `DOOM II`, `Heretic`, `Hexen` or `ERROR!` |
| `0x00000200` | `SQF_IWAD` | String IWAD name |
| `0x00000400` | `SQF_FORCEPASSWORD` | Byte `sv_forcepassword` |
| `0x00000800` | `SQF_FORCEJOINPASSWORD` | Byte `sv_forcejoinpassword` |
| `0x00001000` | `SQF_GAMESKILL` | Byte `skill` |
| `0x00002000` | `SQF_BOTSKILL` | Byte `botskill` |
| `0x00004000` | `SQF_DMFLAGS` | Deprecated. Long `dmflags`, `dmflags2`, `compatflags` |
| `0x00010000` | `SQF_LIMITS` | Short `fraglimit`; Short `timelimit` (truncated to a whole number); Short minutes left, **only if** that truncated `timelimit` is non-zero (clamped at 0); Short `duellimit`, `pointlimit`, `winlimit` |
| `0x00020000` | `SQF_TEAMDAMAGE` | Float `teamdamage` |
| `0x00040000` | `SQF_TEAMSCORES` | Deprecated. Two Shorts (team 0, team 1), each frags, wins or points depending on the mode's scoring flags |
| `0x00080000` | `SQF_NUMPLAYERS` | Byte count of in-game players, **bots and spectators included** |
| `0x00100000` | `SQF_PLAYERDATA` | Per player, see below |
| `0x00200000` | `SQF_TEAMINFO_NUMBER` | Byte number of available teams |
| `0x00400000` | `SQF_TEAMINFO_NAME` | One String per team |
| `0x00800000` | `SQF_TEAMINFO_COLOR` | One Long (RGB) per team |
| `0x01000000` | `SQF_TEAMINFO_SCORE` | One Short per team, frags, wins or points depending on the mode |
| `0x02000000` | `SQF_TESTING_SERVER` | Byte 0/1, String: empty on a release build, else a download path of the form `downloads/testing/<ver>/ZandroDev<ver>-<date>windows.zip` |
| `0x04000000` | `SQF_DATA_MD5SUM` | Deprecated. Always an empty String |
| `0x08000000` | `SQF_ALL_DMFLAGS` | Byte 6, then six Longs: `dmflags`, `dmflags2`, `zadmflags`, `compatflags`, `zacompatflags`, `compatflags2` |
| `0x10000000` | `SQF_SECURITY_SETTINGS` | Byte `sv_enforcemasterbanlist` |
| `0x20000000` | `SQF_OPTIONAL_WADS` | Byte count, then one Byte per optional WAD: its index into the `SQF_PWADS` list |
| `0x40000000` | `SQF_DEH` | Byte count, then one String per DeHackEd patch |
| `0x80000000` | `SQF_EXTENDED_INFO` | Long corrected `Flags2`, then the `SQF2_*` fields |

**`SQF_PLAYERDATA`, repeated for each in-game player (count = the `SQF_NUMPLAYERS` byte):**

| Type | Content |
|---|---|
| String | Player name (color codes **not** stripped, unlike `SQF_NAME`) |
| Short | Score: points if the mode earns points, else wins if it earns wins, else frags if it earns frags, else kills |
| Short | Ping |
| Byte | 1 if a true spectator (not a dead player waiting to respawn) |
| Byte | 1 if a bot |
| Byte | Team index, or 255 if not on a team. **Present only when the mode has `PLAYERSONTEAMS`**; absent entirely otherwise, so every later field shifts |
| Byte | Time on the server, in **minutes** |

### Fields (`Flags2`)

| Bit | Flag | Wire data |
|---|---|---|
| `0x01` | `SQF2_PWAD_HASHES` | Byte count, then one String MD5 per PWAD, same order as `SQF_PWADS` |
| `0x02` | `SQF2_COUNTRY` | **3 raw bytes, no terminator.** `sv_country` uppercased if it is exactly 3 characters; `XIP` ("launcher should geolocate") if it is `automatic` (the default, case-insensitive); `XUN` ("unknown") for any other value. Any 3-character value is passed through unvalidated |
| `0x04` | `SQF2_GAMEMODE_NAME` | String, the current mode's name from the `GAMEMODE` lump |
| `0x08` | `SQF2_GAMEMODE_SHORTNAME` | String, the current mode's short name from the `GAMEMODE` lump |
| `0x10` | `SQF2_VOICECHAT` | Byte `sv_allowvoicechat` |

### Game-mode codes (`SQF_GAMETYPE`)

| Code | Mode | Code | Mode |
|---|---|---|---|
| 0 | Cooperative | 8 | Team LMS |
| 1 | Survival | 9 | Possession |
| 2 | Invasion | 10 | Team Possession |
| 3 | Deathmatch | 11 | Team Game |
| 4 | Teamplay | 12 | CTF |
| 5 | Duel | 13 | One-Flag CTF |
| 6 | Terminator | 14 | Skulltag |
| 7 | Last Man Standing | 15 | Domination |

## Segmented replies

Requested with the trailing `2` byte. The server builds the normal reply body (without the 5660023
code) and splits it into chunks of `sv_maxpacketsize - 12` bytes (default `sv_maxpacketsize` is
1024, capped at 8192; see [`console/notes/sv_maxpacketsize.md`](../../console/notes/sv_maxpacketsize.md)).
Each chunk goes out as its own datagram with a 12-byte header:

```text
Long   5660032     SERVER_LAUNCHER_CHALLENGE_SEGMENTED
Byte   Segment     0-based segment number
Byte   NumSegments total segments
Short  Offset      where this chunk goes in the reassembled body
Short  Size        chunk length, header excluded
Short  TotalSize   length of the reassembled body
```

Allocate `TotalSize` bytes, copy each chunk to its `Offset`, and parse once `NumSegments` distinct
segments have arrived. UDP can reorder or drop segments; the server never resends, so a launcher
should time out and re-query (after `sv_queryignoretime`, or it gets IGNORING). Track which
segment numbers have arrived rather than counting datagrams, so a duplicate is not mistaken for a
missing segment. An unsegmented
reply ignores `sv_maxpacketsize` entirely and is limited only by the 8192-byte build buffer.

`sv_maxpacketsize` has no lower clamp. From reading the chunking loop, a value of 12 or less leaves
a zero or negative chunk size, which the loop does not guard against; this was not tested.

## LAN broadcast

Independently of any query, a server with `sv_broadcast` on (the default) and without the
`-nobroadcast` command-line switch sends an unsolicited reply once per second to UDP port 15101
(`DEFAULT_BROADCAST_PORT`). It is a normal unsegmented 5660023 reply with every `SQF_*` and
`SQF2_*` flag requested (then corrected as above) and `Time` = 0, and it skips the ignore-list and
ban checks. On Windows it goes to `255.255.255.255`; elsewhere the server derives a classful
broadcast address (A/B/C by the first octet) from its own local address.

## Wiki/engine divergence

The wiki page (oldid=2289) is current with the source on the structure of the protocol: SQF2,
segmentation, optional WADs, DeHackEd patches and minute-based player time are all there. What
it gets wrong or leaves out, checked against source:

- **Game-name casing.** The wiki lists `"HERETIC"` and `"HEXEN"`; the server sends `Heretic` and
  `Hexen` (`DOOM` and `DOOM II` are uppercase as documented).
- **Denial replies carry `Time`.** The wiki describes the IGNORING and BANNED codes only as a
  leading `Long`; both are followed by the echoed `Time`.
- **Player score includes wins.** The wiki says pointcount/fragcount/killcount; the source picks
  wins for win-scored modes before falling back to frags and kills.
- **Correction rules are never stated.** The wiki says the returned flags are "possibly corrected
  (see below)" but no rule follows; the full set is in "Flag correction" above.
- **Team byte wording.** "Returned on team games, 255 is no team" can be read as "always present,
  255 outside team games". The byte is absent entirely outside `PLAYERSONTEAMS` modes.
- **Testing-server path.** The wiki points at a `skulltag.com/testing/files/` archive; the source
  now sends a `downloads/testing/...` path (relative to zandronum.com). Cosmetic.

**Secondary source, `docs/zandronum-launcher-protocol.txt` (v0.61), is older and further off.**
It stops at `SQF_SECURITY_SETTINGS` (no `SQF_OPTIONAL_WADS`, `SQF_DEH`, `SQF_EXTENDED_INFO` or any
`SQF2_*` field), has no segmented replies, gives player time in seconds (it is minutes), says
`SQF_DATA_MD5SUM` returns a real checksum (it is always empty), and hard-codes the ignore window as
10 seconds rather than `sv_queryignoretime`. Prefer the wiki or this page over it.

## Engine-family divergence

None of this exists on UZDoom or other GZDoom-family engines. Their multiplayer is a
peer-to-peer lockstep netgame (`src/d_net.cpp` in the UZDoom source): one player starts a lobby
with `-host`, the others connect with `-join`, and a short pre-game handshake of `PRE_*` packets
(`src/common/engine/i_net.cpp`) exchanges connection, user-info and game-info before play starts.
There is no dedicated server process, nothing answers a launcher query, no `SQF_*` flags exist, no
LAN broadcast is sent and nothing registers with a master server. A server browser built for
Zandronum cannot list UZDoom games.
