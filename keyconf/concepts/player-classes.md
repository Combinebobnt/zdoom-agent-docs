# Player classes in KEYCONF

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/keysections.cpp:220-304`
(`ClearIWADPlayerClasses`, the `clearplayerclasses`/`addplayerclass` CCMDs),
`src/playsim/p_user.cpp:483-531` (`ValidatePlayerClass`, `SetupPlayerClasses`, `playerclasses`),
`src/d_main.cpp:3655-3665`, `src/gamedata/gi.cpp:370-371`, `src/gamedata/a_weapons.cpp:523`,
`src/d_netinfo.cpp`, `src/g_level.cpp` and `src/menu/doommenu.cpp`, and the Zandronum source's
`src/p_user.cpp:192-281`, `src/d_main.cpp:2995-3006`, `src/gi.cpp:330-331`, `src/d_netinfo.cpp`,
`src/g_level.cpp`, `src/p_mobj.cpp`, `src/menu/menu.cpp`, `src/menu/menudef.cpp`,
`src/menu/playermenu.cpp`, `src/team.cpp`,
`src/cl_commands.cpp`, `src/cl_main.cpp`, `src/sv_main.cpp` and `src/sv_commands.cpp`.

Two KEYCONF commands edit the engine's player-class list: `clearplayerclasses` empties it and
`addplayerclass <class> [nomenu]` appends to it. They are the older way to set up player classes;
the MAPINFO `GameInfo` key `PlayerClasses` is the current one (see
[Creating player classes](../../decorate/concepts/creating-player-classes.md)). Both routes write
the same list, and KEYCONF runs second, so a KEYCONF class setup edits whatever MAPINFO produced.
Per-command syntax and messages are in
[`clearplayerclasses`](../../console/notes/clearplayerclasses.md) and
[`addplayerclass`](../../console/notes/addplayerclass.md).

## Startup order

Both engines build the list in the same three steps inside `D_DoomMain` (UZDoom
`src/d_main.cpp:3655-3665`, Zandronum `src/d_main.cpp:2995-3006`):

1. **`SetupPlayerClasses` seeds the list from MAPINFO.** It clears the list, then walks
   `gameinfo.PlayerClasses` (the merged result of every MAPINFO `GameInfo` block) in order. Each
   name is validated (see below); a valid class is appended, and gets the hidden-from-menu flag if
   its actor has `+NOMENU`. An invalid name prints a message and is dropped. Duplicate names are
   not merged: a MAPINFO list naming a class twice yields two entries.
2. **Every KEYCONF lump runs**, in load order (see [the KEYCONF lump](keyconf-lump.md)). Its
   `clearplayerclasses`/`addplayerclass` lines edit the list built in step 1.
3. **Empty-list check.** If the list is now empty, startup aborts with the fatal error
   `No player classes defined`.

So the fatal error means "no valid class survived", not only "`clearplayerclasses` without
`addplayerclass`". A KEYCONF that clears the list and then adds only misspelled or non-player
classes hits it too, because every failed `addplayerclass` is skipped rather than kept. So does a
MAPINFO list whose every entry fails validation, with no KEYCONF at all.

The list is built once. Neither command does anything after startup: both check the
`ParsingKeyConf` flag and silently return when it is clear, so typing them at the console, running
them from an `alias`, or putting them in a `.cfg` changes nothing and prints nothing.

## MAPINFO and KEYCONF together

MAPINFO's `GameInfo` has two keys for the same list: `PlayerClasses = "A", "B"` replaces the list
so far, and `AddPlayerClasses = "C"` appends to it (UZDoom `src/gamedata/gi.cpp:370-371`,
Zandronum `src/gi.cpp:330-331`). The stock game definitions set `PlayerClasses` (`DoomPlayer`,
`HereticPlayer`, `StrifePlayer`, `ChexPlayer`, or Hexen's three classes), so a mod that sets
neither key inherits the IWAD's classes.

The usual KEYCONF pattern clears that inherited list and rebuilds it:

```text
clearplayerclasses
addplayerclass MyPlayer
addplayerclass MyScoutPlayer
addplayerclass MyDebugPlayer nomenu
```

Without the `clearplayerclasses` line, the added classes go after the IWAD's, and on Zandronum a
class the MAPINFO list already contains is added a second time (see "Engine-family divergence").
A mod that already sets MAPINFO `PlayerClasses` has no reason to also use KEYCONF, and mixing
the two is where the engines disagree most.

## Validation

`addplayerclass` and `SetupPlayerClasses` share one check, `ValidatePlayerClass` (UZDoom
`src/playsim/p_user.cpp:483`, Zandronum `src/p_user.cpp:192`). A class is rejected, with a
console message and no fatal error, when:

- no class of that name exists: `Unknown player class '<name>'`;
- the class exists but does not inherit from `PlayerPawn`: `Invalid player class '<name>'`;
- the class has no `Player.DisplayName`: `Missing displayname for player class '<name>'`.

The display name is required because class selection works by display name: the `playerclass`
cvar holds a display name, matched case-insensitively against each entry's `Player.DisplayName`
(`D_PlayerClassToInt`, in `src/d_netinfo.cpp` on both engines). When the list has exactly one
entry, that lookup returns entry 0 whatever the cvar says.

## The `nomenu` flag

An entry flagged `nomenu` is left out of the **new-game class menu**, the one shown after "New
Game" when more than one class exists (UZDoom `src/menu/doommenu.cpp`, Zandronum
`src/menu/menudef.cpp`). That is the only place the flag is read. A `nomenu` class:

- still appears in the Player Setup menu's Class list (UZDoom fills that menu's `PlayerClass`
  option values from every entry, `src/menu/doommenu.cpp:1107-1124`; Zandronum's
  `DPlayerMenu::GetAllowedPlayerClasses` in `src/menu/playermenu.cpp` filters by team restriction
  only);
- can be picked by random class selection, which draws from the whole list (UZDoom
  `src/g_level.cpp:534`, Zandronum `src/g_level.cpp:372` and, in a Zandronum deathmatch without
  teams, `src/p_mobj.cpp:5443`);
- can be chosen by setting `playerclass` to its display name.

**KEYCONF `addplayerclass` does not copy the actor's `+NOMENU` flag.** It starts each entry with
no flags and sets the hidden flag only from a literal `nomenu` argument. `SetupPlayerClasses`
does copy `+NOMENU` for MAPINFO-listed classes. A `+NOMENU` actor added through KEYCONF without
the argument therefore shows up in the new-game menu. Any argument after the class name other
than `nomenu` (case-insensitive) prints `Unknown flag '<arg>' for player class '<name>'`, and the
class is still added.

**One visible class is not the same as one class.** When at most one entry is visible, the
new-game class menu is skipped and the menu passes no class at all (UZDoom
`src/menu/doommenu.cpp:198-201`, Zandronum `src/menu/menu.cpp:379-381`), so the new game leaves
the `playerclass` cvar untouched (UZDoom `src/g_level.cpp:264`, Zandronum `src/g_level.cpp:176`)
and that cvar decides. Its default is `Fighter`, which matches no display name outside Hexen, and an
unmatched value means random. So a list of one visible class plus `nomenu` classes can start a new
game as a random pick from all of them, hidden ones included, unless the player's `playerclass`
already names a class. Test such a setup with a fresh config, where `playerclass` is still at its
default.

## Checking the result

`playerclasses` (no arguments) prints the final list as `<index>: Class = <actor class>, Name =
<display name>` on both engines (UZDoom `src/playsim/p_user.cpp:524`, Zandronum
`src/p_user.cpp:274`). It is an ordinary console command, not KEYCONF-restricted, and the index it
prints is the one Zandronum puts on the wire (below). It does not show the `nomenu` flag.

## Engine-family divergence

The seeding, validation, fatal check and `nomenu` handling match. The two KEYCONF commands and
the network encoding of the chosen class differ:

- **Duplicates.** UZDoom's `addplayerclass` returns without adding when that class is already in
  the list (`src/gamedata/keysections.cpp:277`). The check runs before the flag arguments are
  read, so re-adding an existing class with `nomenu` does not hide the existing entry. Zandronum's
  `addplayerclass` (`src/p_user.cpp:241`) has no such check: every call appends, so a class named
  in both MAPINFO and KEYCONF, or added twice, appears twice in both menus and gets two indexes.
- **`clearplayerclasses` and `setslotstrict` (UZDoom only).** UZDoom's `clearplayerclasses`
  (`src/gamedata/keysections.cpp:239`) empties the list only while the archived `setslotstrict`
  cvar is on, its default (`src/gamedata/a_weapons.cpp:523`). With it off, the command removes
  only the seven stock classes by name (`DoomPlayer`, `HereticPlayer`, `StrifePlayer`,
  `FighterPlayer`, `ClericPlayer`, `MagePlayer`, `ChexPlayer`) and keeps everything else,
  including custom classes a MAPINFO listed. The removal loop steps past the entry that slides
  into a removed slot, so if a stock class appears twice in a row, one copy survives. KEYCONF
  cannot `set` a cvar, so which behavior applies comes from the player's config, not the mod. A
  KEYCONF that clears and rebuilds the list gets the same final list either way as long as the
  inherited list held only stock classes. Zandronum's `clearplayerclasses` (`src/p_user.cpp:233`)
  always empties the list; it has no `setslotstrict`.
- **Class choice on the network.** UZDoom writes a player's class into userinfo as its display
  name (or `Random`) and each peer resolves the name against its own list (`src/d_netinfo.cpp`,
  the `NAME_PlayerClass` cases). Zandronum sends the list **index** in both directions: the
  client's userinfo carries the index (`src/cl_commands.cpp`, and nothing is sent when the list
  has one entry), the server stores it as a number (`src/sv_main.cpp:2366-2368`), and the spawn
  command sends the index of the class the server spawned (`src/sv_commands.cpp:297`), which the
  client clamps into its own list and uses to pick the actor class (`src/cl_main.cpp:3755-3756`).
  KEYCONF is not one of the lumps a Zandronum server checksums on connect (see
  [the KEYCONF lump](keyconf-lump.md)), so a client whose KEYCONF list differs in order or length
  from the server's is let in and then spawns other players, or itself, as the wrong class
  locally. Keep the class list identical on every client, or set it in MAPINFO, which Zandronum
  does authenticate.
- **Zandronum team restrictions.** In team games Zandronum filters the Player Setup menu's class
  list and random picks by each class's team restriction, and the server replaces a disallowed
  class choice with the first allowed index (`TEAM_EnsurePlayerHasValidClass`, `src/team.cpp`).
  This works on list indexes too, so it inherits the parity requirement above.
