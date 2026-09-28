# `void A_DamageMaster(int amount, name damagetype = "none")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_DamageMaster` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_DamageMaster&oldid=46969) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4457-4475` and `wadsrc/static/actors/actor.txt:280`; telefrag, frozen-corpse and network corrections from `src/p_interaction.cpp:1190-1210, 1261, 1310-1352, 1695-1700, 1745-1749, 1755, 1785-1787, 1837-1839`; extra-argument error from `src/thingdef/thingdef_states.cpp:430`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:4457` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_DamageMaster)`).

Damages the calling actor's master (spawner) by a specified amount; negative amounts heal instead. **Zandronum only: drastically simplified compared to GZDoom/UZDoom, which support flags and actor/species filters.**

## Parameters

- **`amount`** — the amount of damage to inflict (required). Positive values damage; negative values heal. An amount of 1,000,000 or higher (`TELEFRAG_DAMAGE`) skips the `+INVULNERABLE` check. On UZDoom, damage factors and protection also can't reduce it unless the master has `+LAXTELEFRAGDMG`, so it kills regardless of resistance. On Zandronum they still can: `DamageFactor`, per-damage-type factors and protection powerups apply to it like any other damage (`src/p_interaction.cpp:1310-1352`), so a resistant master can survive it. A `+DORMANT` master takes no damage on either engine.
- **`damagetype`** — the name of the damage type to use when processing damage (default `"none"`). Passed to `P_DamageMobj` as the `mod` parameter, which determines whether a special death state (e.g., `Death.Fire`) is triggered instead of the default `Death` state. Death states for custom damage types are resolved in the actor's state table.

## Behavior

When called, the action invokes:
- **Positive damage:** `P_DamageMobj(self->master, self, self, amount, DamageType, DMG_NO_ARMOR)` for `amount > 0`
- **Negative damage (healing):** `P_GiveBody(self->master, -amount)` for `amount < 0`
- **Zero damage:** Silent no-op (neither branch executes)

### Target

The calling actor's `master` pointer (the actor that spawned this one via `A_SpawnItemEx` with `SXF_SETMASTER` or similar). If `master` is NULL, the function returns without effect.

### Damage behavior

- **Invulnerability:** An `+INVULNERABLE` master **will not be harmed**. The function uses only `DMG_NO_ARMOR` and not `DMG_FORCED`, so `P_DamageMobj` rejects the damage when the target has the `MF2_INVULNERABLE` flag set. Zandronum's `P_DamageMobj` does have an internal `DMG_FOILINVUL` flag (`src/p_local.h:606`), but `A_DamageMaster` takes no flags parameter to request it, unlike UZDoom's `DMSS_FOILINVUL`. This is not absolute for a non-player target: `P_DamageMobj` only rejects the damage when the inflictor lacks `+FOILINVUL`, and the inflictor here is the calling actor, so a caller with `+FOILINVUL` bypasses the target's invulnerability (`p_interaction.cpp:1212-1220`).
- **Armor:** Damage bypasses armor entirely — the `DMG_NO_ARMOR` flag prevents armor from reducing the damage.
- **Damage factors:** Unlike `A_KillMaster`, damage factors **are applied** — properties like `DamageFactor` and damage-type-specific factor tables will modify the final damage taken. There is no `DMSS_NOFACTOR`-equivalent flag in Zandronum.
- **Telefrag damage:** If `amount >= 1000000` (the `TELEFRAG_DAMAGE` constant), the `+INVULNERABLE` check is skipped. For a player master, the skill damage factor is skipped too, and god mode and buddha don't protect as long as the amount is still at least `TELEFRAG_DAMAGE` after factors. It is not a guaranteed kill in Zandronum: `DamageFactor`, per-damage-type factors and protection powerups still reduce it (`p_interaction.cpp:1310-1352`), and a `+DORMANT` master is still immune (`p_interaction.cpp:1261`).

### Healing behavior

Negative `amount` values trigger the healing path via `P_GiveBody`, which:
- Returns `false` (no effect) if the target is already dead or has health ≤ 0.
- Clamps healing to the target's maximum health (calculated at the moment of the call; includes any health bonuses).
- Applies the prosperity cheat if active on the target player.

## Dead targets and edge cases

If the target's health is already 0 or below, or if the target is dead (`playerstate == PST_DEAD`), no damage or healing occurs and the function returns without effect. One exception: positive damage on a frozen (ice) corpse master shatters it. In Zandronum that happens for any damage type except `"Ice"` (`p_interaction.cpp:1190-1210`). UZDoom also shatters it with `"Ice"` when the caller has `+ICESHATTER`.

## Network behavior

**Zandronum multiplayer:** The action function itself has no client/server guard, so any network handling comes from `P_DamageMobj` and `P_GiveBody`. When the action runs on a client, `P_DamageMobj` still lowers the master's health locally but leaves the kill to the server (`Die` only runs outside client mode, `p_interaction.cpp:1745-1749`) and skips the wound and pain states (`p_interaction.cpp:1755`, `1785-1787`) and the wake-up and retarget logic (`p_interaction.cpp:1837-1839`). On a client, `P_GiveBody` refuses to heal a player master whose health that client isn't allowed to know (`src/g_shared/a_pickups.cpp:234`). On the server, a player master's damage is sent to clients (`p_interaction.cpp:1697-1699`) and a kill goes through `Die`.

## Engine-family divergence

