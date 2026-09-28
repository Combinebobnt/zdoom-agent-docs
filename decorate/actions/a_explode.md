# `A_Explode(int damage, int distance, int flags, bool alert, int fulldamagedistance, int nails, int naildamage, class<Actor> pufftype)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Explode` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Explode&oldid=54802) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1010-1061` and actor definition in `wadsrc/static/actors/actor.txt:268`; flag bits and splash behavior from `src/p_local.h:539-542` and `src/p_mobj.cpp:7052-7061`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Explode)` in `src/thingdef/thingdef_codeptr.cpp`.

Performs a radius attack (explosion), optionally with additional nail/hitscan components, across the given distance. A wrapper around the engine's internal `P_RadiusAttack` function.

## Engine-family divergence

**This page describes the Zandronum implementation, which is significantly simpler than the newer ZDoom-family versions.** The ZDoom Wiki describes upstream ZDoom/GZDoom/UZDoom features including:
- **Return value:** ZDoom-family versions return the count of actors damaged; Zandronum's `A_Explode` returns nothing (void).
- **Extra flags:** The wiki documents `XF_EXPLICITDAMAGETYPE`, `XF_NOSPLASH`, `XF_THRUSTZ`, `XF_THRUSTLESS`, `XF_NOALLIES`, `XF_CIRCULAR`, `XF_CIRCULARTHRUST` — none of which exist in Zandronum. Only `XF_HURTSOURCE` and `XF_NOTMISSILE` are defined in the Zandronum `constants.txt`.
- **9th parameter:** The wiki shows a `name damagetype` parameter; Zandronum's `A_Explode` uses the actor's own `DamageType` property (no customization via parameter).
- **Parameter types:** Zandronum uses `int` for `distance` and `fulldamagedistance`; the wiki shows `double`.

On Zandronum an undefined upstream constant is an unknown-identifier error that aborts loading. A mod that re-defines them itself (e.g. `const int` with the upstream values) passes the raw bits straight to `P_RadiusAttack`, which only reads bits 1, 2, 4 and 8 (`RADF_*`, `src/p_local.h:539-542`). Most re-defined flags are then silently ignored, but `XF_EXPLICITDAMAGETYPE` (upstream value 8) lands on `RADF_NODAMAGE` and turns the explosion into a damage-free thrust like `A_RadiusThrust`.

Confirmed directly against UZDoom's `A_Explode` (`wadsrc/static/zscript/actors/attacks.zs:591`, `int A_Explode(int damage = -1, double distance = -1.0, int flags = XF_HURTSOURCE, bool alert = false, double fulldamagedistance = 0.0, int nails = 0, int naildamage = 10, class<Actor> pufftype = "BulletPuff", name damagetype = "none", double nailrange = MISSILERANGE)`): the function does return an `int` actor-damaged count; all seven extra flags (`XF_EXPLICITDAMAGETYPE`, `XF_NOSPLASH`, `XF_THRUSTZ`, `XF_THRUSTLESS`, `XF_NOALLIES`, `XF_CIRCULAR`, `XF_CIRCULARTHRUST`) are defined (`wadsrc/static/zscript/constants.zs:283-291`) and functional; the 9th parameter is a `name damagetype` as the wiki describes; and `distance`/`fulldamagedistance` are `double`, not `int`. UZDoom also adds a 10th parameter not covered by the wiki excerpt this page cites, `double nailrange = MISSILERANGE`, which sets the line-attack range used for each nail (Zandronum's fixed nail attacks always use `MISSILERANGE` with no way to override it).

## Engine-family divergence: no client/server authority split

The "Server-side only" bullet under Behavior notes below describes Zandronum's client/server netcode split. UZDoom's `A_Explode` (`wadsrc/static/zscript/actors/attacks.zs:591-640`) contains no network-role branch at all — no check for local-player ownership, no server/client split, and no `+CLIENTSIDEONLY`-gated early return. This matches the cohort-wide pattern: UZDoom's source tree has zero `NETWORK_InClientMode`/`SERVERCOMMANDS_*` occurrences anywhere (confirmed by tree-wide grep). On UZDoom, the radius attack, nail attacks, splash check, and alert all simply run to completion wherever the action executes, regardless of which machine that is.

## Parameters

