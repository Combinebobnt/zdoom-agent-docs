# `void A_Tracer()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Tracer` (retrieved 2026-08-12, https://zdoom.org/w/index.php?title=A_Tracer&oldid=53146) + re-verified against the Zandronum source's `src/g_doom/a_revenant.cpp:52`, plus `src/p_mobj.cpp:6335-6352,6386-6388` (`P_SpawnPuff` client early-return and unsent puff), `src/p_mobj.cpp:7076-7081` (`+RANDOMIZE` first-frame cut), `wadsrc/static/actors/doom/revenant.txt:81`, `src/thingdef/thingdef_codeptr.cpp:1265-1274,1796` (SEEKERMISSILE-gated `tracer` setters), `src/g_strife/a_spectral.cpp:98-101` and `wadsrc/static/actors/actor.txt:177` (`A_Tracer2`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action function (defined on `AActor` in `src/g_doom/a_revenant.cpp`).

**Wiki/source divergence:** The wiki states this function "only works for missiles with the `SEEKERMISSILE` flag." The actual gate is the presence of a live `tracer` pointer. The function does not check `SEEKERMISSILE` itself. The flag matters in practice because generic spawners such as `A_CustomMissile` and `A_FireCustomMissile` only fill in the missile's `tracer` when the missile has `SEEKERMISSILE`. `A_SkelMissile` sets `tracer` unconditionally, and a `tracer` set any other way works too.

A homing function for seeking missiles, typically the Revenant's tracer projectile. The missile steers aggressively toward its `tracer` target, spawning both a visual puff and trailing smoke.

## Behavior

The function **only executes on ticks where `level.time & 3 == 0`** — that is, every 4th tic. This time-based gating has a critical side effect: the homing behavior depends on both the call interval and the tic at which the missile was spawned, creating potential phase-shift situations.

### Call timing effects

The actual homing frequency depends on two factors:

1. **How often the action is called** — typically specified via the state-line duration (e.g., `FATB AB 2 bright A_Tracer` calls it every 2 tics).
2. **The tic modulo 4 that the calls land on**, since the function checks `level.time & 3`. This phase is set by the spawn tic plus how long the first frame lasts (see the `+RANDOMIZE` note below).

This interaction produces three distinct patterns:

- **If the call interval is odd** (e.g., 1, 3, 5 tics): the function will see `level.time` values that cycle through all four remainders (0, 1, 2, 3) eventually. Homing happens once every `interval × 4` tics on average, but **always occurs** regardless of spawn phase.
- **If the call interval is an even but non-multiple of 4** (e.g., 2, 6, 10 tics): the function only homes on even remainders (0, 2) or odd remainders (1, 3), depending on spawn phase. The missile must be spawned during the right half of the cycle (even or odd tic), or homing never occurs at all.
- **If the call interval is a multiple of 4** (e.g., 4, 8, 12 tics): homing occurs consistently at that interval **only if the calls land on tics that are multiples of 4**. Otherwise the function never executes at a tic where `level.time & 3 == 0`, and homing fails entirely.

**Example:** The stock `RevenantTracer` calls `A_Tracer` every 2 tics (`FATB AB 2 BRIGHT A_Tracer`). Since 2 is even but not divisible by 4, a given missile either homes every 4 tics or never, depending on the parity of the tics its calls land on. That parity is not simply the spawn tic's: `RevenantTracer` has `+RANDOMIZE`, so `P_CheckMissileSpawn` cuts 0-3 tics (floored at 1) off its first frame at spawn. Which Revenant missiles home is therefore effectively random from the player's view.

## Behavior details

On a tic where the time check passes:

