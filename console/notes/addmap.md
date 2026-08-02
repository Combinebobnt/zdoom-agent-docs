# `addmap` / `insertmap` (map rotation management)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/maprotation.cpp:588-751` (CCMD implementations).

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
