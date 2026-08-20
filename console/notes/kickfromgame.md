# `kickfromgame` / `kickfromgame_idx`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/sv_main.cpp:8024-8034` (CCMD implementations).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

**Deprecated.** Both commands are thin wrappers around `forcespec` / `forcespec_idx` and should not be used in new code. Use `forcespec` or `forcespec_idx` instead.

## Behavior

- `kickfromgame <player_name>` — forces the named player to spectate. Equivalent to `forcespec <player_name>`.
- `kickfromgame_idx <player_index>` — forces the player at the given index to spectate. Equivalent to `forcespec_idx <player_index>`.

The player can rejoin the game at any time after being forced to spectate.

## Why deprecated

These commands are maintained for backwards compatibility only. They were superseded by the more clearly-named `forcespec` / `forcespec_idx` commands.

## Engine-family divergence

`kickfromgame`/`kickfromgame_idx` are confirmed absent from UZDoom's source entirely — no
`CCMD`/`CVAR` declaration and no bare mention of either name anywhere in the tree. This isn't a
documentation gap; these are Zandronum-only server-administration aliases with no UZDoom
equivalent. Invoking either under UZDoom — from the console, a config file, or ACS's
`ConsoleCommand()` — hits the console dispatcher's command lookup, then its cvar-name fallback,
and when neither matches prints `Unknown command "kickfromgame"` (or `"kickfromgame_idx"`) to
console/log and does nothing else: a visible failure at the console, but easy to miss if triggered
from an unattended context like a server startup script or `autoexec.cfg` line nobody is watching.

As a result, UZDoom has no way to force a player to spectate — by name or by player index — through
this deprecated alias pair; this doc makes no claim about whether the `forcespec`/`forcespec_idx`
commands these wrap have their own UZDoom equivalent, only that the aliases themselves do not.
