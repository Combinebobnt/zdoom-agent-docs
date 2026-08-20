# `A_KillChildren` (destroy spawned children)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_KillChildren` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_KillChildren&oldid=46804) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3561-3576`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_KillChildren)` in `src/thingdef/thingdef_codeptr.cpp`.

Destroys all actors whose master pointer is set to the calling actor, typically creatures spawned by the calling actor. Damage is applied without armor/damage factor modifiers.

## Signature

```text
void A_KillChildren([str damagetype])
```

## Parameters

### `damagetype` (str, optional)

The damage type to apply when killing the children. This determines which death state the victims enter (if they have specialized death states for this damage type), or falls back to the pain state if they have the `NODAMAGE` flag.

Default: `NAME_None` (generic damage type).

## Behavior

When called, this action:

1. **Iterates all actors in the current map** using a global thinker iterator.
2. **Identifies children** by checking if `mo->master == self` (the victim's master pointer equals the calling actor).
3. **Damages each child to death** by calling `P_DamageMobj(mo, self, self, mo->health, damagetype, DMG_NO_ARMOR | DMG_NO_FACTOR)`.
   - Damage amount equals the victim's current health, typically killing it instantly.
   - `DMG_NO_ARMOR` prevents damage reduction from armor properties.
   - `DMG_NO_FACTOR` prevents damage scaling/modifiers.
4. **Continues iterating** through all remaining actors; multiple victims can be killed in one call.

## Master relationship and scope

A child's master relationship is typically established via `A_SpawnItemEx(..., SXF_SETMASTER)` — this action sets the `master` pointer of the spawned actor to point back to the spawner. The `A_KillChildren` action then uses that relationship to identify and destroy victims.

**Important limitation:** Actors spawned with `A_SpawnProjectile` are **not affected** by `A_KillChildren`. The `A_SpawnProjectile` action does not set the `master` pointer and was never designed to spawn creatures targeted by this action. Only use `A_SpawnItemEx` with the `SXF_SETMASTER` flag if you intend to later destroy spawned actors via `A_KillChildren`.

## Damage and state handling

- The victims enter death states **determined by the `damagetype` parameter** — if provided, the engine looks for a death state specific to that damage type (e.g., `Death.Voodoo`).
- If no such state exists, the engine falls back to the generic `Death` state.
- Victims with the `NODAMAGE` flag enter their pain state instead of dying, but `A_KillChildren` still applies the damage and respects the damage type for pain-state selection.
- Victims with the `INVULNERABLE` flag are **unaffected** by this action — they cannot be killed this way.

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

**Zandronum multiplayer:** This action is handled by the server. The iteration and damage calls are resolved server-side; affected clients receive state updates (death/pain transitions) from the server.

**UZDoom has no equivalent split.** UZDoom/GZDoom-family engines have no server-authoritative/client-prediction distinction for action-function execution at all — `A_KillChildren`'s implementation (and the `DoKill` helper it shares with its siblings) contains no `NETWORK_InClientMode`-style check or `SERVERCOMMANDS_*`-style replication call anywhere in the call chain. It simply runs the full iterate-and-damage loop wherever it's invoked.

## Related actions

- **`A_SpawnItemEx`** — the typical way to spawn actors as children (with `SXF_SETMASTER` to establish the master relationship).
- **`A_KillMaster`** — destroys the calling actor's own master instead of its children.
- **`A_KillSiblings`** — destroys all other actors that share the same master.
- **`A_DamageChildren`** — damages children by a fixed amount instead of killing them outright (also more complex in upstream ZDoom; Zandronum's version is simpler).
- **`A_RemoveChildren`** — removes (removes without death animation) all children instead of damaging them.
