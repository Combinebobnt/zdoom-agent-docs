# The `KEYCONF` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `KEYCONF` (https://zdoom.org/w/index.php?title=KEYCONF&oldid=52825, retrieved 2026-09-28) + verified against the UZDoom source's `src/gamedata/keysections.cpp` (`D_LoadWadSettings`), `src/common/console/c_dispatch.cpp` (`KeyConfCommands[]`, `AddCommandString`), `src/gamedata/a_weapons.cpp`, `src/d_main.cpp`; and the Zandronum source's `src/keysections.cpp`, `src/c_dispatch.cpp`, `src/g_shared/a_weapons.cpp`, `src/p_user.cpp`, `src/d_main.cpp`, and `src/network.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

KEYCONF is a plain-text console script. The engine runs it line by line at startup, the same way
it runs a typed console command, except that only nine commands are accepted. Everything a
KEYCONF can do is one of those nine commands; there is no block grammar.

## When it runs

- **Every lump named `KEYCONF` runs, in load order.** The reader loops over all of them, so a
  mod's KEYCONF adds to (and can override) the IWAD's and earlier mods' rather than replacing them.
- **Once, at startup**, from `D_DoomMain` in `d_main.cpp`: after the player-class list is seeded
  from game data, and before the engine checks that at least one player class exists. A KEYCONF
  that empties the list (`clearplayerclasses` with no successful `addplayerclass`) aborts startup
  with the fatal error "No player classes defined". On UZDoom with `setslotstrict` off,
  `clearplayerclasses` keeps custom MAPINFO classes, so the list may not end up empty.
- Before the first lump, the reader clears the key-section list (the Customize Controls menu
  additions) and the queued KEYCONF weapon-slot commands. It is not re-run on map change.

## Line format

- One command per line. Each line goes through the same `AddCommandString` the console uses, so
  `;` separates several commands on one line and double quotes group an argument containing
  spaces.
- **Comments are `//` only**, to end of line, and a `//` inside a double-quoted string is not a
  comment. There are no block comments: a `/*` line is read as a command and rejected.
- Blank lines are skipped.

## The nine-command allowlist

While the lump runs, a global `ParsingKeyConf` flag is set, and the dispatcher checks the first
word of each command against a fixed table before doing anything else. The table is identical on
both engines:

| Command | What it does in KEYCONF | Notes |
|---|---|---|
| `addkeysection` | starts a named section in the Customize Controls menu | [`console/notes/addkeysection.md`](../../console/notes/addkeysection.md) |
| `addmenukey` | adds a bindable command to the current key section | [`console/notes/addmenukey.md`](../../console/notes/addmenukey.md) |
| `defaultbind` | binds a key only if the key is free and the command isn't bound elsewhere | [`console/notes/defaultbind.md`](../../console/notes/defaultbind.md) |
| `alias` | defines an alias that normally runs in a restricted context | [`console/notes/alias.md`](../../console/notes/alias.md) |
| `weaponsection` | names the ini section the user's slot overrides are read from (last one wins) | [`console/notes/weaponsection.md`](../../console/notes/weaponsection.md) |
| `setslot` | replaces a weapon slot's contents | [`console/notes/setslot.md`](../../console/notes/setslot.md) |
| `addslotdefault` | adds a weapon to a slot if it isn't in any slot yet | [`console/notes/addslotdefault.md`](../../console/notes/addslotdefault.md) |
| `clearplayerclasses` | empties the player-class list | [`console/notes/clearplayerclasses.md`](../../console/notes/clearplayerclasses.md) |
| `addplayerclass` | appends a player class, optionally hidden from the menu (UZDoom skips duplicates) | [`console/notes/addplayerclass.md`](../../console/notes/addplayerclass.md) |

The match is case-insensitive and on the whole first word. Any other command prints
`Invalid command for KEYCONF: <the rest of the line>` to the console and is skipped. The lump
keeps running: one bad line does not stop the rest.

Several of these commands behave differently when `ParsingKeyConf` is set than when typed at the
console. `setslot`/`addslotdefault` are queued and replayed at every slot rebuild rather than applied at once, and the
player-class commands only do anything during KEYCONF. The cross-command details are in this
section's other concepts; per-command behavior is in each command's `console/notes/` page.

**Deprecation note.** The wiki marks `setslot`, `clearplayerclasses` and `addplayerclass` as
deprecated. Neither engine warns about or restricts them; the label means newer routes exist on
both engines: MAPINFO GameInfo `PlayerClasses`/`AddPlayerClasses` and `WeaponSlot` keys, and the
player class's own `Player.WeaponSlot` property. See [weapon slots](weapon-slots.md) and
[player classes](player-classes.md) for how KEYCONF interacts with those.

## Gotchas

- **`bind` is not allowed.** UDB's KEYCONF highlighting config lists `bind` as a keyword, but the
  engines reject it with the "Invalid command" message. Use `defaultbind`, which binds only when
  the key is unbound and the command isn't already bound to another key.
- **`addslot` is not allowed either**, even though its handler has a `ParsingKeyConf` branch in
  both engines' `a_weapons.cpp`. The allowlist check runs first, so that branch is unreachable from
  KEYCONF. Use `setslot` or `addslotdefault`.
- **`set`, `exec`, `wait` and other ordinary commands are rejected.** A mod cannot set cvars
  directly from KEYCONF. An `alias` it defines normally runs in a restricted "unsafe" context
  when triggered: Zandronum refuses any cvar set from it unless the cvar is mod-defined, and
  UZDoom applies the set but saves the last value set from a safe context (or empty if none).
  A `defaultbind` command string runs unrestricted. See [unsafe aliases](unsafe-aliases.md) for
  the exceptions.

## Engine-family divergence

The allowlist, the comment rule and the call site match. The line readers are separate
implementations:

- **Line endings.** UZDoom splits lines on `\n` or `\r`. Zandronum splits on `\n` and strips one
  trailing `\r`, so CRLF files work on both; a bare-`\r` (classic Mac) file is one long line on
  Zandronum.
- **Line length.** Zandronum copies each line into a fixed 4096-byte buffer with no length check,
  so keep every KEYCONF line well under 4 KB there. UZDoom's reader uses a growable buffer.
- **Network authentication (Zandronum).** KEYCONF is not in the list of lumps a Zandronum server
  checksums when a client connects (`network.cpp`, the `lumpsToAuthenticate` set). A client with a
  different KEYCONF can join; KEYCONF effects (binds, aliases, the controls menu, slot layout) are
  treated as client-local.
- **`setslotstrict` (UZDoom only).** UZDoom adds an archived `setslotstrict` cvar (default on)
  that changes how KEYCONF `setslot` and `clearplayerclasses` treat existing entries. Zandronum
  has no such cvar. The cvar has no row in `console/inventory/cvars.md`, whose cvar inventory is
  generated from the Zandronum source.
