# dumptrafficmeasure

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); spot-checked against wiki claim.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Displays network traffic measurements for ACS scripts and actor class replication. Syntax: `dumptrafficmeasure [desc]`

## Prerequisites

The server-side cvar `sv_measureoutboundtraffic` must be set to `true` for data to be gathered and reported. By default this is `false` (disabled), so enable it before you want measurements.

## Output order

By default, output is sorted in ascending order (lowest bandwidth usage first). To invert the sort to descending order (highest bandwidth usage first), pass `desc` as the first argument: `dumptrafficmeasure desc`.

## Scope

This command reports on bandwidth consumed by:
- ACS script variables and state replication
- Actor spawn/update/removal traffic

It is primarily a server-side diagnostic; clients see partial output if they run the command locally.

## Engine-family divergence

`dumptrafficmeasure` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. UZDoom's networking model has no equivalent per-script/per-actor-class bandwidth accounting to dump.

Attempting to invoke it under UZDoom (via the console, a config file, or ACS's `ConsoleCommand()`) prints `Unknown command "dumptrafficmeasure"` to console/log and does nothing else — visible if someone's watching, easy to miss if triggered from an unattended server startup script. Since this is a command rather than a cvar being set, there's no "write" to fail; it simply prints nothing and reports no diagnostic data at all, leaving a UZDoom server admin with no way to break down outbound traffic by ACS script variable or actor-class replication cost.
