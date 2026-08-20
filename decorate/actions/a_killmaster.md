# `void A_KillMaster(name damagetype = "none")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_KillMaster` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_KillMaster&oldid=46801) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3542-3554` and `wadsrc/static/actors/actor.txt:242`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:3545` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_KillMaster)`).

Calls `P_DamageMobj` on the calling actor's master (spawner) with a damage amount equal to the master's current health, killing it if it survives the damage checks. **Zandronum only: this function is drastically simplified compared to GZDoom/UZDoom, which add flags and actor/species filters.**

## Parameters

- **`damagetype`** — the name of the damage type to use when processing the damage. Defaults to `"none"`. This is passed to `P_DamageMobj` as the mod parameter, which determines whether the death state triggered is a regular death or a special damage-specific state (e.g., `Death.Fire`). Death states for custom damage types are resolved in the actor's state table.

## Behavior

When called, the action invokes `P_DamageMobj(self->master, self, self, self->master->health, damagetype, DMG_NO_ARMOR | DMG_NO_FACTOR)`.

- **Target:** The calling actor's `master` pointer (the actor that spawned this one). If `master` is NULL, the function returns without effect.
- **Damage amount:** The target's current health value. This is calculated at the moment of the call, so damage calculations may be affected by previous hits in the same tic.
- **Damage flags:** `DMG_NO_ARMOR` and `DMG_NO_FACTOR` are always used:
  - `DMG_NO_ARMOR` — prevents armor from reducing the damage.
  - `DMG_NO_FACTOR` — prevents damage factors (via `DamageFactor` properties or `DamageFactors` defined for the damage type) from being applied.
- **Source and inflictor:** Both are set to the calling actor (`self`). This gives the calling actor full credit for the kill.

## Invulnerability and special resistances

An `+INVULNERABLE` master **will not be harmed** by `A_KillMaster`. The function does not use `DMG_FORCED` and does not set the `DMG_FOILINVUL` flag, so `P_DamageMobj` will reject the damage as soon as it checks the `MF2_INVULNERABLE` flag. There is no way to bypass this in Zandronum's implementation.

Similarly, other invulnerability-like conditions (DORMANT flag, spectral immunity, etc.) are handled by `P_DamageMobj` and apply here.

## Dead masters and zero-health edge case

If the master's health is already 0 or below at the time of the call, `P_DamageMobj` returns early without further processing (see `p_interaction.cpp:1190-1210`). The function does not track whether the master is dead or perform any special cleanup.

## Network behavior

**Zandronum multiplayer:** Unlike `A_KillSiblings` (which has an explicit server-side-only gate), `A_KillMaster` carries no network synchronization guard in the action function itself — `P_DamageMobj` is responsible for handling server/client state. On servers, the damage is applied and propagated to clients via normal actor-death replication. On network clients running non-client-side-only actors, the action will execute but its effects depend on the actor's netcode handling — this is a potential source of desyncs if not used carefully.

## Zandronum-specific: drastically simplified vs. GZDoom/UZDoom

**The ZDoom Wiki page describes the GZDoom/UZDoom version,** which supports far more parameters:

| Feature | Zandronum | GZDoom/UZDoom |
|---|---|---|
| Damagetype | Yes (1 param) | Yes (1 param) |
| Flags (`KILS_*`) | No | Yes (6+ flags) |
| Class filter | No | Yes |
| Species filter | No | Yes |
| Source pointer | No | Yes (configurable via `src` param) |
| Inflictor pointer | No | Yes (configurable via `inflict` param) |

**If you port code from the wiki to Zandronum,** compilation will fail with "unknown identifier" errors for any `KILS_*` flags, and passing more than one argument to `A_KillMaster` will fail with a "too many arguments" error. The wiki's example code using extended parameters **will not compile** in Zandronum.

## Related functions

- **`A_KillChildren`** — kills all actors with `master == self`. Zandronum version also takes only `damagetype`.
- **`A_KillSiblings`** — kills all actors sharing the same master. Zandronum version takes only `damagetype` but includes an explicit server-side-only guard.
- **`A_DamageMaster`** — damages (but not necessarily kills) the master. Zandronum version takes `damagetype` and `damage` amount.
- **`A_SpawnItemEx`** — the primary source of master-child relationships; sets the `master` pointer.
