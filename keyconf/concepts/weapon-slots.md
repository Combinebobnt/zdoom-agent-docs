# Weapon slots and KEYCONF

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/a_weapons.cpp`,
`src/gamedata/a_weapons.h`, `src/gamedata/keysections.cpp`, `src/d_main.cpp`, `src/d_net.cpp`,
`src/p_saveg.cpp` and `wadsrc/static/zscript/actors/player/player.zs`/`player_morph.zs`, and the
Zandronum source's `src/g_shared/a_weapons.cpp`, `src/p_user.cpp`, `src/g_level.cpp`,
`src/g_shared/a_morph.cpp`, `src/g_game.cpp`, `src/d_net.cpp`, `src/d_main.cpp` and
`src/keysections.cpp`. Zandronum's `docs/commands.txt` has no entry for any slot command.

A player's weapon slots (the ten lists that the number keys and `weapnext`/`weapprev` walk) are
not a static table. They are rebuilt from several sources every time a player pawn is set up, and
KEYCONF is only one layer of that rebuild. Three KEYCONF commands touch slots: `setslot`,
`addslotdefault` and `weaponsection`. The first two are **queued and replayed**, not applied
when the lump runs; `weaponsection` is **applied immediately** and only sets a name.

## Queue now, replay at every slot rebuild

While KEYCONF runs, `setslot` and `addslotdefault` do nothing to any slot. Each one pushes its
whole command line, command name included, onto a global list, `KeyConfWeapons` (UZDoom
`a_weapons.cpp:46`, `:564-567`, `:705-708`; Zandronum `a_weapons.cpp:42`, `:1709-1712`,
`:1838-1841`). The list spans every KEYCONF lump in load order, and is cleared once before the
first lump (UZDoom `keysections.cpp:155`, Zandronum `keysections.cpp:163`).

`P_PlaybackKeyConfWeapons` later re-executes every queued line through the console dispatcher
against one specific slot set (UZDoom `:729-737`, Zandronum `:1862-1871`). During that replay the
commands take a third branch that edits the slot set directly, instead of the console branch that
sends a network command.

So the same KEYCONF lines run again on every rebuild, and a later line overrides an earlier one
in the order the lumps loaded.

Actor classes are loaded before KEYCONF on both engines (`PClassActor::StaticInit`/
`FActorInfo::StaticInit` precede `D_LoadWadSettings` in `d_main.cpp`), so a mod's own weapon
names already resolve when the lump is parsed. Parse-time validation differs by command:

- `addslotdefault` checks its weapon at parse time and prints `<name> is not a weapon` and drops
  the line if the check fails. UZDoom only checks that the class exists; Zandronum also requires
  it to be a `Weapon`.
- `setslot` checks nothing at parse time. At replay, an unknown class name is skipped silently,
  and an existing non-weapon class prints `Can't add non-weapon <name> to weapon slots` on every
  rebuild (UZDoom `a_weapons.cpp:79-83`, Zandronum `:993-997`).

## When slots are rebuilt

`SetupWeaponSlots` runs for a player's real pawn (voodoo dolls are skipped):

- from the player pawn's `PostBeginPlay`, so on every new pawn: level start, respawn, and a
  player-class change (UZDoom `player.zs:224`, Zandronum `p_user.cpp:913`);
- when a morph ends, for the restored pawn (UZDoom `player_morph.zs:339`, Zandronum
  `a_morph.cpp:389`); a morphed pawn gets its own setup through its own `PostBeginPlay`;
- after loading a savegame, for every player (UZDoom `p_saveg.cpp:1043`, Zandronum
  `g_level.cpp:2351`). Slots are not stored in the save; they are rebuilt from whatever KEYCONF
  and ini are loaded now.

UZDoom also exposes it to ZScript as the static `WeaponSlots.SetupWeaponSlots(pawn)`.

`P_SetupWeapons_ntohton`, despite the name, is not slot setup. It builds the weapon-class to
network-index table used to transmit weapon types, once at startup.

## Order of application

A rebuild is two stages. `StandardSetup` builds the shared baseline; `LocalSetup` layers the
local machine's KEYCONF and ini on a copy (UZDoom `a_weapons.cpp:373-409`, Zandronum
`:1521-1557`):

1. **The player class's `Player.WeaponSlot`** lists. Every slot is cleared first, then each
   declared slot is filled in order (`SetFromPlayer`).
2. **`Weapon.SlotNumber`/`Weapon.SlotPriority`** for every weapon class not already in some
   slot. A weapon the player class already placed keeps that placement; `SlotNumber` cannot move
   it. Replaced weapons and powered-up (sister) weapons are skipped. Each slot is then sorted by
   priority (`AddExtraWeapons`).
