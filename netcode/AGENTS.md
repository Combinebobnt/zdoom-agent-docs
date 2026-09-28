# netcode/ — Zandronum's out-of-band UDP protocols

The UDP protocols a Zandronum server speaks to external tools rather than to game clients: the
launcher query protocol (server browsers such as Doomseeker), the master-server protocol
(registration, verification, ban-list push, server-list requests), and the RCON protocol (remote
administration). **Read `../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

**This section is Zandronum-only.** UZDoom/GZDoom-family engines run a peer-to-peer lockstep
netgame with a `-host`/`-join` lobby: no dedicated server, no launcher query reply, no master
registration, no RCON. Every file here carries `Applies to: UZDoom=no, Zandronum=yes` and an
`## Engine-family divergence` heading; don't add a UZDoom-side claim without re-verifying that one
exists at all.

**Out of scope:** the client/server game protocol itself, and hosting how-tos (server setup, port
forwarding, moderation, troubleshooting, specific launchers). **Measuring outbound traffic is not
here either:** `sv_measureoutboundtraffic`/`dumptrafficmeasure`/`cleartrafficmeasure` are console
cvar/CCMD semantics and live in [`console/`](../console/INDEX.md)
(`console/concepts/outbound-traffic-measurement.md`).

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand — see the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md` — this section's router.
- `concepts/<protocol>.md` — one file per protocol, plus `concepts/wire-basics.md` for the facts
  all three share (transport, Huffman encoding, byte order, ports, packet size cap, the shared
  flood queue). Archetype 3. Query flags, packet codes and field layouts are inline tables inside
  each concept page, not archetype 2: they are small, closed, and meaningful only in protocol
  order, so no `inventory/`/`notes/` directories are registered.

## Where each protocol is implemented

Zandronum only. Paths are relative to the Zandronum checkout.

| Protocol | Server side | Other side |
|---|---|---|
| Launcher query | `src/sv_master.cpp` (`SERVER_MASTER_SendServerInfo`), dispatch in `src/sv_main.cpp`; `SQF_*`/`SQF2_*` flags in `src/sv_main.h` | any launcher; `docs/zandronum-launcher-protocol.txt` is a first-party but stale description |
| Master server | `src/sv_master.cpp` (heartbeat, verification), `src/sv_ban.cpp` (ban-list receipt) | `masterserver/main.cpp`, the in-repo reference master |
| RCON | `src/sv_rcon.cpp`, `src/sv_rcon.h` | `rcon_utility/main.cpp` (reference client); the in-game `rcon` CCMD path is separate, in `src/cl_main.cpp`/`src/sv_main.cpp` |
| Shared wire layer | `src/network.cpp`, `src/networkshared.cpp`, `src/networkshared.h`, `src/huffman/` | |

`masterserver/` and `rcon_utility/` carry the same Skulltag BSD-style header as `src/`, so they
fall under the same `**Source excerpt:**` rule (`../shared/AUTHORING.md`). Prefer prose tables to
verbatim excerpts anyway.
