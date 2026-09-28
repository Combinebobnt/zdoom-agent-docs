# `dumptrafficmeasure`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02) and Zandronum Wiki `Measuring outbound traffic` (https://wiki.zandronum.com/w/index.php?title=Measuring_outbound_traffic&oldid=756, saved 2026-09-22) + verified 2026-09-22 against the Zandronum source's `src/network/nettraffic.cpp:109-142` (the CCMD), `:75-97` (recording gates) and `src/g_level.cpp:1138` (per-map reset); `desc` sort introduced in `da434a2ba`, an ancestor of the 3.2.1 commit.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Prints the server's per-actor-class and per-ACS-script outbound traffic totals. Syntax:
`dumptrafficmeasure [desc]`. See
[Outbound traffic measurement](../concepts/outbound-traffic-measurement.md) for what the numbers
count and why they are not bandwidth figures.

## Behavior

- **Server only, silent elsewhere.** The command returns immediately unless the process is a
  server (`NETSTATE_SERVER`, `nettraffic.cpp:111-112`). A client running it gets no output at all,
  not even the headers. On a server the output goes through `Printf`, so an RCON client sees it
  too.
- **Needs [`sv_measureoutboundtraffic`](sv_measureoutboundtraffic.md) on first.** With the cvar off
  nothing new is recorded; if nothing was recorded this map, the dump prints just the two headers. Totals reset on every map load and
  on [`cleartrafficmeasure`](cleartrafficmeasure.md).
- **Sort order.** Each block is sorted by byte count, ascending by default so the largest entries
  land at the bottom, nearest the console input. `desc` as the first argument (case-insensitive)
  sorts descending; any other argument is ignored.

## Scope

It reports every byte the server queued for clients while a given actor class's `AActor::Tick` or
a given script's `DLevelScript::RunScript` was running, whatever the command was (spawns, state
and property updates, sounds, HUD messages, and so on). It is not limited to actor
spawn/update/removal or to ACS variable replication. Traffic the server sends outside those two
windows, including player weapon firing and the regular player position updates, doesn't appear
at all. The
concept page lists the paths that drop, inflate, or misattribute bytes.

## Engine-family divergence

UZDoom has no `dumptrafficmeasure` command (confirmed absent from its source); running it there
just prints an unknown-command message. There is no per-actor or per-script traffic accounting in
UZDoom at all. Its `stat network` display (`src/d_net.cpp`) shows latency and tic/ack state per
player but no byte counts.
