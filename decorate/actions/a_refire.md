# `void A_ReFire(statelabel flash = null)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_ReFire` (retrieved 2026-07-31, oldid=54720) + verified against the Zandronum source's `src/p_pspr.cpp:1046-1082` and `src/g_shared/a_weapons.cpp:864-886`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AInventory, A_ReFire)` at `src/p_pspr.cpp:1046`. Defined on the `AInventory` class; only available in weapon/inventory states, not on arbitrary actors.

Checks whether the fire key is still held after an attack. If held, automatically jumps to a follow-up state (usually `Hold` for sustained fire or repeated attacks). If released, resets the refire counter and performs an ammo check that may switch the player to a different weapon if the current one is out of ammunition.

**Engine-family divergence: Zandronum's implementation differs from the ZDoom-wiki ZScript version.** The wiki describes an `autoSwitch` parameter (added to ZDoom in 4.14.2) that does not exist in Zandronum. In Zandronum, the ammo-check behavior is unconditional — when the fire button is released, ammunition checking and potential weapon-switching always occurs, with no way to suppress it from DECORATE.

## Signature

```decorate
void A_ReFire(statelabel flash = null)
```

## Parameters

**`flash`** (state label, optional)  
The state label to jump to when the fire button is held. The parameter name is a legacy misnomer (it has no connection to muzzle flashes or overlays); it is simply the state to enter for sustained fire.

When `null` or omitted, the function automatically selects a state using the engine's built-in fallback logic:
- **For primary fire:** Tries to enter the `Hold` state; if `Hold` is not defined, jumps to the `Fire` state instead.
- **For alternate fire:** Tries to enter the `AltHold` state; if `AltHold` is not defined, jumps to the `AltFire` state instead.

This logic is implemented via the `GetAtkState(bool hold)` and `GetAltAtkState(bool hold)` helper functions in `src/g_shared/a_weapons.cpp:864-886`, which are automatically called by `P_FireWeapon()` and `P_FireWeaponAlt()` when a NULL state is passed.

## Behavior

When called from a weapon state:

1. **Fire button held:** If the attack button (primary or alternate, depending on which fire sequence is active) is still pressed:
   - Increments `player.refire` by 1 (used by functions like `A_FireBullets` to distinguish first shots from sustained fire).
   - Calls `P_FireWeapon()` or `P_FireWeaponAlt()` with the provided state (or auto-selected state if `null`), which jumps the weapon to the target state.
   - The jumped state usually repeats the attack or transitions to a different animation.

2. **Fire button released:** If the attack button is not held:
   - Resets `player.refire` to 0.
   - Calls `CheckAmmo()` on the ready weapon, which may consume ammunition and/or switch the player to a different weapon if the current weapon is out of ammo.

3. **Player dead or weapon-switching pending:** If the player's health is 0 or a weapon-switch is already in progress (`PendingWeapon != WP_NOCHANGE` and `WF_REFIRESWITCHOK` flag set), the function does nothing.

## Interaction with Hold/AltHold states

`A_ReFire` is the standard mechanism for transitioning from a `Fire` sequence to a `Hold` sequence (or `AltFire` to `AltHold`). If a weapon defines a `Hold` state, it is responsible for:

- Using `A_ReFire` at the end of the `Hold` sequence to loop back (continuously firing while the button is held).
- Reaching `Hold` only via the automatic fallback logic in `A_ReFire`, not through explicit state jumps elsewhere.

If no `Hold` state is defined, `A_ReFire` loops in the `Fire` state itself, creating continuous rapid-fire behavior.

## Network behavior

- **Server-authoritative.** In network play, the decision to refire (and thus the weapon state transition) is made server-side only; clients receive the server's decided outcome.
- **Ammo checking in multiplayer:** The `CheckAmmo()` call in the fire-button-released path is also server-side, so weapon-switches due to ammo depletion are synchronized across all players.

## Examples

### Semi-auto pistol

```decorate
Fire:
    PISG A 4;
    PISG B 6 A_FirePistol;
    PISG C 4;
    PISG B 5 A_ReFire;
    Goto Ready;
```

When the player taps the fire button, the sequence plays: A → B (fire) → C → B → Ready. If the player holds the button through the entire sequence, `A_ReFire` on the second B frame checks the button state; since it's held, it jumps back to the beginning of the Fire sequence (or to a `Hold` state if defined). Once the button is released, `A_ReFire` returns to Ready and performs an ammo check.

### Weapon with Hold state for full-auto

```decorate
Fire:
    WEPN A 2 A_FireCustom;
    WEPN B 3 A_ReFire;
    Goto Ready;

Hold:
    WEPN C 1 A_FireCustom;
    WEPN C 0 A_ReFire;
    Loop;
```

On the first shot (when `player.refire == 0`), the Fire sequence plays. If the button is held through the `A_ReFire` on frame B, the automatic fallback (since there is a Hold state) jumps to Hold. The Hold sequence repeats at a faster rate, creating a sustained full-auto effect. Releasing the button during Hold returns to Ready via the ammo-check path.

## See also

- **`A_ClearReFire`** — manually resets `player.refire` to 0 (normally done automatically when the fire button is released, but can be useful in certain attack-animation sequences).
- **`A_FireBullets`** — uses `player.refire` to determine first-shot accuracy; passes `0` to `FBF_USEAMMO` flag for spread behavior on sustained fire.
- **`Creating weapons`** concept — detailed overview of weapon state sequences and how Hold/Fire/AltFire/AltHold states interact.
