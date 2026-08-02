# `A_SetAngle(float angle = 0, int flags = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_SetAngle` (retrieved 2026-08-01, oldid=55323) + verified against
the Zandronum source's native declaration `wadsrc/static/actors/actor.txt:296` and implementation
`src/thingdef/thingdef_codeptr.cpp` (DEFINE_ACTION_FUNCTION_PARAMS) and `src/p_mobj.cpp:3941`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetAngle)` — actor action on AActor.

Sets the actor's facing angle (yaw/horizontal direction) to a specified value in degrees. In DECORATE, this is the only way to change an actor's angle; ZScript allows direct assignment to the `angle` field but this function enables sub-tic interpolation for smoother visual updates.

## Parameters

- **angle**: The actor's new facing angle in degrees (0-360, wraps around). Absolute value, not relative — to rotate by a relative amount, reference the actor's current `angle` field in the expression (e.g., `angle + 45` to rotate 45 degrees counterclockwise).

- **flags**: Bitfield controlling interpolation behavior:
  - `SPF_INTERPOLATE` (value 2) — if set, angles for player actors are interpolated from old to new across the current frame, making the view rotation appear smooth rather than snapping to the new angle. Defined in `wadsrc/static/actors/constants.txt`.
  - `SPF_FORCECLAMP` (value 1) — defined alongside `A_SetAngle` but **not used by this action function** (only used by `A_SetPitch` for pitch clamping).

## Engine scope

**The upstream ZDoom Wiki documents a 3-parameter form with an `int ptr` parameter that does not exist in Zandronum.** Zandronum's A_SetAngle only takes 2 parameters (angle and flags) and always operates on the calling actor — there is no pointer parameter to redirect to a different actor. If you attempt to use the wiki's 3-parameter form, you will get a DECORATE parse error (arity mismatch).

## Behavior

For player actors, if `SPF_INTERPOLATE` is set and the angle actually changes, the engine sets the `CF_INTERPVIEW` flag to enable view interpolation for that frame. Non-player actors ignore the interpolation flag (angles are set immediately either way). The action function itself performs no network replication; whether the resulting angle reaches clients via the general actor-update replication path is untraced.

## Example

A spinning prop that rotates every tic:

```
ACTOR SpinningCacoProp : Actor
{
  States
  {
    Spawn:
      HEAD A 1 A_SetAngle(angle + 15, SPF_INTERPOLATE);
      loop;
  }
}
```
