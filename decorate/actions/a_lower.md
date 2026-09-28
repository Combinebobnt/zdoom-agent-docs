# `void A_Lower()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Lower` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Lower&oldid=47266) + verified against the Zandronum source's `src/p_pspr.cpp:1120–1162` and wadsrc declaration in `wadsrc/static/actors/shared/inventory.txt:21`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function, defined on `AInventory` (callable from weapon state tables).

Lowers a weapon off-screen during a deselect sequence. Intended for a weapon's `Deselect` state. Each call moves the weapon sprite down (increasing its psprite Y offset) until it reaches `WEAPONBOTTOM`, then triggers weapon switching via `P_BringUpWeapon`.

## Engine-family divergence: parameter not supported

The ZDoom wiki describes an optional `lowerspeed` parameter ("how much the weapon is lowered by; default is 6"). **Zandronum does not support this.** Zandronum's `wadsrc/static/actors/shared/inventory.txt:21` declares `A_Lower` as a native action with no parameters.

Calling `A_Lower(12)` in DECORATE is a fatal parse error saying parameters cannot be passed. `A_Lower()` with empty parentheses hits the same error, so call it bare. Every call in Zandronum moves the weapon by the fixed `LOWERSPEED` constant (`FRACUNIT*6`), i.e. 6 units of psprite screen offset (not map units). Starting from `WEAPONTOP` (about 32) that takes 16 calls to reach `WEAPONBOTTOM` (128). To lower faster, use several frames that each call it: a multi-frame line such as `PISG AAAA 0 A_Lower` runs it once per frame, and consecutive zero-tic frames all run in the same tic. Shortening the frames' durations also helps.

## Behavior

Each call moves the weapon down by the fixed increment. The sequence continues until the weapon Y position is at or below `WEAPONBOTTOM`. When `A_Lower` detects a fully lowered weapon, it immediately:

1. Checks if the player is dead (`PST_DEAD`). If so, clears the weapon from the HUD layer and returns without switching.
2. Clears the weapon flash state (rarely used outside Strife).
3. Calls `P_BringUpWeapon` to raise the next pending weapon and enter its `Select` state. If no switch is pending, the current weapon instead snaps back to `WEAPONTOP` and enters its `Ready` state.

### Special cases and caveats

**Spectators.** If the player has the `bSpectating` flag (Zandronum multiplayer), the weapon immediately snaps to `WEAPONBOTTOM` without the normal lowering animation, and `A_Lower` returns without attempting a weapon switch.

**Morphed actors and instant-switch cheat.** If the player is morphed and does **not** have the `PPF_NOMORPHLIMITATIONS` flag set on their actor, or if they have the `CF_INSTANTWEAPSWITCH` cheat flag, the weapon immediately snaps to `WEAPONBOTTOM` instead of lowering normally.

**Repeated calls across frames.** Unlike the wiki's warning about nested function calls, calling `A_Lower` from several consecutive frames (a multi-frame line or several state lines in sequence) works correctly. Each call lowers the weapon further. The call that reaches the bottom performs the weapon switch itself, so the remaining frames of the old `Deselect` sequence are not run.

### Weapon switch control: `ZACOMPATF_FULL_WEAPON_LOWER`

The `ZACOMPATF_FULL_WEAPON_LOWER` compatibility flag (Zandronum-specific) governs whether a pending weapon switch can interrupt the lower sequence. When this flag is clear, `A_Raise` (the counterpart action) checks for a pending weapon and calls `P_DropWeapon` to abort the raise sequence early. `A_Lower` reads neither this flag nor the pending weapon while lowering, so a lower always runs to completion. This creates an asymmetry: `A_Lower` always completes, but `A_Raise` may not. See [Creating weapons](../concepts/creating-weapons.md) for details on the two-function lower/raise sequence.

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

Unlike `A_Raise`, `A_Lower` has no explicit `self == NULL` check. Both return early when `self->player` is null, so a call on a non-player actor is a harmless no-op. The missing `self` check is not reachable from ordinary weapon dispatch either, since `P_SetPsprite` only runs a psprite action when the player's actor exists. Call this action from a weapon state (the owning player's `ps_weapon` layer), where it has an effect.

## See also

- [A_Raise](a_raise.md) — raises the weapon back to `WEAPONTOP` and enters its ready state.
- [Creating weapons](../concepts/creating-weapons.md) — describes the `Select`/`Ready`/`Deselect` state sequence and the lower/raise mechanism in full.
