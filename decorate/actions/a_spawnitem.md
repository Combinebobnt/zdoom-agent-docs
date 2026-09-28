# `A_SpawnItem` (spawn an actor with angular distance)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_SpawnItem` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SpawnItem&oldid=46930) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2520-2582` and the shared `InitSpawnedItem` helper (`src/thingdef/thingdef_codeptr.cpp:2394-2510`); result slot and weapon-call test `src/thingdef/thingdef.h:435-439`, `CallStateChain` preset `src/thingdef/thingdef_codeptr.cpp:135-150`, network gate `src/thingdef/thingdef_codeptr.cpp:105-124`, `GetBobOffset` `src/actor.h:885-892`, `DepleteAmmo` `src/g_shared/a_weapons.cpp:713-756`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SpawnItem)` in `src/thingdef/thingdef_codeptr.cpp`.

Spawns an actor at a specified distance (relative to the calling actor's facing angle) and vertical height, with optional ammo consumption and translation transfer. A simpler predecessor to `A_SpawnItemEx` — use `A_SpawnItemEx` if you need explicit offsets, velocity, or advanced flags.

**Wiki note:** The ZDoom wiki describes this function as returning two values (a `bool` plus an `Actor` pointer). **Zandronum DECORATE has no return values at all.** The action only writes a boolean into the CustomInventory result slot, which nothing but a CustomInventory state chain reads (see "Return value" below). There is no actor-pointer channel. The wiki's example is also in ZScript (`class`/`Default` block syntax), not DECORATE.

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

**`distance == 0` substitution is ineffective.** The code is commented "use the minimum distance that does not result in an overlap" and replaces a `0` with `(self->radius + default radius of itemtype) >> FRACBITS`. But `distance` is itself a fixed-point value, so shifting the radius sum down to whole map units and storing it back as fixed-point leaves an offset of `(r1 + r2) / 65536` map units (e.g. radii 20 and 16 give 36/65536 of a unit). In practice `distance = 0` spawns at the caller's X/Y. There is no automatic overlap avoidance; pass the radius sum yourself if you want it. The angle is applied via `FixedMul(distance, finecosine[angle])` for X and `FixedMul(distance, finesine[angle])` for Y.

### `zheight` (float, default `0`)

Spawn height relative to the calling actor. Positive values place the spawned actor upward, negative values downward. The actual Z coordinate also includes `self->GetBobOffset()` and subtracts `floorclip` from the caller's Z. `GetBobOffset()` is the caller's `+FLOATBOB` bob height; it is 0 for any actor without `+FLOATBOB` (it has nothing to do with player view bobbing).

### `useammo` (bool, default `true`)

Dual purpose:

1. **Ammo depletion** (if called from a weapon state, i.e. a player's action running from a state other than its own actor state and outside a CustomInventory chain): If `true`, the weapon's `DepleteAmmo(bAltFire)` is called, which checks for enough ammo for one use and then deducts it. If there is not enough, nothing spawns. If `false`, ammo is neither checked nor consumed. With `DF_INFINITE_AMMO` or the infinite-ammo cheat, `DepleteAmmo` succeeds without deducting anything. If the player has no `ReadyWeapon`, nothing spawns regardless of `useammo`.

2. **Master/minion relationship** (via `InitSpawnedItem`): If `true`, the call passes `SIXF_SETMASTER`. That only takes effect when the spawned actor and the originator (see below) are both monsters (`+ISMONSTER`); the spawned actor's `master` is then set to the originator, which is the caller unless the caller is a missile. For any other combination (a player spawning a monster, a monster spawning a non-monster, etc.) `master` is not set. Minions do not attack their master, and both can be affected by `A_DamageMaster` and `A_GiveToChildren`. If `false`, no master/minion relationship is formed. The `master` pointer is never sent to clients, so it only exists on the server (or in single player).

### `transfer_translation` (bool, default `false`)

If `true`, the spawned actor inherits the calling actor's color translation (if the spawned actor's `MF2_DONTTRANSLATE` flag is unset). If `false`, no translation is copied.

## Originator and friendliness

For monster-based spawned actors, `InitSpawnedItem` determines the spawned actor's friendliness based on the "originator" — the ultimate non-missile spawner. See `A_SpawnItemEx`'s documentation for the full originator concept; A_SpawnItem uses the same logic. In brief:

- If both the originator and spawned actor are monsters, the spawned actor copies the originator's friendliness.
- If the originator is a player, the spawned actor is friendly to that player.
- If there is no valid originator, normal monster behavior applies.

## Monster spawn restrictions

If the calling actor was killed by a massacre (its `DamageType` is `NAME_Massacre`, as set by the `massacre` cheat and other kill-all-monsters paths) and the spawned actor class is monster-based (`MF3_ISMONSTER` flag set), the spawn does not occur at all. The action returns early without touching the result slot, so a massacred monster's death state cannot spawn new monsters.

For non-monster-based spawned actors, the massacre check does not apply and the spawn proceeds normally.

## Space validation (monsters only)

If the spawned actor is monster-based, Zandronum calls `P_TestMobjLocation(mo)` to ensure the spawn point is passable. If the test fails, the actor is immediately destroyed (via `ClearCounters()` followed by `Destroy()` — `ClearCounters()` prevents kill-count inflation), and the action sets the result to `false`. This validation is automatically performed and cannot be bypassed via flags (unlike `A_SpawnItemEx`'s `SXF_NOCHECKPOSITION`).

## Network behavior (Zandronum multiplayer)

Clients run the action too (their copy of the actor enters the same state), so who actually spawns is decided by a local gate:

- **Network gate check:** `NETWORK_ShouldActorNotBeSpawned(self, missile)` counts the spawn as client-side when the caller or the spawned class's defaults carry `NETFL_CLIENTSIDEONLY`. A client skips every spawn that is not client-side (the server's copy delivers it instead). The server skips every spawn that is client-side. When the gate skips, the action returns early without touching the result slot. Ammo has already been deducted by then in the weapon path.

- **Server broadcast on success:** If spawning on the server and the spawn succeeds:
  - `SERVERCOMMANDS_SpawnThing(mo)` broadcasts the spawn to all clients.
  - If the spawned actor's angle is non-zero, `SERVERCOMMANDS_SetThingAngle(mo)` is sent.
  - If the spawned actor has any non-zero `Translation` (transferred or its own), `SERVERCOMMANDS_SetThingTranslation(mo)` is sent.

- **Client-side-only behavior:** A spawn that gets past the gate on a client is by definition client-side, and the spawned actor gets `NETFL_CLIENTSIDEONLY` set.

## Engine-family divergence: two-value return matches the wiki

The "Wiki note" above states Zandronum has no actor-pointer return channel. That is a
Zandronum-specific limitation, not a UZDoom one: UZDoom's `A_SpawnItem`
(`wadsrc/static/zscript/actors/attacks.zs`, declared `action bool, Actor A_SpawnItem(...)`)
returns two values exactly as the ZDoom Wiki describes — a `bool` plus an `Actor` pointer. Code
targeting UZDoom/GZDoom-family engines can capture the second return value (e.g. `bool ok, Actor
mo = A_SpawnItem(...)`); Zandronum DECORATE cannot capture either value. The `Actor` slot is
`null` on the null-`missile`-class path, the NULL-`player` path, and the massacre/no-ammo
short-circuits (see the next section) — but **not** on the monster-space-check-blocked path: there,
`InitSpawnedItem` calls `mo.Destroy()` and then returns `false`, and `A_SpawnItem` still returns
that same (now-destroyed) `mo` reference as its second value rather than substituting `null`.
Code capturing the actor pointer should check the `bool` first rather than assuming a non-null
second value is safe to use.

## Engine-family divergence: `distance == 0` has no overlap-avoidance substitution

Zandronum's `distance == 0` case has substitution code, but it only moves the spawn point by a
fraction of a map unit (see "`distance == 0` substitution is ineffective" above), so both engines
spawn a `distance = 0` actor at essentially the caller's X/Y. UZDoom's implementation has no
substitution at all:
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

On Zandronum the action returns nothing a caller can capture. It only writes the CustomInventory
result slot, and its early-return paths (massacre check, network gate) leave that slot at the
`true` it was preset to (see "Return value" below). On UZDoom the result is an explicit return
value: every code path in `A_SpawnItem`
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
tell apart from the bool alone. Zandronum's CustomInventory result behaves the same way for its
own early exits: a massacre or network-gate skip also reads as success.

## Engine-family divergence: no client/server authority split

UZDoom's `A_SpawnItem` has no `NETWORK_ShouldActorNotBeSpawned`/`SERVERCOMMANDS_*`-style gate at
all (zero occurrences of either symbol anywhere in the UZDoom source tree). None of the "Network
behavior (Zandronum multiplayer)" section above applies to UZDoom: there is no network gate
check, no server-to-client spawn/angle/translation broadcast, and no client-side-only flagging on
the spawned actor — the action simply spawns (or doesn't) identically wherever it runs.

## Return value

**Zandronum-specific behavior:** Zandronum DECORATE has no return values or `if`. The action's only result is the CustomInventory result slot, which is written only when the action runs inside a CustomInventory state chain (`Use`, `Pickup`, `Drop`) and read only by that chain to decide whether the item use or pickup succeeded. In actor and weapon states nothing is written or read.

Inside a chain, `CallStateChain` presets the slot to `true` before each action. `A_SpawnItem` then sets:

- `false` for a null `itemtype`, or a monster that failed its space check.
- The `InitSpawnedItem` result (`true`) for a completed spawn.

The massacre check and the network gate return without writing the slot, so they leave the preset `true`. A chain whose only action is a skipped `A_SpawnItem` therefore still counts as a successful use. (The weapon/ammo path cannot run inside a chain, since it requires that no chain is active.) **Do not rely on the result alone to detect that something spawned.**

## Relationship to A_SpawnItemEx

`A_SpawnItemEx` is the modern, feature-rich successor to `A_SpawnItem`. The key differences:

| Feature | A_SpawnItem | A_SpawnItemEx |
|---------|---|---|
| Spawn offsets | Fixed forward/up relative to angle | Explicit X/Y/Z offsets with flags |
| Spawn velocity | None (always 0,0,0) | Explicit with flags for relative/absolute |
| Angle control | Always copies caller's angle | Adjustable with flags |
| Master/minion | Tied to `useammo` parameter | Explicit `SXF_SETMASTER` flag |
| Property transfer | Translation and master only | `SXF_*` flag word (Zandronum has 18 flags: pointers, pitch, scale, special, ambush, blood color, etc.) |
| Space check bypass | No (always validated for monsters) | `SXF_NOCHECKPOSITION` flag |
| Telefrag support | No | `SXF_TELEFRAG` flag |
| Result (Zandronum, CustomInventory chains only) | `false` on null class or blocked monster; massacre/network-gate skips leave the preset `true` | Same, plus the `failchance` skip also leaves `true` |

**For new code, prefer `A_SpawnItemEx`** — it is more predictable and feature-complete. Use `A_SpawnItem` only if you need the simplicity of automatic forward-distance spawning and don't require velocity or advanced flags.

## Example (Zandronum DECORATE)

```text
actor TimeBomb
{
    Health 20
    Radius 8
    Height 16
    Mass 50
    DeathSound "bomb/explode"
    +SHOOTABLE
    +NOBLOOD

    States
    {
    Spawn:
        TBOM A 10
        Loop
    Death:
        TBOM A 0 A_Scream
        TBOM B 20 A_SpawnItem("BombDebris", 64, 24)
        TBOM C 5 A_Explode(100, 128)
        Stop
    }
}

actor BombDebris
{
    Radius 4
    Height 8

    States
    {
    Spawn:
        DEBR A 20
        Stop
    }
}
```

## Open questions and untraced details

- Exact behavior of the `distance == 0` substitution with negative radii (should be impossible for valid actors, but the code does not guard against it).
