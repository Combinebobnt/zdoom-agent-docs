# KEYCONF doc index

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse KEYCONF.** Per-command prose for the nine allowed commands lives in
`../console/notes/`, linked from the lump concept's allowlist table.

## Concepts

- [The KEYCONF lump](concepts/keyconf-lump.md) — tier A. Startup console script, every KEYCONF
  lump in load order; `//` comments only, `;` splits commands; the fixed nine-command allowlist
  and its "Invalid command for KEYCONF" rejection (`bind`, `addslot`, `set` included); Zandronum's
  4096-byte line buffer, no connect-time checksum, and UZDoom's `setslotstrict` cvar.
- [Weapon slots and KEYCONF](concepts/weapon-slots.md) — tier B. `setslot`/`addslotdefault` are
  queued and replayed at every slot rebuild (new pawn, unmorph, savegame load); `weaponsection`
  isn't queued and only sets the ini section prefix. Per-slot order: `Player.WeaponSlot`, then
  `Weapon.SlotNumber`, then the GameInfo fallback, then KEYCONF, then the ini
  `[<section>.Weapons]`; `addslot`'s unreachable KEYCONF branch; UZDoom's `setslotstrict`;
  Zandronum slots are client-local and console `setslot` does nothing online.
- [Player classes in KEYCONF](concepts/player-classes.md) — tier B.
  `clearplayerclasses`/`addplayerclass` edit the MAPINFO-seeded list at startup; "No player
  classes defined"; `nomenu` hides from the new-game menu only and KEYCONF ignores the actor's
  `+NOMENU`; UZDoom dedupes and gates clearing on `setslotstrict`; Zandronum sends the class as a
  list index, so client and server lists must match.
- [Unsafe aliases](concepts/unsafe-aliases.md) — tier B. A KEYCONF `alias` is an
  `FUnsafeConsoleAlias`, never written to the config; its body refuses `UNSAFE_CCMD`s, and
  non-CVARINFO cvar sets are refused (Zandronum) or applied but saved as the last safe value
  (UZDoom); `wait` keeps the restriction; the self-toggle idiom misfires and saves a normal alias;
  a same-named alias already in the config runs the mod's body unrestricted; `defaultbind`/`bind`
  command strings run unrestricted.
