# `void A_ChangeVelocity(float x, float y, float z, int flags)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_ChangeVelocity` (retrieved 2026-08-01, oldid=54737) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5054-5098`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_ChangeVelocity)` in `src/thingdef/thingdef_codeptr.cpp:5054`.

Modifies the calling actor's velocity on any or all axes. By default, the new velocity is added to the existing velocity; with the `CVF_REPLACE` flag, the new velocity replaces it entirely. The `CVF_RELATIVE` flag makes the x/y components relative to the actor's current angle (forward/backward and strafe) rather than world coordinates.

## Parameters

- **`x`** — velocity change on the x axis (or forward/backward if `CVF_RELATIVE` is set). In world coordinates, positive x is east; relative to the actor, positive x is forward. Default is 0.0.

- **`y`** — velocity change on the y axis (or side-to-side if `CVF_RELATIVE` is set). In world coordinates, positive y is north; relative to the actor, positive y is right. Default is 0.0.

- **`z`** — velocity change on the z axis (up/down). Positive z is up. Default is 0.0.

- **`flags`** — bitwise combination of velocity-change flags. See "Flags" below.

## Flags

The `flags` parameter controls the velocity-change mode and coordinate system:

- **`CVF_RELATIVE` (1)** — Make x/y relative to the actor's current angle. The x component becomes forward/backward movement; y becomes left/right (strafe). Z is always absolute regardless of this flag.

  **Example:** An actor facing east (0°) with `CVF_RELATIVE` and `x=10` will gain eastward velocity; facing north (90°) with the same call will gain northward velocity. This is useful for creatures that move forward relative to their facing direction, or projectiles that need to strafe while moving.

- **`CVF_REPLACE` (2)** — Replace the actor's existing velocity with the new velocity instead of adding to it. Without this flag, the new velocity is added component-wise to the old (`velx += x`, `vely += y`, `velz += z`). With this flag, the velocity is set directly (`velx = x`, `vely = y`, `velz = z`), discarding the old velocity entirely.

  **Example:** Without `CVF_REPLACE`, `A_ChangeVelocity(10, 0, 0, 0)` on an actor already moving at (5, 5, 0) results in (15, 5, 0). With `CVF_REPLACE`, it results in (10, 0, 0).

Flags are combined with the bitwise OR operator: `CVF_RELATIVE | CVF_REPLACE`.

## Velocity units

Velocity components are stored internally as `fixed_t` (fixed-point 16.16 format). The floats passed as parameters are automatically converted to fixed-point by the action-function parameter machinery. For reference, 1.0 in DECORATE velocity typically corresponds to ~0.015625 units/tic in physics calculations (exact scaling depends on actor speed properties).

## Behavior notes

- **Stopped actors:** If the actor was moving before the call, `A_ChangeVelocity` calls `CheckStopped` internally after updating velocity. This check updates the actor's DEAD/ONGROUND flags and state machine (e.g., transitioning a sliding actor to its idle state).

- **Network multiplayer (Zandronum):** This is server-authoritative. On clients, the call returns early if the actor is client-side-only. On the server (or in single-player), the velocity change proceeds; if the actor is not client-handled, the server broadcasts the velocity update to all clients via `SERVERCOMMANDS_MoveThingExact`.

## Wiki/fork divergence

**The ZDoom wiki lists a `ptr` parameter (the actor pointer, defaulting to `AAPTR_DEFAULT`), but Zandronum's implementation does not support it.** Zandronum's `A_ChangeVelocity` is hard-coded to modify the calling actor (`self`) only; there is no way to modify another actor's velocity via this function in Zandronum. The function signature in Zandronum is `A_ChangeVelocity(float x, float y, float z, int flags)` (4 parameters), not the 5-parameter version the wiki describes.

If you need to modify a specific actor's velocity from outside that actor, you will need a custom action function or a workaround (e.g., an actor with a TID that calls its own `A_ChangeVelocity`).

## Related functions

- **`A_ScaleVelocity(float scale)`** — multiply the actor's velocity by a scalar, simpler than `A_ChangeVelocity` for simple scaling.
- **`A_Stop()`** — set velocity to zero on all axes.
