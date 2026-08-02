# `void A_KillSiblings(name damagetype = "none")`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_KillSiblings` (retrieved 2026-08-01, oldid=46802) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3583-3608` and `wadsrc/static/actors/actor.txt:244`.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:3583` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_KillSiblings)`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

```c
if ( NETWORK_InClientMode() )
{
    if (( self->NetworkFlags & NETFL_CLIENTSIDEONLY ) == false )
        return;
}
```

Calls `P_DamageMobj` on all sibling actors (actors sharing the calling actor's master) excluding the caller itself, dealing damage equal to each victim's current health and typically killing them outright. Damage is applied without armor/damage factor modifiers. **Zandronum only: this function is drastically simplified compared to GZDoom/UZDoom, which add flags and actor/species filters.**

## Network behavior: server-side only with client-side-only exception

Unlike `A_KillMaster` (which carries no network check), `A_KillSiblings` has an explicit network gate. On a network client running the action on a non-client-side-only actor, the function returns without effect — the action is server-only for normal actors. 

However, actors marked with the `+CLIENTSIDEONLY` flag (which sets the internal `NETFL_CLIENTSIDEONLY` network flag) are simulated entirely client-side with no server counterpart, so the action **does execute on clients for these actors**. This allows decorations, effects, and other client-only entities to manage their own sibling relationships without server involvement.

This two-tier design prevents desync: server actors' sibling relationships are managed by the server, while client-only actors (which have no server-side state to conflict) manage themselves.

## Siblings and the master relationship

A sibling relationship is typically established via `A_SpawnItemEx(..., SXF_SETMASTER)` — this action sets the `master` pointer of the spawned actor to point back to the spawner. The `A_KillSiblings` action then uses that relationship to identify victims: all actors whose `master` pointer matches the calling actor's `master` pointer, excluding the caller itself (enforced by the `mo != self` check in the iteration loop).

**Important limitations:**
- **Master must be non-NULL:** If the calling actor has no master (master pointer is NULL), the function returns without effect.
- **Spawned with `A_SpawnProjectile` are not affected:** The `A_SpawnProjectile` action does not set the `master` pointer and was never designed to spawn creatures targeted by this action. Only use `A_SpawnItemEx` with the `SXF_SETMASTER` flag if you intend to later destroy spawned actors via `A_KillSiblings`.

## Parameters

- **`damagetype`** — the name of the damage type to use when processing the damage. Defaults to `"none"`. This is passed to `P_DamageMobj` as the mod parameter, which determines whether the death state triggered is a regular death or a special damage-specific state (e.g., `Death.Fire`). Death states for custom damage types are resolved in the actor's state table.

## Damage and state handling

When called, the action invokes `P_DamageMobj(victim, self, self, victim->health, damagetype, DMG_NO_ARMOR | DMG_NO_FACTOR)` on each sibling.

- **Damage amount:** Each victim's current health value. This is calculated at the moment of the call, so damage calculations may be affected by previous hits in the same tic.
- **Damage flags:** `DMG_NO_ARMOR` and `DMG_NO_FACTOR` are always used:
  - `DMG_NO_ARMOR` — prevents armor from reducing the damage.
  - `DMG_NO_FACTOR` — prevents damage factors (via `DamageFactor` properties or `DamageFactors` defined for the damage type) from being applied.
- **Source and inflictor:** Both are set to the calling actor (`self`). This gives the calling actor full credit for kills.

## Invulnerability and special resistances

An `+INVULNERABLE` sibling **will not be harmed** by `A_KillSiblings`. The function does not use `DMG_FORCED` and does not set the `DMG_FOILINVUL` flag, so `P_DamageMobj` will reject the damage as soon as it checks the `MF2_INVULNERABLE` flag. **Zandronum has no `KILS_FOILINVUL` flag** (present in GZDoom/UZDoom's extended version) — there is no way to bypass invulnerability in Zandronum's implementation.

Similarly, other invulnerability-like conditions (DORMANT flag, spectral immunity, etc.) are handled by `P_DamageMobj` and apply here.

## Dead siblings and zero-health edge case

If a sibling's health is already 0 or below at the time of the call, `P_DamageMobj` returns early without further processing. The function does not track whether siblings are dead or perform any special cleanup.

## Zandronum-specific: drastically simplified vs. GZDoom/UZDoom

**The ZDoom Wiki page describes the GZDoom/UZDoom version,** which supports far more parameters:

| Feature | Zandronum | GZDoom/UZDoom |
|---|---|---|
| Damagetype | Yes (1 param) | Yes (1 param) |
| Flags (`KILS_*`) | No | Yes (8+ flags) |
| Class filter | No | Yes |
| Species filter | No | Yes |
| Source pointer | No | Yes (configurable via `src` param) |
| Inflictor pointer | No | Yes (configurable via `inflict` param) |

**If you port code from the wiki to Zandronum,** compilation will fail with "unknown identifier" errors for any `KILS_*` flags, and passing more than one argument to `A_KillSiblings` will fail with a "too many arguments" error. The wiki's example code using extended parameters **will not compile** in Zandronum.

## Related functions

- **`A_KillMaster`** — kills the calling actor's own master instead of its siblings. Zandronum version takes only `damagetype` and carries no network check.
- **`A_KillChildren`** — kills all actors with `master == self`. Zandronum version also takes only `damagetype` and carries no network check.
- **`A_DamageSiblings`** — damages (but not necessarily kills) siblings. Zandronum version takes `damagetype` and `damage` amount.
- **`A_SpawnItemEx`** — the primary source of sibling relationships; sets the `master` pointer.
