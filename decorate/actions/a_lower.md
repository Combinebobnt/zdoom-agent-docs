# `void A_Lower()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_Lower` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Lower&oldid=47266) + verified against the Zandronum source's `src/p_pspr.cpp:1120–1162` and wadsrc declaration in `wadsrc/static/actors/shared/inventory.txt:21`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function, defined on `AInventory` (callable from weapon state tables).

Lowers a weapon off-screen during a deselect sequence. Must be called from a weapon's `Deselect` state. Decreases the weapon's screen Y position until it reaches `WEAPONBOTTOM`, then triggers weapon switching via `P_BringUpWeapon`.

## Engine-family divergence: parameter not supported

The ZDoom wiki describes an optional `lowerspeed` parameter ("how much the weapon is lowered by; default is 6"). **Zandronum does not support this.** The function declaration in Zandronum's wadsrc is:

```text
action native A_Lower();
```

Attempting to call `A_Lower(12)` in DECORATE results in a parse error — the compiler rejects it because the function signature accepts no arguments. All calls to `A_Lower` in Zandronum decrement the weapon position by a fixed `LOWERSPEED` constant (`FRACUNIT*6` in source), equivalent to 6 map units per call. To make a weapon lower faster, call the function more than once per state (e.g., multiple copies in the same state line) or increase the state duration to fewer tics.

## Behavior

Each call moves the weapon down by the fixed increment. The sequence continues until the weapon Y position is at or below `WEAPONBOTTOM`. When `A_Lower` detects a fully lowered weapon, it immediately:

1. Checks if the player is dead (`PST_DEAD`). If so, clears the weapon from the HUD layer and returns without switching.
2. Clears the weapon flash state (rarely used outside Strife).
3. Calls `P_BringUpWeapon` to raise the next pending weapon and enter its `Select` state.

### Special cases and caveats

**Spectators.** If the player has the `bSpectating` flag (Zandronum multiplayer), the weapon immediately snaps to `WEAPONBOTTOM` without the normal lowering animation, and `A_Lower` returns without attempting a weapon switch.

**Morphed actors and instant-switch cheat.** If the player is morphed and does **not** have the `PPF_NOMORPHLIMITATIONS` flag set on their actor, or if they have the `CF_INSTANTWEAPSWITCH` cheat flag, the weapon immediately snaps to `WEAPONBOTTOM` instead of lowering normally.

**Repeated calls in one state.** Unlike the wiki's warning about nested function calls, repeated direct calls to `A_Lower` on the same state line (or multiple state lines in sequence) work correctly — each call lowers the weapon further, and once the weapon reaches bottom, the weapon switch takes effect immediately on the next call.

### Weapon switch control: `ZACOMPATF_FULL_WEAPON_LOWER`

The `ZACOMPATF_FULL_WEAPON_LOWER` compatibility flag (Zandronum-specific) governs whether a pending weapon switch can interrupt the lower sequence. When this flag is clear, `A_Raise` (the counterpart action) checks for a pending weapon and calls `P_DropWeapon` to abort the raise sequence early. This behavior is mirrored in `A_Lower` — if a weapon switch is pending and the compatibility flag is not set, the weapon lowers to completion normally (see `A_Raise` for the inverse). This creates an asymmetry: `A_Lower` always completes, but `A_Raise` may not. See [Creating weapons](../concepts/creating-weapons.md) for details on the two-function lower/raise sequence.

## Engine-family divergence: spectator and morph special-case snapping

UZDoom's `Weapon::A_Lower` (the UZDoom source's `wadsrc/static/zscript/actors/inventory/weapons.zs`) omits two of the special-case snap-to-`WEAPONBOTTOM` conditions the "Special cases and caveats" section above describes for Zandronum:

- **No spectator case.** UZDoom's source has no `bSpectating`-equivalent field or check anywhere in `A_Lower`, or in the weapon-lowering path generally — there is no multiplayer-spectator snap-to-bottom bypass at all.
- **Morph snap has no opt-out.** UZDoom triggers the instant snap-to-`WEAPONBOTTOM` whenever the acting player pawn is morphed — checked as a bare `Alternative` reference, the native `Actor.Alternative` field a morphed player pawn has pointing back at its pre-morph pawn (set during unmorphing) — unconditionally. Zandronum's `PPF_NOMORPHLIMITATIONS` player-pawn flag, which lets a modder opt a morphed pawn out of this snap so it lowers normally instead, does not exist anywhere in UZDoom's source (UZDoom's `PPF_` flags are a different, smaller set with no equivalent).

One calling-convention note worth recording, since it explains why a bare `Alternative` resolves to the *player's* morph state rather than the weapon's own: UZDoom calls a weapon-defined psprite action function with `self` bound to the player pawn actor, not the weapon object (`FState::CallAction(Owner->mo, Caller, ...)` in the UZDoom source's `src/playsim/p_pspr.cpp`), so `Alternative` inside `A_Lower`'s body is really `player.mo.Alternative`.

Both engines still snap instantly on the `CF_INSTANTWEAPSWITCH` cheat flag; that part is unaffected by this divergence.

## Engine-family divergence: dead-player weapon/flash psprite handling

"Behavior" step 1 above (clearing the weapon on death) differs in mechanism and scope between engines. Zandronum's `A_Lower` sets the `ps_weapon` psprite directly to `NULL` and leaves the flash (`ps_flash`) psprite untouched. UZDoom's `A_Lower` instead clears the flash psprite first (`player.SetPsprite(PSP_FLASH, null)`) and then sets the weapon psprite to whatever state a `DeadLowered` label resolves to (`psp.SetState(player.ReadyWeapon.FindState('DeadLowered'))`), rather than nulling it directly. No stock UZDoom weapon declares a `DeadLowered` state label, so `FindState` returns null for all of them and the practical end result — no visible weapon sprite — matches Zandronum's for every stock weapon. The divergence matters for a custom weapon: UZDoom lets a modder define their own `DeadLowered` state to control what's shown while a dead player's weapon stays lowered (an escape hatch Zandronum's direct-null approach doesn't offer), and UZDoom additionally clears the flash sprite in this path where Zandronum does not.

## Engine-family divergence: null-player guard is symmetric

The "Null pointer safety" section below documents a Zandronum-specific asymmetry between `A_Lower` and `A_Raise`. UZDoom's ZScript-native calling convention has no equivalent "raw self pointer" that a psprite action can receive null for in the first place — `A_Lower` and `A_Raise` are both true instance methods bound to a valid actor, and both early-return, identically, only when the resolved `player` reference itself is null (the UZDoom source's `wadsrc/static/zscript/actors/inventory/weapons.zs`). The two functions are symmetric on UZDoom; the asymmetry described below is Zandronum-only.

## Null pointer safety

Unlike `A_Raise`, `A_Lower` does not guard against `self == NULL` or `self->player == NULL` before dereferencing the player pointer. If called on a non-player actor (e.g., a projectile or monster state), it returns early only if `self->player` is null; a non-weapon caller risks undefined behavior. Always call this action only from a weapon state (within the owning player's `ps_weapon` PSprite layer).

## See also

- [A_Raise](actions/a_raise.md) — raises the weapon back to `WEAPONTOP` and enters its ready state.
- [Creating weapons](../concepts/creating-weapons.md) — describes the `Select`/`Ready`/`Deselect` state sequence and the lower/raise mechanism in full.
