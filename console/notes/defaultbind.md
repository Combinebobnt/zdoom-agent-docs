# defaultbind

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/common/console/c_bind.cpp`,
`src/gameconfigfile.cpp`, `src/gamedata/keysections.cpp` and `src/d_main.cpp`, and the Zandronum
source's `src/c_bind.cpp`, `src/gameconfigfile.cpp`, `src/keysections.cpp` and `src/d_main.cpp`.
`zandronum/docs/commands.txt` has no entry for this command.

Syntax: `defaultbind <key> <command>`. Binds `<command>` to `<key>` only if the key has no bind
**and** the command is not bound to any key yet. It is one of the nine commands a
[KEYCONF](../../keyconf/concepts/keyconf-lump.md) lump may run, and the only way a mod can
suggest a key for its own commands without overwriting the player's setup.

```text
addkeysection "My Mod Controls" mymodkeys
addmenukey "Dash" +mymod_dash
addmenukey "Use Medkit" "use Medkit"
defaultbind q +mymod_dash
defaultbind h "use Medkit"
```

## Behavior

The logic is `FKeyBindings::DefaultBind` (UZDoom `c_bind.cpp:618-641`, Zandronum
`c_bind.cpp:663-686`), applied to the ordinary single-press bind list:

1. **Key name.** Resolved the same way as `bind`'s key argument: a key name such as `q`, `f5`,
   `mouse2` or `joy1`, matched case-insensitively, or `#<number>` for a raw key code. An unknown
   name prints `Unknown key "<name>"` and nothing is bound. The `#<number>` form is not range
   checked on either engine, so only use codes from the engine's own key table.
2. **Key already bound** to anything: nothing happens.
3. **Command already bound** to any key: nothing happens. The check is an exact comparison of
   the whole bind string, ignoring case, so `+attack` counts as bound only if some key's bind is
   exactly `+attack`. A key bound to `+attack; +use` does not count.
4. Otherwise the key is bound to the command.

- **Not KEYCONF-only.** Unlike [`addkeysection`](addkeysection.md) and
  [`addmenukey`](addmenukey.md), the command is not gated on `ParsingKeyConf` (UZDoom
  `c_bind.cpp:721-731`, Zandronum `c_bind.cpp:772-782`). It works the same when typed at the
  console.
- **Arguments.** Fewer than two prints `Usage: defaultbind <key> <command>`. Extra arguments are
  ignored silently, so an unquoted multi-word command keeps only its first word:
  `defaultbind h use Medkit` binds `h` to plain `use`. Quote the command.
- **Single-press only.** Neither the key test nor the command test looks at double-click or
  automap binds, and there is no KEYCONF way to set those.

## When KEYCONF runs relative to the user's binds

On both engines the saved binds are in place before any KEYCONF line runs:

1. The engine's built-in default binds are applied, then replaced by the config's
   `[<Game>.Bindings]`, `[<Game>.DoubleBindings]` and `[<Game>.AutomapBindings]` sections when
   they exist (UZDoom `DoKeySetup`, `gameconfigfile.cpp:803-864`, called at `d_main.cpp:3547`;
   Zandronum `DoGameSetup`, `gameconfigfile.cpp:362-440`, called at `d_main.cpp:2824`).
2. KEYCONF runs later (UZDoom `d_main.cpp:3659`, Zandronum `d_main.cpp:3000`). Each
   `addkeysection` line loads that section's saved binds when it executes.

So `defaultbind` never overrides a key the user bound, nor one of the engine's own defaults. On a
fresh config most obvious keys already carry engine defaults, so pick a key the engine leaves
free, or the default silently fails for every new player.

It can still undo one user choice: **clearing a command's keys does not stick.** An unbound key is
not written to the config, so if the player clears every key for a mod command and leaves the
suggested key free, the next start finds the key unbound and the command unbound, and binds it
again. Binding the suggested key to something else is the only way for a player to keep it off.

## Ordering inside the lump

Put `addkeysection` (and its `addmenukey` lines) before the `defaultbind` lines for its commands.
The section's saved binds only load when its `addkeysection` line runs. A `defaultbind` placed
earlier sees the command as unbound, binds the suggested key, and then the saved binds load on
top: a player who had moved the command to another key ends up with it on both keys.

## Pair it with addmenukey

Where the bind is saved depends on whether its command is listed in a key section:

- **Listed with `addmenukey`:** saved under the section's own ini name and only reloaded while
  the mod's KEYCONF runs. Removing the mod leaves the player's general binds untouched.
- **Not listed:** saved in the general `[<Game>.Bindings]` list like any other bind. It is
  loaded on every later start, with or without the mod, so the key stays bound to a command or
  alias that may no longer exist. Listing the command is also the only way the player can see
  and change the key in the Customize Controls menu.

## Engine-family divergence

The bind logic is identical; the difference is what it prints when it declines.

- **UZDoom** prints `Key already bound to "<command>"` when the key is taken, and
  `Command already bound to "<n>"` when the command is taken, where `<n>` is the numeric key code
  of the first key holding it, not its name (`c_bind.cpp:627-636`). Since a successful default is
  saved and reloaded before KEYCONF on every later start, each `defaultbind` line prints one of
  these on every start after the first. That is harmless console noise.
- **Zandronum** returns silently in both cases (`c_bind.cpp:671-681`). Only `Unknown key` is
  printed.
