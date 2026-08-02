# `A_CheckReload`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_CheckReload` (retrieved 2026-08-01, oldid=47254) + verified against the Zandronum source's `src/p_pspr.cpp:1104-1112` and `src/g_shared/a_weapons.cpp:630-699`. Neither file is touched by the applied ZandronumMCP patch.
**Bucket:** `DEFINE_ACTION_FUNCTION(AInventory, A_CheckReload)` in `src/p_pspr.cpp:1104`.

Checks whether the player's currently-ready weapon has enough ammunition remaining for another attack, and switches to the next available weapon if it does not.

## Parameters

This action function takes no parameters.

## Behavior

When called, `A_CheckReload` determines the active fire mode of the ready weapon (`bAltFire` flag), then calls the weapon's internal `CheckAmmo()` method with the appropriate fire-mode argument and `autoSwitch=true`. This forces an ammo check with automatic weapon switching enabled.

The weapon remains equipped and unchanged if:

- Infinite ammo is active (either via `DF_INFINITE_AMMO` dmflag or the player's `CF_INFINITEAMMO` cheat flag).
- The weapon has the `+WEAPON.AMMO_OPTIONAL` flag set on the active fire mode (primary or alternate), overriding the ammo requirement.
- The weapon has sufficient ammunition: for primary fire, `Ammo1->Amount >= AmmoUse1`; for alternate fire, `Ammo2->Amount >= AmmoUse2` (or both, if the weapon uses both ammo types for one fire mode via `WIF_PRIMARY_USES_BOTH` or `WIF_ALTWEAPON_USES_BOTH`).

If ammo is insufficient and none of the above exceptions apply, `CheckAmmo()` calls `PickNewWeapon(NULL)`, which cycles to the next weapon in selection-order priority (`Weapon.SelectionOrder` property, lower values first).

### Fire-mode selection

The check automatically adapts to the active fire mode: in an `AltFire` or `AltHold` state, it checks alternate-fire ammo (`AmmoType2`/`AmmoUse2`); in a `Fire` or `Hold` state, it checks primary ammo (`AmmoType1`/`AmmoUse1`). This is determined by the ready weapon's `bAltFire` flag at the moment `A_CheckReload` executes.

### Client-mode behavior

In multiplayer with non-`+CLIENTSIDEONLY` actors, the check executes on both server and client, but `CheckAmmo()`'s weapon-switch logic has a network-aware branch: if the calling weapon is not the local player's, the check returns `false` without triggering a switch, and the server replicates the authoritative change to all clients.

### No return value or state jump

`A_CheckReload` produces no return value and does not cause a state transition. The only observable effect is the potential weapon switch via `PickNewWeapon(NULL)`. Unlike conditional jump actions (`A_JumpIf*`), this function does not branch based on ammo state — the weapon switch happens as a side effect of the ammo check, not in response to an action parameter.

## Open questions

**Unguarded `ReadyWeapon` dereference in non-weapon contexts:** `A_CheckReload` is defined on the `AInventory` class, which means it compiles in any inventory item's state table, including a `CustomInventory`, not just a `Weapon`. The implementation unconditionally dereferences `self->player->ReadyWeapon` without checking for NULL. The surrounding context (weapon sprites/layers) suggests this action is intended for weapons only, but reachability from a non-weapon inventory item while `ReadyWeapon` is NULL (e.g., during a weapon switch window, or in a player class with no starting weapon) is not fully traced. A crash-causing path via a `CustomInventory` state calling `A_CheckReload` is plausible but unverified.

## See also

- [`A_ReFire`](a_refire.md) — the related follow-up check after a firing action, which also checks ammo but with different state-flow semantics.
- [Creating weapons](../concepts/creating-weapons.md) — weapon-state structure and the typical placement of `A_CheckReload` in a fire sequence (e.g., after a reload animation but before looping with `A_ReFire`).