1. **Smoke spawning** — spawns a `BulletPuff` puff at the missile's current position (with a small random Z jitter), and a `RevenantTracerSmoke` actor offset by `-velx, -vely` (behind the missile). On UZDoom both run on every machine. On Zandronum the smoke is spawned locally on every machine, but the `BulletPuff` is not: `P_SpawnPuff` returns without spawning on a client when the source is not the console player, and the server spawns it with "tell clients" off (its NetID is freed, nothing is sent). Online Zandronum clients therefore see the smoke trail but never the puff.
2. **Smoke properties** — the smoke actor's vertical velocity is set to 1 map unit per tic (`FRACUNIT`) and its tic count is reduced by 0–3 (random); if this would drop it to 0 or below, it's forced to 1.
3. **Steering** (server-side only; **Zandronum multiplayer: steering is server-authoritative and skipped on clients**):
   - Clients return immediately after spawning smoke (lines 85–88 in source), leaving steering to the server.
   - Server-side: If the missile has no tracer target, or the target is dead, or the missile's speed is 0, or the missile's `CanSeek()` check fails for the target, returns without steering.
   - Otherwise, computes the angle to the target and turns the missile toward it by up to `0xc000000` (binary angle units, equivalent to 16.875°) per homing call, snapping to the exact angle if the step would overshoot. Homing calls happen at most every 4th tic.
   - Updates the missile's `velx` and `vely` based on the new angle and its `Speed` property.
   - If the missile is not flagged as a floor-hugger or ceiling-hugger, adjusts the vertical velocity (`velz`) by exactly `FRACUNIT/8` (1/8 map unit per tic) per homing call, up or down. The aim point is the target's Z plus 40 if the target is at least 56 units tall, otherwise the target's Z plus two-thirds of the *missile's* own height. The needed slope (height difference divided by the distance in tics) only decides the sign of the step.
   - After steering, broadcasts the updated position, angle, and velocity to all clients via `SERVERCOMMANDS_MoveThingExact`.

## Engine-family divergence: client/server authority

UZDoom's `A_Tracer` (now ZScript, `extend class Actor` in `wadsrc/static/zscript/actors/doom/revenant.zs`) carries no equivalent of Zandronum's `NETWORK_InClientMode()` early-return gate after the smoke-spawn step, and no `SERVERCOMMANDS_MoveThingExact` broadcast afterward — that whole client/server authority split does not exist anywhere in UZDoom's source tree. The steering half (target validity checks, angle turn, velocity/vertical-velocity recalculation, delegated to `A_Tracer2(16.875)`) runs unconditionally wherever the actor's state machine executes, instead of being computed once on an authoritative server and replicated to clients. The doc's "Steering (server-side only...)" framing above, including "Clients return immediately after spawning smoke" and the final `SERVERCOMMANDS_MoveThingExact` broadcast, describes Zandronum-specific behavior only; on UZDoom there is no separate client path to desync from, and the function's full body (smoke and steering alike) executes identically on every machine.

## Engine-family divergence: floating-point steering math

Zandronum's `A_Tracer`/underlying steering computes the turn angle with `R_PointToAngle2` (a fixed-point `angle_t` arctangent), applies the up-to-`TRACEANGLE` (`0xc000000`, 16.875°) turn step with BAM wraparound comparisons, and derives `velx`/`vely` via `FixedMul` against `finecosine`/`finesine` table lookups. The vertical-seek divisor comes from `P_AproxDistance` (an octagonal approximation of 2D distance, not true Euclidean) divided by `Speed` in fixed-point. UZDoom's steering (in `A_Tracer2`, which `A_Tracer` calls with `traceang = 16.875`) is fully floating-point: `AngleTo(dest)` and `deltaangle(angle, exact)` use `DAngle`/double-precision trig rather than a BAM table, the turn step is applied as a plain double-degree add/subtract clamped by `deltaangle`, `VelFromAngle()` derives `Vel.X`/`Vel.Y` from `Angles.Yaw.Cos()`/`.Sin()` (native double `cos`/`sin`), and the vertical-seek divisor comes from `AActor::DistanceBySpeed()` (the true Euclidean 2D distance divided by speed, floored at 1) rather than the octagonal approximation. On Zandronum that divisor is also truncated to a whole number of tics, since `dist / self->Speed` is an integer division of two fixed-point values. Both engines aim at the same target position, turn by the same nominal 16.875° per homing call, and step vertical velocity by exactly 1/8 either way. The per-call angle can differ slightly, and the up-or-down choice for the vertical step can flip when the needed slope sits close to the current vertical velocity. That is likelier at short range, where the whole-tic truncation is proportionally largest, and at bearings where the octagonal approximation's error peaks (about 11.8% near 26.6° off an axis).

## See also

- `A_Tracer2` — the same steering without the 4th-tic gate or the smoke, used by Strife's projectiles. On Zandronum it takes no parameters and always turns by `0xe000000` (19.6875°). On UZDoom it takes the turn rate as a parameter.
- `A_SeekerMissile` — a different homing implementation.
- `SEEKERMISSILE` actor flag — commonly set on `A_Tracer` missiles because spawners such as `A_CustomMissile` only assign `tracer` to missiles with it. `A_Tracer` itself does not check the flag.
