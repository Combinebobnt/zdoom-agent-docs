# `A_CheckRailReload` (Skulltag railgun 4-shot reload check)

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-22)
**Provenance:** engine source only. Zandronum, read at upstream `master` @bdd0f7beb (line numbers are that commit's): `src/g_doom/a_doomweaps.cpp:922-937`, `src/g_shared/a_weapons.cpp:630-701` (`AWeapon::CheckAmmo`), `src/p_interaction.cpp:2279-2293` (`PLAYER_ResetSpecialCounters`), `src/gamemode.cpp:940-950`, `wadsrc/static/actors/shared/inventory.txt:53`, `wadsrc_st/static/actors/skulltagweapons.txt:59-102` (the stock `RailGun`). Present since the original Skulltag 0.97c2 import (bc562a817), an ancestor of the 3.2.1 commit 28f736fb3. UZDoom source @98b16b78fc has no declaration of this name.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_CheckRailReload)` in `src/g_doom/a_doomweaps.cpp`; declared `action native` on `Inventory` in `inventory.txt`, so it belongs in weapon or `CustomInventory` states.

Counts railgun shots and makes Skulltag's stock `RailGun` skip its reload animation on three
shots out of four. Hard-wired to that one class: on any other weapon it does nothing visible.

## Signature

```text
A_CheckRailReload()
```

## What it does

1. Returns if the caller has no player.
2. Increments the player's `RailgunShots` counter.
3. If the new count is not a multiple of 4 **and** the player's `ReadyWeapon` is exactly the
   class named `Railgun`, it sets the weapon sprite to the state 8 entries after that weapon's
   `Fire` label. In the stock `RailGun` that is the `RLGG A 6` frame just before `A_ReFire`, so
   the six reload frames (`G` through `L`) are skipped. The call replaces the current frame
   immediately, so the `F` frame's own 6 tics never elapse either.
4. On every 4th shot it falls through and the full reload sequence plays. The code calls
   `CheckAmmo` here with a comment about not reloading when out of ammo, but the call can't
   switch weapons and its result is discarded, so it has no effect. The reload plays even with
   no ammo left.

With the stock timings a normal shot takes 18 tics (`E 12`, `A 6`) and every 4th takes 60.

## Caveats

- **Exact class, by name.** The comparison is `GetClass() == Railgun`, not an inheritance check.
  A weapon inheriting from `RailGun` never gets the skip, so it always plays the full reload,
  while the counter still advances.
- **Fixed offset.** `Fire + 8` assumes the stock state layout. The stock `RailGun` lives in
  Skulltag's actor pack, which Zandronum doesn't autoload. A mod that defines its own class
  named `Railgun` with a different `Fire` sequence gets the same jump to whatever sits 8 states
  after its `Fire` label, possibly outside the intended sequence.
- **No null check on `ReadyWeapon`.** Both branches dereference it. Calling this from a player
  with no ready weapon (for example from a `CustomInventory` `Use` state while unarmed) crashes.
- **One counter per player, shared across weapons.** `RailgunShots` is not reset on weapon
  switch, so the 4-shot cycle continues where it left off. It is reset alongside the player's
  other streak counters (`PLAYER_ResetSpecialCounters`, called from several player-lifecycle
  points) and when kill counts are reset between rounds. It is saved in savegames
  (`src/p_user.cpp:4526`).
- **Not network-gated.** It runs wherever the weapon state runs, server and predicting client
  alike, and nothing sends the counter over the network.
- **Other weapons.** For anything but the class `Railgun`, the only effect is incrementing the
  shared counter. A custom weapon wanting "reload every N shots" should keep its own counter,
  for example an inventory item checked with `A_JumpIfInventory`.

## Zandronum-specific: absent on UZDoom

UZDoom has no `A_CheckRailReload` at all (it keeps `A_FireRailgun`, `A_FireRailgunLeft`,
`A_FireRailgunRight` and the `A_RailWait` stub, but not this). A state table calling it doesn't
resolve on UZDoom, and there is no per-player railgun shot counter to read.

## See also

- [A_FireRailgun](a_firerailgun.md), the attack the stock `RailGun` pairs this with.
- [Skulltag legacy classes](../concepts/skulltag-legacy-classes.md) for the actor pack the stock
  `RailGun` comes from.
