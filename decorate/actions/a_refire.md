# `void A_ReFire(statelabel flash = null)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `A_ReFire` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_ReFire&oldid=54720) + verified against the Zandronum source's `src/p_pspr.cpp:1046-1082` and `src/g_shared/a_weapons.cpp:864-886`. **Tic-timing addition (2026-09-22):** the "Tic timing" section is source-derived, read from the Zandronum source's `src/p_pspr.cpp:204-267` (`P_SetPsprite`), `:338` (`P_FireWeapon`) and `:1046-1082`, bodies unchanged since `28f736fb3`; and the UZDoom source (@98b16b78fc) `wadsrc/static/zscript/actors/inventory/stateprovider.zs:434` (`A_ReFire`), `wadsrc/static/zscript/actors/player/player.zs:410` (`FireWeapon`) and `src/playsim/p_pspr.cpp:479-585` (`DPSprite::SetState`). The "Network behavior" section is source-derived from the Zandronum source's `src/p_pspr.cpp:338-382` (`P_FireWeapon`), `src/g_shared/a_weapons.cpp:689-700` (`CheckAmmo` client gate), `src/p_user.cpp:1205-1243` (`PickNewWeapon`), `src/p_user.cpp:4174` and `src/cl_pred.cpp:291` (client-side `P_MovePsprites`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AInventory, A_ReFire)` at `src/p_pspr.cpp:1046`. Defined on the `AInventory` class; only available in weapon/inventory states, not on arbitrary actors.

Checks whether the fire key is still held after an attack. If held, automatically jumps to a follow-up state (usually `Hold` for sustained fire or repeated attacks). If released, resets the refire counter and performs an ammo check that may switch the player to a different weapon if the current one is out of ammunition.

**Engine-family divergence: Zandronum's implementation differs from the ZDoom-wiki ZScript version.** The wiki describes an `autoSwitch` parameter (added to ZDoom in 4.14.2) that does not exist in Zandronum. In Zandronum, the ammo-check behavior is unconditional — when the fire button is released, ammunition checking and potential weapon-switching always occurs, with no way to suppress it from DECORATE.

## Signature

```decorate
void A_ReFire(statelabel flash = null)
```

Zandronum declares it in `wadsrc/static/actors/shared/inventory.txt` as `A_ReFire(state flash = "")`; omitting the argument means no explicit state. On Zandronum, `A_ReFire()` with empty parentheses is a parse error; call it bare (`A_ReFire`).

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
   - On Zandronum the jump is ammo-gated. `P_FireWeapon()` first runs `CheckAmmo()` (with auto-switch on); if there isn't enough ammo it resets `player.refire` to 0 and returns without jumping, so the `A_ReFire` state runs its tics and falls through to its successor, and the out-of-ammo check may already have started a weapon switch. `P_FireWeaponAlt()` likewise returns without jumping when the weapon has no `AltFire` state or not enough alt ammo, but leaves `player.refire` incremented.

2. **Fire button released:** If the attack button is not held:
   - Resets `player.refire` to 0.
   - Calls `CheckAmmo()` on the ready weapon. It only checks ammo counts (it never uses ammo up) and may switch the player to a different weapon if the current one is out of ammo.

3. **Player dead or weapon-switching pending:** If the player's health is 0 or less, or a weapon-switch is already in progress (`PendingWeapon != WP_NOCHANGE` and `WF_REFIRESWITCHOK` flag set), the held-fire branch is skipped even while the fire button is down. Execution falls through to the same path as a released fire button: `player.refire` resets to 0 and `CheckAmmo()` runs.

## Interaction with Hold/AltHold states

`A_ReFire` is the standard mechanism for transitioning from a `Fire` sequence to a `Hold` sequence (or `AltFire` to `AltHold`). If a weapon defines a `Hold` state, it is responsible for:

- Using `A_ReFire` at the end of the `Hold` sequence to loop back (continuously firing while the button is held).
- Reaching `Hold` only via the automatic fallback logic in `A_ReFire`, not through explicit state jumps elsewhere.

If no `Hold` state is defined, `A_ReFire` loops in the `Fire` state itself, creating continuous rapid-fire behavior.

## Tic timing

Both engines, same shape. When attack is held, `A_ReFire` sets the weapon layer to `Hold` (or `Fire`) from inside its own action call, a nested `P_SetPsprite` / `DPSprite::SetState` that replaces the `A_ReFire` state before its duration starts counting. The nested call leaves the layer on the new state's duration, so the outer state-set exits there.

