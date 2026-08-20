# `void A_Raise()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_Raise` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Raise&oldid=47269) + verified against the Zandronum source's `src/p_pspr.cpp:1170–1220` and wadsrc declaration in `wadsrc/static/actors/shared/inventory.txt:22`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function, defined on `AInventory` (callable from weapon state tables).

Raises a weapon onto the screen during a select sequence. Must be called from a weapon's `Select` state. Decreases the weapon's screen Y position until it reaches `WEAPONTOP`, then triggers entry into the weapon's `Ready` state.

## Engine-family divergence: parameter not supported

The ZDoom wiki describes an optional `raisespeed` parameter ("how much the weapon is raised by; default is 6"). **Zandronum does not support this.** The function declaration in Zandronum's wadsrc is:

```text
action native A_Raise();
```

Attempting to call `A_Raise(12)` in DECORATE results in a parse error — the compiler rejects it because the function signature accepts no arguments. All calls to `A_Raise` in Zandronum move the weapon up by a fixed `RAISESPEED` constant (`FRACUNIT*6` in source), representing 6 fixed-point units per call. To make a weapon raise faster, call the function more than once per state (e.g., multiple copies in the same state line) or decrease the state duration to fewer tics.

## Behavior

Each call moves the weapon up by the fixed increment. The sequence continues until the weapon Y position is at or above `WEAPONTOP`. When `A_Raise` detects a fully raised weapon, it immediately:

1. Caps the weapon Y position at `WEAPONTOP` to normalize it.
2. Looks up the weapon's `Ready` state via `ReadyWeapon->GetReadyState()`.
3. Sets the weapon PSprite layer to that state.

### Special cases and caveats

**Weapon switch interruption.** If the player has a pending weapon switch (the `PendingWeapon` field is set) and the `ZACOMPATF_FULL_WEAPON_LOWER` compatibility flag is not enabled, `A_Raise` calls `P_DropWeapon` and returns immediately without moving the weapon. This can leave the weapon mid-raise if a switch is requested during the `Select` sequence. See [Creating weapons](../concepts/creating-weapons.md) for details on the weapon switching model.

**Respawn invulnerability disabling.** When a player completes raising a weapon that isn't the pistol or fists, if they have respawn invulnerability active (the `APowerRespawnInvulnerable` inventory item), it is removed — in single-player immediately, and in multiplayer coordinated through the server. This is a Zandronum-specific behavior not present in upstream ZDoom/GZDoom.

**Repeated calls in one state.** Unlike the wiki's warning about nested function calls, repeated direct calls to `A_Raise` on the same state line (or multiple state lines in sequence) work correctly — each call raises the weapon further, and once the weapon reaches the top, the Ready state activation takes effect immediately on the next call.

## Engine-family divergence: weapon-switch interruption is unconditional on UZDoom

UZDoom's `A_Raise` (the UZDoom source's `wadsrc/static/zscript/actors/inventory/weapons.zs`) has no equivalent of the `ZACOMPATF_FULL_WEAPON_LOWER` compatibility flag described above — UZDoom's source contains no `ZACOMPATF_` flags, and no `compat_fullweaponlower`-style cvar, at all. UZDoom's pending-weapon check is unconditional (`if (player.PendingWeapon != WP_NOCHANGE) { player.mo.DropWeapon(); return; }`), matching Zandronum's *default* (the compat flag is clear by default) but with no way to opt into the alternative: a Zandronum server can set `compat_fullweaponlower` so a pending switch waits for the raise sequence to finish instead of aborting it early; on UZDoom, a pending switch always aborts the raise, with no server-side setting to change that.

## Engine-family divergence: null `ReadyWeapon` handling

Zandronum's `A_Raise` always advances the weapon position (`psp->sy -= RAISESPEED`) on every call regardless of whether `ReadyWeapon` is set, and only branches on its nullness once the weapon reaches `WEAPONTOP` — nulling the PSprite state directly if `ReadyWeapon` is null at that point (see "Null pointer safety" below). UZDoom's `A_Raise` instead checks `player.ReadyWeapon == null` up front, before touching the PSprite position at all, and returns immediately if so — the weapon does not move on that call, rather than continuing to animate toward the top and ending in a nulled state. A weapon whose `ReadyWeapon` is transiently null while raising visually freezes on UZDoom instead of continuing to animate toward `WEAPONTOP` as it does on Zandronum.

## Engine-family divergence: null-player guard is symmetric

The "Null pointer safety" section below documents a Zandronum-specific asymmetry between `A_Raise` and `A_Lower` — `A_Raise` guards against `self == NULL`, `A_Lower` does not. UZDoom's ZScript-native calling convention has no equivalent "raw self pointer" that a psprite action can receive null for in the first place — `A_Raise` and `A_Lower` are both true instance methods bound to a valid actor, and both early-return, identically, only when the resolved `player` reference itself is null (the UZDoom source's `wadsrc/static/zscript/actors/inventory/weapons.zs`). The two functions are symmetric on UZDoom; the asymmetry described below is Zandronum-only.

## Null pointer safety

`A_Raise` guards against `self == NULL` and `self->player == NULL` with early returns before dereferencing the player pointer. It is safe to call from any actor type (though it only makes sense from a player's weapon state). However, if the weapon's `ReadyWeapon` is NULL (which can occur if a weapon is deselected while raising), the PSprite state is set to NULL instead of failing.

Both of these are Zandronum-specific behaviors — see "Engine-family divergence: null `ReadyWeapon` handling" and "Engine-family divergence: null-player guard is symmetric" above for how UZDoom differs.

## See also

- [A_Lower](actions/a_lower.md) — lowers the weapon off-screen and triggers the next weapon selection.
- [Creating weapons](../concepts/creating-weapons.md) — describes the `Select`/`Ready`/`Deselect` state sequence and the raise/lower mechanism in full.
