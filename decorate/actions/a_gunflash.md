# `A_GunFlash(state flash = "", int flags = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_GunFlash` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_GunFlash&oldid=53828) + verified against
the Zandronum source's `src/p_pspr.cpp:1234–1276`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `AInventory` class (action function), defined at `src/p_pspr.cpp:1234`. Compiles for any `Inventory` subclass, including `Weapon`.

Creates a new weapon sprite layer in the flash slot and plays a state sequence on it. Usually called
during a weapon's `Fire` or `AltFire` state sequence to display a muzzle flash or other firing effect.

## Parameters

- **`flash`** — state label naming the flash sequence to play. If empty string (the default), the
  function looks the state up on the player's `ReadyWeapon`: `AltFlash` if the weapon's current
  attack was started through `AltFire`, falling back to `Flash` if that is missing or the attack
  came through `Fire`. If no such state exists, `flash` stays
  `NULL` and the layer is cleared without playing a new sequence.
- **`flags`** — control behavior. Only one flag is defined:
  - `GFF_NOEXTCHANGE` (value 1) — if set, prevents the player's body state from changing. If not
    set (the default), the player pawn calls `PlayAttacking2()`, which jumps to its `Melee` state
    if the class defines one (the stock Doom player's `Melee` is its bright firing frame, then
    `Goto Missile`).

## Behavior details

The flash sprite layer occupies the **fixed `ps_flash` slot** — one of five hardcoded weapon/player
sprite layers in Zandronum (`ps_weapon`, `ps_flash`, `ps_targetcenter`, `ps_targetleft`,
`ps_targetright`). **This is not the same as the arbitrary-layer system** described in the ZDoom
wiki's `A_Overlay`, which does not exist in Zandronum.

If the `GFF_NOEXTCHANGE` flag is not set, the function calls the player's `PlayAttacking2()`
method to transition the player to its `Melee` state — **but only if the player is alive**
(`player->mo->health > 0`). A dead player (e.g., killed by a reflection rune while firing) does not
receive the state change.

In multiplayer, the player state change is **server-authoritative**: the server sends a
`SERVERCOMMANDS_SetPlayerState` command (`STATE_PLAYER_ATTACK2`) to every client except the
firing player's own (`SVCF_SKIPTHISCLIENT`), and those clients call `PlayAttacking2()` when the
command arrives. Inside the action itself, `NETWORK_IsConsolePlayerOrNotInClientMode` limits the
direct call to the server, single player, and a client acting for its own console player.

## Engine-family divergence: no dead-player guard in UZDoom

UZDoom's `A_GunFlash` calls `player.mo.PlayAttacking2()` unconditionally whenever
`GFF_NOEXTCHANGE` is not set — there is no equivalent of Zandronum's `player->mo->health > 0`
check described above. A dead player (e.g. killed by a reflection rune while firing, the scenario
Zandronum's guard comment cites) still has `PlayAttacking2()` invoked on UZDoom, transitioning
the body to its melee/attack-secondary state even though it is already dead.

## Zandronum-specific: client/server behavior

UZDoom has no client/server authority split at all — its source tree contains no
`SERVERCOMMANDS_*` or `NETWORK_InClientMode`-style constructs anywhere, for this function or in
general. `A_GunFlash`'s player-state change and flash-sprite update both happen unconditionally
and locally; the server-authoritative `SERVERCOMMANDS_SetPlayerState` broadcast and the
console-player/client gating described above are entirely Zandronum-specific netcode with no
UZDoom counterpart.

## Engine-family divergence: NULL-handling

UZDoom's ZScript implementation returns early when the caller has no player or the player has no
`ReadyWeapon`. Zandronum returns early **only when there is no player**. When `ReadyWeapon` is
`NULL`, the function continues: the default-flash lookup is skipped, so the flash layer is set to
whatever explicit `flash` state was passed, or cleared when none was (`P_SetPsprite(player,
ps_flash, NULL)`), and, if `GFF_NOEXTCHANGE` is not set, the `PlayAttacking2()` call still
executes. This arises when the action runs while the player has no ready weapon, for example from a
`CustomInventory` item's state sequence. The source comment cites a crash log where
`client_GiveInventory` reached this function with `ReadyWeapon == NULL` while giving a
`CustomInventory` item.

Confirmed directly against UZDoom's `Weapon`-class `A_GunFlash`
(`wadsrc/static/zscript/actors/inventory/weapons.zs`): its first check is that early return, so
UZDoom does not carry Zandronum's `ReadyWeapon == NULL` continuation path or its associated
`P_SetPsprite`/`PlayAttacking2` side effects.

## Engine-family divergence: A_GunFlash is Weapon-only in UZDoom

In Zandronum, `A_GunFlash` is defined on the `AInventory` bucket (see "Bucket" above), so it runs
its real logic — including the `ReadyWeapon == NULL` continuation path described above — no matter
which `Inventory` subclass calls it. In UZDoom, the real implementation is defined only on the
`Weapon` class (`wadsrc/static/zscript/actors/inventory/weapons.zs`). `CustomInventory` (via its
`StateProvider` base) instead gets a separate, deprecated (since version 2.3) **empty-body stub**
version of `A_GunFlash` — calling it from a `CustomInventory` state sequence in UZDoom does
nothing at all (no flash-layer change, no player state change, just a compile-time deprecation
notice), rather than reaching either the real function's logic or its NULL-handling edge case.

## Example usage

```decorate
ACTOR Deagle : Weapon
{
  States
  {
  Ready:
    DEAG A 1 A_WeaponReady
    Loop
  Deselect:
    DEAG A 1 A_Lower
    Loop
  Select:
    DEAG A 1 A_Raise
    Loop
  Fire:
    DEAG C 3 A_GunFlash
    DEAG C 0 A_FireBullets(5, 7, 1, 50)
    Goto Ready
  Flash:
    DEFL A 1 Bright A_Light1
    DEFL A 2 Bright A_Light2
    Goto LightDone
  }
}
```

`A_GunFlash` is called bare: on Zandronum, `A_GunFlash()` with empty parentheses is a parse error
because the action has parameters.

Illuminating the flash with `A_Light1`/`A_Light2` is optional. On UZDoom, dynamic-light actions
such as `A_AttachLight` or `A_AttachLightDef` can be used instead; Zandronum has neither.
**Important**: if using `A_Light1`/`A_Light2`, the flash sequence **must** either call `A_Light0`
afterward or end with `Goto LightDone` (a built-in `Weapon` state that calls `A_Light0` and removes
the sprite layer). Otherwise the player's view of the whole map stays brightened until something
else resets the player's extra light (on Zandronum, for example, death or finishing the level).
The level does not keep climbing with each attack: `A_Light1`/`A_Light2` set a fixed value rather
than adding to it.

## See also

- `A_Light0`, `A_Light1`, `A_Light2` — lighting functions for flash sequences.
- `A_AttachLight`, `A_AttachLightDef` — alternative ways to add dynamic lights to firing weapons
  (UZDoom only).
- [Creating weapons](../concepts/creating-weapons.md) — weapon states, `Flash`/`AltFlash` reserved
  state names, and the two-layer `ps_weapon`/`ps_flash` sprite model.
