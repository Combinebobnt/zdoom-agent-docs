# `A_Warp` (warping actor to another actor's position)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Warp` (retrieved 2026-07-31, oldid=54969) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5539-5703`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Warp)` in `src/thingdef/thingdef_codeptr.cpp`.

Warps the calling actor to the position of another actor (typically specified via an actor pointer constant like `AAPTR_TARGET`). Originally designed as a more versatile analog to `A_Fire` (used by the Arch-Vile's flame attack).

**IMPORTANT: Engine-family divergence.** The ZDoom Wiki describes a more recent version of `A_Warp` with additional parameters and flags not present in Zandronum 3.2.1. See "Zandronum-specific notes" below for what is actually available in Zandronum.

## Signature

```
bool A_Warp(int ptr_destination, fixed xofs = 0, fixed yofs = 0, fixed zofs = 0,
            angle angle = 0, int flags = 0, state success_state = null)
```

Returns `true` if the warp succeeded, `false` otherwise (only 7 parameters in Zandronum; the wiki's additional `heightoffset`, `radiusoffset`, and `pitch` parameters do not exist).

## Parameters

### `ptr_destination` (int)

Actor pointer constant specifying the target actor to warp to. See actor pointers for more information. Common values:
- `AAPTR_TARGET` — the calling actor's current target
- `AAPTR_TRACER` — the calling actor's tracer pointer
- `AAPTR_MASTER` — the calling actor's master
- `AAPTR_OWNER` — the calling actor's owner

If the target actor does not exist or has been removed, the warp fails silently (even if `success_state` is defined, it will not jump).

### `xofs` (fixed, optional, default 0)

X-axis offset in map units. Positive values move the warped actor forward (relative to the target's angle, unless `WARPF_ABSOLUTEOFFSET` is set), negative values move backward. When `WARPF_ABSOLUTEOFFSET` is not set, this value is rotated by the target actor's angle.

### `yofs` (fixed, optional, default 0)

Y-axis offset in map units. Positive values move the warped actor to the right (relative to the target's angle, unless `WARPF_ABSOLUTEOFFSET` is set), negative values move to the left. In relative mode (default), this is perpendicular to the forward/backward axis and rotated by the target's angle.

### `zofs` (fixed, optional, default 0)

Z-axis (vertical) offset in map units. Positive values move the warped actor upward, negative values downward. When `WARPF_TOFLOOR` is set, this becomes relative to the target's floor height instead of the target's z-position.

### `angle` (angle, optional, default 0)

Angle change in BAM units (32-bit integer, 2^32 BAM = full rotation). If `WARPF_ABSOLUTEANGLE` is not set, this is added as an offset to the target's angle. If `WARPF_USECALLERANGLE` is set, the angle is added to the calling actor's angle instead.

### `flags` (int, optional, default 0)

Bitfield controlling warp behavior. Flags are combined using `|`. Only the following flags exist in Zandronum:

#### Offset/positioning flags

- `WARPF_ABSOLUTEOFFSET` (0x1) — By default, `xofs` and `yofs` are rotated by the target's angle (relative positioning). This flag disables rotation, treating them as absolute coordinate offsets instead.

- `WARPF_ABSOLUTEANGLE` (0x2) — By default, the `angle` parameter is added to the target's angle. This flag causes the `angle` parameter to be used as an absolute angle value instead.

- `WARPF_ABSOLUTEPOSITION` — **Does not exist in Zandronum** (GZDoom/UZDoom only). The wiki lists this, but Zandronum has no equivalent for treating x/y/z offsets as absolute world coordinates while still respecting `WARPF_TOFLOOR`.

- `WARPF_TOFLOOR` (0x100) — Makes the `zofs` parameter relative to the target's floor height rather than its z-position. The warp is first positioned at the target's x/y with z at the ceiling, then adjusted to the floor and offset by `zofs`.

#### Angle/rotation flags

- `WARPF_USECALLERANGLE` (0x4) — By default, the warped actor's angle is set to the target's angle (plus `angle` offset if applicable). This flag instead sets the angle to the calling actor's angle plus the `angle` parameter. Can be used to create orbiting effects by incrementally changing the `angle` parameter each call.

#### Movement/velocity flags

- `WARPF_STOP` (0x80) — Zeroes the warped actor's velocity (`velx`, `vely`, `velz`) after positioning. Similar to calling `A_Stop` after the warp.

- `WARPF_COPYVELOCITY` — **Does not exist in Zandronum** (GZDoom/UZDoom only). The wiki lists this for copying the target's velocity; Zandronum has no equivalent.

#### Collision and validation flags

- `WARPF_NOCHECKPOSITION` (0x8) — By default, the warp validates that the resulting position is collision-valid (`P_TestMobjLocation`), potentially preventing the warp if the actor would overlap a wall or solid object. This flag skips that check, blindly accepting any position.

- `WARPF_TESTONLY` (0x200) — Does not actually warp the actor; instead, only tests whether a warp would succeed and jumps to `success_state` if it would (ignoring all positioning flags except `WARPF_NOCHECKPOSITION`, which is still honored). Useful for checking if a position is valid before committing other state changes.

#### Interpolation flags

- `WARPF_INTERPOLATE` (0x10) — By default, the warp resets interpolation data to the new position (eliminating smooth rendering between the old and new position). This flag preserves the actor's existing interpolation state across the warp.

- `WARPF_WARPINTERPOLATION` (0x20) — Updates the interpolation data based on the position delta (`self->x - oldx`, etc.), causing smooth visual interpolation from the old position to the new one across the next frame render.

- `WARPF_COPYINTERPOLATION` (0x40) — Copies the target actor's interpolation data, causing the warped actor to mimic the target's visual position in the next frame.

#### Advanced behavior flags

- `WARPF_BOB` — **Does not exist in Zandronum** (GZDoom/UZDoom only). The wiki lists this for synchronizing floatbob phase with the target.

- `WARPF_MOVEPTR` — **Does not exist in Zandronum** (GZDoom/UZDoom only). The wiki lists this for warping the target instead of the calling actor.

- `WARPF_USETID` — **Does not exist in Zandronum** (GZDoom/UZDoom only). The wiki lists this for using a TID instead of an actor pointer.

- `WARPF_COPYPITCH` — **Does not exist in Zandronum** (GZDoom/UZDoom only). The wiki lists this for copying the target's pitch.

### `success_state` (state label, optional, default null)

State to jump to if the warp succeeds. If provided and the warp succeeds, the calling actor jumps to this state (does not combine with other state jumps in the same action frame). If the target actor does not exist, this state is never jumped to, regardless of how the warp would otherwise succeed.

## Additional parameters in the wiki (not in Zandronum)

The ZDoom Wiki describes three additional parameters that **do not exist in Zandronum 3.2.1**:

- `heightoffset` (double) — Adds `target->height * heightoffset` to the `zofs` parameter. Not in Zandronum.
- `radiusoffset` (double) — Adds `target->radius * radiusoffset` to both `xofs` and `yofs`. Not in Zandronum.
- `pitch` (double) — Sets the warped actor's pitch, with special interaction with `WARPF_COPYPITCH`. Not in Zandronum.

These parameters exist in GZDoom/UZDoom but are unavailable in Zandronum.

## Return value

Returns `true` if the warp succeeded, `false` otherwise. Success is determined by:
1. The target actor existing (non-null).
2. Either `WARPF_NOCHECKPOSITION` being set, or `P_TestMobjLocation(self)` passing after the position is set.

If `success_state` is provided and the return value would be `true`, the function jumps to `success_state` instead of returning.

## Network behavior (Zandronum multiplayer)

A_Warp is handled server-side only. In network play, the client's local call to A_Warp has no effect; the server computes the actual warp and broadcasts the result to all clients via `SERVERCOMMANDS_MoveThingIfChanged`.

## Example (Zandronum DECORATE)

Replicating the Arch-Vile's flame effect (orbiting projectile):

```
actor ArchVileFlame : Actor
{
    Default
    {
        Radius 6;
        Height 8;
        Speed 0;
        RenderStyle Add;
        Alpha 1.0;
        +MISSILE
    }

    var int user_angle;

    States
    {
    Spawn:
        AFBM A 1 Bright NoDelay 
            A_Warp(AAPTR_TARGET, 32, 0, 32, user_angle, 
                   WARPF_ABSOLUTEANGLE | WARPF_NOCHECKPOSITION | WARPF_INTERPOLATE)
        TNT1 A 0 A_SetUserVar("user_angle", user_angle + 8)
        Loop;
    }
}
```

Simple example: warp to target's location, zero velocity:

```
actor TeleportEffect : Actor
{
    States
    {
    Activate:
        TNT1 A 0 A_Warp(AAPTR_TARGET, 0, 0, 0, 0, WARPF_STOP, "Success")
        TNT1 A 5;
        Stop;
    Success:
        TNT1 A 1;
        Stop;
    }
}
```

## See also

- **`A_Teleport`** — teleports the actor to a map location specified by a line tag and optional sector tag (more restricted than A_Warp, but compatible with line-special infrastructure).
- **Actor pointers** — the constants (`AAPTR_TARGET`, `AAPTR_TRACER`, etc.) used to select the target actor.
