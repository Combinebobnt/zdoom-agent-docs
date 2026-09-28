# `void A_ScaleVelocity(float scale)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_ScaleVelocity` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_ScaleVelocity&oldid=54499) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5021-5046` and `wadsrc/static/actors/actor.txt`, plus `src/thingdef/thingdef_codeptr.cpp:3751-3761` (`CheckStopped`), `src/basicinlines.h:43` (`MulScale16`) and `src/network.cpp:1598-1612` (client-handled test).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_ScaleVelocity)` in `src/thingdef/thingdef_codeptr.cpp:5021`.

Multiplies the calling actor's velocity on each axis by a scale factor. Positive scale values above 1.0 accelerate the actor; values between 0.0 and 1.0 slow it down.

## Parameters

- **`scale`** — the multiplier applied to the actor's velocity components (x, y, and z). Each component is scaled independently: `velx *= scale`, `vely *= scale`, `velz *= scale`.

## Behavior notes

- **Velocity units (Zandronum):** Velocity is stored internally as fixed-point (`fixed_t`, 16.16 format). The float parameter is converted to fixed-point, and each component is multiplied via `FixedMul` (`MulScale16`, `src/basicinlines.h:43`), a 64-bit multiply followed by an arithmetic right shift. That shift rounds toward negative infinity, not toward zero. So repeated scaling with a factor like `0.95` steps a positive component down to exactly zero, but a negative component never reaches zero. It settles on a small negative value of roughly `1/(1 - scale)` fixed-point units (about -19/65536 for `0.95`). An actor moving in a negative direction on any axis therefore never gets all three components to exactly zero this way.

- **Stopped-actor handling:** If the actor was moving before the call, `A_ScaleVelocity` calls `CheckStopped` after updating velocity. `CheckStopped` only acts when the caller is a player's own pawn and all three velocity components are now exactly zero. It then plays the pawn's idle animation (`PlayIdle`) and zeroes the player's separate bobbing velocity, as `A_Stop` does. It touches no actor flags, and for non-player actors it does nothing.

- **Network multiplayer (Zandronum):** This is server-authoritative. On clients, the function returns early unless the actor is client-handled (see "Network caveat" below). On the server (or in single-player), the velocity change proceeds normally. If the actor is not client-handled, the server broadcasts the velocity update to all clients via `SERVERCOMMANDS_MoveThingExact(self, CM_VELX|CM_VELY|CM_VELZ)`.

- **Network caveat:** The `NETWORK_InClientModeAndActorNotClientHandled(self)` guard at the function's start returns immediately on clients unless the actor is client-handled. An actor counts as client-handled when it has `+CLIENTSIDEONLY` or has no network ID (`NetID == 0`, `src/network.cpp:1598-1612`). Other actors' velocity changes are applied only on the server and replicated to clients afterward.

## Engine-family divergence

**The ZDoom wiki describes a `ptr` parameter (the actor pointer, defaulting to `AAPTR_DEFAULT`), but Zandronum's implementation does not support it.** Zandronum's `A_ScaleVelocity` is hard-coded to modify the calling actor (`self`) only; there is no way to modify another actor's velocity via this function in Zandronum. The function signature in Zandronum is `A_ScaleVelocity(float scale)` (1 parameter only), not the 2-parameter version the wiki describes.

If you need to scale a specific actor's velocity from outside that actor, you will need a custom action function or a workaround (e.g., an actor with a TID that calls its own `A_ScaleVelocity`).

## Engine-family divergence: `ptr` parameter and velocity representation on UZDoom

**UZDoom's `A_ScaleVelocity` is implemented in ZScript** (`extend class Actor` in the stdlib's `actors/actions.zs`), not the native C++ path Zandronum uses, and its signature matches the wiki's 2-parameter form the section above says Zandronum lacks: `void A_ScaleVelocity(double scale, int ptr = AAPTR_DEFAULT)`. It resolves `ptr` via `GetPointer(ptr)` and returns immediately if that resolves to `NULL`, so on UZDoom a caller genuinely can scale another actor's velocity through this one function — the workaround described above is a Zandronum-only necessity.

**Velocity is also represented differently.** UZDoom's `Actor.Vel` is a native `vector3` of `double` components, and the scale multiply is a plain floating-point `ref.Vel *= scale` — there is no fixed-point `FixedMul` truncation step. Repeated scaling by a sub-1.0 factor on UZDoom asymptotically approaches zero from either sign. The fixed-point rounding quirk described above (positive components hitting exactly zero, negative ones stalling at a small nonzero value) is Zandronum-specific.

## Engine-family divergence: no network-authority gating on UZDoom

UZDoom's source tree has no equivalent of Zandronum's `NETWORK_InClientModeAndActorNotClientHandled` guard or `SERVERCOMMANDS_*` replication calls anywhere (confirmed by a tree-wide grep for both) — UZDoom carries no client/server authority split at all. `A_ScaleVelocity` and the `CheckStopped` helper it calls run unconditionally regardless of net role; the "Network multiplayer (Zandronum)" and "Network caveat" bullets above describe mechanisms that are entirely absent on UZDoom, not merely disabled or handled differently.

## Related functions

- **`A_ChangeVelocity(float x, float y, float z, int flags)`** — add or replace velocity on specific axes with optional coordinate-system and angle-relative modes; more flexible but also more complex than `A_ScaleVelocity`.
- **`A_Stop()`** — set velocity to zero on all axes.
