# `void A_DamageSelf(int amount, name damagetype = "none", int flags = 0, class<Actor> filter = null, name species = "None", int src = AAPTR_DEFAULT, int inflict = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `A_DamageSelf` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_DamageSelf&oldid=54180) + verified against the UZDoom source's `src/playsim/p_actionfunctions.cpp:3962-3978`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/playsim/p_actionfunctions.cpp:3962` (`DEFINE_ACTION_FUNCTION(AActor, A_DamageSelf)`).

**GZDoom/UZDoom only: does not exist in Zandronum.** Damages the calling actor by a specified amount; negative amounts heal instead. Supports flags, actor/species filtering, and configurable damage source/inflictor pointers.

## Availability

This action function **exists only in UZDoom and GZDoom-family engines.** It is not implemented in Zandronum. Related functions that exist in Zandronum (`A_DamageMaster`, `A_DamageChildren`, `A_DamageSiblings`) support only 2 parameters (`amount` and `damagetype`), without flags or filtering.

## Parameters

- **`amount`** — the amount of damage to inflict (required). Positive values damage; negative values heal. An amount of 1,000,000 or higher is treated specially and results in killing the actor regardless of health or any damage modifiers.
- **`damagetype`** — the name of the damage type to use when processing damage (default `"none"`). Determines which death state is triggered (e.g., `Death.Fire` for fire damage).
- **`flags`** — bitflags modifying the function's behavior (default 0). See "Flags" below.
- **`filter`** — actor class filter (default `null`). If non-null, the actor is only damaged if it belongs to this class (modified by `DMSS_EXFILTER` if set).
- **`species`** — species filter (default `"None"`). If not `"None"`, the actor is only damaged if its species matches (modified by `DMSS_EXSPECIES` if set).
- **`src`** — actor pointer constant for the damage source, i.e., the actor responsible for the damage (default `AAPTR_DEFAULT`, which is `self`). Common values: `AAPTR_NULL` (no source), `AAPTR_TARGET`, `AAPTR_MASTER`.
- **`inflict`** — actor pointer constant for the inflictor, i.e., the actor dealing the damage (normally a projectile or puff; default `AAPTR_DEFAULT`, which is `self`). Used to determine whether certain flags like `DMSS_FOILINVUL` apply.

## Flags

The `flags` parameter accepts the following named constants (combine with `|`):

- **`DMSS_FOILINVUL`** — damage bypasses invulnerability if an inflictor is provided. Ignored if the actor is a player.
- **`DMSS_FOILBUDDHA`** — if the damage would kill, the actor dies even under "buddha" effect if an inflictor is provided. Ignored if the actor is a player.
- **`DMSS_NOPROTECT`** — damage bypasses damage-modifying inventory items (e.g., protection powerups).
- **`DMSS_NOFACTOR`** — damage bypasses the actor's damage factors.
- **`DMSS_AFFECTARMOR`** — damage does not bypass armor — armor can reduce the damage.
- **`DMSS_KILL`** — inflicts damage equal to the actor's current health plus `amount`, killing the actor under normal conditions. Bypasses damage factors and armor but not damage-modifying items.
- **`DMSS_EXFILTER`** — inverts the class filter: the actor is only damaged if it does **not** match the class in `filter`.
- **`DMSS_EXSPECIES`** — inverts the species filter: the actor is only damaged if its species does **not** match `species`.
- **`DMSS_EITHER`** — the actor is damaged if either its class matches `filter` **or** its species matches `species` (instead of requiring both).
- **`DMSS_INFLICTORDMGTYPE`** — ignores the specified `damagetype` and uses the damage type of the `inflict` actor instead.

## Zandronum comparison

| Feature | Zandronum | UZDoom/GZDoom |
|---|---|---|
| Basic damage (amount) | No `A_DamageSelf` exists | Yes |
| Damagetype parameter | N/A | Yes |
| Flags (`DMSS_*`) | N/A | Yes (10+ flags) |
| Class filter | N/A | Yes |
| Species filter | N/A | Yes |
| Source pointer (`src`) | N/A | Yes (configurable) |
| Inflictor pointer (`inflict`) | N/A | Yes (configurable) |

Zandronum ships with `A_DamageMaster`, `A_DamageChildren`, and `A_DamageSiblings` — all taking only `amount` and `damagetype` parameters — but no `A_DamageSelf` variant at all.

## Behavior

The action invokes `DoDamage(self, inflictor, source, amount, damagetype, flags, filter, species)` with the specified parameters. The actual damage calculation respects all flags and filters; see the UZDoom source's `DoDamage` function for the full semantics.

### Healing behavior

Negative `amount` values heal the actor instead of damaging it, subject to the same flags and filters.

### Filter and species interaction

- If `filter` is non-null and the actor's class does not match, no damage occurs (unless `DMSS_EXFILTER` is set, which inverts the test).
- If `species` is not `"None"` and the actor's species does not match, no damage occurs (unless `DMSS_EXSPECIES` is set, which inverts the test).
- If both are specified, normally both conditions must pass (default AND logic); `DMSS_EITHER` changes this to OR logic.

## Related functions

- **`A_DamageMaster`** — **Zandronum and GZDoom-family**. Damages the calling actor's master; Zandronum version takes only 2 parameters (`amount`, `damagetype`). GZDoom version takes the same 7-parameter signature as `A_DamageSelf`.
- **`A_DamageChildren`** — **Zandronum and GZDoom-family**. Damages all actors with `master == self`. Zandronum version takes only 2 parameters.
- **`A_DamageSiblings`** — **Zandronum and GZDoom-family**. Damages all actors sharing the same master. Zandronum version takes only 2 parameters.
- **`A_DamageTarget`** — **GZDoom/UZDoom only**. Damages the calling actor's target.
- **`A_DamageTracer`** — **GZDoom/UZDoom only**. Damages the calling actor's tracer.
