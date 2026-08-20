# `A_SpawnItem` (spawn an actor with angular distance)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_SpawnItem` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SpawnItem&oldid=46930) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2520-2582` and the shared `InitSpawnedItem` helper (`src/thingdef/thingdef_codeptr.cpp:2394-2510`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SpawnItem)` in `src/thingdef/thingdef_codeptr.cpp`.

Spawns an actor at a specified distance (relative to the calling actor's facing angle) and vertical height, with optional ammo consumption and translation transfer. A simpler predecessor to `A_SpawnItemEx` — use `A_SpawnItemEx` if you need explicit offsets, velocity, or advanced flags.

**Wiki note:** The ZDoom wiki describes this function as returning two values (a `bool` plus an `Actor` pointer). **Zandronum only returns a single boolean** (the result slot) — there is no actor-pointer return channel in Zandronum's DECORATE. The wiki's example is also in ZScript (`class`/`Default` block syntax), not DECORATE.

## Signature

```text
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

## Engine-family divergence: two-value return matches the wiki

The "Wiki note" above states Zandronum has no actor-pointer return channel. That is a
Zandronum-specific limitation, not a UZDoom one: UZDoom's `A_SpawnItem`
(`wadsrc/static/zscript/actors/attacks.zs`, declared `action bool, Actor A_SpawnItem(...)`)
returns two values exactly as the ZDoom Wiki describes — a `bool` plus an `Actor` pointer. Code
targeting UZDoom/GZDoom-family engines can capture the second return value (e.g. `bool ok, Actor
mo = A_SpawnItem(...)`); the same call in Zandronum only yields the boolean. The `Actor` slot is
`null` on the null-`missile`-class path, the NULL-`player` path, and the massacre/no-ammo
short-circuits (see the next section) — but **not** on the monster-space-check-blocked path: there,
`InitSpawnedItem` calls `mo.Destroy()` and then returns `false`, and `A_SpawnItem` still returns
that same (now-destroyed) `mo` reference as its second value rather than substituting `null`.
Code capturing the actor pointer should check the `bool` first rather than assuming a non-null
second value is safe to use.

## Engine-family divergence: `distance == 0` has no overlap-avoidance substitution

Zandronum's `distance == 0` case silently substitutes `(calling_actor.radius +
spawned_actor.radius) >> FRACBITS` to avoid spawning the new actor exactly on top of the caller
(see "Special behavior when `distance == 0`" above). UZDoom's implementation has no equivalent:
the raw `distance` parameter (including an unmodified `0`) is passed straight to
`Vec3Angle(distance, Angle, ...)`, a native double-precision helper (`AActor::Vec3Angle`,
`src/playsim/actorinlines.h`) that computes `length * angle.Cos()` / `length * angle.Sin()` with
no radius adjustment anywhere in the call chain. Passing `distance = 0` (or omitting it) in
UZDoom spawns the new actor at the caller's exact X/Y position (offset only by whatever
`zheight`/bob/floorclip produce on Z) — there is no built-in overlap avoidance. Also incidental:
UZDoom's angle math uses native `double`/`DAngle::Cos()`/`Sin()` throughout, not the fixed-point
`finecosine`/`finesine` tables and `FixedMul` Zandronum's version uses; this doesn't change
observable results for in-range values, but it is a different code path.

## Engine-family divergence: result is always set, but true isn't a spawn-success signal

The "Return value" section below documents several Zandronum early-return paths (massacre check,
NULL/out-of-ammo weapon, network gate) that skip `ACTION_SET_RESULT` entirely, leaving the result
at whatever a prior action in the state set it to. **UZDoom's implementation has no such
ambiguity**: every code path in `A_SpawnItem`
(`wadsrc/static/zscript/actors/attacks.zs:391-422`) ends in an explicit `return <bool>, <Actor>` —
`false, null` for a null `missile` class or a NULL `player` when called from a weapon state;
`true, null` for the massacre-check short-circuit *and* for a NULL or out-of-ammo weapon; and
`res, mo` (from `InitSpawnedItem`'s own return) for an actual spawn attempt.

That does not make the boolean a reliable "did an actor spawn" signal, though — it means something
narrower. `InitSpawnedItem(mo, flags)` is called "for an inventory item's use state" per its own
comment, and the massacre/no-ammo short-circuits deliberately return `true` (not `false`) so a
weapon or inventory item's use-state chain treats "declined to spawn because the caller was
massacred" or "declined because there's no ammo" as a non-failure, not as a failed item use. A
`true` result on UZDoom can mean "an actor was spawned and passed validation" **or** "spawning was
skipped for a reason that isn't an item-use failure" — those are different outcomes a caller can't
tell apart from the bool alone. The "do not rely on the result alone to detect failure" caveat
below still applies on UZDoom, just for this reason instead of Zandronum's unset-on-early-return
one; the third bullet under "Open questions and untraced details" about a persisting prior result
is the one part of that caveat that's Zandronum-specific, since UZDoom's bool is always a definite
value even though it isn't always a spawn-success value.

## Engine-family divergence: no client/server authority split

UZDoom's `A_SpawnItem` has no `NETWORK_ShouldActorNotBeSpawned`/`SERVERCOMMANDS_*`-style gate at
all (zero occurrences of either symbol anywhere in the UZDoom source tree). None of the "Network
behavior (Zandronum multiplayer)" section above applies to UZDoom: there is no network gate
check, no server-to-client spawn/angle/translation broadcast, and no client-side-only flagging on
the spawned actor — the action simply spawns (or doesn't) identically wherever it runs.

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

```text
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
