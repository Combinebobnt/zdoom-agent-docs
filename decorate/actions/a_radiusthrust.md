# `void A_RadiusThrust(int force = 128, int distance = -1, int flags = RTF_AFFECTSOURCE, int fullthrustdistance = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_RadiusThrust` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RadiusThrust&oldid=54717) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1076-1109` and internal `P_RadiusAttack` in `src/p_map.cpp:5728-5910`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RadiusThrust)` in `src/thingdef/thingdef_codeptr.cpp`.

Applies a radial thrust (knockback) to nearby actors without damage, pushing them away from the calling actor's center. This is equivalent to `A_Explode` with only the thrust component and no damage. The underlying mechanism is the engine's internal `P_RadiusAttack` function.

## Engine-family divergence

**This page describes the Zandronum implementation, which has fewer parameters and flags than UZDoom's.** UZDoom's `A_RadiusThrust` (`void A_RadiusThrust(int force = 128, double distance = -1.0, int flags = RTF_AFFECTSOURCE, double fullthrustdistance = 0.0, name species = "None")`, `wadsrc/static/zscript/actors/attacks.zs:660`) differs from the Zandronum behavior described throughout this file:

- **5th parameter (`species`) is real and functional.** UZDoom accepts a `name species` parameter (default `"None"`); when set to anything else, only actors whose `Species` matches are thrust — enforced inside the shared `P_RadiusAttack` (`src/playsim/p_map.cpp`) as `(species != NAME_None) && (thing->Species != species)`. Zandronum's `A_RadiusThrust` does not support this parameter at all; the function always thrusts every eligible actor regardless of species.
- **Extra flags are real and implemented.** UZDoom's `RTF_THRUSTZ` (16) and `RTF_CIRCULARTHRUST` (512) (`wadsrc/static/zscript/constants.zs:294-302`) are honored by the shared `P_RadiusAttack` thrust code: `RTF_THRUSTZ` forces the vertical-velocity component to apply even on this no-damage call (normally skipped when `RADF_NODAMAGE` is set unless this flag is present); `RTF_CIRCULARTHRUST` thrusts the target directly away from the blast's 3D center instead of the default horizontal-angle-plus-separate-Z-component calculation. Neither flag exists in Zandronum — only three flags are defined there (`RTF_AFFECTSOURCE` = 1, `RTF_NOIMPACTDAMAGE` = 2, `RTF_NOTMISSILE` = 4), and all three share the same bit values as UZDoom's, so the low three bits are portable between engines.
- **Parameter types and defaults:** Zandronum uses `int` for all numeric parameters — plain integer map units, only shifted into fixed-point (`<< FRACBITS`) at the point they're used internally, not fixed-point at the interface; UZDoom's `distance` and `fullthrustdistance` are `double` (floating-point map units) — same unit, different in-engine representation.
- **No client/server authority gating.** UZDoom's `A_RadiusThrust` has no equivalent of Zandronum's client-mode early return (Zandronum's action function checks `NETWORK_InClientMode()` and returns immediately on a client before doing anything else) — on UZDoom the function always runs to completion on every machine. UZDoom's source tree has no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style client/server split anywhere, so the "Server-side only" bullet under Behavior notes below does not apply to UZDoom.
- **`MF7_DONTTHRUST` target-side opt-out.** UZDoom actors flagged `+DONTTHRUST` (`MF7_DONTTHRUST`, `src/playsim/actor.h:368`) are skipped by the thrust computation unconditionally — no flag on the `A_RadiusThrust` call is needed to trigger this, it's a property of the target. Zandronum's equivalent thrust block has no matching per-target check at all; `+DONTTHRUST` does not exist in Zandronum, so no actor can opt out of being thrust this way there.
- **Can damage destructible geometry, unlike Zandronum which has no such system.** `P_RadiusAttack` unconditionally calls `P_GeometryRadiusAttack` (`src/playsim/p_destructible.cpp:442`) before the actor-thrust loop, passing `force` straight through as `bombdamage` — that function has no `flags` parameter at all, so it cannot see and does not honor `RADF_NODAMAGE`. On a map using UZDoom's health-sector/health-group destructible geometry (UDMF-only, no Zandronum equivalent), an `A_RadiusThrust` call that is nominally damage-free will still deal `force`-scaled damage to nearby destructible sectors/3D floors/linedefs via `P_DamageLinedef` and the sector-damage-group path.

Everything else described in this file — the force-substitution-on-zero fallback, the distance-defaults-to-`abs(force)` fallback, the `MF2_NODMGTHRUST`/`bNoDamageThrust` temporary-negation logic gated on `RTF_NOTMISSILE`, and the terrain-splash trigger after the thrust pass — matches UZDoom's implementation.

## Parameters

- **`force`** — The raw power of the thrust, determining how fast affected actors are pushed away. Velocity imparted to a target is calculated as `force / (2 * mass)`, so a force of 40000 pushes a 1000-mass actor (Baron of Hell) with velocity 20 units/tic (rocket speed). Negative values push actors toward the source instead of away. Default (when omitted in DECORATE) is 128, per the native declaration in `actor.txt`. Separately, the function has a runtime safety net: if `force` evaluates to exactly 0 (e.g. an expression that resolves to zero), it is replaced with 128 rather than producing a no-op thrust.
- **`distance`** — Radius (in map units) of the thrust effect. At the center, actors receive the full force of the blast. At the outer edge (`distance` units away), actors receive no thrust. If `distance` is 0 or negative at runtime, it defaults to `abs(force)`. Default is -1 (triggers the fallback).
- **`flags`** — Bitfield altering the function's behavior. Supported flags (constants from `constants.txt`):
  - `RTF_AFFECTSOURCE` (value 1, the default) — If set, the damage source (the `target` of the calling actor, or the caller itself if `RTF_NOTMISSILE` is set) is affected by the thrust. If unset, the source is immune.
  - `RTF_NOIMPACTDAMAGE` (value 2) — If set, actors thrust by the blast do not inflict melee damage when they collide with walls or other actors. Collision physics still apply; this flag only suppresses the damage dealt on impact.
  - `RTF_NOTMISSILE` (value 4) — Treat the calling actor as the damage/thrust source directly. By default, the engine assumes the calling actor is a projectile and uses its `target` field as the source; setting this flag overrides that assumption (the caller becomes the source itself).
- **`fullthrustdistance`** — Inner radius (in map units) within which the full blast force is applied without falloff. Targets outside this radius receive linearly-reduced thrust as they approach the outer `distance` boundary. Default is 0 (no inner radius; thrust falls off from the center outward). The engine clamps this to `[0, distance - 1]`.

## Behavior notes

- **Server-side only:** Automatically no-ops on client machines in multiplayer (returns early without effect). No exemption for `+CLIENTSIDEONLY` actors.
- **Default parameter 1 fallback:** If `force` is 0, the engine substitutes 128 (a moderate blast).
- **Default parameter 2 fallback:** If `distance` is 0 or negative, the engine uses `abs(force)` instead, making the radius proportional to the blast strength.
- **`MF2_NODMGTHRUST` temporary negation:** Only when `RTF_NOTMISSILE` is **not** set (the default, "calling actor is a projectile" mode) and `self->target` is non-NULL: if `self->target` has `MF2_NODMGTHRUST` set, the engine clears it for the duration of the thrust call and restores it afterward. This prevents a shooter's own thrust-immunity flag from making the function a no-op on their own projectiles. When `RTF_NOTMISSILE` **is** set, this negation is skipped entirely — the caller itself is the source and its own `MF2_NODMGTHRUST` (if any) is left untouched.
- **Triggers terrain splashes:** `A_RadiusThrust` calls `P_CheckSplash(self, distance << FRACBITS)` after the thrust pass, identically to `A_Explode` — a terrain splash can still occur even though this function deals no damage.

## See also

- `A_Explode` — performs a radius attack with damage, plus optional nail/hitscan components; both wrap the same internal `P_RadiusAttack` engine function.
- `RadiusAttack` — the underlying ACS function exposing the same mechanism via script.
