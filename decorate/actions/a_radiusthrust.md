# `void A_RadiusThrust(int force = 128, int distance = -1, int flags = RTF_AFFECTSOURCE, int fullthrustdistance = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_RadiusThrust` (retrieved 2026-08-01, oldid=54717) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1076-1109` and internal `P_RadiusAttack` in `src/p_map.cpp:5728-5910`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RadiusThrust)` in `src/thingdef/thingdef_codeptr.cpp`.

Applies a radial thrust (knockback) to nearby actors without damage, pushing them away from the calling actor's center. This is equivalent to `A_Explode` with only the thrust component and no damage. The underlying mechanism is the engine's internal `P_RadiusAttack` function.

## Zandronum vs. ZDoom-family divergence

**This page describes the Zandronum implementation, which has fewer parameters and flags than the newer ZDoom-family versions.** The ZDoom Wiki describes upstream ZDoom/GZDoom/UZDoom features including:

- **5th parameter (`species`):** The wiki documents a `name species` parameter to limit thrust to actors of a specific species; Zandronum's `A_RadiusThrust` does not support this parameter at all. The function always thrusts all eligible actors regardless of species.
- **Extra flags:** The wiki documents `RTF_THRUSTZ` and `RTF_CIRCULARTHRUST` — neither exists in Zandronum. Only three flags are defined in the Zandronum `constants.txt`: `RTF_AFFECTSOURCE` (1), `RTF_NOIMPACTDAMAGE` (2), and `RTF_NOTMISSILE` (4).
- **Parameter types and defaults:** Zandronum uses `int` for all numeric parameters; the ZScript definition shown on the wiki uses `double` for distance parameters.

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