**UZDoom's `A_DamageMaster` is a native function (`src/playsim/p_actionfunctions.cpp:4033`) implementing exactly the wiki-described signature and flag set** — `amount`, `damagetype`, `flags` (the `DMSS_*` bits, defined at `p_actionfunctions.cpp:3908`), `filter`, `species`, `src`, and `inflict`, all present and behaving as the wiki describes. With default arguments (only `amount`/`damagetype` supplied, as in this doc's own examples), the core mechanics verified in UZDoom match Zandronum's documented behavior exactly: armor is bypassed (`DMG_NO_ARMOR` applied whenever `DMSS_AFFECTARMOR` isn't set), an `MF2_INVULNERABLE` master is not harmed unless `DMSS_FOILINVUL` is passed, damage factors are applied (no `DMSS_NOFACTOR`), `amount >= 1000000` (`TELEFRAG_DAMAGE`) bypasses the invulnerability check, and a dead/`health <= 0` master is left untouched. The `filter`/`species` checks (`DoCheckClass`/`DoCheckSpecies`) pass through unconditionally when left at their defaults (`null`/`"None"`), so the two-parameter call form behaves identically to Zandronum's fixed two-parameter function.

### Network behavior

UZDoom's `A_DamageMaster` (and the `DoDamage`/`P_DamageMobj`/`P_GiveBody` helpers it calls) contain **no client/server authority gating at all** — a tree-wide search of `~/source/UZDoom/src` turns up zero occurrences of `NETWORK_InClientMode` or any `SERVERCOMMANDS_*` call. This is a general property of UZDoom, not something specific to this action: the engine has no client/server split anywhere in its source tree. This contrasts with Zandronum, where `P_GiveBody` itself contains an explicit `NETWORK_InClientMode()` check (`src/g_shared/a_pickups.cpp:234`) that suppresses healing on clients not permitted to know the target's health, and where damage/kill propagation to clients relies on the server/client replication model described above. On UZDoom, damage and healing triggered by this action apply directly and unconditionally, with no equivalent client-side suppression or explicit server-command broadcast in the action's own code path.

### Healing (`P_GiveBody`) differences

UZDoom's `P_GiveBody` (`src/playsim/p_mobj.cpp:1232`) differs from Zandronum's in two respects relevant to `A_DamageMaster`'s healing path, beyond the network gate above:

- **No prosperity cheat:** Zandronum's `P_GiveBody` special-cases `CF_PROSPERITY` (a Zandronum/Skulltag-era cheat/rune) to raise the healing cap to `deh.MaxSoulsphere + 50`. **The `CF_PROSPERITY` identifier does still exist in UZDoom's ZScript stdlib** (`wadsrc/static/zscript/constants.zs`, `CF_PROSPERITY = 0`), inside a block explicitly commented "These flags no longer exist, but keep the names for some stray mod that might have used them" — it's a compile-time-only compatibility shim that compiles to an inert zero, not a working cheat bit. The functional behavior — no prosperity healing-cap boost — is genuinely absent on UZDoom; the existing doc's "Applies the prosperity cheat if active on the target player" bullet under "Healing behavior" does not apply there.
- **Skill-based healing scaling:** UZDoom scales positive player healing by `G_SkillProperty(SKILLP_HealthFactor)` (clamped to a minimum of 1) before applying it; Zandronum's `P_GiveBody` applies `num` directly with no skill-based scaling. This only affects player masters, since monster masters go through the non-player branch in both engines' `P_GiveBody`.

Both engines otherwise agree: healing is refused outright if the target's health is `<= 0` or its `playerstate == PST_DEAD`, and the amount is clamped to the target's (recomputed) max health.

## Zandronum-specific: drastically simplified vs. GZDoom/UZDoom

**The ZDoom Wiki page describes the GZDoom/UZDoom version,** which supports far more parameters and flags:

| Feature | Zandronum | GZDoom/UZDoom |
|---|---|---|
| Basic damage | Yes (1 param) | Yes (1 param) |
| Damagetype | Yes (1 param) | Yes (1 param) |
| Flags (`DMSS_*`) | No | Yes (exactly 10 flags: `FOILINVUL`, `AFFECTARMOR`, `KILL`, `NOFACTOR`, `FOILBUDDHA`, `NOPROTECT`, `EXFILTER`, `EXSPECIES`, `EITHER`, `INFLICTORDMGTYPE`) |
| Class filter | No | Yes |
| Species filter | No | Yes |
| Source pointer (`src`) | No | Yes (configurable) |
| Inflictor pointer (`inflict`) | No | Yes (configurable) |

**Special god/buddha resistance notes:** The wiki claims this function respects `god2` and `buddha2` protective effects on players. These flags **do not exist in Zandronum at all** — they are GZDoom/UZDoom-only additions. In Zandronum, only the basic `CF_GODMODE` and `CF_BUDDHA` cheats exist (handled by `P_DamageMobj`), plus the `+INVULNERABLE` flag for actors.

**If you port code from the wiki to Zandronum,** no `DMSS_*` constant exists at all, and passing more than two arguments to `A_DamageMaster` fails at parse time with `Expected ')', got ','.` at the comma before the third argument (`src/thingdef/thingdef_states.cpp:430`). The wiki's example code using extended parameters **will not compile** in Zandronum.

## Related functions

- **`A_KillMaster`** — kills the master outright (damage = master's health). Takes only `damagetype` parameter; also uses `DMG_NO_ARMOR | DMG_NO_FACTOR`.
- **`A_DamageChildren`** — damages all actors with `master == self`. Zandronum version takes `amount` and `damagetype`.
- **`A_DamageSiblings`** — damages all actors sharing the same master. Zandronum version takes `amount` and `damagetype`.
- **`A_SpawnItemEx`** — the primary source of master-child relationships; sets the `master` pointer.