3. **The game's MAPINFO `GameInfo` `weaponSlot` lists**, but only if all ten slots are still
   empty after steps 1 and 2 (`SetFromGameInfo`, a compatibility fallback).
4. **The queued KEYCONF commands**, replayed in order (`P_PlaybackKeyConfWeapons`).
5. **The user's ini**, `[<section>.Weapons]` (see `weaponsection` below). Each `Slot[N]=` key
   present there replaces that whole slot; slots the ini doesn't mention keep their KEYCONF
   result (`RestoreSlots`, UZDoom `:489-514`, Zandronum `:1637-1662`).

So, per slot: **ini beats KEYCONF, KEYCONF beats `Player.WeaponSlot`, and `Player.WeaponSlot`
beats `Weapon.SlotNumber`.** KEYCONF wins over the player class because it runs later, not
because of any priority flag.

The local result is then compared with the baseline and every differing slot is sent as a
`DEM_SETSLOT` network command (`SendDifferences`), which applies it to the player when that
command executes. UZDoom does the local stage for the console player, plus bots when this machine
is the net arbitrator. Bots get the KEYCONF replay but not the ini (`a_weapons.cpp:749-772`). For
Zandronum see the divergence section.

### What `setslot` and `addslotdefault` do at replay

- **`setslot <slot> <weapon> ...`** clears the slot, then appends each weapon in order
  (UZDoom's clearing depends on `setslotstrict`, below). A weapon is only de-duplicated within
  that one slot, so listing a weapon that steps 1 to 3 put in a different slot leaves it in both.
  Anything that was in the cleared slot and isn't listed again leaves every slot, so it can no
  longer be selected by number.
- **`addslotdefault <slot> <weapon>`** adds the weapon to the end of the slot only if it is not
  in any slot yet (`AddDefaultWeapon`). By the time KEYCONF replays, step 2 has already placed
  every weapon with a `SlotNumber`, so `addslotdefault` only affects weapons with neither a
  `SlotNumber` nor a `Player.WeaponSlot` entry. It cannot move a weapon.

Example: move the super shotgun out of slot 3 (where `DoomPlayer`'s `Player.WeaponSlot` puts it)
into slot 8.

```text
// KEYCONF
weaponsection MyModName
setslot 3 Shotgun
setslot 8 SuperShotgun
```

`addslotdefault 8 SuperShotgun` would do nothing here, since `SuperShotgun` is already in slot 3
by the time it replays.

Slot numbers go through `atoi`: a non-numeric first argument is slot 0, and a number of 10 or more
prints the usage text instead.

## `weaponsection`: which ini section overrides KEYCONF

`weaponsection <name>` sets one global string, immediately, even inside KEYCONF (UZDoom
`a_weapons.cpp:651-657`, Zandronum `:1784-1790`). It does not scope the slot commands after it:
the name is only read when `LocalSetup` looks for the user's ini overrides, so its position in
the lump doesn't matter. Only the last `weaponsection` executed counts, across all KEYCONF lumps.
With no argument it does nothing, and nothing ever clears it.

The ini lookup, per rebuild, using the pawn's class name:

- With a section name set: `[<name>.<PlayerClass>.Weapons]` first; if that section is absent
  or has no `Slot[N]` keys, `[<name>.Weapons]`.
- With none set: `[<PlayerClass>.Weapons]`.

The name is a free string the mod chooses, not something matched against the IWAD or game. Its
purpose is isolation. Weapon sections in the ini aren't prefixed by game, so without
`weaponsection` a user's `[DoomPlayer.Weapons]` layout for plain Doom would override a mod's
KEYCONF slots whenever the mod keeps the `DoomPlayer` class. A mod that sets its own name makes
its players start from its KEYCONF layout until they add a matching section.

```text
[MyModName.Weapons]
Slot[3]=Shotgun
Slot[8]=SuperShotgun
```

Neither engine ever writes these sections. `setslot` with no arguments prints the current layout
and the exact section header to paste into the config file by hand (see
[`setslot`](../../console/notes/setslot.md)). An empty `Slot[N]=` value empties that slot. The ini
is read from the config already loaded in memory, so edits need a restart.

## `addslot` is not reachable from KEYCONF

`addslot` has a `ParsingKeyConf` queue branch in both engines' handler (UZDoom `:629-632`,
Zandronum `:1762-1765`), but it is not on the nine-command allowlist, which is checked first. In
KEYCONF it is rejected with `Invalid command for KEYCONF` and never queued (see
[the lump concept](keyconf-lump.md)). At the console it appends a weapon to a slot without
checking other slots.

## Console use is temporary

Typed at the console (outside KEYCONF and outside a replay), `setslot`, `addslotdefault` and
`addslot` send a `DEM_SETSLOT`/`DEM_ADDSLOTDEFAULT`/`DEM_ADDSLOT` network command that edits the
player's current slots (UZDoom `d_net.cpp:3057-3091`, Zandronum `d_net.cpp:2527-2567`). Nothing is
queued and nothing is written to the ini, so the change is lost at the next rebuild: next level,
respawn, morph end or savegame load. For a lasting change, use the ini section above.

## Engine-family divergence

- **`setslotstrict` (UZDoom only).** An archived cvar, default `true`, declared in
  `a_weapons.cpp:523`. It only affects the KEYCONF replay branch of `setslot`: when true the slot
  is cleared before the weapons are appended (the Zandronum behavior); when false nothing is
  cleared, so KEYCONF `setslot` only appends to what steps 1 to 3 produced, and a bare
  `setslot <slot>` does nothing (`:568-580`). When false, the same cvar also makes KEYCONF
  `clearplayerclasses` remove only the stock IWAD classes instead of all of them (`keysections.cpp:239-261`; see
  [player classes](player-classes.md)). Because it is a user setting, a mod cannot rely on either
  value. Console `setslot` always clears. Zandronum has no such cvar and always clears at replay
  (`a_weapons.cpp:1713-1720`).
- **Zandronum multiplayer: slots are local, never sent by the server.** On a client,
  `SetupWeaponSlots` runs the local stage for every player, not just the console player, and
  assigns the result directly instead of sending `DEM_SETSLOT` (`p_user.cpp:939-969`). So each
  client computes every player's slots from its own KEYCONF and ini. The server has no slot
  replication command, and weapon selection reaches it as a weapon class
  (`CLIENTCOMMANDS_WeaponSelect`), so it doesn't need the client's layout. KEYCONF is also not
  checksummed at connect (see [the lump concept](keyconf-lump.md)), so clients can differ. UZDoom
  is peer-to-peer: each player's own machine computes its slots and broadcasts the differences as
  `DEM_SETSLOT`/`DEM_SETSLOTPNUM`.
- **Zandronum online: console slot commands do nothing (source-traced, not observed).** Queued
  `DEM_*` commands are executed by `RunNetSpecs`, which Zandronum only calls when neither in
  client mode nor running as a server (`g_game.cpp:1653-1669`). A client typing `setslot`,
  `addslotdefault` or `addslot` in an online game therefore changes nothing; KEYCONF and the ini
  still work, because the client applies them directly at rebuild.
- **Negative slot numbers.** `setslot`'s range check only rejects numbers of 10 or more.
  UZDoom's replay goes through bounds-checked helpers (`a_weapons.h:110-124`), so a negative slot
  in KEYCONF is ignored there. Zandronum's replay indexes the slot array directly
  (`a_weapons.cpp:1715-1718`), an unchecked index. The console path on both engines reads the slot
  back as an unsigned byte and only guards the clear, not the add. Never pass a negative slot.
- **Parse-time check of `addslotdefault`.** UZDoom accepts any existing class and silently
  ignores a non-weapon at replay; Zandronum rejects a non-weapon at parse time with
  `<name> is not a weapon`.
- **Zandronum's `GameInfo` fallback (step 3) is buggy.** Its inner loop advances the slot index
  instead of the weapon index (`a_weapons.cpp:1494`), so only the first weapon of each
  consecutive non-empty slot is added. It only matters when steps 1 and 2 left every slot empty.
- **Step 2 filtering.** Zandronum skips weapon classes whose game filter excludes the current
  game (`:1447-1452`); UZDoom asks each weapon's `CheckAddToSlots` virtual, whose default returns
  `SlotNumber` unless the class is replaced or powered-up, so a ZScript weapon can override it.

## See also

- [The KEYCONF lump](keyconf-lump.md): the allowlist and when KEYCONF runs.
- [Creating player classes](../../decorate/concepts/creating-player-classes.md):
  `Player.WeaponSlot`.
- [Creating weapons](../../decorate/concepts/creating-weapons.md): `Weapon.SlotNumber` and
  `SlotPriority`.
- [MAPINFO `GameInfo` block](../../mapinfo/concepts/gameinfo-block.md): the `weaponSlot` fallback.
- Per-command notes: [`setslot`](../../console/notes/setslot.md),
  [`addslotdefault`](../../console/notes/addslotdefault.md),
  [`weaponsection`](../../console/notes/weaponsection.md).
