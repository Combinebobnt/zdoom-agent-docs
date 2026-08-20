# `A_SetAngle(float angle = 0, int flags = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_SetAngle` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SetAngle&oldid=55323) + verified against
the Zandronum source's native declaration `wadsrc/static/actors/actor.txt:296` and implementation
`src/thingdef/thingdef_codeptr.cpp` (DEFINE_ACTION_FUNCTION_PARAMS) and `src/p_mobj.cpp:3941`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetAngle)` — actor action on AActor.

Sets the actor's facing angle (yaw/horizontal direction) to a specified value in degrees. In DECORATE, this is the only way to change an actor's angle; ZScript allows direct assignment to the `angle` field but this function enables sub-tic interpolation for smoother visual updates.

## Parameters

- **angle**: The actor's new facing angle in degrees (0-360, wraps around). Absolute value, not relative — to rotate by a relative amount, reference the actor's current `angle` field in the expression (e.g., `angle + 45` to rotate 45 degrees counterclockwise).

- **flags**: Bitfield controlling interpolation behavior:
  - `SPF_INTERPOLATE` (value 2) — if set, angles for player actors are interpolated from old to new across the current frame, making the view rotation appear smooth rather than snapping to the new angle. Defined in `wadsrc/static/actors/constants.txt`.
  - `SPF_FORCECLAMP` (value 1) — defined alongside `A_SetAngle` but **not used by this action function** (only used by `A_SetPitch` for pitch clamping).
  - UZDoom defines a third flag, `SPF_SCALEDNOLERP` (value 4), not present in Zandronum — see Engine-family divergence below.

## Engine-family divergence

**Confirmed by direct UZDoom source read: UZDoom's `A_SetAngle` implements the wiki's 3-parameter form.** Its native declaration is `A_SetAngle(double angle = 0, int flags = 0, int ptr = AAPTR_DEFAULT)` — the `ptr` parameter selects which actor pointer (`AAPTR_TARGET`, `AAPTR_MASTER`, etc.) to redirect the angle change to, resolved the same way other actor-pointer parameters are (`AAPTR_DEFAULT`, the default, resolves to the calling actor itself, so a 2-argument call behaves identically to Zandronum's always-self behavior). Zandronum's `A_SetAngle` only takes 2 parameters (angle and flags) and always operates on the calling actor — there is no pointer parameter to redirect to a different actor. If you attempt to use the wiki's 3-parameter form on Zandronum, you will get a DECORATE parse error (arity mismatch).

**UZDoom also defines a third flag value, `SPF_SCALEDNOLERP` (value 4), that Zandronum does not have** (Zandronum's `constants.txt` defines only `SPF_FORCECLAMP`=1 and `SPF_INTERPOLATE`=2). For player actors, setting `SPF_SCALEDNOLERP` defers the angle change into `player->angleOffsetTargets.Yaw` (a `deltaangle` from the actor's current yaw) and sets the `CF_SCALEDNOLERP` cheat flag, instead of writing the new yaw immediately and setting `CF_INTERPVIEW` the way `SPF_INTERPOLATE` does — a materially different deferred-offset mechanism, not just an alternate spelling of interpolation. Non-player actors are unaffected by either flag (both only take effect when the actor has a `player` field).

## Behavior

For player actors, if `SPF_INTERPOLATE` is set and the angle actually changes, the engine sets the `CF_INTERPVIEW` flag to enable view interpolation for that frame. Non-player actors ignore the interpolation flag (angles are set immediately either way). The action function itself performs no network replication; whether the resulting angle reaches clients via the general actor-update replication path is untraced.

**This "network replication" framing is Zandronum-specific and does not apply to UZDoom.** UZDoom's source tree has no client/server authority split at all — no server-authoritative broadcast mechanism and no clientside-vs-serverside execution distinction of the kind Zandronum implements (confirmed: no `SERVERCOMMANDS_`-style broadcast calls anywhere in `p_mobj.cpp`'s angle/pitch/roll setters). UZDoom-family engines instead use a lockstep model where every peer runs the same simulation from the same synchronized input stream, so `A_SetAngle` sets `Angles.Yaw` identically and deterministically on every peer — there is no separate server/client copy for it to diverge between.

## Example

A spinning prop that rotates every tic:

```text
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
