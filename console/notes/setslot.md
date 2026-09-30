# `setslot`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/a_weapons.cpp` (`CCMD(setslot)`,
`:542-596`) and `src/d_net.cpp` (`DEM_SETSLOT`), and the Zandronum source's
`src/g_shared/a_weapons.cpp` (`:1687-1736`), `src/d_net.cpp` and `src/g_game.cpp`. The online
no-op was also observed live on Zandronum. Zandronum's `docs/commands.txt` has no entry for it.

Replaces the contents of one weapon slot. Syntax: `setslot <slot> [<weapon class> ...]`, slot 0
to 9. Allowed in KEYCONF. How it combines with `Player.WeaponSlot`, `Weapon.SlotNumber` and the
ini is in [Weapon slots and KEYCONF](../../keyconf/concepts/weapon-slots.md).

## With no slot: print the layout

`setslot` with no argument, or with a slot of 10 or more, prints a usage line and the console
player's current slot layout as `Slot[N]=...` lines. In a game it also prints the config file
path and the section header to paste them under, `[<weaponsection>.<PlayerClass>.Weapons]`, or
`[<PlayerClass>.Weapons]` when no [`weaponsection`](weaponsection.md) is set. This is the only
help either engine gives for making a layout permanent: nothing writes that section for you.

## At the console

The slot is cleared, then each named weapon is appended in order; `setslot 5` alone empties slot 5
and prints `Slot 5 cleared`. The change goes out as a `DEM_SETSLOT` network command and edits the
player's live slots only. It is not saved to the ini, so it is lost at the next slot rebuild:
next level, respawn, morph end or savegame load. Unknown class names are skipped silently; a
non-weapon class prints `Can't add non-weapon <name> to weapon slots`.

A weapon is only de-duplicated within the target slot. Naming a weapon that sits in another slot
leaves it in both.

## In KEYCONF

Nothing happens when the lump runs. The line is queued and replayed on every slot rebuild, after
the player class and weapon defaults are applied and before the user's ini overrides. The replay
clears the slot first, so any weapon that was placed there by `Player.WeaponSlot` or
`Weapon.SlotNumber` and isn't listed again is removed from every slot. Class names are not checked
when the lump is parsed; a typo just drops that weapon at each replay.

## Gotchas

- The slot number goes through `atoi`: `setslot x Pistol` targets slot 0.
- Don't use a negative slot. It passes the range check, and neither engine's console path
  bounds-checks the add; Zandronum's KEYCONF replay doesn't either.

## Engine-family divergence

- **UZDoom's `setslotstrict` cvar** (archived, default `true`) controls only the KEYCONF replay.
  When it is false the slot is not cleared, so KEYCONF `setslot` appends to the existing slot and
  a bare `setslot <slot>` in KEYCONF does nothing. The console form always clears. Zandronum has
  no such cvar and always clears.
- **Zandronum online play:** a client typing `setslot` changes nothing. The `DEM_SETSLOT` command
  is written but Zandronum only executes queued `DEM_*` commands outside client and server mode
  (`g_game.cpp:1653-1669`). Observed live (2026-09-29, local test build, DOOM2 MAP01 listen server
  plus one joined client): the client's `setslot 5` still printed `Slot 5 cleared` but its layout
  kept `RocketLauncher` in slot 5, and `setslot 2 BFG9000` added nothing. The same `setslot 5` in
  single player emptied the slot. KEYCONF `setslot` still works there, because clients apply the
  KEYCONF and ini layout directly.