- **Held:** the `A_ReFire` state's own tics are **not** spent. In the semi-auto pistol example below, a held cycle is 4+6+4 = 14 tics; the `B 5 A_ReFire` frame's 5 tics never run.
- **Tapped:** attack is released when `A_ReFire` runs, no state change happens, and its tics are spent in full before `Goto Ready`. The exception is an empty weapon: when the out-of-ammo check picks another weapon (on UZDoom, only with `autoSwitch` true), the switch moves the layer to the weapon's `Deselect` state at once.
- Doom's Shotgun is the same case: its `A_ReFire` frame is 7 tics, and the held refire is 37 tics, which excludes them.
- `AltFire`/`AltHold` behave identically through `P_FireWeaponAlt` / `FireWeaponAlt`.
- A Fire sequence with no `A_ReFire` that just falls back to `Ready` also adds no tics there when held, since fire is accepted the same tic Ready is entered. See [A_WeaponReady](a_weaponready.md)'s "Tic timing".

## Network behavior

Zandronum:

- **Runs on both sides, sends nothing itself.** `A_ReFire` has no network code. A client ticks its own player's weapon layer locally (`P_PlayerThink` calls `P_MovePsprites` for the console player), so it makes the refire decision from its own button state. The server makes the same decision independently from the input the client sent. When the held path reaches `P_FireWeapon()`/`P_FireWeaponAlt()`, the server only tells the other clients to play the player body's attack animation (`SERVERCOMMANDS_SetPlayerState`, skipping the firing client); the weapon layer's jump itself is not sent.
- **Out-of-ammo switch also runs on both sides.** The server's `CheckAmmo()` picks a new weapon for any player. On a client it only does so for the console player (it returns without switching for other players, whose ammo the client may not know exactly), and that client's `PickNewWeapon` also sends its choice to the server with a weapon-select client command.

## Examples

### Semi-auto pistol

```decorate
ACTOR MyPistol : Pistol
{
    States
    {
    Fire:
        PISG A 4
        PISG B 6 A_FirePistol
        PISG C 4
        PISG B 5 A_ReFire
        Goto Ready
    }
}
```

When the player taps the fire button, the sequence plays: A → B (fire) → C → B → Ready. If the player holds the button through the entire sequence, `A_ReFire` on the second B frame checks the button state; since it's held, it jumps back to the beginning of the Fire sequence (or to a `Hold` state if defined). Once the button is released, `A_ReFire` returns to Ready and performs an ammo check.

### Weapon with Hold state for full-auto

```decorate
ACTOR MyAutoGun : Chaingun
{
    States
    {
    Fire:
        CHGG A 6 A_FireBullets(5.6, 0, 1, 5)
        CHGG B 3 A_ReFire
        Goto Ready
    Hold:
        CHGG A 2 A_FireBullets(5.6, 0, 1, 5)
        CHGG B 0 A_ReFire
        Goto Ready
    }
}
```

On the first shot (when `player.refire == 0`), the Fire sequence plays. If the button is held through the `A_ReFire` on frame B, the automatic fallback (since there is a Hold state) jumps to Hold. While held, the 0-tic `A_ReFire` jumps straight back to the start of Hold, so after the first shot's 6 tics the gun fires every 2 tics. Releasing the button during Hold falls through to `Goto Ready` via the ammo-check path. Ending Hold with `Loop` instead would be a bug: on release, the 0-tic `A_ReFire` state falls through to the loop and fires again every cycle, so the weapon never stops.

## Engine-family divergence: full wiki autoSwitch parameter

UZDoom's `A_ReFire` (`wadsrc/static/zscript/actors/inventory/stateprovider.zs`) is the full ZDoom-wiki ZScript version referenced in the intro paragraph above, not Zandronum's unconditional variant: it takes the wiki's `autoSwitch` parameter (default `true`) and forwards it to `Weapon::CheckAmmo(fireMode, autoSwitch)` (`wadsrc/static/zscript/actors/inventory/weapons.zs`). When `autoSwitch` is `false`, `CheckAmmo` still reports whether the weapon has enough ammo but skips the `PlayerPawn.PickNewWeapon` call it would otherwise make on an out-of-ammo refire — so nothing forces a weapon switch. The "no way to suppress it from DECORATE" limitation described above for Zandronum does not apply to UZDoom.

## Engine-family divergence: no client/server split

UZDoom has no client/server authority split anywhere in its source tree (no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style construct exists at all) — the "Network behavior" section above (client and server each running the refire decision and the out-of-ammo switch) is Zandronum-only. On UZDoom, `A_ReFire`'s refire check and its `CheckAmmo` call execute identically regardless of network role.

## See also

- **`A_ClearReFire`** — manually resets `player.refire` to 0 (normally done automatically when the fire button is released, but can be useful in certain attack-animation sequences).
- **`A_FireBullets`** — uses `player.refire` to determine first-shot accuracy: with `numbullets` 1 and `player.refire` 0 the shot has no spread; once refire is counting, the spread applies.
- **`Creating weapons`** concept — detailed overview of weapon state sequences and how Hold/Fire/AltFire/AltHold states interact.
