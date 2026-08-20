# `A_CheckReload`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_CheckReload` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CheckReload&oldid=47254) + verified against the Zandronum source's `src/p_pspr.cpp:1104-1112` and `src/g_shared/a_weapons.cpp:630-699`. Neither file is touched by the applied ZandronumMCP patch.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AInventory, A_CheckReload)` in `src/p_pspr.cpp:1104`.

Checks whether the player's currently-ready weapon has enough ammunition remaining for another attack, and switches to the next available weapon if it does not.

## Engine-family divergence: declared on `Weapon`, not `AInventory`

Zandronum declares `A_CheckReload` once, on the shared `AInventory` class, so it compiles (and can be called) from any inventory item's state table — this is the source of the "Open questions" concern below about an unguarded `ReadyWeapon` dereference from a non-weapon context. UZDoom splits this into two separate declarations instead: the real implementation (`wadsrc/static/zscript/actors/inventory/weapons.zs:477`) is declared directly on the `Weapon` class and guards its body with `if (player != NULL)` before touching `player.ReadyWeapon`; `CustomInventory` (`wadsrc/static/zscript/actors/inventory/stateprovider.zs:487`) separately declares its own `A_CheckReload` as an empty, `deprecated("2.3", "must be called from Weapon")` no-op. Calling `A_CheckReload` from a `CustomInventory` item's state table on UZDoom therefore does nothing (with a compile-time deprecation warning) rather than reaching the `AInventory`-level body — the specific crash path the Zandronum-side "Open questions" note flags as unverified does not exist on UZDoom, because there is no shared body left for a non-weapon caller to reach.

## Engine-family divergence: no client/server authority split

The "Client-mode behavior" section below is Zandronum-specific. UZDoom's `Weapon::CheckAmmo` (`wadsrc/static/zscript/actors/inventory/weapons.zs:974-1042`, called by `A_CheckReload`) contains no network-role branch at all — no check for whether the calling weapon belongs to the local player, and no server/client split in the `PickNewWeapon` call. This matches the cohort-wide pattern: UZDoom's source tree has no `NETWORK_InClientMode`/`SERVERCOMMANDS_*` occurrences anywhere, confirmed by grep for this file. On UZDoom, `A_CheckReload` simply runs the ammo check and switches weapons unconditionally wherever it executes.

## Engine-family divergence: infinite-ammo cheat flag removed

Zandronum's ammo-sufficiency exception includes the player's `CF_INFINITEAMMO` cheat flag. On UZDoom, `CF_INFINITEAMMO` is a vestigial constant defined as `0` in `wadsrc/static/zscript/constants.zs:1227`, under a block explicitly commented "These flags no longer exist, but keep the names for some stray mod that might have used them" — it is not read anywhere in `Weapon::CheckAmmo` or elsewhere in the source tree. UZDoom's equivalent "unlimited ammo" exception instead checks the `sv_infiniteammo` flag-cvar (a view onto the same `DF_INFINITE_AMMO` dmflag Zandronum checks directly, so that half of the exception is unchanged) or whether the player owns a `PowerInfiniteAmmo` powerup item (`FindInventory('PowerInfiniteAmmo', true)`) — an inventory-based mechanism with no Zandronum equivalent in this code path.

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
