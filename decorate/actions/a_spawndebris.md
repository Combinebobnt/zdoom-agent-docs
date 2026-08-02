# `A_SpawnDebris` (spawning debris particles from an actor's health counter)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_SpawnDebris` (retrieved 2026-08-01, oldid=43415) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3215-3277`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SpawnDebris)` in `src/thingdef/thingdef_codeptr.cpp`.

Spawns multiple debris actors around the calling actor, using the debris class's `Health` value as a count. Each spawned piece is assigned one of the debris class's declared states and thrown with randomized velocity.

## Signature

```
void A_SpawnDebris(class<Actor> type [, bool translation [, fixed mult_h [, fixed mult_v]]])
```

**Note on types:** The ZDoom wiki lists parameters as `string type` and `float` multipliers. Zandronum DECORATE uses `class<Actor>` for the actor class (not a string), and `fixed`-point values (1.0 = `FRACUNIT`) rather than `double` for the multipliers.

## Parameters

### `type` (class<Actor>)

The debris actor class to spawn. Required; if null, the action returns without spawning. The debris class must declare a `Health` value specifying how many pieces to spawn — the first `Health` **states declared directly in that class** are assigned to the spawned pieces in order. Inherited states are not used for the count.

### `translation` (bool, default `false`)

If `true`, each spawned debris actor receives the calling actor's color translation table (the `Translation` property). Defaults to `false` — spawned actors inherit their class's default translation.

### `mult_h` (fixed, default `FRACUNIT` / 1.0)

Multiplier for the horizontal (X and Y) velocity components of spawned debris. Units are fixed-point (1.0 = `FRACUNIT`). **Clamped to a minimum of `FRACUNIT`** — passing 0, negative values, or values less than 1.0 all result in `FRACUNIT` (no velocity reduction). This means **horizontal velocity cannot be eliminated by this parameter**.

### `mult_v` (fixed, default `FRACUNIT` / 1.0)

Multiplier for the vertical (Z) velocity component. Units are fixed-point. **Clamped to a minimum of `FRACUNIT`** — passing 0 or negative values defaults to `FRACUNIT`. Vertical velocity is always positive (upward).

## Behavior

### Spawn count and state assignment

For each debris actor spawned (count = `Health` of the debris template):
- The actor is positioned around the calling actor's center with random X/Y offsets (roughly ±8 map units) and Z positioned uniformly between the calling actor's feet and top (plus any bob offset).
- If the piece index is less than the number of states declared in the debris class (`NumOwnedStates`), the piece is assigned the corresponding state from the class's `OwnedStates` array. If the index exceeds the declared state count, the debris actor uses its default `Spawn` state instead.
- **A debris class with zero declared states results in all pieces using the default spawn state.**
- **A Health value of 0 or less results in no debris being spawned.**

### Velocity

Each spawned piece receives randomized velocity:
- **X velocity:** `mult_h * Random2()` scaled by fixed-point encoding (~±4 map units/tic per unit of `mult_h`).
- **Y velocity:** `mult_h * Random2()` scaled by fixed-point encoding (~±4 map units/tic per unit of `mult_h`).
- **Z velocity:** Always positive (upward). Range is 5–12 map units/tic times `mult_v`, selected as `((random(0,7))+5) * mult_v`.

### Translation

If `translation` is true, the debris actor's `Translation` is set to match the calling actor's translation **before** the piece's initial state is assigned.

## Zandronum multiplayer behavior — velocity replication bug

**In Zandronum multiplayer, debris velocity is never replicated to clients.** Each debris actor is spawned on the server and sent to all clients via `SERVERCOMMANDS_SpawnThing`, which does not include velocity information (only class, position, and netID). The velocities are then set on the server's actor instance (lines 3268–3270 of the source), but the sync command that follows (`SERVERCOMMANDS_MoveThing` at line 3274) targets the **calling actor** (`self`), not the spawned debris actor (`mo`).

**Consequence:** Clients see debris appear with zero velocity and fall under local physics, while the server sees the same debris thrown. This is observable as a desync in debris trajectories between server and clients, particularly noticeable at distance or when debris is long-lived.

Related discussion: `decorate/concepts/crash-and-bug-checklist.md` may cover multiplayer-specific action-function gotchas.

## Example

```
ACTOR SentinelDebris
{
  Health 15
  Radius 1
  Height 1
  States
  {
  Spawn:
    SNT1 A -1
    SNT2 A -1
    SNT3 A -1
    SNT3 A -1
    SNT4 A -1
    SNT4 A -1
    SNT5 A -1
    SNT6 A -1
    SNT7 A -1
    SNT7 A -1
    SNT8 A -1
    SNT8 A -1
    SNT9 A -1
    SNT9 A -1
    SNT0 A -1
  }
}

ACTOR DestructiblePillar
{
  Health 50
  States
  {
  Death:
    PILR A 0 A_SpawnDebris("SentinelDebris", true, 1.5, 2.0);
    PILR A 10 A_Explode(20, 128);
    Stop;
  }
}
```

This spawns 15 debris pieces (per `SentinelDebris` Health), assigns the first 15 sprites/frames from `SentinelDebris`'s `Spawn` state, transfers the pillar's translation to each piece, and throws them with 1.5× horizontal velocity and 2.0× vertical velocity.

## See also

- `A_SpawnItemEx` — a more flexible spawning function with per-actor offsets and control flags, preferred when fine control is needed.