- **`damage`** — Damage inflicted at the center of the explosion. If negative (default `-1`), the actor's `ExplosionDamage` property is used instead (default 128 if unset). When `damage` is negative, `alert` is forced to `false` and `distance` and `flags` are replaced with property values (see below); `fulldamagedistance`, `nails`, `naildamage` and `pufftype` are still used as passed.
- **`distance`** — Radius of the explosion. Damage falls off linearly with distance. If `distance` is 0 or negative, defaults to `damage`. **Overflow warning:** a radius larger than 32767 overflows the fixed-point blockmap search box (`bombdistance << FRACBITS`, `src/p_map.cpp:5740`), so the search area wraps (empty or truncated) and targets inside the intended radius can be missed.
- **`flags`** — Bitfield altering the function's behavior. Supported flags (constants from `constants.txt`):
  - `XF_HURTSOURCE` (value 1, the default) — If set, the explosion's source and the calling actor itself can be damaged by it. If unset (`flags = 0`), both are skipped. The source is the caller's `target` (normally the shooter of a projectile), or the caller itself with `XF_NOTMISSILE`.
  - `XF_NOTMISSILE` (value 4) — Treat the calling actor as the damage source. By default, the engine assumes the calling actor is a projectile and uses its `target` field as the source; setting this flag overrides that assumption.
  - When `damage` is negative, `flags` is ignored in favor of the actor's `DontHurtShooter` property (if present, behaves as `flags = 0`; otherwise as `flags = 1`).
- **`alert`** — Whether the explosion triggers sound alerts to nearby monsters (calls `P_NoiseAlert`). Only fires when the caller's `target` is a player; the sound spreads from the explosion's sector and alerts monsters to that player. Forced to `false` if `damage` is negative. Default is `false`.
- **`fulldamagedistance`** — Inner radius within which the full damage is inflicted without falloff. Targets outside this radius take linearly-reduced damage. Default is 0 (no inner radius; damage falls off immediately). Clamped to `[0, distance - 1]` in the engine.
- **`nails`** — Number of hitscan attacks performed in a ring around the explosion center. Each nail fires horizontally from 8 units above the actor's mid-height (for a non-player caller; a player uses its `AttackZOffset`) in evenly-spaced directions (360 / `nails` degrees apart), starting at map angle 0 regardless of the actor's facing. Nails fire before the radius attack. Default is 0 (no nail attack). Each nail uses the same `naildamage` and `pufftype`. Setting this to 30 emulates SMMU's `A_NailBomb` action.
- **`naildamage`** — Damage per individual nail attack. Only used if `nails > 0`. Default is 10.
- **`pufftype`** — The actor class to spawn as a puff/impact effect for nail attacks. Default is `"BulletPuff"`. Ignored if `nails == 0`.

## Behavior notes

- **Server-side only:** Automatically no-ops on client machines in multiplayer (returns early without damage or thrust). No `+CLIENTSIDEONLY` exemption exists.
- **Negative damage with property fallback:** If `damage < 0`, the function reads `ExplosionDamage` and `ExplosionRadius` properties from the actor's definition. If `ExplosionRadius` was never set, the radius falls back to the resolved damage value. An explicit `ExplosionRadius` of 0 or less is not re-defaulted: `P_RadiusAttack` then returns immediately without damaging anything (nails and the splash check still run; `alert` is already forced off in this path).
- **Splash effects:** The splash check always runs (there is no `XF_NOSPLASH` equivalent in Zandronum; the wiki describes this feature as upstream-only). A splash still needs the caller to be near the floor of a liquid terrain in a sector without `Transfer_Heights`. `A_Explode` passes `distance << FRACBITS` and `P_CheckSplash` shifts by `FRACBITS` again (`src/p_mobj.cpp:7052-7061`), which overflows 32-bit `int`, so in practice the height allowance is 0 and only a caller at or below floor height splashes.
- **Nail attack aiming:** Nail attacks fire horizontally (0 vertical aim) and do not use the actor's target for direction — they form a full ring based on actor position and the `nails` parameter.
- **Thrust is computed from pre-`DamageFactor` damage:** Inside `P_RadiusAttack` (`src/p_map.cpp:5833-5887`), the falloff-adjusted damage (`points`) is used directly for the knockback/thrust calculation (`thrust = points * 0.5f / thing->Mass`, `p_map.cpp:5887`). The actual HP damage dealt goes through `P_DamageMobj` separately, which is where the victim's `DamageFactor` gets applied (`src/p_interaction.cpp:1339-1342`) — the resulting reduced/amplified damage (`newdam`) is never fed back into the thrust calculation. **Consequence: an actor with `DamageFactor` `0.0` for the explosion's damage type takes zero HP damage but still receives full knockback.** To suppress both damage and thrust for a given actor, use `radiusdamagefactor 0.0` on that actor instead (see [radiusdamagefactor](../notes/radiusdamagefactor-actor.md)), which scales the pre-`DamageFactor` `points` value itself and therefore zeroes both. `MF2_NODMGTHRUST` on the bomb spot or its source also suppresses thrust (for everyone), independent of any damage factor.

## See also

- `A_RadiusThrust` — applies radial knockback without damage (both wrap the same internal `P_RadiusAttack` engine function).
- `A_Explode512` — Strife-specific variant; see `src/g_strife/a_thingstoblowup.cpp`.
- [radiusdamagefactor](../notes/radiusdamagefactor-actor.md) — per-victim property that scales both damage and thrust together, unlike `DamageFactor`.
