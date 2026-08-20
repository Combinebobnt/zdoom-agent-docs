# `void A_ScaleVelocity(float scale)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_ScaleVelocity` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_ScaleVelocity&oldid=54499) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5021-5046` and `wadsrc/static/actors/actor.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_ScaleVelocity)` in `src/thingdef/thingdef_codeptr.cpp:5021`.

Multiplies the calling actor's velocity on each axis by a scale factor. Positive scale values above 1.0 accelerate the actor; values between 0.0 and 1.0 slow it down.

## Parameters

- **`scale`** — the multiplier applied to the actor's velocity components (x, y, and z). Each component is scaled independently: `velx *= scale`, `vely *= scale`, `velz *= scale`.

## Behavior notes

- **Velocity units:** Velocity is stored internally as fixed-point (`fixed_t`, 16.16 format). The float parameter is converted to fixed-point, and multiplication is performed via `FixedMul`, which truncates (does not round) the result. Repeated scaling with values like `0.95` will eventually truncate to exactly zero rather than asymptotically approaching it — this is expected behavior and why the internal `CheckStopped` path can fire.

- **Stopped-actor handling:** If the actor was moving before the call, `A_ScaleVelocity` calls `CheckStopped` internally after updating velocity. This updates the `DEAD`/`ONGROUND` flags and may transition the actor's state (e.g., a sliding actor to idle). The `CheckStopped` helper only triggers state transitions for players; for non-players, it is effectively a status flag update.

- **Network multiplayer (Zandronum):** This is server-authoritative. On clients, the function returns early if the actor is not client-side-only (see "Network caveat" below). On the server (or in single-player), the velocity change proceeds normally. If the actor is not client-handled, the server broadcasts the velocity update to all clients via `SERVERCOMMANDS_MoveThingExact(self, CM_VELX|CM_VELY|CM_VELZ)`.

- **Network caveat:** The `NETWORK_InClientModeAndActorNotClientHandled(self)` guard at the function's start returns immediately on clients if the actor is server-authoritative (not marked `+CLIENTSIDEONLY`). This means such actors' velocity changes are applied only on the server and replicated to clients afterward, ensuring consistency.

## Engine-family divergence

**The ZDoom wiki describes a `ptr` parameter (the actor pointer, defaulting to `AAPTR_DEFAULT`), but Zandronum's implementation does not support it.** Zandronum's `A_ScaleVelocity` is hard-coded to modify the calling actor (`self`) only; there is no way to modify another actor's velocity via this function in Zandronum. The function signature in Zandronum is `A_ScaleVelocity(float scale)` (1 parameter only), not the 2-parameter version the wiki describes.

If you need to scale a specific actor's velocity from outside that actor, you will need a custom action function or a workaround (e.g., an actor with a TID that calls its own `A_ScaleVelocity`).

## Engine-family divergence: `ptr` parameter and velocity representation on UZDoom

**UZDoom's `A_ScaleVelocity` is implemented in ZScript** (`extend class Actor` in the stdlib's `actors/actions.zs`), not the native C++ path Zandronum uses, and its signature matches the wiki's 2-parameter form the section above says Zandronum lacks: `void A_ScaleVelocity(double scale, int ptr = AAPTR_DEFAULT)`. It resolves `ptr` via `GetPointer(ptr)` and returns immediately if that resolves to `NULL`, so on UZDoom a caller genuinely can scale another actor's velocity through this one function — the workaround described above is a Zandronum-only necessity.

**Velocity is also represented differently.** UZDoom's `Actor.Vel` is a native `vector3` of `double` components, and the scale multiply is a plain floating-point `ref.Vel *= scale` — there is no fixed-point `FixedMul` truncation step. Repeated scaling by a sub-1.0 factor on UZDoom asymptotically approaches zero rather than hard-truncating to exactly zero the way 16.16 fixed-point division does; the "eventually truncates to exactly zero" quirk described above is Zandronum-specific.

## Engine-family divergence: no network-authority gating on UZDoom

UZDoom's source tree has no equivalent of Zandronum's `NETWORK_InClientModeAndActorNotClientHandled` guard or `SERVERCOMMANDS_*` replication calls anywhere (confirmed by a tree-wide grep for both) — UZDoom carries no client/server authority split at all. `A_ScaleVelocity` and the `CheckStopped` helper it calls run unconditionally regardless of net role; the "Network multiplayer (Zandronum)" and "Network caveat" bullets above describe mechanisms that are entirely absent on UZDoom, not merely disabled or handled differently.

## Related functions

- **`A_ChangeVelocity(float x, float y, float z, int flags)`** — add or replace velocity on specific axes with optional coordinate-system and angle-relative modes; more flexible but also more complex than `A_ScaleVelocity`.
- **`A_Stop()`** — set velocity to zero on all axes.
