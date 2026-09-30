# `addslotdefault`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/a_weapons.cpp`
(`CCMD(addslotdefault)` `:687-719`, `AddSlotDefault` `:664-685`, `AddDefaultWeapon` `:225-239`)
and `src/d_net.cpp` (`DEM_ADDSLOTDEFAULT`), and the Zandronum source's
`src/g_shared/a_weapons.cpp` (`:1797-1852`, `AddDefaultWeapon` `:1223`), `src/d_net.cpp` and
`src/g_game.cpp`. The online no-op was also observed live on Zandronum. Zandronum's
`docs/commands.txt` has no entry for it.

Adds a weapon to the end of a slot **only if that weapon is not in any slot yet**. Syntax:
`addslotdefault <slot> <weapon class>`, slot 0 to 9, exactly one weapon. Allowed in KEYCONF. How
it combines with `Player.WeaponSlot`, `Weapon.SlotNumber` and the ini is in
[Weapon slots and KEYCONF](../../keyconf/concepts/weapon-slots.md).

Wrong argument count or a slot of 10 or more prints
`Usage: addslotdefault <slot> <weapon>`. An unknown class prints `<name> is not a weapon`.

## It cannot move a weapon

If the weapon is already in some slot, the command silently does nothing. By the time a KEYCONF
`addslotdefault` replays, every weapon with a `Weapon.SlotNumber` and every weapon in the player
class's `Player.WeaponSlot` lists is already placed. So it only affects weapons that have neither.
To move a weapon, use [`setslot`](setslot.md) on both the old and new slot.

## At the console

Sent as a `DEM_ADDSLOTDEFAULT` network command that edits the player's live slots. Not saved to
the ini, so it is lost at the next slot rebuild (next level, respawn, morph end, savegame load).

## In KEYCONF

The class is checked when the lump is parsed. If it passes, the line is queued and replayed on
every slot rebuild, in order with the other queued `setslot`/`addslotdefault` lines; if it fails,
the error prints once at startup and the line is dropped.

## Engine-family divergence

- **Parse-time check.** Zandronum requires the class to exist and be a `Weapon`. UZDoom only
  requires it to exist; a non-weapon passes, gets queued, and is then silently ignored at each
  replay.
- **Zandronum online play:** a client typing `addslotdefault` changes nothing, because Zandronum
  never executes queued `DEM_*` commands in client or server mode (`g_game.cpp:1653-1669`).
  Observed live (2026-09-29, local test build, DOOM2 MAP01 listen server plus one joined client):
  the client's `addslotdefault 5 GoldWand` printed no error, and its layout still had only
  `RocketLauncher` in slot 5 after 75 tics. The same command in single player appended `GoldWand`
  to slot 5. The KEYCONF form still applies on clients.
