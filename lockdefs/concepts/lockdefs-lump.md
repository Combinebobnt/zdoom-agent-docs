# The `LOCKDEFS` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `LOCKDEFS` (https://zdoom.org/w/index.php?title=LOCKDEFS&oldid=48713, retrieved 2026-09-28) + verified against the UZDoom source's `src/gamedata/a_keys.cpp`, `src/p_setup.cpp`, `src/d_main.cpp`, `src/playsim/p_lnspec.cpp`, `src/playsim/p_spec.cpp`, `src/playsim/mapthinkers/a_doors.cpp`, `src/am_map.cpp`, `src/scripting/vmthunks_actors.cpp`, `src/g_statusbar/sbarinfo_commands.cpp`, `wadsrc/static/lockdefs.txt`, `wadsrc_extra/static/filter/harmony/lockdefs.txt`, `wadsrc/static/xlat/defines.i` and `wadsrc/static/zscript/ui/statusbar/doom_sbar.zs`, and the Zandronum source's `src/g_shared/a_keys.cpp`, `src/g_shared/a_keys.h`, `src/p_setup.cpp`, `src/d_main.cpp`, `src/p_lnspec.cpp`, `src/p_spec.cpp`, `src/p_doors.cpp`, `src/am_map.cpp`, `src/m_cheat.cpp`, `src/p_user.cpp`, `src/g_shared/sbarinfo_commands.cpp`, `wadsrc/static/lockdefs.txt`, `wadsrc/static/sbarinfo/doom.txt` and `wadsrc/static/xlat/defines.i`; UDB `Build/Scripting/ZDoom_LOCKDEFS.cfg` checked for its keyword list.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

LOCKDEFS maps a lock number to the inventory items that open it. Map specials and UDMF lines carry
only the number; everything else (which keys, the "you need a key" text, the failure sound, the
automap color) comes from here.

## When it is read

- **Every lump named `LOCKDEFS` is parsed, in load order**, by `P_InitKeyMessages`. The lock table
  and key numbers persist across lumps, so a mod's lump adds to or overrides the stock one.
- **Once, at startup**, from `P_Init` (`src/p_setup.cpp`), which `D_DoomMain` calls after actor
  classes and SNDINFO are loaded. Class names and sound names therefore resolve at parse time on
  both engines. It is not re-read per map.
- The table is cleared once before the first lump. Zandronum clears it again at shutdown.

## Grammar

The lump uses the engine's standard script tokenizer: `//` and `/* */` comments, whitespace-
separated tokens, double quotes for strings with spaces. Keywords are case-insensitive. Two
top-level statements exist:

```text
ClearLocks

Lock 1
{
    RedCard                  // bare class name: required
    Any { MyKeyA MyKeyB }    // group: any one of these
    Message "$MY_NEEDRED"    // shown when the lock is tried from its own line
    RemoteMessage "You need the red key to activate this"
    Mapcolor 255 0 0
    LockedSound "*keytry", "misc/keytry"
}

Lock 2 Heretic { KeyBlue }
```

Anything else at top level is the fatal error `Unknown command <token> in LockDef`.

### `ClearLocks`

Deletes every lock defined so far and resets every key class's key number to 0 (see "Key numbers"
below). The stock lump starts with it. A mod that wants to replace the stock locks outright starts
its own lump with `ClearLocks`; a mod that only adds or overrides a few numbers should not.

### `Lock <number> [game]`

- `<number>` is an integer. Redefining a number that already exists **replaces that lock
  wholesale** (keys, messages, sound and color all reset to defaults first). There is no merge.
- `[game]` is optional. If present it is compared case-insensitively against the running game's
  name: `Doom`, `Heretic`, `Hexen`, `Strife` or `Chex`. Chex Quest does not match `Doom`. On a
  mismatch, and for any other word (a typo or an unknown game name), the block is still fully
  parsed but written into a throwaway lock, and the keys it names get no key numbers.
- `-1` is accepted and behaves the same as a game mismatch: parsed, then discarded. `0` and anything
  below `-1` are the fatal error `Lock index <n> out of range`. The upper bound differs by engine;
  see "Engine-family divergence".
