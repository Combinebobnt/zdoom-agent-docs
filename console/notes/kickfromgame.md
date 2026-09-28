# `kickfromgame` / `kickfromgame_idx`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/sv_main.cpp:8024-8034` (CCMD implementations), `src/sv_main.cpp:7933-7960` and `7964-8019` (`forcespec_idx`/`forcespec` guards and reason argument), `src/sv_main.cpp:3942-3968` (`SERVER_ForceToSpectate`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

**Deprecated.** Both commands are thin wrappers around `forcespec` / `forcespec_idx` and should not be used in new code. Use `forcespec` or `forcespec_idx` instead.

## Behavior

- `kickfromgame <player_name> [reason]`: forces the named player to spectate. Equivalent to `forcespec <player_name> [reason]`.
- `kickfromgame_idx <player_index> [reason]`: forces the player at the given index to spectate. Equivalent to `forcespec_idx <player_index> [reason]`.

Each CCMD just calls the matching `forcespec` handler with the same arguments, so it inherits that handler's rules. It does nothing unless run on a server, and it silently does nothing when invoked through ACS `ConsoleCommand()`. The optional reason is one argument, so quote it if it has spaces. It is shown in the "has been forced to spectate" message broadcast to everyone. Nothing marks the player as barred afterwards: they can rejoin under the normal join rules.

## Why deprecated

These commands are maintained for backwards compatibility only. They were superseded by the more clearly-named `forcespec` / `forcespec_idx` commands.

## Engine-family divergence

`kickfromgame`/`kickfromgame_idx` are confirmed absent from UZDoom's source entirely — no
`CCMD`/`CVAR` declaration; the only mention is a commented-out `KickFromGame(2)` entry in the Zandronum ACS-function list inside `src/playsim/p_acs.cpp` (line 4831 at `5a9b0ec511`). This isn't a
documentation gap; these are Zandronum-only server-administration aliases with no UZDoom
equivalent. Invoking either under UZDoom from the console or a config file hits the console
dispatcher's command lookup, then its cvar-name fallback, and when neither matches prints
`Unknown command "kickfromgame"` (or `"kickfromgame_idx"`) to console/log and does nothing else: a
visible failure at the console, but easy to miss if triggered from an unattended context like a
server startup script or `autoexec.cfg` line nobody is watching. Calling either through ACS's
`ConsoleCommand()` never gets that far: UZDoom's `ConsoleCommand` p-codes only print a "doesn't
support execution of console commands from scripts" error and discard their arguments, so nothing
reaches the dispatcher.

As a result, UZDoom has no way to force a player to spectate — by name or by player index — through
this deprecated alias pair; this doc makes no claim about whether the `forcespec`/`forcespec_idx`
commands these wrap have their own UZDoom equivalent, only that the aliases themselves do not.
