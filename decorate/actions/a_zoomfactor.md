# `A_ZoomFactor(float scale = 1, int flags = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_ZoomFactor` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_ZoomFactor&oldid=46783) + verified against the Zandronum source at the 3.2.1 version-bump commit (28f736fb3) for presence in `wadsrc/static/actors/shared/inventory.txt` and engine implementation details in `src/g_shared/a_weapons.cpp:2056-2075`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AWeapon, A_ZoomFactor)` in the Zandronum source's `src/g_shared/a_weapons.cpp:2083`.

Adjusts the player's field-of-view multiplier for the current weapon. Each weapon maintains its own independent FOV scale, allowing weapons to have different zoom levels. **Restricted to Weapon and derived classes** — the action is defined on the `AWeapon` class and cannot be called from other actor types.

## Parameters

- **`scale`** (float, default 1.0) — The field-of-view scaling divisor. The player's FOV is multiplied by `1/scale` (effectively divided by `scale`); values outside `[0.1, 50]` are clamped silently before inversion. A value of 1.0 restores the unzoomed FOV. Examples:
  - `A_ZoomFactor(2.0)` → FOV is halved (zoomed in 2x)
  - `A_ZoomFactor(4.0)` → FOV is divided by 4 (zoomed in 4x)
  - `A_ZoomFactor(0.5)` → FOV is doubled (zoomed out 2x)
  - `A_ZoomFactor(0)` clamps to 0.1 → FOV × 10 (zoomed out maximally)
  - `A_ZoomFactor(100)` clamps to 50 → FOV × 0.02 (zoomed in 50x)

- **`flags`** (int, default 0) — Bitfield controlling zoom behavior. Constants are defined in `wadsrc/static/actors/shared/inventory.txt`:
  - `ZOOM_INSTANT` (value 1): Normally FOV changes are spread over several ticks for a smooth zoom animation. This flag makes the transition instant.
  - `ZOOM_NOSCALETURNING` (value 2): Normally the player's turning sensitivity (mouse/gamepad look input) is also scaled by the zoom factor — increasing when zoomed in, decreasing when zoomed out. This flag disables turn-input scaling, leaving the unzoomed sensitivity in effect while zoomed. **Implementation detail:** internally achieved by negating the stored scale value; has no effect on FOV itself, only on the sign-check for turn-input multipliers. A negative `scale` argument is never passed to the negation step because any input (positive or negative) is clamped to `[0.1, 50]` before the flag's negation is applied, so ZOOM_NOSCALETURNING is the only source of a negative internal value.

## Behavior

A `NULL` player pointer or no ready weapon causes the function to return silently with no effect. The function always operates on `player->ReadyWeapon`, never on `self` — during normal weapon switching, a weapon's `Deselect` state runs before `ReadyWeapon` is updated to the incoming weapon (via `P_BringUpWeapon` called at the end of `A_Lower`), so resetting zoom in `Deselect` correctly affects the departing weapon. If `A_ZoomFactor` is called from an unusual context where the calling weapon is not the ready weapon, it operates on whatever weapon is currently ready.

A default `scale` of 1.0 restores baseline FOV. To implement multi-level zoom (as in the examples below), call `A_ZoomFactor` with different scale values in different states, typically triggered by `A_WeaponReady` conditions or attack state transitions.

## Examples

**Two-level weapon zoom:**
```text
ACTOR SniperPistol : Pistol
{
  States
  {
  AltFire:
    PISG ABC 6
    TNT1 A 0 A_JumpIfInventory("SniperPistol_Zoomed", 2, "ZoomOut")
    TNT1 A 0 A_JumpIfInventory("SniperPistol_Zoomed", 1, "Zoom2")
    // fall through to Zoom1
  Zoom1:
    TNT1 A 0 A_ZoomFactor(2.0)
    TNT1 A 0 A_GiveInventory("SniperPistol_Zoomed", 1)
    Goto "AltFireDone"
  Zoom2:
    TNT1 A 0 A_ZoomFactor(4.0)
    TNT1 A 0 A_GiveInventory("SniperPistol_Zoomed", 1)
    Goto "AltFireDone"
  ZoomOut:
    TNT1 A 0 A_ZoomFactor(1.0)
    TNT1 A 0 A_TakeInventory("SniperPistol_Zoomed", 2)
    Goto "AltFireDone"
  AltFireDone:
    PISG C 5 A_ReFire
    Goto "Ready"
  }
}
```

**Instant zoom with disabled turn scaling:**
```text
TNT1 A 0 A_ZoomFactor(3.0, ZOOM_INSTANT | ZOOM_NOSCALETURNING)
```

## See also

- [Creating weapons](../concepts/creating-weapons.md) — weapon states and the per-weapon FOV-scale model.
- ACS `SetPlayerWeaponZoomFactor` — the ACS equivalent, sharing the same underlying engine implementation (via `P_SetPlayerWeaponZoomFactor` helper in `src/g_shared/a_weapons.cpp:2056-2075`); not yet documented in this tree.