- A discarded block is parsed with the same rules as a live one, so a bad name inside an `Any { }`
  in a `Heretic`-only block still aborts startup in Doom.

### Inside a lock block

The block body is a list of statements until `}`:

| Statement | Meaning |
|---|---|
| `<ClassName>` | A required item. The class must exist and descend from `Inventory` (not only `Key`). A non-inventory actor class is the fatal error `'<name>' is not an inventory item`. **A name that is not a class at all is silently skipped.** |
| `Any { <Class> <Class> ... }` | A group satisfied by holding any one of the listed items. Inside the braces an unknown name is the fatal error `Unknown item '<name>'`. An empty `Any { }` is dropped. |
| `Message "<text>"` | Printed (centered) when the lock is tried from the lock's own line or door. |
| `RemoteMessage "<text>"` | Printed when the lock guards something elsewhere (a tagged door, a remote switch). If only one of the two messages is given, the other copies it. |
| `Mapcolor <r> <g> <b>` | Three integers: the automap color of lines using this lock, and of key things that satisfy it. |
| `LockedSound "<sound>"[, "<sound>" ...]` | Replaces the failure-sound list. The first entry that resolves to a real sound is played. |

A message beginning with `$` is looked up in [LANGUAGE](../../language/concepts/language-lump.md) when printed. The default failure-sound
list, used when `LockedSound` is absent, is `*keytry` (the player-class sound) then `misc/keytry`.

The silent skip of unknown bare names is the main trap. The dispatcher treats any unrecognized
word as a class name, so:

- A misspelled key name disappears. If it was the only key, the lock ends up with **no required
  items, and an empty lock opens for any item descended from `Key`**.
- A misspelled keyword is also silent: `Mesage "text"` is two skipped words, not an error.
- `LockedSound "a" "b"` without the comma keeps only `"a"`; `"b"` is then read as a class name and
  skipped.

## How a lock is checked

`P_CheckKeys(actor, lock, remote)` runs whenever something lock-gated is activated:

| Source | Lock number from | `remote` (picks `RemoteMessage`) |
|---|---|---|
| UDMF line `locknumber` field, checked before any special on that line | the field | true unless the special is 7, 8 or 11-14 (`Polyobj_DoorSwing`/`Slide`, `Door_Open`/`Raise`/`LockedRaise`/`Animated`) |
| `Door_LockedRaise` (arg 3), `Generic_Door` (arg 4) | the arg | the door's tag arg is nonzero |
| `Door_Animated` (arg 3) | the arg | the tag arg is nonzero |
| `ACS_LockedExecute` / `ACS_LockedExecuteDoor` (arg 4) | the arg | true / false |

A lock number of 0 (or below) means "not locked" everywhere. The lock-taking specials are tier-C
rows in [`acs/INDEX.md`](../../acs/INDEX.md); the ACS side of the locked script specials is in
[`acs/functions/acs_execute.md`](../../acs/functions/acs_execute.md).

The check itself:

1. **Undefined lock number:** fails, prints `$TXT_DOES_NOT_WORK` (or `$TXT_RETAIL_ONLY` for lock
   103 in shareware Doom), and plays the default sound.
2. **Lock with no required items:** passes if the actor holds any `Key`-derived item.
3. **Otherwise every entry must pass.** A bare class name is a group of one; an `Any` group passes
   if one member does. Matching is by **exact class**: a subclass of `RedCard` does not satisfy
   `RedCard`. (UZDoom adds a `Species` route; see below and
   [`decorate/classes/key.md`](../../decorate/classes/key.md).) The amount held does not matter.
4. **On failure**, the message and sound fire only for the local viewer (see the divergence
   section), and the special does not run.

`Mapcolor` only shows when the automap color scheme displays lock colors: the cvar-driven custom
scheme, the overlay scheme, the Raven preset, or an AMCOLORS set with `showlocks true`. The Doom
and Strife presets draw every locked line in the plain locked color. When lock colors are shown,
a defined lock without `Mapcolor` has color 0 and draws black; only an undefined lock number falls
back to the scheme's locked color (`am_lockedcolor` in the custom scheme). Key things on the
automap take the color of the lowest-numbered lock they satisfy.

