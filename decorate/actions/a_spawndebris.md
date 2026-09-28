# `A_SpawnDebris` (spawning debris particles from an actor's health counter)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_SpawnDebris` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SpawnDebris&oldid=43415) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3215-3277`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SpawnDebris)` in `src/thingdef/thingdef_codeptr.cpp`.

Spawns multiple debris actors around the calling actor, using the debris class's `Health` value as a count. Each spawned piece is assigned one of the debris class's declared states and thrown with randomized velocity.

## Signature

```text
void A_SpawnDebris(class<Actor> spawntype [, bool transfer_translation [, float mult_h [, float mult_v]]])
```

**Note on types:** The ZDoom wiki lists parameters as `string type` and `float` multipliers. Zandronum's DECORATE declaration (`wadsrc/static/actors/actor.txt:231`) takes `class<Actor>` for the actor class (not a string) and declares the multipliers `float` with defaults of 1. You write them as decimals (`1.5`); the native reads them as fixed-point (1.0 = `FRACUNIT`).

## Parameters

### `spawntype` (class<Actor>)

The debris actor class to spawn. Required; if null, the action returns without spawning. The debris class's `Health` value is the number of pieces to spawn. Piece N is assigned the Nth **state declared directly in the spawned class**, when there is one. Inherited states are never assigned.

### `transfer_translation` (bool, default `false`)

If `true`, each spawned debris actor receives the calling actor's color translation table (the `Translation` property). Defaults to `false`, so spawned actors keep their class's default translation.

### `mult_h` (float, default 1.0)

Multiplier for the horizontal (X and Y) velocity components of spawned debris. **Only 0 and negative values are replaced by 1.0.** Positive values below 1.0 are honored and scale the throw down, so a very small positive value all but eliminates horizontal velocity.

### `mult_v` (float, default 1.0)

Multiplier for the vertical (Z) velocity component. As with `mult_h`, 0 or negative values are replaced by 1.0 and positive values below 1.0 scale the throw down. Vertical velocity is always positive (upward).

## Behavior

### Spawn count and state assignment

For each debris actor spawned (count = `Health` of the debris template):
- The actor is positioned around the calling actor's center with random X/Y offsets (roughly ±8 map units) and Z positioned uniformly between the calling actor's feet and top (plus any bob offset).
- If the piece index is less than the number of states declared in the debris class (`NumOwnedStates`), the piece is assigned the corresponding state from the class's `OwnedStates` array. If the index exceeds the declared state count, the debris actor uses its default `Spawn` state instead.
- **A debris class with zero declared states results in all pieces using the default spawn state.**
- **A Health value of 0 or less results in no debris being spawned.**
- Pieces are spawned with replacement allowed. The count always comes from the named class's `Health`, but the state assignment uses the class actually spawned, so a `replaces` class supplies its own declared states.

### Velocity

Each spawned piece receives randomized velocity:
- **X velocity:** `mult_h * Random2()` scaled by fixed-point encoding (~±4 map units/tic per unit of `mult_h`).
- **Y velocity:** `mult_h * Random2()` scaled by fixed-point encoding (~±4 map units/tic per unit of `mult_h`).
- **Z velocity:** Always positive (upward). Range is 5–12 map units/tic times `mult_v`, selected as `((random(0,7))+5) * mult_v`.

### Translation

If `transfer_translation` is true, the debris actor's `Translation` is set to match the calling actor's translation **before** the piece's per-index state is assigned.

## Zandronum-specific: velocity replication bug

**In Zandronum multiplayer, debris velocity is never replicated to clients.** Each debris actor is spawned on the server and sent to all clients via `SERVERCOMMANDS_SpawnThing`, which does not include velocity information (only class, position, and netID). The velocities are then set on the server's actor instance (lines 3268–3270 of the source), but the sync command that follows (`SERVERCOMMANDS_MoveThing` at line 3274) targets the **calling actor** (`self`), not the spawned debris actor (`mo`).

**Consequence:** Clients see debris appear with zero velocity and fall under local physics, while the server sees the same debris thrown. This is observable as a desync in debris trajectories between server and clients, particularly noticeable at distance or when debris is long-lived. Translation and the per-index frame do reach clients (`SERVERCOMMANDS_SetThingTranslation` and `SERVERCOMMANDS_SetThingFrame` are sent for each piece); only velocity is lost.

**Client-side-only debris avoids this.** If the calling actor or the debris class has `+CLIENTSIDEONLY`, `NETWORK_ShouldActorNotBeSpawned` (`src/thingdef/thingdef_codeptr.cpp:105-125`) makes the server skip the action entirely and each client spawns and throws its own pieces locally. Each client rolls its own random offsets and velocities, so pieces differ between clients but are all thrown.

Related discussion: `decorate/concepts/crash-and-bug-checklist.md` may cover multiplayer-specific action-function gotchas.

## Engine-family divergence: no client/server split; native double-typed signature

UZDoom has no client/server authority split anywhere in its source tree (no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style construct exists at all). `A_SpawnDebris`'s UZDoom implementation (`src/playsim/p_actionfunctions.cpp`) spawns each debris actor and sets its position and velocity directly on that single actor instance, with no separate broadcast/sync step afterward — the "Zandronum-specific: velocity replication bug" above (a desync caused by the sync command targeting the wrong actor) has no counterpart on UZDoom because there is no client/server split for it to desync across.

The native declaration's types also differ. UZDoom declares `A_SpawnDebris` in `wadsrc/static/zscript/actors/actor.zs` with the same parameter names (`spawntype`, `transfer_translation`, `mult_h`, `mult_v`) and the same defaults as Zandronum's DECORATE declaration. The difference is that UZDoom types `mult_h`/`mult_v` as `double` and computes in floating point, where Zandronum declares them `float` but stores and multiplies them as fixed-point. The wiki's `string type` wording doesn't match either engine, both of which take `class<Actor>`.

Aside from these two points, the spawn-count/state-assignment, position-offset, and velocity-randomization logic (including replacing a non-positive `mult_h`/`mult_v` with 1.0) is the same on both engines. `src/playsim/p_actionfunctions.cpp:1550-1589` follows the Zandronum source's structure and uses the same `pr_spawndebris` random stream with `Random2()`. One ordering detail differs: Zandronum rolls the Z velocity before X and Y, while UZDoom rolls X, Y, then Z.

## Example

```text
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
  Radius 16
  Height 64
  +SOLID
  +SHOOTABLE
  States
  {
  Spawn:
    PILR A -1
    Stop
  Death:
    PILR A 0 A_SpawnDebris("SentinelDebris", true, 1.5, 2.0)
    PILR A 10 A_Explode(20, 128)
    Stop
  }
}
```

This spawns 15 debris pieces (per `SentinelDebris` Health), assigns the first 15 sprites/frames from `SentinelDebris`'s `Spawn` state, transfers the pillar's translation to each piece, and throws them with 1.5× horizontal velocity and 2.0× vertical velocity.

## See also

- `A_SpawnItemEx` — a more flexible spawning function with per-actor offsets and control flags, preferred when fine control is needed.
