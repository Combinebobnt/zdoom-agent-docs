# `void A_DamageChildren(int amount, name damagetype = "none")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_DamageChildren` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_DamageChildren&oldid=46971) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4483-4507` and `wadsrc/static/actors/actor.txt:281`; telefrag, network, `SXF_SETMASTER` and parse-error corrections from `src/p_interaction.cpp:1183, 1212-1220, 1261, 1295-1352, 1746`, `src/g_shared/a_pickups.cpp:234`, `src/thingdef/thingdef_codeptr.cpp:2439-2454`, `src/thingdef/thingdef_states.cpp:430` and `src/thingdef/thingdef_parse.cpp:91-97`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:4483` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_DamageChildren)`).

Damages all of the calling actor's child actors (those with `master == self`) by a specified amount; negative amounts heal instead. **Zandronum only: drastically simplified compared to GZDoom/UZDoom, which support flags and actor/species filters.**

## Parameters

- **`amount`** — the amount of damage to inflict (required). Positive values damage; negative values heal. An amount of 1,000,000 or higher (`TELEFRAG_DAMAGE`) is treated specially. On UZDoom it kills the target regardless of damage resistance unless the target has `+LAXTELEFRAGDMG`. On Zandronum it only skips the invulnerability checks, and damage factors still scale it (see "Telefrag damage" below).
- **`damagetype`** — the name of the damage type to use when processing damage (default `"none"`). Passed to `P_DamageMobj` as the `mod` parameter, which determines whether a special death state (e.g., `Death.Fire`) is triggered instead of the default `Death` state. Death states for custom damage types are resolved in the target actor's state table.

## Behavior

When called, the action iterates through all actors in the game world and damages those where the actor's `master` pointer matches the calling actor's address.

For each child actor found:
- **Positive damage:** `P_DamageMobj(child, self, self, amount, DamageType, DMG_NO_ARMOR)` for `amount > 0`
- **Negative damage (healing):** `P_GiveBody(child, -amount)` for `amount < 0` — but **see the bug note below**
- **Zero damage:** Silent no-op (neither branch executes)

### Children definition

A child actor is defined by having its `master` field point to the calling actor. This relationship is commonly established via `A_SpawnItemEx(..., SXF_SETMASTER)` or by directly assigning the spawner's address to the `master` field. On UZDoom, `SXF_SETMASTER` sets `master` unconditionally. On Zandronum it only takes effect when the spawned actor and the spawner (or, for a missile spawner, the first non-missile up its `target` chain) are both `+ISMONSTER` (`thingdef_codeptr.cpp:2439-2454`); any other spawn gets no master link.

### Damage behavior

- **Invulnerability:** A child with `+INVULNERABLE` **will not be harmed**. The function uses only `DMG_NO_ARMOR` and never passes `DMG_FORCED` or `DMG_FOILINVUL`, so `P_DamageMobj` rejects the damage when the target has the `MF2_INVULNERABLE` flag set. Zandronum's `P_DamageMobj` does support a `DMG_FOILINVUL` flag internally (`src/p_local.h:606`, used by other callers such as `A_BFGSpray`), but `A_DamageChildren` has no flags parameter to request it, so this action function itself has no way to bypass invulnerability. This is not absolute for a non-player target: `P_DamageMobj` only rejects the damage when the inflictor lacks `+FOILINVUL`, and the inflictor here is the calling actor, so a caller with `+FOILINVUL` bypasses the target's invulnerability (`p_interaction.cpp:1212-1220`).
- **Armor:** Damage bypasses armor entirely — the `DMG_NO_ARMOR` flag prevents armor from reducing the damage.
- **Damage factors:** Unlike `A_KillChildren`, damage factors **are applied** — properties like `DamageFactor` and damage-type-specific factor tables will modify the final damage taken. There is no `DMSS_NOFACTOR`-equivalent flag in Zandronum.
- **Telefrag damage:** If `amount >= 1000000` (the `TELEFRAG_DAMAGE` constant), the `+INVULNERABLE` and spectral checks are skipped (`p_interaction.cpp:1183, 1212`). On Zandronum that is all it skips: `DamageFactor`, per-damage-type factors and protection powerups still reduce it (`p_interaction.cpp:1295-1352`), so a resistant child can survive it. On UZDoom the factor and protection block is skipped unless the child has `+LAXTELEFRAGDMG`, so it kills regardless of resistance. A `+DORMANT` child takes no damage on either engine (`p_interaction.cpp:1261`).

### Healing behavior

Negative `amount` values trigger the healing path via `P_GiveBody`, which:
- Returns `false` (no effect) if the target is already dead or has health ≤ 0.
- Clamps healing to the target's maximum health (calculated at the moment of the call; includes any health bonuses).
- Applies the prosperity cheat if active on the target player.

