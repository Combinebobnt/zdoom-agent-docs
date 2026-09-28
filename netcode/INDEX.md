# Netcode doc index

Router only. See `AGENTS.md` for scope, `../shared/AUTHORING.md` for tiers/engine-scope/licensing.

**Zandronum-only section** — UZDoom/GZDoom-family engines have no dedicated server, so none of
these protocols exists there.

**Looking for `sv_measureoutboundtraffic`, `dumptrafficmeasure` or `cleartrafficmeasure`?**
Outbound-traffic measurement lives in
[`console/concepts/outbound-traffic-measurement.md`](../console/concepts/outbound-traffic-measurement.md),
not here.

## Concepts

- [Wire basics](concepts/wire-basics.md) — tier B. What the three protocols share: UDP on the
  game socket, one command per non-client datagram, the fixed Huffman codec and its `0xFF` raw
  escape (no ZStd on these channels), little-endian field encoding, the port table, packet size
  limits, and the shared 10-second flood queue that silently drops every non-client packet from an
  ignored IP.
- [Launcher query protocol](concepts/launcher-protocol.md) — tier A. Request layout (199, flags,
  time, optional flags2, trailing segmented byte) and parsing traps; flag-correction rules;
  field-by-field reply incl. SQF2; 12-byte segment header (`sv_maxpacketsize - 12` chunks); ignore
  list (IGNORING) vs silent flood-queue drop, ignore-before-ban order; LAN broadcast to 15101.
- [Master-server protocol](concepts/master-server-protocol.md) — tier B. Heartbeat 5660020 every
  30 s, MD5-string verification handshake (206 / 5660029), 60 s drop, 10 servers per IP, ban-list
  push 207 (legacy 205) with receipt 5660030, launcher list request 5660028 v2 and legacy 199, MSC
  block layout; the master half describes the in-repo reference master, not necessarily
  `master.zandronum.com`.
- [RCON protocol](concepts/rcon-protocol.md) — tier A. Remote-admin UDP protocol: packet codes both
  ways, salted-MD5 login (lowercase hex, empty/1-4 char password disables it), login payload,
  updates, tab-complete, 10 s/40 s timeouts; the failed-login rate limit is dead code; stale-buffer
  `SVRC_BANNED`/`SVRC_OLDPROTOCOL` replies; the in-game `send_password` path sends the password in
  plaintext.
