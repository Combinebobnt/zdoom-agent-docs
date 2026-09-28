# `void A_KillMaster(name damagetype = "none")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_KillMaster` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_KillMaster&oldid=46801) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3542-3554`, `wadsrc/static/actors/actor.txt:242`, and (invulnerability-bypass correction, 2026-09-25) `src/p_interaction.cpp:1212-1220`; protection, network, `SXF_SETMASTER` and parse-error corrections from `src/p_interaction.cpp:1310-1335, 1746`, `src/thingdef/thingdef_codeptr.cpp:2439-2454`, `src/thingdef/thingdef_states.cpp:430`, `src/thingdef/thingdef_parse.cpp:91-97` and `wadsrc/static/actors/actor.txt:280`.
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
  - `DMG_NO_FACTOR` — prevents damage factors (via `DamageFactor` properties or `DamageFactors` defined for the damage type) from being applied. Inventory damage modifiers still apply (a `PowerDamage` on the caller, a `PowerProtection` on the master), so a protected master can survive the call.
- **Source and inflictor:** Both are set to the calling actor (`self`). This gives the calling actor full credit for the kill.

## Invulnerability and special resistances

`A_KillMaster` itself sets neither `DMG_FORCED` nor `DMG_FOILINVUL`, so a plain `+INVULNERABLE` master is normally rejected as soon as `P_DamageMobj` checks the `MF2_INVULNERABLE` flag (`p_interaction.cpp:1212-1220`). This is not absolute, though: for a non-player master, the rejection only fires when the inflictor lacks `+FOILINVUL`, and the inflictor here is the calling actor (`self`). A calling actor with `+FOILINVUL` bypasses the master's invulnerability. The check is also skipped outright when the damage amount (the master's own health) reaches `TELEFRAG_DAMAGE`.

Similarly, other invulnerability-like conditions (DORMANT flag, spectral immunity, etc.) are handled by `P_DamageMobj` and apply here.

## Dead masters and zero-health edge case

If the master's health is already 0 or below at the time of the call, `P_DamageMobj` returns early (see `p_interaction.cpp:1190-1210`); a frozen (`MF_ICECORPSE`) corpse gets its shatter flags set first, but no damage is applied either way. The function does not track whether the master is dead or perform any special cleanup.

## Network behavior

**Zandronum multiplayer:** Unlike `A_KillSiblings` (which returns early on clients unless the caller is `+CLIENTSIDEONLY`), `A_KillMaster` has no client-mode guard, so a client running the calling state executes it too. In practice the result stays server-authoritative. The `master` pointer is never sent to clients by the network protocol, so on a client `master` is normally NULL and the action does nothing. Even where a client does hold a `master`, deaths are server-side: `P_DamageMobj` only calls `Die` outside client mode (`p_interaction.cpp:1746`). Clients receive the resulting death from the server.

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

**If you port code from the wiki to Zandronum,** passing a second argument to `A_KillMaster` (e.g. `A_KillMaster("Fire", KILS_FOILINVUL)`) aborts DECORATE parsing with a fatal script error `Expected ')', got ','.` (`src/thingdef/thingdef_states.cpp:430`), since the parser expects the closing parenthesis right after the single `damagetype` argument. The wiki's example code using extended parameters **will not load** in Zandronum. A bare `KILS_*` word passed as the only argument does not error at all: the name parameter accepts any bare token, so it silently becomes a damage type of that name.

## Related functions

- **`A_KillChildren`** — kills all actors with `master == self`. Zandronum version also takes only `damagetype`.
- **`A_KillSiblings`** — kills all actors sharing the same master. Zandronum version takes only `damagetype` but includes an explicit server-side-only guard.
- **`A_DamageMaster`** — damages (but not necessarily kills) the master. Zandronum version takes `amount` and `damagetype`.
- **`A_SpawnItemEx`** — the primary source of master-child relationships; sets the `master` pointer via `SXF_SETMASTER`. On UZDoom it does so unconditionally. On Zandronum only when the spawned actor and the spawner are both monsters (`thingdef_codeptr.cpp:2439-2454`); any other spawn gets no master link.
