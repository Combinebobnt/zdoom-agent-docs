# `void A_Raise()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Raise` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Raise&oldid=47269) + verified against the Zandronum source's `src/p_pspr.cpp:1170–1220` and wadsrc declaration in `wadsrc/static/actors/shared/inventory.txt:22`; parameter rejection at `src/thingdef/thingdef_states.cpp:432-440`, psprite action gate at `src/p_pspr.cpp:255`, zero-tic chaining at `src/p_pspr.cpp:216-267`, `WEAPON.ALLOW_WITH_RESPAWN_INVUL` at `src/thingdef/thingdef_data.cpp:384`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function, defined on `AInventory` (callable from weapon state tables).

Raises a weapon onto the screen during a select sequence. Must be called from a weapon's `Select` state. Decreases the weapon's screen Y position until it reaches `WEAPONTOP`, then triggers entry into the weapon's `Ready` state.

## Engine-family divergence: parameter not supported

The ZDoom wiki describes an optional `raisespeed` parameter ("how much the weapon is raised by; default is 6"). **Zandronum does not support this.** Zandronum's wadsrc declares `A_Raise` with an empty parameter list.

Writing `A_Raise(12)` in DECORATE is a fatal parse error ("You cannot pass parameters to ..."), and so is `A_Raise()` with empty parentheses; call it bare. All calls to `A_Raise` in Zandronum move the weapon up by the fixed `RAISESPEED` constant, 6 units of the weapon sprite's vertical offset (`FRACUNIT*6` in fixed point). A state line holds only one action, so to make a weapon raise faster, chain several zero-tic states that each call `A_Raise` ahead of the ticking one (zero-tic weapon states run within the same tic), or shorten the state duration.

## Behavior

Each call moves the weapon up by the fixed increment. The sequence continues until the weapon Y position is at or above `WEAPONTOP`. When `A_Raise` detects a fully raised weapon, it immediately:

1. Caps the weapon Y position at `WEAPONTOP` to normalize it.
2. Looks up the weapon's `Ready` state via `ReadyWeapon->GetReadyState()`.
3. Sets the weapon PSprite layer to that state.

### Special cases and caveats

**Weapon switch interruption.** If the player has a pending weapon switch (the `PendingWeapon` field is set) and the `ZACOMPATF_FULL_WEAPON_LOWER` compatibility flag is not enabled, `A_Raise` calls `P_DropWeapon` and returns immediately without moving the weapon. The weapon jumps to its `Deselect` state and lowers from its partly raised position if a switch is requested during the `Select` sequence. See [Creating weapons](../concepts/creating-weapons.md) for details on the weapon switching model.

**Respawn invulnerability disabling.** When a player completes raising a weapon that lacks the `+WEAPON.ALLOW_WITH_RESPAWN_INVUL` flag (Doom's `Fist`, `Pistol` and `Chainsaw` carry it), any respawn invulnerability they have (the `APowerRespawnInvulnerable` inventory item) is removed. The removal runs everywhere except on network clients, so in single-player and on the server; the server then tells clients to take the item away. This is a Zandronum-specific behavior not present in upstream ZDoom/GZDoom.

**Repeated calls across states.** Calling `A_Raise` from several states in sequence works: each call raises the weapon further. The call that reaches `WEAPONTOP` switches to the `Ready` state at once, so any `Select` states after it are never reached.

## Engine-family divergence: weapon-switch interruption is unconditional on UZDoom

UZDoom's `A_Raise` (the UZDoom source's `wadsrc/static/zscript/actors/inventory/weapons.zs`) has no equivalent of the `ZACOMPATF_FULL_WEAPON_LOWER` compatibility flag described above — UZDoom's source contains no `ZACOMPATF_` flags, and no `compat_fullweaponlower`-style cvar, at all. UZDoom's pending-weapon check is unconditional (any pending switch drops the weapon and returns), matching Zandronum's *default* (the compat flag is clear by default) but with no way to opt into the alternative: a Zandronum server can set `compat_fullweaponlower` so a pending switch waits for the raise sequence to finish instead of aborting it early; on UZDoom, a pending switch always aborts the raise, with no server-side setting to change that.

## Engine-family divergence: null `ReadyWeapon` handling

Zandronum's `A_Raise` always advances the weapon position (`psp->sy -= RAISESPEED`) on every call regardless of whether `ReadyWeapon` is set, and only branches on its nullness once the weapon reaches `WEAPONTOP` — nulling the PSprite state directly if `ReadyWeapon` is null at that point (see "Null pointer safety" below). UZDoom's `A_Raise` instead checks for a null `ReadyWeapon` up front, before touching the PSprite position at all, and returns immediately if so. The weapon does not move on that call, rather than continuing to animate toward the top and ending in a nulled state.

On Zandronum this branch is unreachable from weapon states: the psprite code runs no action function at all while `ReadyWeapon` is null, so `A_Raise` never executes from a weapon's `Select` sequence in that case. Zandronum's null-`ReadyWeapon` path only runs when `A_Raise` is called outside the psprite path, such as from a `CustomInventory` state chain on a player holding no weapon.

## Engine-family divergence: null-player guard is symmetric

The "Null pointer safety" section below documents a Zandronum-specific asymmetry between `A_Raise` and `A_Lower` — `A_Raise` guards against `self == NULL`, `A_Lower` does not. UZDoom's ZScript-native calling convention has no equivalent "raw self pointer" that a psprite action can receive null for in the first place — `A_Raise` and `A_Lower` are both true instance methods bound to a valid actor, and both early-return, identically, only when the resolved `player` reference itself is null (the UZDoom source's `wadsrc/static/zscript/actors/inventory/weapons.zs`). The two functions are symmetric on UZDoom; the asymmetry described below is Zandronum-only.

## Null pointer safety

`A_Raise` guards against `self == NULL` and `self->player == NULL` with early returns before dereferencing the player pointer. It is declared on `Inventory`, so only `Inventory`-derived classes can call it, and it returns harmlessly when the calling actor is not a player (it only makes sense from a player's weapon state). If the player's `ReadyWeapon` is NULL when the weapon reaches `WEAPONTOP`, the weapon PSprite state is set to NULL instead of failing. As noted above, weapon states never reach this, since Zandronum skips psprite actions while `ReadyWeapon` is null.

Both of these are Zandronum-specific behaviors — see "Engine-family divergence: null `ReadyWeapon` handling" and "Engine-family divergence: null-player guard is symmetric" above for how UZDoom differs.

## See also

- [A_Lower](a_lower.md) — lowers the weapon off-screen and triggers the next weapon selection.
- [Creating weapons](../concepts/creating-weapons.md) — describes the `Select`/`Ready`/`Deselect` state sequence and the raise/lower mechanism in full.
