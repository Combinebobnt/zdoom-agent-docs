# Network command and buffer size limits

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-13)
**Provenance:** written from the UZDoom source's `src/d_net.cpp`, `src/common/engine/i_protocol.cpp`,
and `src/common/engine/i_net.h`; no wiki page covers this. The loopback consequence was then
observed in a live singleplayer run (2026-09-27; see "Observed loopback consequence" below).

`EventHandler.SendNetworkCommand()`/`SendNetworkBuffer()` (see
[Event handlers: `StaticEventHandler` and `EventHandler`](../classes/eventhandler.md)) let a mod
send arbitrarily large typed payloads, but the engine's own size-encoding path has a bug that
silently mis-sizes a command well before any documented limit, plus a separate hard budget shared
with the rest of the packet. Both are worth knowing before sending a large `NetworkBuffer`.

## The skip-length precedence bug

The engine computes the byte count it needs to skip past a network command from a high byte and a
low byte, meant to combine into one 16-bit count with 2 added for a header. Operator precedence in
that computation binds the `+2` to the low byte before it's combined with the shifted high byte,
instead of adding it to the already-combined value. Since the value is written big-endian, this
undercounts by exactly 256 bytes whenever the low byte is already 254 or 255 **and** the high byte
is odd — sizes of 510, 511, 1022, 1023, 1534, 1535 bytes and so on (the start of a series that
recurs at every following odd-high-byte boundary, not an exhaustive list).

This is reachable from ordinary ZScript, not a theoretical edge case: `SendNetworkCommand`/
`SendNetworkBuffer` write their size as a plain 16-bit int, and 128 `NET_INT` arguments is already
512 bytes — past the first broken boundary.

## Two failure modes, depending on path

**Remote packets** mis-size and get dropped: the receiving side's packet-size computation comes
out wrong, the size check on the incoming packet fails, prints an "Incorrect packet size" message,
and drops the packet — stalling lockstep with that peer for the tic.

**Loopback packets take a different, more surprising path.** A peer's own locally-generated
commands — and in singleplayer, *every* command — go through a loopback shortcut that returns the
locally-buffered data before the remote-packet size check above ever runs, because the send side's
routing check for the local client is evaluated ahead of its own network-mode guard. A bad-size
command on this path skips the size check entirely and reaches the parser that splits each tic's
command data from its user command. That parser's skip lands 256 bytes short, inside the payload,
and from there it reads payload bytes as command tags. The skip dispatch has no default case, so
an unrecognized tag skips nothing and the parser moves on one byte at a time. What happens next
depends entirely on the payload's content (see "Observed loopback consequence" below).

**Lead with the loopback path when explaining this to someone:** it means a mod sending a
bad-size command can mis-parse on its own machine with no other player, server, or netgame
involved at all — not just something that shows up under real network conditions.

## Budget context: `MAX_MSGLEN`

The total per-tic packet budget is a fixed 14000-byte constant, shared with every player's own
usercmd data packed into the same packet — so the effective ceiling on one network command or
buffer is lower than 14000 bytes in any game with more than one player, not a private allowance
per command. Exceeding the total budget is a hard engine error, not silent truncation — don't rely
on an oversized send just getting quietly cut down to size.

## Observed loopback consequence

Run 2026-09-27 in an offline singleplayer game (DOOM2.WAD MAP01) on a local UZDoom build whose
network code matches @5a9b0ec511 apart from cast-only changes. A `StaticEventHandler` built a
`NetworkBuffer` byte by byte with `AddInt8`, sent it with `SendNetworkBuffer()`, and logged what
its `NetworkCommandProcess` override received (byte count and checksum).

| Payload | Result |
|---|---|
| 509 or 512 bytes (controls, not on a broken boundary) | Delivered intact |
| 510 bytes, all zero | Delivered intact |
| 510 bytes, all zero except a `1` at offset 100 or 253 | Delivered intact |
| 510 bytes, all zero except a `1` at offset 254 or 300 | Fatal error, see below |
| 510 bytes of `AddInt(i)` for i = 0..126, zero-padded | Delivered intact |
| 511 bytes, all zero except a `1` at offset 254 | Delivered intact |
| 511 bytes, all zero except a `1` at offset 255 | Fatal error, see below |

What this shows:

- **Only the last 256 bytes of the payload are at risk.** The parser resumes at payload offset
  `size - 256`, exactly as the source predicts, and the boundary is sharp (253 vs 254 for 510
  bytes, 254 vs 255 for 511).
- **A byte there equal to the user-command tag (`1`) is fatal.** The parser takes it as the start
  of the tic's movement data and cuts the command short. When the tic later runs, a read overruns
  the truncated data, and the engine aborts the game with the error "Attempted to
  read past end of stream". The level ends and the game drops to the full-screen console. The
  process does not crash, and `NetworkCommandProcess` never sees the command. A `2` (the
  empty-user-command tag) ends the parser's scan the same way in source, but only `1` was run.
- **Anything else can pass by luck.** Zero bytes are the "bad command" tag, which skips nothing,
  so a zero tail is walked byte by byte up to the real user command and the command arrives
  intact. The small-integer payload also survived: its nonzero tail bytes happened to be tags
  whose skip lengths hopped over the rest without landing on a `1` or `2`. Other tag values with
  larger skips could plausibly land elsewhere; that was not exhaustively tested.

The practical upshot: a mod sending a broken-size command can test clean on one set of data and
then end the game for its own player on another, offline, with no network involved. Avoid the
broken sizes entirely (pad or split the payload) rather than relying on what the data happens to
contain.

## See also

- [Event handlers: `StaticEventHandler` and `EventHandler`](../classes/eventhandler.md) — the
  `SendNetworkCommand`/`SendNetworkBuffer`/`NetworkCommandProcess` API surface this bug affects.
- [Multiplayer-safe ZScript](multiplayer-safe-zscript.md) — general network-event usage guidance;
  this file narrows one specific gap in it rather than covering new API surface.
