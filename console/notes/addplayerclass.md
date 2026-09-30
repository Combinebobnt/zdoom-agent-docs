# `addplayerclass`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/keysections.cpp:262-304` (the
`addplayerclass` CCMD) and `src/playsim/p_user.cpp:483-521` (`ValidatePlayerClass`,
`SetupPlayerClasses`), and the Zandronum source's `src/p_user.cpp:192-272`.

```text
addplayerclass <class> [nomenu]
```

Appends an actor class to the end of the player-class list. `<class>` is the actor class name
(case-insensitive), not its `Player.DisplayName`. The list order is the order of the new-game
class menu and the Player Setup menu's Class list.

**KEYCONF only.** The command does something only while a KEYCONF lump is being run at startup.
Anywhere else, or with no class argument, it returns without doing anything and prints nothing.

## Arguments after the class name

- `nomenu` (case-insensitive) hides the class from the new-game class menu only. It still appears
  in the Player Setup menu, can be picked by random class selection, and can be chosen by setting
  `playerclass` to its display name.
- Any other word prints `Unknown flag '<word>' for player class '<class>'`; the class is still
  added.
- The actor's own `+NOMENU` flag is **not** copied. Only the `nomenu` argument hides a class added
  this way, unlike a class listed in MAPINFO `GameInfo` `PlayerClasses`, where `+NOMENU` is
  honored.

## Rejected classes

The class is checked first, and a failing line prints one of these and adds nothing. Startup
continues:

- `Unknown player class '<class>'`: no class by that name.
- `Invalid player class '<class>'`: the class does not inherit from `PlayerPawn`.
- `Missing displayname for player class '<class>'`: the class has no `Player.DisplayName`.

If a `clearplayerclasses` earlier left the list empty and every `addplayerclass` after it is
rejected, startup aborts with `No player classes defined`.

## Engine-family divergence

- **UZDoom** skips the add when the class is already in the list, so repeating a class, or adding
  one MAPINFO already listed, is harmless. The duplicate check comes before the arguments are
  read, so `addplayerclass <class> nomenu` on a class already present does not hide it.
- **Zandronum** has no duplicate check: every call appends, so the class appears twice in both
  menus. Put `clearplayerclasses` first when rebuilding a list MAPINFO may already contain.

Zandronum also sends a player's class over the network as an index into this list, so the list
has to match between server and clients. See
[Player classes in KEYCONF](../../keyconf/concepts/player-classes.md) for that, the MAPINFO
interaction and the `nomenu` details, and [`clearplayerclasses`](clearplayerclasses.md) for
clearing the list first.
