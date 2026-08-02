# `A_SpawnItem` (spawn an actor with angular distance)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_SpawnItem` (retrieved 2026-08-01, oldid=46930) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2520-2582` and the shared `InitSpawnedItem` helper (`src/thingdef/thingdef_codeptr.cpp:2394-2510`).
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SpawnItem)` in `src/thingdef/thingdef_codeptr.cpp`.

Spawns an actor at a specified distance (relative to the calling actor's facing angle) and vertical height, with optional ammo consumption and translation transfer. A simpler predecessor to `A_SpawnItemEx` — use `A_SpawnItemEx` if you need explicit offsets, velocity, or advanced flags.

**Wiki note:** The ZDoom wiki describes this function as returning two values (a `bool` plus an `Actor` pointer). **Zandronum only returns a single boolean** (the result slot) — there is no actor-pointer return channel in Zandronum's DECORATE. The wiki's example is also in ZScript (`class`/`Default` block syntax), not DECORATE.

## Signature

```
bool A_SpawnItem(class<Actor> itemtype = "Unknown", float distance = 0, float zheight = 0, 
                 bool useammo = true, bool transfer_translation = false)
```

**Note on types:** The DECORATE parameter types are `float` (fixed-point in the engine), not `double` as the wiki may suggest for other engines.

## Parameters

### `itemtype` (class<Actor>, default `"Unknown"`)

The actor class to spawn. If the class is invalid or null, the action sets the result to `false` and returns immediately.

### `distance` (float, default `0`)

Spawn distance from the calling actor, relative to its facing angle. Positive values place the spawned actor forward, negative values backward. 

**Special behavior when `distance == 0`:** Instead of spawning at exactly the same location as the caller, the distance is automatically set to avoid overlap. Specifically, the engine uses `(calling_actor.radius + spawned_actor.radius) >> FRACBITS` — the sum of both radii, converted from fixed-point to map units. This is a **silent substitution**: the code does not modify your parameter, but the spawn point changes if you pass `0`. To spawn at the same location, use a very small non-zero value (e.g., `0.1`). The angle is applied via `FixedMul(distance, finecosine[angle])` for X and `FixedMul(distance, finesine[angle])` for Y.

### `zheight` (float, default `0`)

Spawn height relative to the calling actor. Positive values place the spawned actor upward, negative values downward. The actual Z coordinate also includes `self->GetBobOffset()` (player bobbing, if applicable) and subtracts `floorclip` from the caller's Z.

### `useammo` (bool, default `true`)

Dual purpose:

1. **Ammo depletion** (if called from a weapon state): If `true` and the calling weapon has ammo, the weapon's `DepleteAmmo(bAltFire)` is called. If `false`, ammo is not consumed. If the weapon has no ammo remaining and `useammo` is `true`, the action returns early (without setting the result, leaving it unchanged from any prior action).

2. **Master/minion relationship** (via `InitSpawnedItem`): If `true`, the spawned actor becomes a "minion" of the calling actor via `SIXF_SETMASTER` — the spawned actor's `master` pointer is set to the calling actor. Minions do not attack their master, and both can be affected by `A_DamageMaster` and `A_GiveToChildren`. If `false`, no master/minion relationship is formed.

**Caveat:** If the function is called from a weapon and the weapon is NULL or `DepleteAmmo` fails (no ammo), the action returns early without calling `ACTION_SET_RESULT`. This differs from a successful spawn, which always sets the result. The calling state's prior result (or default) remains if an early ammo failure occurs.

### `transfer_translation` (bool, default `false`)

If `true`, the spawned actor inherits the calling actor's color translation (if the spawned actor's `MF2_DONTTRANSLATE` flag is unset). If `false`, no translation is copied.

## Originator and friendliness

For monster-based spawned actors, `InitSpawnedItem` determines the spawned actor's friendliness based on the "originator" — the ultimate non-missile spawner. See `A_SpawnItemEx`'s documentation for the full originator concept; A_SpawnItem uses the same logic. In brief:

- If both the originator and spawned actor are monsters, the spawned actor copies the originator's friendliness.
- If the originator is a player, the spawned actor is friendly to that player.
- If there is no valid originator, normal monster behavior applies.

## Monster spawn restrictions

If the calling actor was killed by a massacre (its `DamageType` is `NAME_Massacre`) and the spawned actor class is monster-based (`MF3_ISMONSTER` flag set), the spawn does not occur at all. The action returns early without setting the result, preventing re-spawning during a player elimination.

For non-monster-based spawned actors, the massacre check does not apply and the spawn proceeds normally.

## Space validation (monsters only)

If the spawned actor is monster-based, Zandronum calls `P_TestMobjLocation(mo)` to ensure the spawn point is passable. If the test fails, the actor is immediately destroyed (via `ClearCounters()` followed by `Destroy()` — `ClearCounters()` prevents kill-count inflation), and the action sets the result to `false`. This validation is automatically performed and cannot be bypassed via flags (unlike `A_SpawnItemEx`'s `SXF_NOCHECKPOSITION`).

## Network behavior (Zandronum multiplayer)

Zandronum's server is authoritative for all spawn decisions:

- **Network gate check:** If `NETWORK_ShouldActorNotBeSpawned(self, missile)` returns true (server denies the spawn), the action returns early without setting the result.

- **Server broadcast on success:** If spawning on the server and the spawn succeeds:
  - `SERVERCOMMANDS_SpawnThing(mo)` broadcasts the spawn to all clients.
  - If the spawned actor's angle is non-zero, `SERVERCOMMANDS_SetThingAngle(mo)` is sent.
  - If the spawned actor received a translation (from `transfer_translation`), `SERVERCOMMANDS_SetThingTranslation(mo)` is sent.

- **Client-side-only behavior:** When the action is called in client mode and the spawn succeeds (not blocked by `NETWORK_ShouldActorNotBeSpawned`), the spawned actor gets the `NETFL_CLIENTSIDEONLY` flag set, marking it as a visual-only client update.

## Return value

**Zandronum-specific behavior:** The action sets a single boolean result:

- `true` if the spawn succeeded (the actor was created and passed space validation, if applicable).
- `false` if the spawn failed (null missile class, failed space check, or certain network gates).

**Important:** Several error conditions return early **without calling `ACTION_SET_RESULT`**, leaving the result unchanged:
- Massacre check (calling actor was eliminated).
- Weapon is NULL or ammo depletion fails (when called from a weapon).
- Network gate denies the spawn (`NETWORK_ShouldActorNotBeSpawned`).

In these cases, the action's result remains whatever the prior action in the state set it to (or the actor's default). **Do not rely on the result alone to detect failure.** If precise failure detection is needed, use a helper variable or call a diagnostic action before `A_SpawnItem` to confirm the spawn conditions (e.g., check `player->ReadyWeapon` and weapon ammo before calling).

## Relationship to A_SpawnItemEx

`A_SpawnItemEx` is the modern, feature-rich successor to `A_SpawnItem`. The key differences:

| Feature | A_SpawnItem | A_SpawnItemEx |
|---------|---|---|
| Spawn offsets | Fixed forward/up relative to angle | Explicit X/Y/Z offsets with flags |
| Spawn velocity | None (always 0,0,0) | Explicit with flags for relative/absolute |
| Angle control | Always copies caller's angle | Adjustable with flags |
| Master/minion | Tied to `useammo` parameter | Explicit `SXF_SETMASTER` flag |
| Property transfer | Translation and master only | 15+ transfer flags (scale, pointers, special, etc.) |
| Space check bypass | No (always validated for monsters) | `SXF_NOCHECKPOSITION` flag |
| Telefrag support | No | `SXF_TELEFRAG` flag |
| Result behavior | Doesn't set on some failures | Always sets (or early-returns on `failchance`) |

**For new code, prefer `A_SpawnItemEx`** — it is more predictable and feature-complete. Use `A_SpawnItem` only if you need the simplicity of automatic forward-distance spawning and don't require velocity or advanced flags.

## Example (Zandronum DECORATE)

```
actor TimeBomb : Actor
{
    Default
    {
        Radius 8;
        Height 16;
        Mass 50;
        DeathSound "bomb/explode";
    }

    States
    {
    Spawn:
        Tbomb A 10;
        Loop;
    Death:
        Tbomb A 0 A_Scream;
        TOMB B 20 A_SpawnItem("BombDebris", 64, 24);
        TOMB C 5 A_Explode(100, 128);
        Stop;
    }
}

actor BombDebris : Actor
{
    Default
    {
        Radius 4;
        Height 8;
        Speed 5;
    }

    States
    {
    Spawn:
        DEBR A 20;
        Stop;
    }
}
```

## Open questions and untraced details

- Exact behavior of the `distance == 0` substitution with negative radii (should be impossible for valid actors, but the code does not guard against it).
- Whether `GetBobOffset()` ever returns non-zero when called from non-player-pawn actors (the code unconditionally adds it).
- Interaction between early-return paths (ammo/weapon/network failures) and the calling state's prior result — whether the prior result persists or defaults to `false` if no action before `A_SpawnItem` explicitly set it.
