# `A_KillChildren` (destroy spawned children)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_KillChildren` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_KillChildren&oldid=46804) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3561-3576`; `SXF_SETMASTER` monster-only rule from `thingdef_codeptr.cpp:2415-2454` (`InitSpawnedItem`); damage-modifier, pain and server-only `Die` behavior from `src/p_interaction.cpp:1295-1341,1746-1748,1770-1789` and `src/p_mobj.cpp:7737-7773` (`TakeSpecialDamage`); action set from `wadsrc/static/actors/actor.txt:206,239-243`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_KillChildren)` in `src/thingdef/thingdef_codeptr.cpp`.

Destroys all actors whose master pointer is set to the calling actor, typically creatures spawned by the calling actor. Damage is applied without armor/damage factor modifiers.

## Signature

```text
void A_KillChildren([str damagetype])
```

## Parameters

### `damagetype` (str, optional)

The damage type to apply when killing the children. This determines which death state the victims enter (if they have specialized death states for this damage type). A child with the `NODAMAGE` flag survives instead, and the damage type then only selects which pain state it may enter (see "Damage and state handling").

Default: `NAME_None` (generic damage type).

## Behavior

When called, this action:

1. **Iterates all actors in the current map** using a global thinker iterator.
2. **Identifies children** by checking if `mo->master == self` (the victim's master pointer equals the calling actor).
3. **Damages each child to death** by calling `P_DamageMobj(mo, self, self, mo->health, damagetype, DMG_NO_ARMOR | DMG_NO_FACTOR)`.
   - Damage amount equals the victim's current health, typically killing it instantly.
   - `DMG_NO_ARMOR` prevents damage reduction from armor properties.
   - `DMG_NO_FACTOR` skips only the child's `DamageFactor` and per-damage-type damage factors. Inventory damage modifiers still apply (a `PowerDamage` on the caller, a `PowerProtection` on the child), as do the caller's and child's special-damage hooks, so a protected child can survive the call.
4. **Continues iterating** through all remaining actors; multiple victims can be killed in one call.

## Master relationship and scope

A child's master relationship is typically established via `A_SpawnItemEx(..., SXF_SETMASTER)`. The `A_KillChildren` action then uses that relationship to identify and destroy victims. The engines differ on when that flag takes effect:

- **UZDoom:** `SXF_SETMASTER` always sets the spawned actor's `master` to the spawner (or, for a missile spawner, the actor at the end of its `target` chain).
- **Zandronum:** `SXF_SETMASTER` only sets `master` when the spawned actor is a monster (`ISMONSTER`) and the spawner (resolved the same way) is also a monster. A player, a decoration, or any other non-monster spawner gets no master link, and neither does a non-monster child such as a missile or effect, so `A_KillChildren` from that spawner finds nothing. `SXF_TRANSFERPOINTERS` copies the caller's own `master`, not the caller.

**Important limitation:** Projectiles fired with the dedicated missile-spawning action (`A_SpawnProjectile` on UZDoom; Zandronum has no `A_SpawnProjectile`, its equivalent is `A_CustomMissile`) are **not affected** by `A_KillChildren`, since that action does not set the `master` pointer. Use `A_SpawnItemEx` with the `SXF_SETMASTER` flag if you intend to later destroy spawned actors via `A_KillChildren`, subject to Zandronum's monster-only restriction above.

**Cleanup gap: a master that is removed rather than killed never calls this.** Calling
`A_KillChildren` from the master's `Death` state only covers a real death. ACS
[`Thing_Remove`](../../acs/functions/thing_remove.md), `A_Remove` (UZDoom only), `A_RemoveMaster`/`A_RemoveChildren`/`A_RemoveSiblings`, and anything else that destroys
the master without a death state leave its children alive with a null `master`. A looping child
that must not outlive its master can guard itself, e.g. `A_CheckFlag("SHOOTABLE", "<loop>",
AAPTR_MASTER)` followed by `A_Die` (`A_CheckFlag` doesn't jump on a null pointer). On Zandronum,
keep the fall-through as the server-only `A_Die`, not a jump: clients never learn `master`, so a
client-evaluated "master missing" jump would fire on every client from spawn.

## Damage and state handling

- The victims enter death states **determined by the `damagetype` parameter** — if provided, the engine looks for a death state specific to that damage type (e.g., `Death.Voodoo`).
- If no such state exists, the engine falls back to the generic `Death` state, but only when the child has one. A child that has only specialized death states, none matching `damagetype`, takes no damage at all and survives.
- A `DeathType` set on the calling actor overrides `damagetype` for death-state selection, and a `PainType` on the caller overrides it for pain-state selection.
- Victims with the `NODAMAGE` flag take no damage and survive. They may enter their pain state (selected by the damage type), but only if the usual pain roll against their `PainChance` for that damage type succeeds, or the caller has `+FORCEPAIN`.
- Victims with the `INVULNERABLE` flag are **unaffected** by this action — they cannot be killed this way. This is not absolute for a non-player target: `P_DamageMobj` only rejects the damage when the inflictor lacks `+FOILINVUL`, and the inflictor here is the calling actor, so a caller with `+FOILINVUL` bypasses the target's invulnerability (`p_interaction.cpp:1212-1220`).

## Difference from ZDoom Wiki version

The **ZDoom Wiki page describes a much more complex version** of `A_KillChildren` with many additional parameters (`flags`, `filter`, `species`, `src`, `inflict`) and filtering options (`KILS_FOILINVUL`, `KILS_KILLMISSILES`, `KILS_NOMONSTERS`, etc.) that **do not exist in Zandronum 3.2.1**. The Zandronum version is substantially simpler — it only supports a single optional `damagetype` parameter and uses the master-pointer relationship for targeting, with no class/species filtering, no flag options, and no missile targeting.

If you are porting DECORATE code from upstream ZDoom/GZDoom to Zandronum, do not expect the wiki's extended parameter list to work; use the simpler Zandronum signature.

## Engine-family divergence: parameter set

**UZDoom implements the full wiki-documented signature**, unlike Zandronum: `A_KillChildren(name damagetype = "none", int flags = 0, class<Actor> filter = null, name species = "None", int src = AAPTR_DEFAULT, int inflict = AAPTR_DEFAULT)` (`wadsrc/static/zscript/actors/actor.zs`, backed by `DEFINE_ACTION_FUNCTION(AActor, A_KillChildren)` in `src/playsim/p_actionfunctions.cpp`). The extended parameter list the previous section says "does not exist" is a Zandronum-only limitation — on UZDoom it exists and behaves as the wiki describes, routed through a `DoKill` helper shared with `A_KillTarget`, `A_KillTracer`, `A_KillMaster`, and `A_KillSiblings`:

- **`flags`** is a bitmask: `KILS_FOILINVUL` bypasses the `INVULNERABLE` exemption noted above (adds `DMG_FOILINVUL` to the damage call); `KILS_FOILBUDDHA` similarly bypasses Buddha-mode; `KILS_KILLMISSILES` additionally routes missile children through `P_ExplodeMissile` instead of `P_DamageMobj`; `KILS_NOMONSTERS` suppresses the `P_DamageMobj` call entirely (only the missile-explosion effect, if also flagged, still happens); `KILS_EXFILTER`/`KILS_EXSPECIES` invert the `filter`/`species` match; `KILS_EITHER` ORs the filter and species checks together instead of requiring both to pass.
- **`filter`** and **`species`** narrow which children are killed, by actor class and by `species` name respectively (both must pass, unless `KILS_EITHER` is set).
- **`src`** and **`inflict`** (resolved via `COPY_AAPTR`) let the caller pick which actor is reported as the damage source and inflictor instead of always using the calling actor itself for both, as Zandronum does unconditionally.

The base damage call is otherwise unchanged from Zandronum's: each child is damaged for its own current `health` with `DMG_NO_ARMOR | DMG_NO_FACTOR` always applied (the `flags` bits above only ever add further `DMG_*` bits or skip the call, never remove those two), so a UZDoom `A_KillChildren("")` call with no extra arguments behaves the same as Zandronum's. The per-target damage amount (`killtarget->health`) is read fresh from each child inside the shared `DoKill` helper rather than being passed down as a single shared value, so — unlike a healing/damage-loop helper found elsewhere in this tree that mutates its `amount` parameter in place across targets — there is no cross-target state to corrupt here on either engine.

## Zandronum-specific: network behavior

**Zandronum multiplayer:** Unlike `A_KillSiblings`, this action has no server-only guard of its own, so a client running the calling state executes the loop too. In practice the result is still server-authoritative: the `master` pointer is never replicated to clients, so on a client the loop normally matches nothing, and `P_DamageMobj` only calls `Die` on the server. Affected clients receive the resulting death and pain transitions from the server.

**UZDoom has no equivalent split.** UZDoom/GZDoom-family engines have no server-authoritative/client-prediction distinction for action-function execution at all — `A_KillChildren`'s implementation (and the `DoKill` helper it shares with its siblings) contains no `NETWORK_InClientMode`-style check or `SERVERCOMMANDS_*`-style replication call anywhere in the call chain. It simply runs the full iterate-and-damage loop wherever it's invoked.

## Related actions

- **`A_SpawnItemEx`** — the typical way to spawn actors as children (with `SXF_SETMASTER` to establish the master relationship).
- **`A_KillMaster`** — destroys the calling actor's own master instead of its children.
- **`A_KillSiblings`** — destroys all other actors that share the same master.
- **`A_DamageChildren`** — damages children by a fixed amount instead of killing them outright (also more complex in upstream ZDoom; Zandronum's version is simpler).
- **`A_RemoveChildren`** — removes (removes without death animation) all children instead of damaging them.
