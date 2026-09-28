# `void A_KillSiblings(name damagetype = "none")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_KillSiblings` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_KillSiblings&oldid=46802) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3583-3608` and `wadsrc/static/actors/actor.txt:244`; `SXF_SETMASTER` gating at `src/thingdef/thingdef_codeptr.cpp:2439-2454`, `A_CustomMissile`/`A_DamageSiblings` signatures at `wadsrc/static/actors/actor.txt:206,282`, extra-argument parse error at `src/thingdef/thingdef_states.cpp:430` and `src/sc_man.cpp:458`, name-parameter parsing at `src/thingdef/thingdef_parse.cpp:91-97,926`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

## Zandronum-specific: network gate has no UZDoom equivalent

UZDoom's `A_KillSiblings` (`src/playsim/p_actionfunctions.cpp:4270-4296`) carries no client/server authority check at all — there is no `NETWORK_InClientMode()` call, no test of a `+CLIENTSIDEONLY`/`NETFL_CLIENTSIDEONLY`-style flag, and no server/client split anywhere in the function or the shared `DoKill` helper it calls. UZDoom/GZDoom-family engines have no server-authoritative vs. client-predicted execution model for action functions at all, so the entire "server-side only with client-side-only exception" design described above is a Zandronum-only concept: on UZDoom, `A_KillSiblings` simply iterates every actor sharing the caller's master and calls `DoKill` on each, unconditionally, regardless of network state.

## Siblings and the master relationship

A sibling relationship is typically established via `A_SpawnItemEx(..., SXF_SETMASTER)`, which points the spawned actor's `master` at the originator (the spawner, or for a missile spawner, the first non-missile up its `target` chain). On UZDoom, `SXF_SETMASTER` does this unconditionally. On Zandronum it only takes effect when the spawned actor is `+ISMONSTER`, passed its spawn position check, and the originator is itself `+ISMONSTER`; any other spawn leaves `master` unset (or copied from the spawner's own master under `SXF_TRANSFERPOINTERS`). The `A_KillSiblings` action then uses that relationship to identify victims: all actors whose `master` pointer matches the calling actor's `master` pointer, excluding the caller itself (enforced by the `mo != self` check in the iteration loop).

**Important limitations:**
- **Master must be non-NULL:** If the calling actor has no master (master pointer is NULL), the function returns without effect.
- **Projectile spawners are not affected:** UZDoom's `A_SpawnProjectile` does not set the `master` pointer. Zandronum has no `A_SpawnProjectile`; its equivalent `A_CustomMissile` does not set `master` either. Only use `A_SpawnItemEx` with the `SXF_SETMASTER` flag if you intend to later destroy spawned actors via `A_KillSiblings` (on Zandronum, only for monsters spawned by monsters, as above).

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

An `+INVULNERABLE` sibling **will not be harmed** by `A_KillSiblings`. The function does not use `DMG_FORCED` and does not set the `DMG_FOILINVUL` flag, so `P_DamageMobj` will reject the damage as soon as it checks the `MF2_INVULNERABLE` flag. **Zandronum has no `KILS_FOILINVUL` flag** (present in GZDoom/UZDoom's extended version) — there is no way to bypass invulnerability in Zandronum's implementation. This is not absolute for a non-player target: `P_DamageMobj` only rejects the damage when the inflictor lacks `+FOILINVUL`, and the inflictor here is the calling actor, so a caller with `+FOILINVUL` bypasses the target's invulnerability (`p_interaction.cpp:1212-1220`).

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

**If you port code from the wiki to Zandronum,** passing a second argument to `A_KillSiblings` (e.g. `A_KillSiblings("Fire", KILS_FOILINVUL)`) aborts DECORATE parsing with a fatal script error `Expected ')', got ','.`, since the parser expects the closing parenthesis right after the single `damagetype` argument. The wiki's example code using extended parameters **will not load** in Zandronum. A bare `KILS_*` word passed as the only argument does not error at all: the name parameter accepts any bare token, so it silently becomes a damage type of that name.

## Related functions

- **`A_KillMaster`** — kills the calling actor's own master instead of its siblings. Zandronum version takes only `damagetype` and carries no network check.
- **`A_KillChildren`** — kills all actors with `master == self`. Zandronum version also takes only `damagetype` and carries no network check.
- **`A_DamageSiblings`** — damages (but not necessarily kills) siblings. Zandronum version takes `amount` then `damagetype` (`A_DamageSiblings(int amount, name damagetype = "none")`).
- **`A_SpawnItemEx`** — the primary source of sibling relationships; sets the `master` pointer via `SXF_SETMASTER` (on Zandronum, only for monsters spawned by monsters).
