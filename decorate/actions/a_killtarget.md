# `void A_KillTarget(name damagetype = "none", int flags = 0, class<Actor> filter = null, name species = "None", int src = AAPTR_DEFAULT, int inflict = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `A_KillTarget` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_KillTarget&oldid=45098) + verified against the UZDoom source's `src/playsim/p_actionfunctions.cpp:4170-4186`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_KillTarget)` in the UZDoom source's `src/playsim/p_actionfunctions.cpp`.

Kills the calling actor's target pointer, optionally applying class/species filters and configurable damage source/inflictor pointers. Damage is applied without armor or damage factor modifiers, optionally bypassing invulnerability.

## Engine-family divergence

**This action exists only in UZDoom/GZDoom-family engines.** It does not exist in Zandronum 3.2.1 (confirmed by tree-wide grep of `src/`). Zandronum's DECORATE action function set is limited to the Master/Children/Siblings pointer variants, without Target or Tracer support.

## Parameters

- **`damagetype`** — The name of the damage type to use when processing the kill. This determines which death state the target enters (or pain state if the target has the `NODAMAGE` flag). Default is `"none"` (generic damage type).

- **`flags`** — Bitwise-OR'd combination of kill-behavior flags (see Flags section below). Default `0`. These flags control invulnerability bypass, missile handling, monster/missile filter behavior, and filter inversion logic.

- **`filter`** — Actor class name filter. If specified (not `null`), the target is only killed if its class matches this filter. Default is `null` (no class filter; any actor is a candidate).

- **`species`** — Species name filter. If specified (not `"None"`), the target is only killed if its species name matches this value. Default is `"None"` (no species filter).

- **`src`** — The actor pointer to use as the damage source (the "inflictor" in traditional Doom terminology, responsible for the kill). This determines which monster gets credit for a kill in multiplayer scoring and which is used for monster-to-monster prejudice rules. Specified as an `AAPTR_*` constant. Default is `AAPTR_DEFAULT` (the calling actor).

- **`inflict`** — The actor pointer to use as the inflictor (the intermediary actor whose flags may affect damage resistance). This actor's invulnerability/buddha/NODAMAGE flags are checked instead of the source's. Default is `AAPTR_DEFAULT` (the calling actor's own flags determine behavior), confirmed by the native declaration in the UZDoom source's `wadsrc/static/zscript/actors/actor.zs`.

## Flags

- **KILS_FOILINVUL** — Kill actors even if they have the `INVULNERABLE` flag set. Without this flag, the target's `MF2_INVULNERABLE` is respected and the kill fails.

- **KILS_KILLMISSILES** — If the target is a missile (has `MF_MISSILE`), force it to enter its death state. Missiles normally cannot be killed by standard damage calls and this flag overrides that immunity (though the missile must not have `MF5_NODAMAGE`).

- **KILS_NOMONSTERS** — Do not target monsters with this function; only missiles are affected. Alone, this makes the function do nothing, but can be combined with `KILS_KILLMISSILES` to only kill missiles and exclude monsters.

- **KILS_FOILBUDDHA** — Kill actors even if they have the Buddha effect (the `MF7_BUDDHA` flag, which normally prevents damage from killing the actor). Without this flag, the target's Buddha immunity is respected.

- **KILS_EXFILTER** — Invert the class-name filter logic. The target is only killed if its class name **does not** match the `filter` value. Has no effect if `filter` is `null` (no filter specified).

- **KILS_EXSPECIES** — Invert the species filter logic. The target is only killed if its species **does not** match the `species` value. Has no effect if `species` is `"None"` (no filter specified).

- **KILS_EITHER** — Require only one filter to match instead of both. Normally, if both `filter` and `species` are specified (not their defaults), the target must match **both** to be killed. With `KILS_EITHER`, the target is killed if it matches **either** the class name or species, whichever is specified.

## Behavior

When called, the action:

1. **Tests the filters** — If a `filter` and/or `species` are specified, checks whether the target's class name and/or species match (or don't match, if `KILS_EXFILTER`/`KILS_EXSPECIES` are set). If the target fails the filter test, the action returns without effect.

2. **Determines damage flags** — Always uses `DMG_NO_ARMOR | DMG_NO_FACTOR`. Optionally adds `DMG_FOILINVUL` (if `KILS_FOILINVUL` is set) and `DMG_FOILBUDDHA` (if `KILS_FOILBUDDHA` is set).

3. **Handles missiles** — If the target is a missile (has `MF_MISSILE`) and `KILS_KILLMISSILES` is set, and the missile isn't protected by invulnerability/Buddha (unless foiled by the corresponding flag) and lacks `MF5_NODAMAGE`, calls `P_ExplodeMissile` to destroy it. This call always passes `NULL` for both source and inflictor, ignoring the `src`/`inflict` parameters.

4. **Applies damage** — Unless `KILS_NOMONSTERS` is set, separately calls `P_DamageMobj` with the target's current health as the damage amount and the resolved `src`/`inflict` pointers, killing it if no invulnerability/buddha effects prevent it. This step is independent of step 3, not an alternative to it: if the target is a missile, `KILS_KILLMISSILES` is set, and `KILS_NOMONSTERS` is clear, both `P_ExplodeMissile` and `P_DamageMobj` run against the same target in the same call.

## Target relationship

The target pointer is typically established via `A_SetTarget`, a hitscan attack that acquires a target via line-of-fire, or a melee attack that targets a nearby threat. If the calling actor's target is NULL at the time of the call, the action returns without effect.

## Null pointer safety

If the calling actor's target pointer is NULL, or if the target pointer set via `src` or `inflict` is NULL, the function handles it gracefully — no error or crash occurs.

## Comparison with Zandronum

The **Zandronum wiki has no `A_KillTarget` entry** because this function does not exist in Zandronum's codebase. Zandronum provides only:
- `A_KillMaster` — kills the calling actor's spawner
- `A_KillChildren` — kills all actors spawned by the calling actor
- `A_KillSiblings` — kills all actors sharing the same spawner

These simpler functions do not support flags, filters, or source/inflictor pointer configuration — they take only an optional `damagetype` parameter.

## Related actions

- **`A_KillMaster`** — kills the calling actor's master pointer (Zandronum-available).
- **`A_KillChildren`** — kills all actors with `master == self` (Zandronum-available).
- **`A_KillSiblings`** — kills all actors sharing the same master (Zandronum-available).
- **`A_KillTracer`** — kills the calling actor's tracer pointer (UZDoom/GZDoom-family only, same parameters and flags as `A_KillTarget`).
- **`A_DamageTarget`** — damages (but not necessarily kills) the target by a fixed amount (UZDoom/GZDoom-family only).
- **`A_RemoveTarget`** — removes the target without death animation (UZDoom/GZDoom-family only).
