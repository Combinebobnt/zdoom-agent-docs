# `void A_ChangeVelocity(float x, float y, float z, int flags)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_ChangeVelocity` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_ChangeVelocity&oldid=54737) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5054-5098` (`CheckStopped` at `:3751-3762`), `src/thingdef/thingdef_expression.cpp:135-151` (float-to-fixed conversion) and `src/network.cpp:1598-1612` (client-handled test).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_ChangeVelocity)` in `src/thingdef/thingdef_codeptr.cpp:5054`.

Modifies the calling actor's velocity on any or all axes. By default, the new velocity is added to the existing velocity; with the `CVF_REPLACE` flag, the new velocity replaces it entirely. The `CVF_RELATIVE` flag makes the x/y components relative to the actor's current angle (forward/backward and strafe) rather than world coordinates.

## Parameters

- **`x`** — velocity change on the x axis (or forward/backward if `CVF_RELATIVE` is set). In world coordinates, positive x is east; relative to the actor, positive x is forward. Default is 0.0.

- **`y`** — velocity change on the y axis (or side-to-side if `CVF_RELATIVE` is set). In world coordinates, positive y is north; relative to the actor, positive y is left (the rotation maps +y to the actor's angle plus 90 degrees). Default is 0.0.

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

Units are map units per tic. On Zandronum, velocity components are stored as `fixed_t` (16.16 fixed point), and each parameter is converted by multiplying by `FRACUNIT`, so `1.0` is exactly 1 map unit/tic. There is no further scaling by actor speed or any other property. Fractions finer than 1/65536 are truncated.

## Behavior notes

- **Stopped players:** If the actor was moving before the call, `A_ChangeVelocity` calls `CheckStopped` afterwards. That check only does anything for a player's own body (`player->mo == self`) whose velocity is now zero on all three axes: it switches the player to its idle animation (`PlayIdle`) and clears the player's stored walking velocity. Non-player actors are unaffected; no flags are changed.

- **Network multiplayer (Zandronum):** This is server-authoritative. On clients, the call returns early unless the actor is client-handled (`NETFL_CLIENTSIDEONLY` set, or `NetID == 0`), so client-side-only actors do run it locally. On the server (or in single-player), the velocity change proceeds; if the actor is not client-handled, the server then sends the new x/y/z velocity to all clients via `SERVERCOMMANDS_MoveThingExact`.

## Engine-family divergence

**The ZDoom wiki lists a `ptr` parameter (the actor pointer, defaulting to `AAPTR_DEFAULT`), but Zandronum's implementation does not support it.** Zandronum's `A_ChangeVelocity` is hard-coded to modify the calling actor (`self`) only; there is no way to modify another actor's velocity via this function in Zandronum. The function signature in Zandronum is `A_ChangeVelocity(float x, float y, float z, int flags)` (4 parameters), not the 5-parameter version the wiki describes.

DECORATE on Zandronum cannot define new action functions, so to modify another actor's velocity use ACS `SetActorVelocity` on its TID, or have that actor call its own `A_ChangeVelocity`.

## Engine-family divergence: velocity units

**UZDoom stores velocity natively as double-precision floats, not the 16.16 `fixed_t` format described above.** `AActor.Vel` in UZDoom is a native `vector3` of doubles, and `A_ChangeVelocity`'s `x`/`y`/`z` parameters are declared as `double` and used directly in the rotation/addition math with no fixed-point conversion step. The `fixed_t` 16.16 storage described in "Velocity units" above is Zandronum's internal representation only; UZDoom has no fixed-point conversion step. On both engines a value of `1.0` means 1 map unit/tic of velocity change.

The rotation math itself (`CVF_RELATIVE`'s x/y-to-forward/strafe conversion) is identical between the two engines: world X is x times cos(angle) minus y times sin(angle), and world Y is x times sin(angle) plus y times cos(angle). Zandronum computes this with `DMulScale16` on fine-angle sine/cosine tables; UZDoom uses double-precision trigonometry.

## Related functions

- **`A_ScaleVelocity(float scale)`** — multiply the actor's velocity by a scalar, simpler than `A_ChangeVelocity` for simple scaling.
- **`A_Stop()`** — set velocity to zero on all axes.
