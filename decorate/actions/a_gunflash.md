# `A_GunFlash(state flash = "", int flags = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_GunFlash` (retrieved 2026-08-01, oldid=53828) + verified against
the Zandronum source's `src/p_pspr.cpp:1234–1267`.
**Bucket:** `AInventory` class (action function), defined at `src/p_pspr.cpp:1234`. Compiles for any `Inventory` subclass, including `Weapon`.

Creates a new weapon sprite layer in the flash slot and plays a state sequence on it. Usually called
during a weapon's `Fire` or `AltFire` state sequence to display a muzzle flash or other firing effect.

## Parameters

- **`flash`** — state label naming the flash sequence to play. If empty string (the default), the
  function automatically selects `AltFlash` (if called in `AltFire`) or `Flash` (if called in `Fire`
  or any other state). If no such state exists, `flash` stays `NULL` and the layer is cleared
  without playing a new sequence.
- **`flags`** — control behavior. Only one flag is defined:
  - `GFF_NOEXTCHANGE` (value 1) — if set, prevents the player's body state from changing to
    `Missile` (attack animation). If not set (the default), the player transitions to `Missile`
    (representing the player firing their weapon).

## Behavior details

The flash sprite layer occupies the **fixed `ps_flash` slot** — one of five hardcoded weapon/player
sprite layers in Zandronum (`ps_weapon`, `ps_flash`, `ps_targetcenter`, `ps_targetleft`,
`ps_targetright`). **This is not the same as the arbitrary-layer system** described in the ZDoom
wiki's `A_Overlay`, which does not exist in Zandronum.

If the `GFF_NOEXTCHANGE` flag is not set, the function calls the player's `PlayAttacking2()`
method to transition the player to `Missile` state — **but only if the player is alive**
(`player->mo->health > 0`). A dead player (e.g., killed by a reflection rune while firing) does not
receive the state change.

In multiplayer, the player state change is **server-authoritative**: the server sends a
`SERVERCOMMANDS_SetPlayerState` command to clients for the state transition, and clients do not
run `PlayAttacking2()` locally for other players. Only the console player (or when the player is
in single-player mode) executes `PlayAttacking2()` on the client side.

## NULL-handling divergence from ZScript

Unlike the ZScript reference implementation (which returns early if `player == null || player.ReadyWeapon == null`),
Zandronum returns early **only if `player == NULL`**. When `ReadyWeapon == NULL`, the function
continues: the flash layer is cleared (via `P_SetPsprite(player, ps_flash, NULL)`) and — if
`GFF_NOEXTCHANGE` is not set — the `PlayAttacking2()` call still executes. This can occur when
`A_GunFlash()` is called from a `CustomInventory` item's state sequence instead of a weapon.
The function includes a comment referencing a crash log from `client_GiveInventory` calling
this function in such a scenario.

## Example usage

```decorate
Fire:
    DEAG C 3 A_GunFlash();
    DEAG C 0 A_FireBullets(5, 7, 1, 50);
    Goto Ready;

Flash:
    DEFL A 1 Bright A_Light1;
    DEFL A 2 Bright A_Light2;
    Goto LightDone;
```

Illuminating the flash with `A_Light1`/`A_Light2` is optional — modern approaches like
`A_AttachLight` or `A_AttachLightDef` (for dynamic lights) can be used instead. **Important**: if
using `A_Light1`/`A_Light2`, the flash sequence **must** either call `A_Light0` afterward or end
with `Goto LightDone` (a built-in `Weapon` state that calls `A_Light0` and removes the sprite
layer). Failure to do so will leave the entire map permanently brightened and will brighten further
with each weapon attack.

## See also

- `A_Light0`, `A_Light1`, `A_Light2` — lighting functions for flash sequences.
- `A_AttachLight`, `A_AttachLightDef` — alternative ways to add dynamic lights to firing weapons.
- [Creating weapons](../concepts/creating-weapons.md) — weapon states, `Flash`/`AltFlash` reserved
  state names, and the two-layer `ps_weapon`/`ps_flash` sprite model.
