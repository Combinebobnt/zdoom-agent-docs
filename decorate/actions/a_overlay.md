# `bool A_Overlay(int layer, statelabel start = null, bool nooverride = false)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `A_Overlay` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Overlay&oldid=54630) + verified against UZDoom source's `src/playsim/p_pspr.cpp:1187-1205`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Creates a new weapon/player sprite layer and sends it into a specified state sequence.

## Availability note

**This action does not exist in Zandronum** — it relies on an arbitrary-layer PSprite model (the `DPSprite` class) that Zandronum's codebase lacks entirely. Zandronum's weapon/overlay system is fixed to exactly five hardcoded layers (`ps_weapon`, `ps_flash`, `ps_targetcenter`, `ps_targetleft`, `ps_targetright`). Multi-layer weapon animation in Zandronum is only achievable through the `A_GunFlash` action on the `ps_flash` layer, which this function supersedes on engines that have it.

## Parameters

- `int layer` — A numeric layer ID, positive or negative (range `[-2147483647, 2147483647]` except `0`). Lower numbers are rendered below higher numbers. Predefined constants exist: `PSP_STRIFEHANDS` (`-1`), `PSP_WEAPON` (`1`), `PSP_FLASH` (`1000`), and three targeting-reticle IDs (`PSP_TARGETCENTER`, `PSP_TARGETLEFT`, `PSP_TARGETRIGHT`). **Note:** per the wiki, `PSP_WEAPON` should never be passed to `A_Overlay` (it's the main weapon layer), and `PSP_STRIFEHANDS` has special hardcoded quirks and should not be reused. Layer `0` is invalid. *(Numerics from wiki; Zandronum equivalents not cross-checked since this feature is absent.)*

- `statelabel start` — The state label the overlay should begin in (e.g., `"MuzzleFlash"`). If omitted or explicitly `null`, this is not undefined behavior: the layer is created and then immediately destroyed as part of the same call (a null target state hits the "object removed itself" path in the layer's state-setting logic), so no visible overlay ever appears. The function still returns `true` in this case — the return value only reflects whether layer creation was attempted, not whether the layer survived. The wiki example always provides an explicit state, and callers should too, since an omitted state is effectively a no-op.

- `bool nooverride` — If true, the function returns false without creating a layer if a layer with the specified ID already exists. If false, an existing layer is replaced.

## Return value

`true` if the layer was successfully created; `false` if creation failed (no player attached to the calling actor, or `nooverride` was true and the layer already exists).

## Restrictions

This action is only callable from contexts where a player-attached PSprite exists:
- From a `PlayerPawn` state.
- From a `StateProvider`-derived state that already draws via PSprite (e.g., a `Weapon`'s `Ready`/`Fire`/`Hold` state, or a `CustomInventory`'s `Use` state).

Regular actors and non-PSprite inventory items cannot use overlays.

## Related actions

The wiki lists `OverlayID`, `A_OverlayFlags`, `A_OverlayOffset`, and other overlay-manipulation actions — all of which are likewise absent in Zandronum. Verify their availability before using on a Zandronum target.

## See also

- [Creating weapons](../concepts/creating-weapons.md) — covers the two-layer `ps_weapon`/`ps_flash` Zandronum model and `A_GunFlash` as the closest Zandronum equivalent.
