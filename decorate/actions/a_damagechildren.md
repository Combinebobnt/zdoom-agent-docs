# `void A_DamageChildren(int amount, name damagetype = "none")`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_DamageChildren` (retrieved 2026-08-01, oldid=46971) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4483-4507` and `wadsrc/static/actors/actor.txt:281`.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:4483` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_DamageChildren)`).

Damages all of the calling actor's child actors (those with `master == self`) by a specified amount; negative amounts heal instead. **Zandronum only: drastically simplified compared to GZDoom/UZDoom, which support flags and actor/species filters.**

## Parameters

- **`amount`** — the amount of damage to inflict (required). Positive values damage; negative values heal. An amount of 1,000,000 or higher is treated specially via the `TELEFRAG_DAMAGE` mechanism and results in killing the target regardless of health or damage resistance.
- **`damagetype`** — the name of the damage type to use when processing damage (default `"none"`). Passed to `P_DamageMobj` as the `mod` parameter, which determines whether a special death state (e.g., `Death.Fire`) is triggered instead of the default `Death` state. Death states for custom damage types are resolved in the target actor's state table.

## Behavior

When called, the action iterates through all actors in the game world and damages those where the actor's `master` pointer matches the calling actor's address.

For each child actor found:
- **Positive damage:** `P_DamageMobj(child, self, self, amount, DamageType, DMG_NO_ARMOR)` for `amount > 0`
- **Negative damage (healing):** `P_GiveBody(child, -amount)` for `amount < 0` — but **see the bug note below**
- **Zero damage:** Silent no-op (neither branch executes)

### Children definition

A child actor is defined by having its `master` field point to the calling actor. This relationship is commonly established via `A_SpawnItemEx(..., SXF_SETMASTER)` or by directly assigning the spawner's address to the `master` field.

### Damage behavior

- **Invulnerability:** A child with `+INVULNERABLE` **will not be harmed**. The function uses only `DMG_NO_ARMOR` and not `DMG_FORCED`, so `P_DamageMobj` rejects the damage when the target has the `MF2_INVULNERABLE` flag set. No flags exist in Zandronum to bypass invulnerability as they do in GZDoom/UZDoom.
- **Armor:** Damage bypasses armor entirely — the `DMG_NO_ARMOR` flag prevents armor from reducing the damage.
- **Damage factors:** Unlike `A_KillChildren`, damage factors **are applied** — properties like `DamageFactor` and damage-type-specific factor tables will modify the final damage taken. There is no `DMSS_NOFACTOR`-equivalent flag in Zandronum.
- **Telefrag damage:** If `amount >= 1000000` (the `TELEFRAG_DAMAGE` constant), the damage check bypasses all damage resistance and invulnerability checks, forcing a kill under normal conditions.

### Healing behavior

Negative `amount` values trigger the healing path via `P_GiveBody`, which:
- Returns `false` (no effect) if the target is already dead or has health ≤ 0.
- Clamps healing to the target's maximum health (calculated at the moment of the call; includes any health bonuses).
- Applies the prosperity cheat if active on the target player.

**BUG (Zandronum 3.2.1):** The `amount` parameter is negated and **reassigned inside the iteration loop** (`amount = -amount;` in `thingdef_codeptr.cpp:4502`, identical pattern to `A_DamageSiblings`). After the first child is healed, `amount` is now positive, so all *subsequent* children found in the same call are **damaged** instead of healed. This function is unreliable for healing more than one child at a time in Zandronum — call it once per child, or use `A_DamageMaster` if only a single target is needed.

## Dead targets and edge cases

If a child actor's health is already 0 or below, or if the target is dead (`playerstate == PST_DEAD`), no damage or healing occurs for that child and iteration continues.

## Network behavior

**Zandronum multiplayer:** The action carries no explicit network synchronization guard in the action function itself — `P_DamageMobj` and `P_GiveBody` are responsible for server/client state replication. On servers, damage is applied and propagated to clients via normal actor-death replication. On network clients, execution depends on the children's `+CLIENTSIDEONLY` flag and the normal Zandronum actor-replication rules — this is a potential source of desyncs if not used carefully on non-client-side-only actors.

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

**If you port code from the wiki to Zandronum,** compilation will fail with "unknown identifier" errors for any `DMSS_*` flags, and passing more than two arguments to `A_DamageChildren` will fail with a "too many arguments" error. The wiki's example code using extended parameters **will not compile** in Zandronum.

## Related functions

- **`A_DamageMaster`** — damages the calling actor's master (spawner). Zandronum version takes `amount` and `damagetype`.
- **`A_DamageSiblings`** — damages all actors sharing the same master as the calling actor. Zandronum version takes `amount` and `damagetype`.
- **`A_DamageTarget`** — damages the calling actor's target. Zandronum version takes `amount` and `damagetype`.
- **`A_DamageTracer`** — damages the calling actor's tracer. Zandronum version takes `amount` and `damagetype`.
- **`A_KillChildren`** — kills all child actors outright. Takes only `damagetype` parameter; uses `DMG_NO_ARMOR | DMG_NO_FACTOR`.
- **`A_SpawnItemEx`** — the primary source of master-child relationships; sets the `master` pointer via the `SXF_SETMASTER` flag.
