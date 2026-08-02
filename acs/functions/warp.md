# Warp

**Tier:** A
**Engine:** Zandronum 3.2.1 (verified against the `3.3-alpha` local checkout).
**Provenance:** `Warp - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Warp&oldid=51056`), verified 2026-07-29 against the Zandronum source's `src/p_acs.cpp`.

`bool Warp(int tid, fixed xofs, fixed yofs, fixed zofs, fixed angle, int flags [, str success_state [, bool exact]])`

## Bucket

Extension function, `ACSF_Warp` (index `-92` in `zcommon.bcs`'s `special` table). The implementation is in `p_acs.cpp` (lines 6953–7115), `case ACSF_Warp:`.

## Synopsis

Teleports the calling actor to a reference actor's location, with optional offsets and angle adjustments. Returns `true` on success, `false` if the reference actor doesn't exist or the warp fails (e.g., collision blocked with `WARPF_NOCHECKPOSITION` not set).

## Parameters

- `tid` — TID of the reference actor to warp to. If `WARPF_USEPTR` is set in `flags`, this becomes an actor pointer (`AAPTR_*`) instead of a TID.
- `xofs` — X-axis offset applied *after* angle rotation (unless `WARPF_ABSOLUTEOFFSET` or `WARPF_ABSOLUTEPOSITION` is set). In relative mode: positive = forward relative to the reference actor's facing, negative = backward. In absolute mode: world-space X coordinate.
- `yofs` — Y-axis offset, same angle-rotation semantics as `xofs`. In relative mode: positive = right, negative = left. In absolute mode: world-space Y coordinate.
- `zofs` — Z-axis (vertical) offset. Positive = higher, negative = lower. When `WARPF_TOFLOOR` is set, `zofs` is added to the floor Z of the destination; otherwise it's added to the reference actor's Z (or used as an absolute coordinate if `WARPF_ABSOLUTEPOSITION` is set).
- `angle` — Angle offset (in Doom angle units, 0–2^32-1 = 0°–360°). Unless `WARPF_ABSOLUTEANGLE` is set, this is added to the reference actor's angle (or caller's angle if `WARPF_USECALLERANGLE` is set).
- `flags` — Bitfield controlling behavior and appearance. Can combine multiple flags with `|`.
- `success_state` — Optional state name to jump to on success. Default is `""` (no state jump). The exact-match behavior is controlled by the `exact` parameter.
- `exact` — If `true`, the state name must match exactly. If `false` (default), partial name matches are allowed (see `SetActorState`).

## Flags

### Behavior flags

- `WARPF_ABSOLUTEOFFSET` — Do not apply the destination angle to the XY offset. The offset remains in world space rather than being rotated to match the reference actor's facing.
- `WARPF_ABSOLUTEANGLE` — Treat `angle` as an absolute angle, not an offset to add to the reference actor's angle.
- `WARPF_ABSOLUTEPOSITION` — Treat `xofs`, `yofs`, and `zofs` as absolute world coordinates, not relative to the reference actor. Overrides `WARPF_ABSOLUTEOFFSET` but can still interact with `WARPF_TOFLOOR`.
- `WARPF_USECALLERANGLE` — Use the calling actor's own angle instead of the reference actor's when computing the offset rotation. **Note:** Adding the `angle` parameter to the caller's angle causes orbital motion around the reference point.
- `WARPF_NOCHECKPOSITION` — Skip collision/geometry validation; blindly accept the resulting position. Without this flag, the warp fails if the destination collides with solid geometry.
- `WARPF_STOP` — Set the caller's velocity to zero after the warp completes.
- `WARPF_TOFLOOR` — Set the caller's Z position relative to the floor of the destination location (computed after XY positioning), not relative to the reference actor's Z. Useful for floor-relative placement in new areas.
- `WARPF_TESTONLY` — Do not actually warp; only check whether it *would* succeed and allow the state jump if the warp-check passes. Caller remains at its original position.
- `WARPF_BOB` — Apply the reference actor's float-bob offsets to the warp destination, making the caller follow the bob pattern.
- `WARPF_MOVEPTR` — Warp the *reference* actor instead of the calling actor. All other flags and offset calculations remain the same, but the caller's state jump (and success/failure determination) is still handled by the calling actor.
- `WARPF_USEPTR` — Interpret `tid` as an actor pointer (e.g., `AAPTR_TARGET`, `AAPTR_MASTER`) instead of a numeric TID.
- `WARPF_COPYVELOCITY` — Copy the reference actor's velocity to the caller after warping, regardless of the angle applied.
- `WARPF_COPYPITCH` — Copy the reference actor's pitch to the caller, then add the `pitch` parameter if provided. (**Note:** `pitch` parameter is **not implemented** in Zandronum; see **Fork/wiki notes** below.)

### Appearance/interpolation flags

- `WARPF_INTERPOLATE` — Preserve the caller's previous position for interpolation, making the warp appear as a smooth movement from the old location (visual only, doesn't affect gameplay).
- `WARPF_WARPINTERPOLATION` — Modify interpolation data by the delta `(caller.new - caller.old)`, used internally to smooth sector-relative warps.
- `WARPF_COPYINTERPOLATION` — Copy the reference actor's interpolation data to the caller, allowing the caller to visually "stick" closely to the reference actor.

## Return value

- `true` — The warp succeeded (or passed `WARPF_TESTONLY` validation).
- `false` — The reference actor doesn't exist, or the warp was blocked by geometry (and `WARPF_NOCHECKPOSITION` was not set).

## Failure behavior

The function fails and returns `false` in two cases:
1. The reference actor (identified by `tid` or actor pointer) does not exist.
2. The destination position collides with solid geometry, *unless* `WARPF_NOCHECKPOSITION` is set.

If the warp fails, the caller remains at its original position (restored via `SetOrigin(oldx, oldy, oldz)`).

## Side effects on success

When the warp succeeds:
- The caller is repositioned to the destination.
- The caller's angle is set to `angle` (computed as described above).
- Velocity is zeroed (if `WARPF_STOP` is set), copied from the reference actor (if `WARPF_COPYVELOCITY` is set), or left unchanged.
- Pitch is copied from the reference actor (if `WARPF_COPYPITCH` is set). (**Not implemented** in Zandronum.)
- Interpolation data is updated per the `WARPF_*INTERPOLATION` flags.
- If `success_state` is provided and matches (exactly or partially, per `exact`), the caller jumps to that state.
- Networking: The server sends a `SERVERCOMMANDS_MoveThingIfChanged` to synchronize the warp to all clients.

## Networking

This is a server-side operation in multiplayer. The server handles the warp and broadcasts the new position to clients via `SERVERCOMMANDS_MoveThingIfChanged` if the position actually changed.

## Fork/wiki notes

**ZDoom vs. Zandronum divergence:** The ZDoom Wiki page lists three additional optional parameters (`heightoffset`, `radiusoffset`, `pitch`) that are **not implemented in Zandronum 3.2.1** or the local `3.3-alpha` checkout. These parameters appear to be a later ZDoom extension. Zandronum's signature supports only up to the `exact` parameter (8 arguments total, indices 0–7). Attempts to pass more arguments will be silently ignored, and the `pitch` parameter in `WARPF_COPYPITCH` remains unsupported.

- `heightoffset` (ZDoom only) — Not available. Zandronum does not support height-relative offsets.
- `radiusoffset` (ZDoom only) — Not available. Zandronum does not support radius-relative offsets.
- `pitch` (ZDoom only) — Not available as a parameter. `WARPF_COPYPITCH` copies pitch from the reference actor but cannot add an offset.
