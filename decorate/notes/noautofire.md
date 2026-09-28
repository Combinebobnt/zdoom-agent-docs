# `NOAUTOFIRE` (weapon flag)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Source-derived (no wiki page consulted) — verified against the Zandronum source's
`src/p_pspr.cpp:931-961` (`P_CheckWeaponFire`, the sole consumer of `WIF_NOAUTOFIRE`),
`src/p_pspr.cpp:1466-1469` (`P_MovePsprites`, the ready-bit guard around its only call) and
`src/g_shared/a_pickups.h:360` (`WIF_NOAUTOFIRE` definition).
**Bucket:** `DEFINE_FLAG(WIF, NOAUTOFIRE, AWeapon, WeaponFlags)` in `src/thingdef/thingdef_data.cpp`.

Suppresses **continuous** firing while the fire button is held. A flagged weapon fires only when
the button is down on a ready tic and the player's `attackdown` latch is clear. After a shot, the
next one needs the button to be seen released on a ready tic first.

## Behavior notes

- `P_CheckWeaponFire` (`src/p_pspr.cpp:931-961`) is not run on every tic. Its only caller,
  `P_MovePsprites`, calls it only while the player's `WeaponState` has `WF_WEAPONREADY` or
  `WF_WEAPONREADYALT` set (`p_pspr.cpp:1466-1469`). Those bits are cleared every time the weapon
  psprite enters a new state (`P_SetPsprite`, `p_pspr.cpp:204-211`) and re-set only by
  `A_WeaponReady`, so the check runs only on ready tics.
- Its firing condition is `!player->attackdown || !(weapon->WeaponFlags & WIF_NOAUTOFIRE)`
  (`p_pspr.cpp:941`, and `:950` for alt-fire): fire happens if *either* the `attackdown`
  latch was false on entry, *or* the weapon lacks this flag. Every shot sets the latch to `true`.
- `attackdown` is a **per-player** field (`d_player.h:599`), not per-weapon. Inside the game
  simulation its only reset to `false` is the `else` branch at `p_pspr.cpp:959`. That branch is
  reached only on a ready tic where the button matching the set ready bit is not pressed. On tics
  where the weapon is not ready (firing, raise and lower animations) the function isn't called, so
  the latch keeps its value.
- Consequences for a flagged weapon:
  - Releasing and re-pressing the button entirely within a firing animation does not count as a
    new press. The release has to land on a ready tic.
  - Holding the fire button through a weapon switch carries the latch across. If the old weapon
    was firing, `attackdown` is still `true` when the new weapon's ready state first calls
    `A_WeaponReady`, so a `NOAUTOFIRE` weapon does not fire until the button is released and
    pressed again. A weapon without the flag fires straight away, as it would anyway.
  - A press that starts while the old weapon is lowering or the new one is raising, with the
    latch clear, fires on the new weapon's first ready tic. That is an ordinary first press, not
    autofire.
- `g_game.cpp:2235` sets `attackdown = true` on player reborn ("don't do anything immediately").
  Because the raise animation doesn't touch the latch, this survives until the starting weapon's
  first ready tic. So a `NOAUTOFIRE` starting weapon does not fire on spawn from a button already
  held, until it is released on a ready tic. A weapon without the flag ignores the latch and fires.

## UZDoom: clean agreement, straight ZScript port

UZDoom's `PlayerPawn.CheckWeaponFire` (`wadsrc/static/zscript/actors/player/player.zs:474-505`) is
a line-for-line ZScript port of Zandronum's `P_CheckWeaponFire`, down to the same comment block.
Every element of the mechanism above matches:

- The flag is exposed as `bNoAutofire`, declared as a ZScript `flagdef` named `NoAutoFire` against
  the `WeaponFlags` field (`wadsrc/static/zscript/actors/inventory/weapons.zs:95`) rather than a
  `DEFINE_FLAG` table entry — UZDoom's DECORATE-compat layer maps the legacy `+WEAPON.NOAUTOFIRE`
  token onto this `flagdef` by name, so the surface syntax a mapper writes is unchanged, only the
  declaration mechanism moved from a C++ macro table to a ZScript field flag. The underlying bit
  value (`WIF_NOAUTOFIRE`, `src/gamedata/a_weapons.h:166`) is unchanged from Zandronum.
- The fire condition is the same short-circuit test: fire is allowed if the `attackdown` latch was
  clear on entry, or the weapon lacks the no-autofire flag (`player.zs:485` and `:494`, primary and
  alt-fire respectively) — the same two-term `||` Zandronum uses.
- `attackdown` is the same kind of per-player, non-weapon-specific latch (native field,
  `src/playsim/d_player.h:366`), reset to `false` in the identical `else` branch
  (`player.zs:503`). As on Zandronum, `CheckWeaponFire`'s caller only runs it while
  `WF_WEAPONREADY` or `WF_WEAPONREADYALT` is set on `player.WeaponState`, so that branch is only
  reached on a ready tic with the matching button up.
- Those ready-state bits are cleared and re-granted the same way: UZDoom's `DPSprite::SetState`
  (`src/playsim/p_pspr.cpp:479-485`) clears the ready-flag mask whenever the weapon psprite enters
  a new state — the exact same point Zandronum's `P_SetPsprite` (`src/p_pspr.cpp:204-211`) clears
  it — and `A_WeaponReady`'s `DoReadyWeaponToFire`
  (`wadsrc/static/zscript/actors/inventory/weapons.zs:399-426`) re-sets them, mirroring Zandronum's
  `DoReadyWeaponToFire`. Since raise/lower/select/deselect states still don't call
  `A_WeaponReady`, the weapon-switch behavior described above (a fire button held through the
  switch keeps the latch set, so a `NOAUTOFIRE` weapon waits for a release) reproduces
  identically on UZDoom.
- The reborn-spawn initialization has the same shape and the same practical effect: UZDoom's
  `G_PlayerReborn` also initializes the `attackdown` latch to true on reborn, with an inline
  comment explaining the same intent as Zandronum's (`src/g_game.cpp:1468`), and it survives the
  starting weapon's raise animation the same way on both engines.

No behavioral divergence was found for this mechanism; the two implementations are functionally
identical, so no `## Engine-family divergence` section applies here.

## See also

- [Weapon states concept](../concepts/) — if a weapon-ready/select-state doc exists, cross-link
  once written; not yet present as of this note.
