# `kickfromgame` / `kickfromgame_idx`

**Tier:** B
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/sv_main.cpp:8024-8034` (CCMD implementations).

**Deprecated.** Both commands are thin wrappers around `forcespec` / `forcespec_idx` and should not be used in new code. Use `forcespec` or `forcespec_idx` instead.

## Behavior

- `kickfromgame <player_name>` — forces the named player to spectate. Equivalent to `forcespec <player_name>`.
- `kickfromgame_idx <player_index>` — forces the player at the given index to spectate. Equivalent to `forcespec_idx <player_index>`.

The player can rejoin the game at any time after being forced to spectate.

## Why deprecated

These commands are maintained for backwards compatibility only. They were superseded by the more clearly-named `forcespec` / `forcespec_idx` commands.
