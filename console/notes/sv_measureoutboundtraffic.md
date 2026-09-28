# `sv_measureoutboundtraffic`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `Measuring outbound traffic` (https://wiki.zandronum.com/w/index.php?title=Measuring_outbound_traffic&oldid=756, saved 2026-09-22) + verified against the Zandronum source's `src/network/nettraffic.cpp:71` (declaration), `:75-97` (recording gates) and `src/g_level.cpp:1138` (per-map reset); introduced in `cc60cf3b8`, an ancestor of the 3.2.1 commit.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

`Bool`, default `false`. When true on a server, the server records how many bytes it queues for
clients during each actor class's tick and each ACS script's run, for
[`dumptrafficmeasure`](dumptrafficmeasure.md) to print. See
[Outbound traffic measurement](../concepts/outbound-traffic-measurement.md) for what is counted
and its caveats.

- **Flags are `0`.** Not `CVAR_ARCHIVE`, so it isn't saved to the config and is `false` again after
  a restart; not `CVAR_SERVERINFO`, so clients never receive it. Set it in the server's launch line
  or startup config if you want recording from the first map.
- **Server only.** The recording functions check both the cvar and `NETSTATE_SERVER`
  (`nettraffic.cpp:80, 93`), so setting it on a client does nothing.
- **Takes effect immediately, but doesn't reset anything.** Turning it off stops adding to the
  totals without clearing them, and turning it back on adds to the old totals. Only
  [`cleartrafficmeasure`](cleartrafficmeasure.md) or a map load clears them.

## Engine-family divergence

UZDoom has no such cvar (confirmed absent from its source) and no per-actor or per-script traffic
accounting. Its `stat network` display (`src/d_net.cpp`) shows latency and tic/ack state but no
byte counts.
