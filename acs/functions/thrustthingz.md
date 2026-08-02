# ThrustThingZ

**Tier:** A
**Engine:** Zandronum 3.3-alpha (3.2.1 expected to match — action specials in this range are stable)
**Provenance:** ZDoom Wiki page (saved 2026-07-29), verified against Zandronum fork source code

**Classification:** Action special (index 128)

## Signature

```
int ThrustThingZ(int tid, int force, int direction, int mode);
```

## Summary

Thrusts an actor vertically with a specified force. Can either set the actor's Z-velocity to zero and then apply the force, or add the force to the actor's current Z-velocity.

## Parameters

- **`tid`** — Thing ID of the actor to thrust. If `0`, thrusts the script's activator (typically the player who triggered the script).

- **`force`** — Vertical thrust magnitude, in units per tic (1 second = 35 tics), divided by 4. Internally multiplied by `FRACUNIT` and divided by 4 to get fixed-point acceleration. Positive values thrust upward; the `direction` parameter modifies this.

- **`direction`** — Thrust direction. `0` = upward (default), `1` = downward. The engine negates the computed thrust force if this is non-zero.

- **`mode`** — Velocity handling. `0` = set the actor's Z-velocity to zero before applying thrust, `1` = add thrust to the actor's current Z-velocity.

## Return value

Always returns `true`.

## Behavior notes

- **Activator vs. TID:** When `tid` is 0, the function applies to the script's activator via the `it` pointer (the player or actor that triggered the script). When `tid` is non-zero, the function iterates through all actors with that TID and applies the thrust to each one independently.

- **Server-side execution:** The thrust is only applied on the server or in single-player mode. In multiplayer, after applying the velocity change, the server broadcasts the actor's position and Z-velocity to clients via `SERVERCOMMANDS_MoveThingExact` (or `SERVER_UpdateThingVelocity` for the activator).

- **Gravity:** This function manipulates Z-velocity directly; it does not disable gravity. Actors affected by gravity will continue to fall, with the initial Z-velocity set/modified by this function.

## Related

- **`ThrustThing`** — similar function that applies *horizontal* thrust instead of vertical. Can be combined with `ThrustThingZ` to produce diagonal or arbitrary-direction forces.

## Example

Floating item that bobs up and down:

```c
// In a ZScript-like ACS context (pseudo-code):
ThrustThingZ(0, 1, 0, 1);  // Thrust self upward, add to current velocity
// ... later in same script or next frame:
ThrustThingZ(0, 1, 1, 0);  // Thrust self downward, reset to new velocity
```
