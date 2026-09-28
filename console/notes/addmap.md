# `addmap` / `insertmap` (map rotation management)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/maprotation.cpp:588-751` (CCMD implementations), `src/maprotation.cpp:430-532` (argument parsing, limit defaults/clamping, insert position), `src/maprotation.cpp:111-123`, `176-188` and `230-343` (eligibility and fallback), `src/maprotation.cpp:606-683` (`maplist` display).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Add or insert a map into the server's map rotation list. Both support optional per-map player-count limits. The map name must resolve to a known level; otherwise the command prints `map <name> doesn't exist.` and adds nothing.

## `addmap` — append to rotation

`addmap <lumpname> [minplayers] [maxplayers]`

Appends a map to the end of the rotation list and prints the position it landed at.

## `insertmap` — insert at position

`insertmap <lumpname> <position> [minplayers] [maxplayers]`

Inserts a map so that it becomes entry number `<position>` in `maplist`'s 1-based numbering. Existing entries from that number on shift down by one. So `insertmap MAP05 2` puts MAP05 second, after entry 1. A position of `0` (or any non-numeric text, which parses as 0) appends to the end, exactly like `addmap`. A negative position, or one greater than the list length plus one, prints `Bad index specified!` and adds nothing. The command's own help text says "after <position>", but the code places the map at `<position>`, not after it.

Use the `maplist` command to display the current rotation with index numbers.

## Optional player limits

Both commands accept two optional parameters that restrict when a map is eligible for play:

- `minplayers`: the map is eligible only when the eligible-player count is at least this many
- `maxplayers`: the map is eligible only when the eligible-player count is at most this many

The eligible-player count is every in-game player who is not a true spectator, plus any spectator waiting in the join queue.

When omitted, `minplayers` defaults to `0` and `maxplayers` defaults to `MAXPLAYERS` (64), i.e. no limit. Passed values are clamped: `minplayers` to 0-64 and `maxplayers` to 1-64, so passing `0` for `maxplayers` means a maximum of 1 player, not "no limit". If `minplayers` ends up greater than `maxplayers`, the two are swapped.

The limits are stored and applied when picking the next map, but they are not absolute. If no entry's limits admit the current player count, the next map falls back to an entry with the lowest `minplayers` (too few players) or the highest `maxplayers` (too many players). A next map set by ACS `SetNextMapPosition` can also ignore its limits.

`maplist` shows the limits: any entry whose limits differ from the defaults gets a `(min = N, max = M)` suffix (only the non-default half is printed), and entries the current player count can't enter are drawn in a darker color.

## Related

- `addmapsilent` / `insertmapsilent`: same as `addmap`/`insertmap` but without the confirmation message
- `maplist`: display the current rotation list
- `delmap` / `delmap_idx`: remove a map from rotation
- `clearmaplist`: clear the entire rotation list
- `sv_maprotation`: cvar, enable/disable map rotation

## Engine-family divergence

`addmap`/`insertmap` are confirmed absent from UZDoom's source entirely. There is no `CCMD`/`CVAR`
declaration and no bare mention of either name anywhere in the tree. This isn't a documentation
gap; UZDoom's netcode has no dedicated-server map-rotation-list concept for these commands to
manage.

Typing either under UZDoom at the console or running it from a config file hits the console
dispatcher's command lookup, then its cvar-name fallback, and when neither matches prints
`Unknown command "addmap"` (or `"insertmap"`) and does nothing else. That is a visible failure at
the console, but easy to miss from an unattended context like an `autoexec.cfg` line nobody is
watching. ACS's `ConsoleCommand()` never reaches that dispatcher on UZDoom: the script opcode just
prints a message that the game doesn't support executing console commands from scripts, whatever
the command text is.

As a result, UZDoom has no console-driven way to append or insert a map into a rotation list, with
or without the per-map `minplayers`/`maxplayers` eligibility limits this file documents. The
entire mechanism simply does not run.
