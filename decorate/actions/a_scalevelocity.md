# `void A_ScaleVelocity(float scale)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_ScaleVelocity` (retrieved 2026-08-01, oldid=54499) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5021-5046` and `wadsrc/static/actors/actor.txt`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_ScaleVelocity)` in `src/thingdef/thingdef_codeptr.cpp:5021`.

Multiplies the calling actor's velocity on each axis by a scale factor. Positive scale values above 1.0 accelerate the actor; values between 0.0 and 1.0 slow it down.

## Parameters

- **`scale`** — the multiplier applied to the actor's velocity components (x, y, and z). Each component is scaled independently: `velx *= scale`, `vely *= scale`, `velz *= scale`.

## Behavior notes

- **Velocity units:** Velocity is stored internally as fixed-point (`fixed_t`, 16.16 format). The float parameter is converted to fixed-point, and multiplication is performed via `FixedMul`, which truncates (does not round) the result. Repeated scaling with values like `0.95` will eventually truncate to exactly zero rather than asymptotically approaching it — this is expected behavior and why the internal `CheckStopped` path can fire.

- **Stopped-actor handling:** If the actor was moving before the call, `A_ScaleVelocity` calls `CheckStopped` internally after updating velocity. This updates the `DEAD`/`ONGROUND` flags and may transition the actor's state (e.g., a sliding actor to idle). The `CheckStopped` helper only triggers state transitions for players; for non-players, it is effectively a status flag update.

- **Network multiplayer (Zandronum):** This is server-authoritative. On clients, the function returns early if the actor is not client-side-only (see "Network caveat" below). On the server (or in single-player), the velocity change proceeds normally. If the actor is not client-handled, the server broadcasts the velocity update to all clients via `SERVERCOMMANDS_MoveThingExact(self, CM_VELX|CM_VELY|CM_VELZ)`.

- **Network caveat:** The `NETWORK_InClientModeAndActorNotClientHandled(self)` guard at the function's start returns immediately on clients if the actor is server-authoritative (not marked `+CLIENTSIDEONLY`). This means such actors' velocity changes are applied only on the server and replicated to clients afterward, ensuring consistency.

## Wiki/fork divergence

**The ZDoom wiki describes a `ptr` parameter (the actor pointer, defaulting to `AAPTR_DEFAULT`), but Zandronum's implementation does not support it.** Zandronum's `A_ScaleVelocity` is hard-coded to modify the calling actor (`self`) only; there is no way to modify another actor's velocity via this function in Zandronum. The function signature in Zandronum is `A_ScaleVelocity(float scale)` (1 parameter only), not the 2-parameter version the wiki describes.

If you need to scale a specific actor's velocity from outside that actor, you will need a custom action function or a workaround (e.g., an actor with a TID that calls its own `A_ScaleVelocity`).

## Related functions

- **`A_ChangeVelocity(float x, float y, float z, int flags)`** — add or replace velocity on specific axes with optional coordinate-system and angle-relative modes; more flexible but also more complex than `A_ScaleVelocity`.
- **`A_Stop()`** — set velocity to zero on all axes.
