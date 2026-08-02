# `void A_DamageTracer(int amount, name damagetype = "none", int flags = 0, class<Actor> filter = null, name species = "None", int src = AAPTR_DEFAULT, int inflict = AAPTR_DEFAULT)`

**Tier:** A
**Engine:** UZDoom 4.15pre / GZDoom-family — **does not exist in Zandronum**
**Provenance:** ZDoom Wiki `A_DamageTracer` (retrieved 2026-08-01, oldid=46970) + verified against the UZDoom source's `src/playsim/p_actionfunctions.cpp:4009-4026`.
**Bucket:** No Zandronum implementation; UZDoom defines it in `src/playsim/p_actionfunctions.cpp:4009` as a `DEFINE_ACTION_FUNCTION`.

Damages the calling actor's tracer actor by a specified amount. **This function does not exist in Zandronum** — the `tracer` pointer is available (used by `A_Tracer2` and other seeking-projectile functions), but Zandronum provides no damage-family action to target it. Negative amounts heal instead.

## Parameters

- **`amount`** — the amount of damage to inflict (required). Positive values damage; negative values heal. An amount of 1,000,000 or higher is treated specially and results in killing the target.
- **`damagetype`** — the name of the damage type (default `"none"`). Used when processing damage to determine if a special death state is triggered.
- **`flags`** — damage modifier flags combining any of the `DMSS_*` constants (default `0`). These include:
  - `DMSS_FOILINVUL` — damage an invulnerable target (requires an inflictor).
  - `DMSS_FOILBUDDHA` — kill a target protected by buddha2 (requires an inflictor).
  - `DMSS_NOPROTECT` — bypass damage-modifying items.
  - `DMSS_NOFACTOR` — ignore the target's damage factors.
  - `DMSS_AFFECTARMOR` — allow armor to absorb damage.
  - `DMSS_KILL` — inflict cumulative damage equal to the target's health plus amount.
  - `DMSS_EXFILTER` — invert the class filter (damage if **not** matching the class).
  - `DMSS_EXSPECIES` — invert the species filter (damage if **not** matching the species).
  - `DMSS_EITHER` — damage if either class **or** species matches (default is both must match).
  - `DMSS_INFLICTORDMGTYPE` — use the inflictor's damage type instead of the specified `damagetype`.
- **`filter`** — actor class to filter on; damage only actors matching this class (default `null`). No effect if `DMSS_EITHER` is absent.
- **`species`** — actor species to filter on; damage only actors matching this species (default `"None"`). No effect if `DMSS_EITHER` is absent.
- **`src`** — the source actor pointer (the one responsible for the damage, used for obituaries and mod handling). Default is `AAPTR_DEFAULT` (the calling actor).
- **`inflict`** — the inflictor pointer (the projectile/object doing the damage). Default is `AAPTR_DEFAULT` (the calling actor).

## Target

The calling actor's `tracer` pointer — assigned by homing-projectile functions like `A_Tracer2` and `A_SeekerMissile`. If `tracer` is NULL, the function returns without effect.

## Behavior

The function delegates all damage calculation to an internal helper that processes the `flags` and filter parameters. It respects all standard damage mechanics: invulnerability checks, armor, damage factors, and `god2`/`buddha2` protections (the latter GZDoom/UZDoom-family only).

## Zandronum non-availability

**Zandronum has no equivalent.** The `tracer` pointer is available for use by any actor, and `A_Tracer2` uses it for seeking behavior, but no Zandronum action function targets the tracer for damage. Code using `A_DamageTracer` will fail to compile in Zandronum with an "unknown identifier" error.

## Related functions

- **`A_DamageMaster`** — damages the calling actor's master (spawner). Zandronum version has only 2 parameters (`amount`, `damagetype`); GZDoom/UZDoom version supports the full 7-parameter set.
- **`A_DamageChildren`** — damages all actors with `master == self`. Zandronum version has only 2 parameters.
- **`A_DamageSiblings`** — damages all actors sharing the same master. Zandronum version has only 2 parameters.
- **`A_Tracer2`** — seeks toward the target stored in the `tracer` field; common source of the tracer assignment.
- **`A_SeekerMissile`** — another homing function that maintains the tracer.
