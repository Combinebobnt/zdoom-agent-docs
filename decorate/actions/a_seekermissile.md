# `A_SeekerMissile`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_SeekerMissile` (retrieved 2026-08-01, oldid=48951) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:638-658`, `src/p_mobj.cpp` (`P_SeekerMissile` implementation), and `wadsrc/static/actors/actor.txt:204`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SeekerMissile)` in `src/thingdef/thingdef_codeptr.cpp`.

A parameterized homing function for seeking missiles. Adjusts the calling actor's angle and velocity each call to steer toward its `tracer` target, with optional target acquisition. Unlike the simpler `A_Tracer`/`A_Tracer2`, this function exposes the turning thresholds and acquisition parameters as configurable arguments.

## Signature

```decorate
void A_SeekerMissile(int threshold, int turnmax, int flags = 0, int chance = 50, int distance = 10)
```

## Parameters

### `threshold` (int)

The angle threshold (in degrees, range [0, 90]) inside which the missile will steer directly toward its tracer. If the angle to the target is smaller than this threshold, the function applies full steering toward the target. If larger, it applies only partial steering via the `turnmax` limit.

**Note on clamping:** Values outside [0, 90] are silently clamped (not rejected). The source code clamps both threshold and turnmax to this range with `clamp<int>(ang1, 0, 90)` and `clamp<int>(ang2, 0, 90)`, converting the degrees to binary angle units via `* ANGLE_1`.

### `turnmax` (int)

The maximum change of movement direction per call (in degrees, range [0, 90]). This controls how fast the missile can turn. If set higher than `threshold`, the missile can turn more aggressively when the target is far off-angle. If set lower than `threshold`, turning is limited even when close to the target angle.

