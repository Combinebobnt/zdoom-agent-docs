# dumptrafficmeasure

**Tier:** B
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); spot-checked against wiki claim.

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