**BUG (Zandronum 3.2.1, still present at 3.3-alpha):** The `amount` parameter is negated and **reassigned inside the iteration loop** (`amount = -amount;` in `thingdef_codeptr.cpp:4502`, identical pattern to `A_DamageSiblings`). After the first matching child is processed (even one that is dead or already at full health), `amount` is positive, so all *subsequent* children found in the same call are **damaged** instead of healed. Calling it again does not help, since every call walks all children. `A_DamageSiblings` has the identical in-loop negation, so it is no substitute. To heal several children, have each child heal itself from its own states, for example with the `HealThing` action special.

## Engine-family divergence: healing-reassignment bug does not reproduce on UZDoom

**UZDoom does not have the Zandronum healing bug described above.** UZDoom's `A_DamageChildren` (`src/playsim/p_actionfunctions.cpp:4057-4080`) iterates all thinkers and, for each matching child, calls a shared `DoDamage(mo, inflictor, source, amount, damagetype, flags, filter, species)` helper (`p_actionfunctions.cpp:3922-3955`), passing the loop's `amount` **by value** on every call. The negation for the healing path (`amount = -amount;`) happens only inside `DoDamage`'s own local parameter copy and is discarded when that call returns — it never mutates the outer loop variable. Each child in a single `A_DamageChildren` call therefore always receives the original, correctly-signed `amount`, so healing (or damaging) multiple children in one call works reliably on UZDoom. Additionally, UZDoom's `A_DamageChildren` takes the full `(amount, damagetype, flags, filter, species, src, inflict)` signature described by the wiki (see the comparison table below), including `DMSS_FOILINVUL`/`DMSS_FOILBUDDHA` flags to bypass `+INVULNERABLE`/Buddha; Zandronum's `P_DamageMobj` has an equivalent `DMG_FOILINVUL` flag internally, but `A_DamageChildren` has no flags parameter to request it, and no buddha-bypass flag exists in Zandronum at all. The `god2`/`buddha2` cheats (`CF_GODMODE2`/`CF_BUDDHA2`) the wiki mentions do genuinely exist in UZDoom's `p_interaction.cpp`.

## Dead targets and edge cases

If a child actor's health is already 0 or below, or if the target is dead (`playerstate == PST_DEAD`), no damage or healing occurs for that child and iteration continues.

## Network behavior

**Zandronum multiplayer:** The action has no client-mode guard, unlike `A_KillSiblings`, so a client running the calling state executes the loop too. In practice the result stays server-authoritative. The `master` pointer is never sent to clients by the network protocol, so on a client the loop normally matches no children. Deaths are server-side: `P_DamageMobj` only calls `Die` outside client mode (`p_interaction.cpp:1746`). On a client, `P_GiveBody` refuses to heal a player whose health that client isn't allowed to know (`src/g_shared/a_pickups.cpp:234`).

## Zandronum-specific: drastically simplified vs. GZDoom/UZDoom

**The ZDoom Wiki page describes the GZDoom/UZDoom version,** which supports far more parameters and flags:

| Feature | Zandronum | GZDoom/UZDoom |
|---|---|---|
| Basic damage | Yes (1 param) | Yes (1 param) |
| Damagetype | Yes (1 param) | Yes (1 param) |
| Flags (`DMSS_*`) | No | Yes (11+ flags) |
| Class filter | No | Yes |
| Species filter | No | Yes |
| Source pointer (`src`) | No | Yes (configurable) |
| Inflictor pointer (`inflict`) | No | Yes (configurable) |

**Special god/buddha resistance notes:** The wiki claims this function respects `god2` and `buddha2` protective effects on players. These flags **do not exist in Zandronum at all** — they are GZDoom/UZDoom-only additions. In Zandronum, only the basic `CF_GODMODE` and `CF_BUDDHA` cheats exist (handled by `P_DamageMobj`), plus the `+INVULNERABLE` flag for actors.

**If you port code from the wiki to Zandronum,** passing more than two arguments to `A_DamageChildren` aborts DECORATE parsing with a fatal script error `Expected ')', got ','.` at the comma before the third argument (`src/thingdef/thingdef_states.cpp:430`), before any `DMSS_*` flag is even read. The wiki's example code using extended parameters **will not load** in Zandronum. A bare `DMSS_*` word placed in the `damagetype` slot does not error at all: the name parameter accepts any bare token, so it silently becomes a damage type of that name.

## Related functions

- **`A_DamageMaster`** — damages the calling actor's master (spawner). Zandronum version takes `amount` and `damagetype`.
- **`A_DamageSiblings`** — damages all actors sharing the same master as the calling actor. Zandronum version takes `amount` and `damagetype`.
- **`A_DamageTarget`** — damages the calling actor's target. UZDoom only; Zandronum has no `A_DamageTarget`.
- **`A_DamageTracer`** — damages the calling actor's tracer. UZDoom only; Zandronum has no `A_DamageTracer`.
- **`A_KillChildren`** — kills all child actors outright. Takes only `damagetype` parameter; uses `DMG_NO_ARMOR | DMG_NO_FACTOR`.
- **`A_SpawnItemEx`** — the primary source of master-child relationships; sets the `master` pointer via the `SXF_SETMASTER` flag (on Zandronum, only for monsters spawned by monsters).
