# `clearplayerclasses`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/keysections.cpp:220-258`
(`ClearIWADPlayerClasses`, the `clearplayerclasses` CCMD), `src/gamedata/a_weapons.cpp:523` and
`src/d_main.cpp:3655-3665`, and the Zandronum source's `src/p_user.cpp:233-239` and
`src/d_main.cpp:2995-3006`.

```text
clearplayerclasses
```

Empties the player-class list so a following `addplayerclass` can rebuild it from scratch. Takes no
arguments; extra words on the line are ignored.

**KEYCONF only.** The command does something only while a KEYCONF lump is being run at startup.
Anywhere else (typed at the console, in a `.cfg`, inside an `alias`) it returns without doing
anything and prints nothing. The list it clears is the one `SetupPlayerClasses` just built from
MAPINFO's `GameInfo` `PlayerClasses`, plus anything an earlier KEYCONF line or lump added.

**Always follow it with at least one valid `addplayerclass`.** Right after KEYCONF finishes, both
engines abort startup with the fatal error `No player classes defined` if the list is empty. An
`addplayerclass` whose class name is misspelled, not a `PlayerPawn` or missing a
`Player.DisplayName` adds nothing, so it does not save you from that error.

## Engine-family divergence

- **Zandronum** always empties the list.
- **UZDoom** empties it only while the archived `setslotstrict` cvar is on (the default). With it
  off, only the seven stock classes (`DoomPlayer`, `HereticPlayer`, `StrifePlayer`,
  `FighterPlayer`, `ClericPlayer`, `MagePlayer`, `ChexPlayer`) are removed and any other class
  already in the list stays. The value comes from the player's config: KEYCONF cannot `set` it.
  The same cvar also changes KEYCONF `setslot`; see [`setslot`](setslot.md).

Full interaction with MAPINFO, `nomenu` and multiplayer class selection:
[Player classes in KEYCONF](../../keyconf/concepts/player-classes.md). The KEYCONF allowlist
itself: [the KEYCONF lump](../../keyconf/concepts/keyconf-lump.md).