Both angles are specified in degrees (Zandronum's DECORATE integer only, not angle types as the wiki implies).

### `flags` (int, optional, default 0)

Bitfield controlling seeking behavior. Combine flags using `|`:

#### Defined flags (Zandronum 3.2.1)

- `SMF_LOOK` (1) — Target acquisition: if set, the missile will attempt to acquire a target via `P_RoughMonsterSearch` if it does not already have a `tracer` set. On each call, a random roll (0–255) is made with 0–`chance` success; on success, the engine searches blockmap rings out to `distance` blocks (128 map units each) for a seekable target. The `SCREENSEEKER` flag on the projectile can further restrict the search to targets in the shooter's field of vision.

- `SMF_PRECISE` (2) — Precise 3D trajectory: if set, the missile homes in true 3D, recalculating its vertical velocity each call to steer toward the target's vertical position. If unset, vertical movement follows a simpler physics approximation and the missile may not track a target moving significantly above or below its spawn height.

- `SMF_CURSPEED` (4) — Use current speed: if set, the missile maintains its current velocity magnitude (the length of its velocity vector) while changing direction. If unset, the missile's speed is recalculated from its `Speed` property each call, which may be slower or faster depending on the actor definition.

### `chance` (int, optional, default 50)

Used only if `SMF_LOOK` is set. The probability (0–255) that target acquisition will be attempted on each call. Default 50 ≈ 19.5% chance per call; a value ≥256 is always.

### `distance` (int, optional, default 10)

Used only if `SMF_LOOK` is set. The maximum search distance in blockmap blocks (units of 128 map units). Default 10 = approximately 1280 map units. The engine uses the BLOCKMAP to perform this search, so the actual range is not always exact and depends on the actor's position relative to blockmap boundaries. Values much larger than 20 should be avoided, as the search can become resource-intensive.

## Behavior

When called, `A_SeekerMissile` performs the following steps:

1. **Target acquisition** (if `SMF_LOOK` is set and no tracer is present):
   - Makes a random roll. If the roll succeeds (< `chance`), calls `P_RoughMonsterSearch` with the given `distance` to find a seekable target.
   - If a target is found, it becomes the new `tracer`.
   - **Network note**: This search occurs on both server and client. Clients burn RNG and perform the blockmap search, but the actual seeking (step 2 below) is server-only.

2. **Seeking via `P_SeekerMissile`** (server-side only):
   - If the missile has a valid `tracer`, the function `P_SeekerMissile` adjusts the missile's angle and velocity to steer toward it, subject to the `threshold` and `turnmax` constraints.
   - In client mode, `P_SeekerMissile` returns `false` immediately without steering.
   - If seeking fails (target invalid, dead, unkeen, or no `tracer`), `P_SeekerMissile` returns `false`.

3. **Tracer cleanup** (if seeking failed and `SMF_LOOK` is set):
   - If `P_SeekerMissile` returned `false` and `SMF_LOOK` was set, clears the `tracer` field so the next call will attempt target reacquisition.

## Network behavior (Zandronum multiplayer)

- **Target acquisition** (`SMF_LOOK` branch) is **not** gated on server mode. Clients perform the RNG roll and blockmap search, consuming resources and burning random numbers, even though only the server's acquired target matters. This can lead to subtle desynchronization if the RNG sequence is expected to match between client and server for networked logic elsewhere.
- **Steering** (`P_SeekerMissile`) is **server-only**. Clients receive the resulting position/angle/velocity updates via `SERVERCOMMANDS_MoveThingExact(...)`, but do not steer independently.

## Comparison with A_Tracer / A_Tracer2

| Feature | A_SeekerMissile | A_Tracer | A_Tracer2 |
|---|---|---|---|
| **Configurable turning** | Yes (threshold / turnmax) | No (fixed turn rate) | No (fixed turn rate) |
| **Auto target acquisition** | Optional (SMF_LOOK flag) | No (requires pre-set tracer) | No (requires pre-set tracer) |
| **3D seeking** | Optional (SMF_PRECISE flag) | Yes, always | Yes, always |
| **Spawn interval gating** | No (runs every call) | Yes (1-in-4 tics) | No (runs every call) |
| **Smoke trail** | No | Yes (RevenantTracerSmoke) | No |
| **Speed preservation** | Configurable (SMF_CURSPEED) | Recalcs from Speed property | Recalcs from Speed property |

## Fork/wiki divergences

**Distance unit arithmetic in wiki:** The wiki's examples state "a value of 4 means a range of 512 map units (4 * 64 = 512)" and "distance=10 ... roughly 1080 map units". Both are incorrect. The distance parameter is in blockmap blocks (128 map units each), so:
- distance=4 → 512 map units (4 × 128)
- distance=10 → 1280 map units (10 × 128)

The wiki's arithmetic is internally inconsistent (mixing 64-unit and 128-unit conventions).

**MaxTargetRange property:** The wiki conflates seeker-missile acquisition with weapon-fire tracer assignment. `MaxTargetRange` is an actor property used at weapon-spawn time (via `P_AimLineAttack`) to set the initial tracer on a projectile fired from a weapon. It is **not** read by `A_SeekerMissile` — that function uses only the `distance` parameter for its blockmap search.

## Example (Zandronum DECORATE)

```decorate
ACTOR MagicMissile
{
  Projectile
  +RANDOMIZE
  +SEEKERMISSILE
  Height 16
  Radius 8
  Speed 10
  Damage 15
  RenderStyle "Add"
  Alpha 0.8

  States
  {
  Spawn:
    MMIS B 2 Bright A_SeekerMissile(0, 2, SMF_LOOK, 50, 10)
    Loop
  Death:
    MMIS CDE 5 Bright
    Stop
  }
}
```

This missile has a low `turnmax` (2 degrees) and a low `threshold` (0 degrees), giving it a "laggy" turning effect. The `SMF_LOOK` flag with default `chance` (50/256) and `distance` (10 blocks) allows it to acquire targets up to roughly 1280 map units away.

## See also

- `A_Tracer` — a simpler homing function with a fixed 1-in-4 tic gate; spawns a smoke trail.
- `A_Tracer2` — a simpler homing function with no tic gate; runs every call.
- `SEEKERMISSILE` actor flag — a convention flag; not required by `A_SeekerMissile` itself (can be omitted), but used by weapon-spawning code to set `tracer` at projectile creation time.
