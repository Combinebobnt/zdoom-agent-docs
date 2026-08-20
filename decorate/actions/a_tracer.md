# `void A_Tracer()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-12)
**Provenance:** ZDoom Wiki `A_Tracer` (retrieved 2026-08-12, https://zdoom.org/w/index.php?title=A_Tracer&oldid=53146) + re-verified against the Zandronum source's `src/g_doom/a_revenant.cpp:52`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action function (defined on `AActor` in `src/g_doom/a_revenant.cpp`).

**Wiki/source divergence:** The wiki states this function "only works for missiles with the `SEEKERMISSILE` flag." The actual gate is the presence of a live `tracer` pointer — the function does not check `SEEKERMISSILE` itself. SEEKERMISSILE is important because missiles spawned with that flag typically have `tracer` populated by the calling action (e.g., `A_SkelMissile`), but a manually-set tracer pointer would also work.

A homing function for seeking missiles, typically the Revenant's tracer projectile. The missile steers aggressively toward its `tracer` target, spawning both a visual puff and trailing smoke.

## Behavior

The function **only executes on ticks where `level.time & 3 == 0`** — that is, every 4th tic. This time-based gating has a critical side effect: the homing behavior depends on both the call interval and the tic at which the missile was spawned, creating potential phase-shift situations.

### Call timing effects

The actual homing frequency depends on two factors:

1. **How often the action is called** — typically specified via the state-line duration (e.g., `FATB AB 2 bright A_Tracer` calls it every 2 tics).
2. **The tic modulo-4 when the missile was spawned** — since the function checks `level.time & 3`.

This interaction produces three distinct patterns:

- **If the call interval is odd** (e.g., 1, 3, 5 tics): the function will see `level.time` values that cycle through all four remainders (0, 1, 2, 3) eventually. Homing happens once every `interval × 4` tics on average, but **always occurs** regardless of spawn phase.
- **If the call interval is an even but non-multiple of 4** (e.g., 2, 6, 10 tics): the function only homes on even remainders (0, 2) or odd remainders (1, 3), depending on spawn phase. The missile must be spawned during the right half of the cycle (even or odd tic), or homing never occurs at all.
- **If the call interval is a multiple of 4** (e.g., 4, 8, 12 tics): homing occurs consistently at that interval **only if the missile was spawned on a tic that is also a multiple of 4**. If spawned during any other tic, the function never executes at a tic where `level.time & 3 == 0`, and homing fails entirely.

**Example:** The stock Revenant's tracer calls `A_Tracer` every 2 tics. Since 2 is even but not divisible by 4, the missile homes reliably only if spawned on an even tic; missiles spawned on odd tics never home.

## Behavior details

On a tic where the time check passes:

1. **Smoke spawning** — spawns a `BulletPuff` puff at the missile's current position, and a `RevenantTracerSmoke` actor offset by `-velx, -vely` (behind the missile). This occurs on **all machines** (clients and server).
2. **Smoke properties** — the smoke actor's vertical velocity is set to 1 (in fixed-point units) and its tic count is reduced by 0–3 (random); if this would drop it to 0 or below, it's forced to 1.
3. **Steering** (server-side only; **Zandronum multiplayer: steering is server-authoritative and skipped on clients**):
   - Clients return immediately after spawning smoke (lines 85–88 in source), leaving steering to the server.
   - Server-side: If the missile has no tracer target, or the target is dead, or the missile's speed is 0, or the missile's `CanSeek()` check fails for the target, returns without steering.
   - Otherwise, computes the angle to the target and adjusts the missile's angle by up to `0xc000000` (binary angle units, equivalent to 16.875°) per tic, turning toward it.
   - Updates the missile's `velx` and `vely` based on the new angle and its `Speed` property.
   - If the missile is not flagged as a floor-hugger or ceiling-hugger, computes and adjusts the vertical velocity (`velz`) to steer toward the target's Z position, changing it by up to `±FRACUNIT/8` per tic.
   - After steering, broadcasts the updated position, angle, and velocity to all clients via `SERVERCOMMANDS_MoveThingExact`.

## Engine-family divergence: client/server authority

UZDoom's `A_Tracer` (now ZScript, `extend class Actor` in `wadsrc/static/zscript/actors/doom/revenant.zs`) carries no equivalent of Zandronum's `NETWORK_InClientMode()` early-return gate after the smoke-spawn step, and no `SERVERCOMMANDS_MoveThingExact` broadcast afterward — that whole client/server authority split does not exist anywhere in UZDoom's source tree. The steering half (target validity checks, angle turn, velocity/vertical-velocity recalculation, delegated to `A_Tracer2(16.875)`) runs unconditionally wherever the actor's state machine executes, instead of being computed once on an authoritative server and replicated to clients. The doc's "Steering (server-side only...)" framing above, including "Clients return immediately after spawning smoke" and the final `SERVERCOMMANDS_MoveThingExact` broadcast, describes Zandronum-specific behavior only; on UZDoom there is no separate client path to desync from, and the function's full body (smoke and steering alike) executes identically on every machine.

## Engine-family divergence: floating-point steering math

Zandronum's `A_Tracer`/underlying steering computes the turn angle with `R_PointToAngle2` (a fixed-point `angle_t` arctangent), applies the up-to-`TRACEANGLE` (`0xc000000`, 16.875°) turn step with BAM wraparound comparisons, and derives `velx`/`vely` via `FixedMul` against `finecosine`/`finesine` table lookups. The vertical-seek divisor comes from `P_AproxDistance` (an octagonal approximation of 2D distance, not true Euclidean) divided by `Speed` in fixed-point. UZDoom's steering (in `A_Tracer2`, which `A_Tracer` calls with `traceang = 16.875`) is fully floating-point: `AngleTo(dest)` and `deltaangle(angle, exact)` use `DAngle`/double-precision trig rather than a BAM table, the turn step is applied as a plain double-degree add/subtract clamped by `deltaangle`, `VelFromAngle()` derives `Vel.X`/`Vel.Y` from `Angles.Yaw.Cos()`/`.Sin()` (native double `cos`/`sin`), and the vertical-seek divisor comes from `AActor::DistanceBySpeed()` (`max(1., Distance2D(dest) / speed)`, true Euclidean 2D distance) rather than the octagonal approximation. Both engines aim at the same target position and turn by the same nominal 16.875°/tic, but the exact per-tic angle and vertical-velocity values can differ slightly, most noticeably at short range or steep vertical offsets where the octagonal approximation's error is largest.

## See also

- `A_Tracer2` — a simpler steering function used by Strife's projectiles (exists in Zandronum but accepts only the turn rate).
- `A_SeekerMissile` — a different homing implementation.
- `SEEKERMISSILE` actor flag — required for this function to work correctly.
