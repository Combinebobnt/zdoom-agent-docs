# `alias`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** Zandronum `docs/commands.txt` (`alias` entry), verified against both engines'
source (UZDoom `src/common/console/c_dispatch.cpp`, the `alias` CCMD, `FConsoleAlias` and
`SubstituteAliasParams`; Zandronum `src/c_dispatch.cpp`, same names), and observed live on both
engines.

Defines a new console command that runs a stored command string. One of the nine commands
allowed in KEYCONF, where it creates a restricted "unsafe" alias instead: see
[`keyconf/concepts/unsafe-aliases.md`](../../keyconf/concepts/unsafe-aliases.md).

## Syntax

```text
alias                          // list every alias
alias <name>                   // delete the alias <name>
alias <name> "<command>"       // create <name>, or replace its command
```

- The command string is one argument, so quote it when it contains spaces or `;`. Inside the
  quotes `;` separates several commands, since the body is run through `AddCommandString` like a
  typed console line. Nested quotes are escaped as `\"`.
- Only the first three words count. `alias a b c` defines `a` as `b`; the `c` is ignored.
- A name that is already a built-in command is refused with `<name> is a normal command`, both
  when creating and when deleting. An alias cannot shadow a CCMD.
- Deleting an alias that is currently running is deferred until its body finishes
  (`FConsoleAlias::SafeDelete`).
- An alias calling itself, directly or through another alias, is stopped with
  `Alias <name> tried to recurse.` A `wait`-delayed call is not recursion, since it runs after the
  body has returned, so `alias loop "echo tick; wait 35; loop"` repeats roughly every 35 tics.
- Names starting with `+`/`-` are ordinary aliases too. A key bound to `+name` sends `-name` on
  release, so an `alias +name`/`alias -name` pair gives a hold-to-activate command.
- `clearaliases` deletes every alias, KEYCONF ones included.

## Argument substitution

If the body contains a `%` anywhere, it is scanned for parameters each time the alias runs
(`SubstituteAliasParams`):

- `%1`, `%2`, ... (or `%{1}`, needed when a digit follows) is replaced by that argument of the
  alias call. `%0` is the alias name itself.
- A missing argument is replaced by nothing.
- `%%` produces a literal `%`.
- **No substitution inside a double-quoted string** in the body. See "Engine-family divergence"
  for UZDoom's `%"` escape.

```text
alias givex "give %1; echo gave %1"
givex shotgun
```

## Persistence

Each alias has two slots. Slot 0 is saved to the config's `[<game>.ConsoleAliases]` section at
exit; slot 1 is not saved, and slot 1 wins when both are set. A runtime `alias` normally writes
slot 0, so an alias defined at the console or in `autoexec.cfg` persists. `alias` listing output
colors them: slot 0 yellow, slot 1 orange.

## KEYCONF vs runtime

| | Runtime `alias` (console, config, bind, cfg file) | `alias` in KEYCONF |
|---|---|---|
| Object created | ordinary `FConsoleAlias` | `FUnsafeConsoleAlias` |
| Slot | 0 (saved to the config) | 1 (never saved; re-created from the lump each startup) |
| When it runs | normal context | unsafe context: `UNSAFE_CCMD`s (`exec`, `logfile`, `save`, ...) refused; non-CVARINFO cvar sets refused (Zandronum) or not saved (UZDoom) |
| Redefining an existing name | writes slot 0, unless slot 1 is already set, then slot 1 | writes slot 1; the existing object's class is unchanged |

Two consequences worth knowing, detailed in the concept page:

- A player redefining a KEYCONF alias at the console only changes slot 1: the new body still runs
  restricted and is lost at exit. Delete it first (`alias <name>`) to make a normal alias.
- If the player's config already has a saved alias of the same name, KEYCONF writes its body into
  that ordinary object's slot 1, and the mod's body then runs **unrestricted**. A KEYCONF alias
  that redefines itself (the toggle idiom) creates exactly such a saved alias as a side effect.

## ACS

Zandronum's ACS `ConsoleCommand` can neither run an alias nor use the `alias` command; UZDoom's
`ConsoleCommand` does nothing at all. See
[`acs/functions/consolecommand.md`](../../acs/functions/consolecommand.md).

## Engine-family divergence

The CCMD, both slots, recursion guard and KEYCONF handling are the same code on both engines.

- **Quoted substitution (UZDoom only).** UZDoom opens a substitution-enabled quoted string with
  `%"`: the `%` is dropped, the `"` kept, and `%N` inside is replaced up to the closing `"`. It
  also steps over an escaped `\"` outside quotes. Zandronum has no `%"` form: no substitution
  ever happens inside quotes there.
- **`wait 0`.** Zandronum accepts `wait 0` as a one-tic wait: its source comment
  (`c_dispatch.cpp:807-810`) says `wait`/`wait 1` always delayed two tics, kept for old aliases,
  and `wait 0` was added as the true one-tic form. UZDoom ignores a zero count and runs the rest
  of the line immediately. UZDoom's queue entry counts one tic fewer for the same `wait N`; its
  exact delay was not measured.
- **Listing.** Zandronum's `alias` listing prints a slot-0 line for every alias even when that
  slot is empty (the emptiness test in `FConsoleAlias::PrintAlias`, `c_dispatch.cpp:1341`, is
  always true), so each KEYCONF alias shows an extra blank yellow `name :` line. UZDoom prints only
  non-empty slots.
- **ACS.** Zandronum's `alias` CCMD returns immediately when called from ACS `ConsoleCommand`
  (`c_dispatch.cpp:1424-1425`), and the dispatcher refuses to run any alias from there
  (`c_dispatch.cpp:673-677`).
