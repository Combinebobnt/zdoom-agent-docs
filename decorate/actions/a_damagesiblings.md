# `void A_DamageSiblings(int amount, name damagetype = "none")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_DamageSiblings` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_DamageSiblings&oldid=46972) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4517-4545` and `wadsrc/static/actors/actor.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:4517` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_DamageSiblings)`).

Damages all actors that share the calling actor's master (spawner), excluding the calling actor itself; negative amounts heal instead. **Zandronum only: drastically simplified compared to GZDoom/UZDoom, which support 7 parameters with flags and actor/species filters.**

## Parameters

- **`amount`** — the amount of damage to inflict (required). Positive values damage; negative values heal. An amount of 1,000,000 or higher is treated specially and results in killing the target regardless of health or damage resistance.
- **`damagetype`** — the name of the damage type to use when processing damage (default `"none"`). Passed to `P_DamageMobj` as the `mod` parameter, determining whether a special death state (e.g., `Death.Fire`) is triggered.

## Behavior

When called, the action:

1. **Iterates all thinkers** (all actors in the level) via `TThinkerIterator<AActor>`, checking each actor.
2. **Selects siblings**: Damages only actors where `actor->master == self->master` and `actor != self`. Returns silently if `self->master` is NULL (the calling actor has no master).
3. **For positive damage:** Calls `P_DamageMobj(sibling, self, self, amount, DamageType, DMG_NO_ARMOR)`.
4. **For negative damage (healing):** Calls `P_GiveBody(sibling, -amount)` — but **see the bug note below**.

### Target criteria

- **Siblings are actors sharing the same `master` pointer** (the actor that spawned this one via `A_SpawnItemEx` with `SXF_SETMASTER` or similar).
- **The calling actor is excluded** from the damage (the `mo != self` check).
- **If the calling actor has no master** (master is NULL), the entire function returns without effect; no actors are damaged.

### Damage behavior

- **Invulnerability:** An `+INVULNERABLE` sibling **will not be harmed**. The function uses only `DMG_NO_ARMOR` and not `DMG_FORCED`, so invulnerable targets reject the damage.
- **Armor:** Damage bypasses armor entirely — the `DMG_NO_ARMOR` flag prevents armor reduction.
- **Damage factors:** Damage factors **are applied** — properties like `DamageFactor` will modify the final damage taken. There is no `DMSS_NOFACTOR`-equivalent flag in Zandronum.
- **Telefrag damage:** If `amount >= 1000000`, the damage check bypasses damage resistance and invulnerability, forcing a kill under normal conditions.

### Healing behavior

Negative `amount` values trigger healing via `P_GiveBody` for each sibling:

- Returns without effect if the target is dead or health ≤ 0.
- Clamps healing to the target's maximum health.
- **BUG (Zandronum 3.2.1):** The `amount` parameter is negated and **reassigned inside the while loop**. After the first sibling is healed, `amount` is now positive, so all *subsequent* siblings in the same call are **damaged** instead of healed. If you have multiple siblings and need to heal all of them with a single `A_DamageSiblings` call, this function is unreliable — do not use it for that purpose in Zandronum. Workarounds: (1) call the function once per sibling, or (2) use separate `A_DamageChildren` or `A_DamageMaster` calls if your actor hierarchy permits.

## Performance note

This function scans the entire thinker list (all actors in the level) on every call via `TThinkerIterator`, making it **O(n) in the total actor count**, not O(1). Call it sparingly or cache the result if damaging the same sibling set repeatedly. In contrast, `A_DamageMaster` is O(1) because it dereferences a single `master` pointer.

## Network behavior

**Zandronum multiplayer:** The action carries no explicit network synchronization guard in the action function itself — `P_DamageMobj` and `P_GiveBody` are responsible for server/client state replication. On servers, damage is applied and propagated to clients. On network clients, execution depends on the actor's `+CLIENTSIDEONLY` flag.

## Engine-family divergence: no client/server authority split