## Key numbers

Parsing also numbers the `Key`-derived classes: each one gets the next number the first time it is
named in a live (not discarded) lock, counting from 1 and continuing across lumps until a
`ClearLocks`. Non-key inventory items can open locks but never get a number. The number is not the
lock number. It decides:

- which keys the `give keys` cheat gives (only numbered ones),
- which keys a player spawns with in deathmatch (all numbered ones),
- SBARINFO `keyslot` conditions, which test key numbers, on both engines,
- key ordering on the alternative HUD, on both engines.

So a lump that starts with `ClearLocks` and never mentions a key leaves that key out of the cheat,
the deathmatch loadout and the status bar.

## What the stock lump defines

The stock numbers come from the line-translation enum in `xlat/defines.i`, which both engines'
Doom-format line types map onto: `RCard`=1, `BCard`=2, `YCard`=3, `RSkull`=4, `BSkull`=5,
`YSkull`=6, `AnyKey`=100, `AllKeys`=101, and a `CardIsSkull` flag of +128 for "card or skull
counts". Every stock lock except 100 and 228 is game-filtered.

| Game | Locks | Meaning |
|---|---|---|
| Doom | 1-6 | the single key in enum order (red card ... yellow skull) |
| Doom | 129-131 | any red/blue/yellow key: card, skull, or a Heretic key (green stands in for red) |
| Doom | 132-134 | red/blue/yellow card or skull |
| Doom | 229 | one key of each color |
| Doom | 101 | all six keys |
| (any) | 100, 228 | any key (no items listed) |
| Heretic | 1-3, 129-131 | green, blue, yellow key |
| Heretic | 101, 229 | all three |
| Hexen | 1-11 | one lock per key, steel through castle |
| Hexen | 101, 229 | all eleven |
| Strife | 1-27, 50, 51 | one lock per key item; 7, 8, 9 and 27 list no item, so any key opens them |
| Chex | 1-3, 129-131 (both); 4-6, 132-134, 229, 101 (UZDoom only) | Chex key cards, plus skulls on UZDoom |

UZDoom also ships a Harmony-only replacement lump that maps Doom locks 1-6, 100, 101, 129-134, 228
and 229 onto Harmony's key classes.

## Gotchas

- **A typo can unlock a door.** See the silent-skip rule above. After editing a lock, test that
  the door refuses the wrong key, not just that it accepts the right one.
- **Overriding one stock lock is safe without `ClearLocks`.** A later `Lock 1 Doom { ... }`
  replaces only lock 1. Starting with `ClearLocks` also discards every stock lock you didn't
  redefine and every key number.
- **A custom key needs a lock that names it.** Subclassing `RedCard` is not enough on either
  engine by class; add the class to the lock (usually inside an `Any` group) or, on UZDoom only,
  give it `Species RedCard`.
- **`Mapcolor` has no default.** Set it on every lock used on a map, or its lines draw black under
  any scheme that shows lock colors.

## Engine-family divergence

