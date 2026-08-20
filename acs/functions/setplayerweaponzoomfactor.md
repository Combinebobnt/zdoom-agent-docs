# `int SetPlayerWeaponZoomFactor(int player, fixed zoom[, int flags])`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** Zandronum Wiki `SetPlayerWeaponZoomFactor` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=SetPlayerWeaponZoomFactor&oldid=2268) + verified against the Zandronum source at the 3.2.1 tag (28f736fb3) for the ACS extension function (`case ACSF_SetPlayerWeaponZoomFactor` in `src/p_acs.cpp`) and implementation (`P_SetPlayerWeaponZoomFactor` in `src/g_shared/a_weapons.cpp:2056-2075`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -174; dispatched as `ACSF_SetPlayerWeaponZoomFactor`).

Adjusts the player's field-of-view multiplier for the current weapon, identical in behavior to the DECORATE `A_ZoomFactor` action function. Each weapon maintains its own independent FOV scale, allowing weapons to have different zoom levels.

## Parameters

- **`player`** (int) — Player index (0-63). Must be a valid player currently in the game. Dead players (playerstate == PST_DEAD) return failure silently.
- **`zoom`** (fixed) — The field-of-view scaling divisor as a fixed-point value. The player's FOV is multiplied by `1/zoom` (effectively divided by `zoom`); values are clamped to the range [0.1, 50.0] before inversion. A value of 1.0 (FRACUNIT in fixed point) restores the unzoomed FOV.
  - `zoom = 2.0` → FOV is halved (zoomed in 2x)
  - `zoom = 4.0` → FOV is divided by 4 (zoomed in 4x)
  - `zoom = 0.5` → FOV is doubled (zoomed out 2x)
  - `zoom = 0` clamps to 0.1 → FOV × 10 (zoomed out maximally)
  - `zoom = 50.0` is clamped at upper limit → FOV × 0.02 (zoomed in 50x)
- **`flags`** (int, optional; default 0) — Bitfield controlling zoom behavior. Constants are shared with DECORATE's `A_ZoomFactor`:
  - **Bit 0 / value 1 (`ZOOM_INSTANT`):** Normally FOV changes are spread over several ticks for a smooth zoom animation. This flag makes the transition instant (sets `FOV = DesiredFOV * zoom` immediately).
  - **Bit 1 / value 2 (`ZOOM_NOSCALETURNING`):** Normally the player's turning sensitivity (mouse/gamepad look input) is also scaled by the zoom factor — increasing when zoomed in, decreasing when zoomed out. This flag disables turn-input scaling by negating the stored scale value internally, leaving the unzoomed sensitivity in effect while zoomed. Has no effect on FOV itself, only on the sign-check for turn-input multipliers.

## Return value

- **`1`** — Success: the player is valid, not dead, and has a ready weapon.
- **`0`** — Failure: the player index is invalid, the player is dead, or the player has no ready weapon.

## Behavior

The function operates on `player->ReadyWeapon`, never on the caller's own weapon context. A NULL player pointer or missing ready weapon causes the function to return 0 with no effect. The clamping of zoom to [0.1, 50.0] happens before the reciprocal is computed, so effective `FOVScale` values range from 0.02 to 10. Dead players (checked via `playerstate != PST_DEAD`) cannot have their zoom adjusted, as they have no active weapon to scale.

In multiplayer (server mode), the zoom change is automatically synchronized to clients via `SERVERCOMMANDS_SetWeaponZoomFactor`.

## Engine-family divergence

This function does not exist in UZDoom or the GZDoom family. UZDoom provides only the DECORATE `A_ZoomFactor` action function (called from weapon states), not an ACS-callable equivalent. Any ACS script written for Zandronum using `SetPlayerWeaponZoomFactor` cannot be ported to UZDoom without replacing the call with equivalent state-machine logic in DECORATE.

## See also

- DECORATE [A_ZoomFactor](../../decorate/actions/a_zoomfactor.md) — the DECORATE equivalent, sharing the same underlying `P_SetPlayerWeaponZoomFactor` helper in the Zandronum engine.
- [Creating weapons](../../decorate/concepts/creating-weapons.md) — weapon states and the per-weapon FOV-scale model.
