# `weaponsection`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/a_weapons.cpp`
(`CCMD(weaponsection)` `:651-657`, `LocalSetup` `:393-409`, `RestoreSlots` `:489-514`) and the
Zandronum source's `src/g_shared/a_weapons.cpp` (`:1784-1790`, `LocalSetup` `:1541-1557`,
`RestoreSlots` `:1637-1662`). Zandronum's `docs/commands.txt` has no entry for it.

Sets the name used to find the user's weapon-slot overrides in the config file. Syntax:
`weaponsection <name>`. Allowed in KEYCONF, where a mod uses it to keep its slot layout apart from
the user's settings for other mods and the plain game.

## What it does

It stores one global string, immediately. Unlike [`setslot`](setslot.md) and
[`addslotdefault`](addslotdefault.md), it is not queued in KEYCONF, and it does not attach to the
slot commands after it: its position in the lump doesn't matter, and the last `weaponsection`
executed wins across all KEYCONF lumps. With no argument it does nothing. Nothing clears it.

The name is read at every slot rebuild, when the engine looks for ini overrides for the pawn's
class:

1. `[<name>.<PlayerClass>.Weapons]`;
2. if that is absent or has no `Slot[N]` keys, `[<name>.Weapons]`.

With no name set, only `[<PlayerClass>.Weapons]` is tried. Each `Slot[N]=<weapons>` key found
replaces that slot, over whatever KEYCONF set.

The name is any string the mod picks; it is not matched against the IWAD or game. Without it, a
user's `[DoomPlayer.Weapons]` layout from plain Doom applies to every mod that keeps the
`DoomPlayer` class, overriding the mod's KEYCONF slots.

## At the console

Same effect, for the rest of the session: the new name is used from the next slot rebuild on. It
is not archived.

The full rebuild order is in [Weapon slots and KEYCONF](../../keyconf/concepts/weapon-slots.md).
