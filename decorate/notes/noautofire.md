# `NOAUTOFIRE` (weapon flag)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Source-derived (no wiki page consulted) — verified against the Zandronum source's
`src/p_pspr.cpp:931-961` (`P_CheckWeaponFire`, the sole consumer of `WIF_NOAUTOFIRE`) and
`src/g_shared/a_weapons.h`/`a_pickups.h:360` (`WIF_NOAUTOFIRE` definition).
**Bucket:** `DEFINE_FLAG(WIF, NOAUTOFIRE, AWeapon, WeaponFlags)` in `src/thingdef/thingdef_data.cpp`.

Suppresses **continuous** firing while the fire button is held through consecutive tics in which
the weapon is already ready — it does not suppress a single shot the instant the weapon
transitions into its ready state, if the fire button happens to already be down at that moment.

## Behavior notes

- `P_CheckWeaponFire` (`src/p_pspr.cpp:931-961`) runs every tic a weapon exists. Its firing
  condition is `!player->attackdown || !(weapon->WeaponFlags & WIF_NOAUTOFIRE)`: fire happens if
  *either* the player's per-tic `attackdown` latch was false on entry, *or* the weapon lacks this
  flag. So for a flagged weapon, the button must go from not-considered-down to down across one
  tic boundary to produce a shot; while already-down state alone does not.
- Critically, `attackdown` is a **per-player** field (`d_player.h:599`), not per-weapon, and it is
  forced back to `false` on every tic the weapon is *not* in its ready state (the `else` branch at
  `p_pspr.cpp:959`, reached whenever neither the primary nor alt-fire "weapon ready" bit is set —
  e.g. every tic of a weapon-raise/lower animation, since `A_WeaponReady` is what sets those bits
  and raise/lower states don't call it).
- Net effect: if a player holds the fire button down continuously while switching from one weapon
  to another, the raise animation's tics reset `attackdown` to `false`, so the instant the new
  weapon's ready state calls `A_WeaponReady` (setting the ready bit) with the button still held,
  `P_CheckWeaponFire` sees `!attackdown == true` and fires immediately — **regardless of whether
  the new weapon has `NOAUTOFIRE` set**. The flag only prevents a *second* shot on the next tic
  while the button stays down; it does not, and cannot by this logic, prevent the first one.
- A mod that wants to prevent "fires on switch if the button was already held" needs to gate on
  something else (e.g. its own edge-detection via `keysPressed()`/`keysHeld()` in ACS, or an
  explicit inventory/state check in the weapon's own ready state), since the engine's own
  `attackdown` latch does not survive a weapon switch.
- `g_game.cpp:2235` sets `attackdown = true` on player reborn ("don't do anything immediately"),
  which looks like it should suppress an immediate shot on spawn — but this initialization is
  itself undone by the very first tic of the starting weapon's raise animation (same `else`
  branch), unless that weapon's raise is a single zero-tic transition straight into its ready
  state. In practice, almost any DECORATE `Select:` block with a nonzero-duration frame defeats
  this safeguard.

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
  (`player.zs:503`) whenever neither `WF_WEAPONREADY` nor `WF_WEAPONREADYALT` is set on
  `player.WeaponState`.
- Those ready-state bits are cleared and re-granted the same way: UZDoom's `DPSprite::SetState`
  (`src/playsim/p_pspr.cpp:479-485`) clears the ready-flag mask whenever the weapon psprite enters
  a new state — the exact same point Zandronum's `P_SetPsprite` (`src/p_pspr.cpp:204-211`) clears
  it — and `A_WeaponReady`'s `DoReadyWeaponToFire`
  (`wadsrc/static/zscript/actors/inventory/weapons.zs:399-426`) re-sets them, mirroring Zandronum's
  `DoReadyWeaponToFire`. Since raise/lower/select/deselect states still don't call
  `A_WeaponReady`, the weapon-switch edge case described above (an already-held fire button firing
  immediately on the new weapon's first ready tic, regardless of `NOAUTOFIRE`) reproduces
  identically on UZDoom.
- The reborn-spawn initialization has the same shape and the same practical defeat: UZDoom's
  `G_PlayerReborn` also initializes the `attackdown` latch to true on reborn, with an inline
  comment explaining the same intent as Zandronum's (`src/g_game.cpp:1468`), and it is undone the
  same way by the starting weapon's raise animation on both engines.

No behavioral divergence was found for this mechanism; the two implementations are functionally
identical, so no `## Engine-family divergence` section applies here.

## See also

- [Weapon states concept](../concepts/) — if a weapon-ready/select-state doc exists, cross-link
  once written; not yet present as of this note.
