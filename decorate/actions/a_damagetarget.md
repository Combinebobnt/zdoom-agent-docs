# `void A_DamageTarget(int amount [, name damagetype [, int flags [, class<Actor> filter [, name species [, int src [, int inflict]]]]]])`

**Tier:** A
**Engine:** UZDoom 4.15pre / GZDoom-family — does not exist in Zandronum
**Provenance:** ZDoom Wiki `A_DamageTarget` (retrieved 2026-08-01, oldid=46968) + verified against the UZDoom source's `src/playsim/p_actionfunctions.cpp:3985-4002`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_DamageTarget)` in the UZDoom source's `src/playsim/p_actionfunctions.cpp:3985`.

Damages the calling actor's target pointer by a specified amount. Negative amounts heal instead. This function cannot be used in Zandronum — only GZDoom-family engines (UZDoom, GZDoom) implement it. **See "Zandronum alternatives" below** if you are targeting Zandronum.

## Parameters

- **`amount`** — the amount of damage to inflict (required). Positive values damage; negative values heal. An amount of 1,000,000 or higher is treated specially via the `TELEFRAG_DAMAGE` mechanism and results in killing the target regardless of health or damage resistance.

- **`damagetype`** — the name of the damage type to use (default `"none"`). Passed to the damage calculation function to determine whether a special death state (e.g., `Death.Fire`) is triggered instead of the default `Death` state. Death states are resolved in the target actor's state table.

- **`flags`** — bitfield of `DMSS_*` flags controlling damage behavior (see Flags section below). Default `0`. The following flags are supported:
  - `DMSS_FOILINVUL` — damage bypasses actor invulnerability; requires an inflictor actor set via the `inflict` parameter.
  - `DMSS_FOILBUDDHA` — if damage is sufficient to kill the actor, it dies even under `buddha` effect; requires an inflictor.
  - `DMSS_NOPROTECT` — damage bypasses damage-modifying powerups and inventory items in the target's possession.
  - `DMSS_NOFACTOR` — damage bypasses the target's damage factors (properties like `DamageFactor`).
  - `DMSS_AFFECTARMOR` — damage does **not** bypass armor (the default is to bypass it); armor can absorb/reduce damage.
  - `DMSS_KILL` — inflicts damage equal to the sum of the actor's current health and amount, guaranteed to kill. Bypasses damage factors and armor (but not damage-modifying items).
  - `DMSS_EXFILTER` — inverts class filter logic; the actor is only damaged if its class **does not** match the `filter` parameter.
  - `DMSS_EXSPECIES` — inverts species filter logic; the actor is only damaged if its species **does not** match the `species` parameter.
  - `DMSS_EITHER` — the actor is damaged if either its class name matches `filter` **or** its species matches `species` (OR logic instead of AND).
  - `DMSS_INFLICTORDMGTYPE` — ignores the `damagetype` parameter and uses the damage type of the inflictor actor instead.

- **`filter`** — the actor class to damage (default `"none"`/null). The actor is only damaged if its class name matches this value. Inverted by `DMSS_EXFILTER`.

- **`species`** — the actor species to damage (default `"none"`). The actor is only damaged if its species matches this value. Inverted by `DMSS_EXSPECIES`.

- **`src`** — the actor responsible for the damage (source/attacker), as an actor pointer enum (default `AAPTR_DEFAULT`, the calling actor itself). `AAPTR_NULL` means no source. This is used for obituary and client-side sound/blood effects.

- **`inflict`** — the actor doing the damage (the inflictor), as an actor pointer enum (default `AAPTR_DEFAULT`, the calling actor itself). `AAPTR_NULL` means no inflictor — this disables `DMSS_FOILINVUL` and `DMSS_FOILBUDDHA` even if set, since those flags require a real inflictor to function.

## Behavior

### Target pointer

The function operates on `self->target`, the calling actor's current target pointer. If the target is NULL, the function silently returns with no effect.

### Damage calculation and application

Damage is processed through the shared `DoDamage` helper, which applies the following steps:
1. Resolve the `src` and `inflict` actor pointers using `COPY_AAPTR`.
2. Apply the damage via the engine's damage handler, respecting flags, filters, and damage factors.
3. Perform invulnerability/buddha/armor/factor checks as appropriate for the combination of flags set.

### Class and species filtering

- If `filter` is set and `DMSS_EITHER` is not set, the target is damaged only if its class matches `filter` exactly (or not, if `DMSS_EXFILTER` inverts the check).
- If `species` is set and `DMSS_EITHER` is not set, the target is damaged only if its species matches `species` exactly (or not, if `DMSS_EXSPECIES` inverts the check).
- If both `filter` and `species` are set and `DMSS_EITHER` is not set, both checks must pass (AND logic).
- If `DMSS_EITHER` is set, the target is damaged if **either** check passes (OR logic).

### Dead targets

If the target's health is already 0 or below, or if it is otherwise already dead, no damage occurs and the function silently returns.

## Zandronum alternatives

**This action does not exist in Zandronum.** Zandronum provides a drastically simplified set of damage actions:

| Name | Parameters | What it damages |
|---|---|---|
| `A_DamageMaster` | `amount, damagetype` | `master` pointer |
| `A_DamageChildren` | `amount, damagetype` | All actors with `master == self` |
| `A_DamageSiblings` | `amount, damagetype` | All actors sharing the same `master` |

**None of these support the `flags`, `filter`, `species`, `src`, or `inflict` parameters that A_DamageTarget provides.** If you need to damage a target in Zandronum with advanced filtering or special damage modes, you must either:
- Use `A_DamageMaster` + `A_SpawnItemEx` to set up master relationships instead of relying on the natural `target` pointer.
- Implement filtering logic in ACS code and call `A_SetDamageType` / custom helper functions.
- Design your actor relationships to use the simpler `master` pointer semantics instead.

## Related functions

- **`A_DamageTracer`** — damages the `tracer` pointer with the same extended parameter set. Functionally identical except for pointer substitution.
- **`A_DamageMaster`** — damages the `master` pointer. **Zandronum only: 2-parameter simplified version** (see table above).
- **`A_DamageChildren`** — damages all child actors (`master == self`). **Zandronum only: 2-parameter simplified version.**
- **`A_DamageSiblings`** — damages all sibling actors (shared `master`). **Zandronum only: 2-parameter simplified version.**
- **`A_KillTarget`** — kills the target outright (damage = target's health).
- **`A_GiveToTarget`** — gives inventory items to the target (UZDoom/GZDoom-family only).
- **`A_TakeFromTarget`** — removes inventory items from the target (UZDoom/GZDoom-family only).

## Engine availability

This action exists only in UZDoom/GZDoom-family engines (GZDoom 2.3.1+, UZDoom 4.15pre+). It does not exist in Zandronum, which provides only the Master/Children/Siblings damage variants without advanced filtering or control-pointer parameters. **Zandronum users cannot compile or use `A_DamageTarget`** — attempting to call it will result in a parse error ("unknown action function").
