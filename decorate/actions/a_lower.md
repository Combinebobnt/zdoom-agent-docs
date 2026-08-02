# `void A_Lower()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Lower` (retrieved 2026-07-31, oldid=47266) + verified against the Zandronum source's `src/p_pspr.cpp:1120–1162` and wadsrc declaration in `wadsrc/static/actors/shared/inventory.txt:21`.
**Bucket:** Action function, defined on `AInventory` (callable from weapon state tables).

Lowers a weapon off-screen during a deselect sequence. Must be called from a weapon's `Deselect` state. Decreases the weapon's screen Y position until it reaches `WEAPONBOTTOM`, then triggers weapon switching via `P_BringUpWeapon`.

## Engine-family divergence: parameter not supported

The ZDoom wiki describes an optional `lowerspeed` parameter ("how much the weapon is lowered by; default is 6"). **Zandronum does not support this.** The function declaration in Zandronum's wadsrc is:

```
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

## Null pointer safety

Unlike `A_Raise`, `A_Lower` does not guard against `self == NULL` or `self->player == NULL` before dereferencing the player pointer. If called on a non-player actor (e.g., a projectile or monster state), it returns early only if `self->player` is null; a non-weapon caller risks undefined behavior. Always call this action only from a weapon state (within the owning player's `ps_weapon` PSprite layer).

## See also

- [A_Raise](actions/a_raise.md) — raises the weapon back to `WEAPONTOP` and enters its ready state.
- [Creating weapons](../concepts/creating-weapons.md) — describes the `Select`/`Ready`/`Deselect` state sequence and the lower/raise mechanism in full.
