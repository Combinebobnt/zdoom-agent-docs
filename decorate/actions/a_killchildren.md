# `A_KillChildren` (destroy spawned children)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_KillChildren` (retrieved 2026-08-01, oldid=46804) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3561-3576`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_KillChildren)` in `src/thingdef/thingdef_codeptr.cpp`.

Destroys all actors whose master pointer is set to the calling actor, typically creatures spawned by the calling actor. Damage is applied without armor/damage factor modifiers.

## Signature

```
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

## Network behavior

**Zandronum multiplayer:** This action is handled by the server. The iteration and damage calls are resolved server-side; affected clients receive state updates (death/pain transitions) from the server.

## Related actions

- **`A_SpawnItemEx`** — the typical way to spawn actors as children (with `SXF_SETMASTER` to establish the master relationship).
- **`A_KillMaster`** — destroys the calling actor's own master instead of its children.
- **`A_KillSiblings`** — destroys all other actors that share the same master.
- **`A_DamageChildren`** — damages children by a fixed amount instead of killing them outright (also more complex in upstream ZDoom; Zandronum's version is simpler).
- **`A_RemoveChildren`** — removes (removes without death animation) all children instead of damaging them.
