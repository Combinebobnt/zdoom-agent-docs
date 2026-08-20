# `addmap` / `insertmap` (map rotation management)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/maprotation.cpp:588-751` (CCMD implementations).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Add or insert a map into the server's map rotation list. Both support optional per-map player-count limits.

## `addmap` — append to rotation

`addmap <lumpname> [minplayers] [maxplayers]`

Appends a map to the end of the rotation list.

## `insertmap` — insert at position

`insertmap <lumpname> <position> [minplayers] [maxplayers]`

Inserts a map into the rotation list at the given position (0-indexed or after the nth entry, depending on implementation). Use the `maplist` command to display the current rotation with index numbers.

## Optional player limits

Both commands accept two optional parameters that restrict when a map is eligible for play:

- `minplayers` — the map is only considered for rotation when the server has at least this many active players
- `maxplayers` — the map is only considered for rotation when the server has at most this many active players

Both default to `0` (no limit) when omitted. The `maplist` command does not currently display these limits, but they are stored and enforced.

## Related

- `maplist` — display the current rotation list
- `delmap` / `delmap_idx` — remove a map from rotation
- `clearmaplist` — clear the entire rotation list
- `sv_maprotation` — cvar: enable/disable map rotation

## Engine-family divergence

`addmap`/`insertmap` are confirmed absent from UZDoom's source entirely — no `CCMD`/`CVAR`
declaration and no bare mention of either name anywhere in the tree. This isn't a documentation
gap; UZDoom's netcode has no dedicated-server map-rotation-list concept for these commands to
manage. Invoking either under UZDoom — from the console, a config file, or ACS's
`ConsoleCommand()` — hits the console dispatcher's command lookup, then its cvar-name fallback,
and when neither matches prints `Unknown command "addmap"` (or `"insertmap"`) to console/log and
does nothing else: a visible failure at the console, but easy to miss if triggered from an
unattended context like a server startup script or `autoexec.cfg` line nobody is watching.

As a result, UZDoom has no console-driven way to append or insert a map into a rotation list, with
or without the per-map `minplayers`/`maxplayers` eligibility limits this file documents — the
entire mechanism simply does not run.