The keyword set, error messages, game filter, message copying and sound defaults match. Both
engines drop an empty `Any { }` group and both resolve sound names when the lump is parsed
(Zandronum's string-to-sound-ID conversion calls the same lookup), so neither is a difference.
Neither engine has a keyword the other lacks. The real differences:

- **Lock-number range.** Zandronum keeps locks in a fixed 256-slot array: `ParseLock` accepts
  1-254 and rejects 255 and above as "out of range" (`src/g_shared/a_keys.cpp:211-227`).
  `P_CheckKeys` returns "unlocked" for any number above 255 (`:405`), and 255 is always
  undefined. UZDoom keeps locks in a map keyed by number and accepts any positive number
  (`src/gamedata/a_keys.cpp:141`, `:254-260`); its `P_CheckKeys` has no upper bound (`:473`).
  So a UDMF `locknumber 300` or an ACS-issued `Door_LockedRaise` with lock 300 is open on
  Zandronum and locked (with `$TXT_DOES_NOT_WORK` unless defined) on UZDoom. Keep portable locks
  in 1-254.
- **Key matching.** UZDoom also accepts an item whose `Species` equals the required class name,
  and matches a Dehacked-replaced pickup against its original class. Zandronum matches exact
  class only. Details in [`decorate/classes/key.md`](../../decorate/classes/key.md).
- **Voodoo dolls.** UZDoom redirects a voodoo doll to its player's real body before checking, and
  prints the failure message for a voodoo doll of the local player unless the
  `compat_novdolllockmsg` compat flag is set. Zandronum checks the actor it was given and prints
  only when that actor is the console player's camera.
- **Netplay messages (Zandronum).** A Zandronum server also sends the failure message to the
  failing player's client (`src/g_shared/a_keys.cpp:450-460`), and its failure-sound call is flagged
  for relay to clients.
- **Quiet checks and scripting (UZDoom).** UZDoom's `P_CheckKeys` takes a `quiet` flag that
  suppresses message and sound, exposed to ZScript as `Actor.CheckKeys(locknum, remote, quiet)`,
  plus `Key.IsLockDefined(locknum)`, `Key.GetMapColorForLock` and `Key.GetMapColorForKey`.
  Zandronum has no script access to locks beyond the lock-taking specials.
- **`FS_Execute`.** Its lock arg is honored on UZDoom. Zandronum's `FS_Execute` is a no-op.
- **Doom status bar keys.** UZDoom's built-in Doom status bar (`doom_sbar.zs`) lights its key
  boxes by testing locks 1-6 quietly, so redefining lock 1 to accept a custom key lights the red
  box. Zandronum's Doom status bar is SBARINFO (`sbarinfo/doom.txt`) using `keyslot`, which tests
  key numbers 1-6, so the order keys are first named in LOCKDEFS decides the boxes.
- **Whether `Mapcolor` shows by default.** `am_colorset` defaults to 0 (the custom scheme, which
  shows lock colors) on Zandronum, but to -1 on UZDoom, which picks the game's preset. In Doom and
  Strife that preset hides lock colors, so an out-of-the-box UZDoom automap draws all locked lines
  in one color; Heretic and Hexen get the Raven preset, which shows them.
- **Key-number width.** Zandronum stores the key number in a byte (`src/g_shared/a_keys.h:12`), so
  numbering wraps after 255 distinct keys. UZDoom uses an `int` field.
- **Stock lump contents.** UZDoom's Chex set is larger (see the table). UZDoom's Chex lock 101
  names a `ChexBlueSkull` class that doesn't exist, which the silent-skip rule drops. Zandronum's
  Strife lock 1 message is a literal English string where UZDoom uses `$TXT_NEEDKEY`.
- **UDB.** UDB's keyword list omits `Chex` as a game name and shows `LockedSound` with one
  argument. Its `//$Title "<name>"` line inside a lock is an editor-only label; the engines see a
  comment.

## Wiki/engine divergence

Where the ZDoom Wiki page, which describes GZDoom-family behavior, differs from these checkouts:

- **Lock-number range.** The wiki states "The number can be any positive value", which is true on
  UZDoom but false on Zandronum, where `ParseLock` only accepts 1–254 (see "Lock-number range"
  above under "Engine-family divergence").
- **Action specials.** The wiki lists "The following five action specials use lock numbers: 13,
  14, 83, 85, 202" (Door_LockedRaise, Door_Animated, ACS_LockedExecute, ACS_LockedExecuteDoor,
  Generic_Door). This list is incomplete: it omits special 158 (`FS_Execute`), which honors its
  lock arg on UZDoom only, and both engines' UDMF `locknumber` field on a linedef, which can
  also be lock-gated (see "How a lock is checked" above).
- **Custom keys and ZScript.** The wiki states "If you want to use custom keys you have to add a
  DECORATE or ZScript lump as well". ZScript does not exist on Zandronum, so a key class for a
  Zandronum mod has to be DECORATE.
