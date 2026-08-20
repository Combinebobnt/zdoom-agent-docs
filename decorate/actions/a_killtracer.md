# `void A_KillTracer(name damagetype = "none", int flags = 0, class<Actor> filter = "none", name species = "none", int src = AAPTR_DEFAULT, int inflict = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `A_KillTracer` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_KillTracer&oldid=46807) + verified against the UZDoom source's `src/playsim/p_actionfunctions.cpp:4193-4209`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_KillTracer)` in the UZDoom source's `src/playsim/p_actionfunctions.cpp`.

Kills the calling actor's tracer with optional filters, damage type customization, and invulnerability bypass. **This action function does not exist in Zandronum** — Zandronum only implements `A_KillMaster`, `A_KillChildren`, and `A_KillSiblings`, with no tracer-related kill variants.

## Engine-family divergence

Zandronum's simplified kill functions take only a `damagetype` parameter and use `DMG_NO_ARMOR | DMG_NO_FACTOR` unconditionally. UZDoom/GZDoom-family engines extend all kill-family functions with configurable flags, actor/species filters, and source/inflictor pointer control. **Code written for the wiki's GZDoom/UZDoom version will not compile in Zandronum** — attempting to pass flags, filter, or species parameters to `A_KillMaster`, `A_KillChildren`, or `A_KillSiblings` in Zandronum will fail with "too many arguments" parse errors.

## Parameters (UZDoom/GZDoom-family)

- **`damagetype`** — the name of the damage type to apply. Defaults to `"none"`. Determines which specialized death state the target enters (e.g., `Death.Fire`), or falls back to the pain state if the target has the `NODAMAGE` flag.

- **`flags`** — bitmap controlling kill behavior. Defaults to `0` (no flags). Supported flags:
  - `KILS_FOILINVUL` — bypasses the target's `INVULNERABLE` flag; applies `DMG_FOILINVUL` flag to damage.
  - `KILS_FOILBUDDHA` — bypasses the target's `BUDDHA` status; applies `DMG_FOILBUDDHA` flag to damage.
  - `KILS_KILLMISSILES` — if the target is a missile (has `MF_MISSILE` set), calls `P_ExplodeMissile` *in addition to* the normal health-damage step below (respects invulnerability and buddha unless the appropriate foil flags are set; never explodes a missile that has the `NODAMAGE` flag, and there is no flag to override that specific gate).
  - `KILS_NOMONSTERS` — skips the health-damage step (`P_DamageMobj`) entirely, for **any** target type, not just non-missile actors. Combined with `KILS_KILLMISSILES`, this is what limits the net effect to missile explosion only; without it, a missile that qualifies for `KILS_KILLMISSILES` is both exploded and damaged in the same call.
  - `KILS_EXFILTER` — inverts the `filter` class check (kills the target if its class does **not** match the filter).
  - `KILS_EXSPECIES` — inverts the `species` check (kills the target if its species does **not** match the specified species).
  - `KILS_EITHER` — relaxes filter/species matching to OR (kills if class **or** species matches) instead of AND (kills if class **and** species match).

- **`filter`** — actor class to match for killing. Defaults to `"none"` (no class filtering; all classes accepted). The target is killed only if its class **exactly matches** this class — this is a strict equality check on the target's own class, not an ancestor/subclass check, so a `filter` of a base class will not match instances of a class derived from it.

- **`species`** — actor species to match for killing. Defaults to `"none"` (no species filtering; all species accepted). The target is killed only if its species matches the specified name.

- **`src`** — the actor pointer responsible for the damage (for credit purposes). Defaults to `AAPTR_DEFAULT` (the calling actor). Resolves via `COPY_AAPTR`, accepting pointers like `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER`.

- **`inflict`** — the actor pointer treated as the inflictor for damage processing. Defaults to `AAPTR_DEFAULT` (the calling actor). The target's damage factors and flag checks apply to this actor's properties, not necessarily the calling actor's.

## Behavior

When called with the tracer pointer non-NULL:

1. **Filter/species checks** — if both a `filter` class and `species` name are provided (or only one), both must match the target (unless `KILS_EITHER` is set, in which case either match suffices). `KILS_EXFILTER` and/or `KILS_EXSPECIES` invert their respective checks. Class matching is a strict class-equality check (see `filter` above), and species matching is a strict name-equality check — neither is hierarchy-aware.
2. **If filter/species pass, up to two independent steps run in sequence (they are not mutually exclusive alternatives):**
   - **Missile explosion** — if `KILS_KILLMISSILES` is set and the target has `MF_MISSILE` set, the engine calls `P_ExplodeMissile` (triggering its death state, puffs, etc.), gated on the target *not* having `INVULNERABLE` (unless `KILS_FOILINVUL`), *not* having `BUDDHA` (unless `KILS_FOILBUDDHA`), and *not* having the `NODAMAGE` flag — this last gate has no override.
   - **Health damage** — unless `KILS_NOMONSTERS` is set, the target (whether or not it is a missile, and whether or not it was just exploded above) additionally receives damage equal to its current health via `P_DamageMobj`, with `DMG_NO_ARMOR | DMG_NO_FACTOR` applied automatically (plus `DMG_FOILINVUL`/`DMG_FOILBUDDHA` if flags request it). This step runs *in addition to*, not instead of, the missile-explosion step: a missile target with `KILS_KILLMISSILES` set is both exploded and damaged unless `KILS_NOMONSTERS` is also set.

If the tracer is NULL, the function returns without effect.

## Related functions

- **`A_KillTarget`** — kills the calling actor's target instead of tracer; same parameter set.
- **`A_KillMaster`** — kills the calling actor's master (spawner). **Zandronum version takes only `damagetype`**; UZDoom/GZDoom version has the full extended parameter set.
- **`A_KillChildren`** — kills all actors whose master pointer is the calling actor. **Zandronum version takes only `damagetype`**; UZDoom/GZDoom version has the full extended parameter set.
- **`A_KillSiblings`** — kills all other actors sharing the same master. **Zandronum version takes only `damagetype`**; UZDoom/GZDoom version has the full extended parameter set.
- **`A_DamageTracer`** — damages (but does not necessarily kill) the tracer with the same extended parameter set; UZDoom/GZDoom-family only.
- **`A_RemoveTracer`** — removes (destroys without death animation) the tracer; UZDoom/GZDoom-family only.
