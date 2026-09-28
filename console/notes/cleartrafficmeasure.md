# `cleartrafficmeasure`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `Measuring outbound traffic` (https://wiki.zandronum.com/w/index.php?title=Measuring_outbound_traffic&oldid=756, saved 2026-09-22) + verified against the Zandronum source's `src/network/nettraffic.cpp:101-105, 146-149` and `src/g_level.cpp:1138`; introduced with the measurement code in `4c44fbe1f`, an ancestor of the 3.2.1 commit.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Empties both the per-actor-class and per-script totals that
[`dumptrafficmeasure`](dumptrafficmeasure.md) prints. Takes no arguments. See
[Outbound traffic measurement](../concepts/outbound-traffic-measurement.md) for the whole system.

- **Only resets; doesn't start or stop anything.** Recording is governed by
  [`sv_measureoutboundtraffic`](sv_measureoutboundtraffic.md) alone, so clearing with the cvar on
  just starts a fresh count from now.
- **Usually redundant at a map start.** The same reset runs automatically on every map load
  (`G_DoLoadLevel`, `g_level.cpp:1138`). Use the command to measure a window within one map, e.g.
  clear, trigger the suspect event, then dump.
- **No server check.** Unlike `dumptrafficmeasure`, it runs on a client too, where it's a harmless
  no-op since a client never records anything.

## Engine-family divergence

UZDoom has no such command (confirmed absent from its source) and no per-actor or per-script
traffic accounting to clear. Its `stat network` display (`src/d_net.cpp`) shows latency and
tic/ack state but no byte counts.