The "Network behavior" section above describes Zandronum's client/server netcode split. UZDoom's `A_DamageSiblings` (`src/playsim/p_actionfunctions.cpp:4087-4113`) contains no network-role branch at all — no check for local-player ownership, no server/client split, and no `+CLIENTSIDEONLY`-gated early-out. This matches the cohort-wide pattern: UZDoom's source tree has zero `NETWORK_InClientMode`/`SERVERCOMMANDS_*` occurrences anywhere (confirmed by tree-wide grep). On UZDoom, the sibling scan and damage/heal calls simply run unconditionally wherever the action executes.

## Engine-family divergence: 7-parameter signature is real and functional in UZDoom

The table in "Zandronum-specific" above describes the wiki's extra parameters and flags as things Zandronum omits. Verified directly against UZDoom's native declaration (`wadsrc/static/zscript/actors/actor.zs:1399`) and implementation (`src/playsim/p_actionfunctions.cpp:4087-4113`, dispatching into the shared `DoDamage` helper at `p_actionfunctions.cpp:3922-3955`), they are real, functioning UZDoom/GZDoom-family behavior: all ten `DMSS_*` flags (`FOILINVUL`, `AFFECTARMOR`, `KILL`, `NOFACTOR`, `FOILBUDDHA`, `NOPROTECT`, `EXFILTER`, `EXSPECIES`, `EITHER`, `INFLICTORDMGTYPE`) are read and applied per sibling, the `filter`/`species` arguments gate which siblings are affected at all (before any damage/heal call, via `DoCheckClass`/`DoCheckSpecies`), and `src`/`inflict` (via `COPY_AAPTR`) let the caller redirect the damage's source and inflictor pointers away from the defaults (the acting sibling itself, per `DoDamage`'s Zandronum-equivalent `P_DamageMobj(sibling, self, self, ...)` call). None of this is reachable from Zandronum, where the function only ever accepts `amount` and `damagetype`.

## Engine-family divergence: the Zandronum healing bug does not reproduce on UZDoom

The "Healing behavior" section above documents a Zandronum-only bug: `amount` is negated and reassigned in place inside the shared `while` loop, so after the first sibling is healed every subsequent sibling in the same call is damaged instead. UZDoom's `A_DamageSiblings` loop (`p_actionfunctions.cpp:4106-4110`) calls the `DoDamage` helper function once per sibling, passing the action function's own `amount` local by value on every iteration; `DoDamage` negates and reassigns `amount` only inside its own function-local copy (`p_actionfunctions.cpp:3949-3953`), which is discarded when it returns. The caller's `amount` is never mutated across iterations. As a result, a negative `amount` correctly heals **every** sibling in a single UZDoom `A_DamageSiblings` call — the workarounds described in the Zandronum bug note (call once per sibling, or use `A_DamageChildren`/`A_DamageMaster` instead) are unnecessary on UZDoom.

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

**Special god/buddha resistance notes:** The wiki claims this function respects `god2` and `buddha2` protective effects on players. These flags **do not exist in Zandronum at all** — they are GZDoom/UZDoom-only. In Zandronum, only the basic `CF_GODMODE` and `CF_BUDDHA` cheats exist (handled by `P_DamageMobj`), plus the `+INVULNERABLE` flag for actors.

**If you port code from the wiki to Zandronum,** compilation will fail with "unknown identifier" errors for any `DMSS_*` flags, and passing more than two arguments to `A_DamageSiblings` will fail with a "too many arguments" error. The wiki's example code **will not compile** in Zandronum.

## Related functions

- **`A_DamageMaster`** — damages the master (spawner) only. Zandronum version takes `amount` and `damagetype`. Also uses `DMG_NO_ARMOR`.
- **`A_DamageChildren`** — damages all actors with `master == self`. Zandronum version takes `amount` and `damagetype`.
- **`A_KillSiblings`** — kills all sibling actors outright (damage = sibling health). Takes only `damagetype` parameter.
- **`A_SpawnItemEx`** — the primary source of master-sibling relationships; sets the `master` pointer with `SXF_SETMASTER` flag.
