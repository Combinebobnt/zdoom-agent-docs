# `void A_Tracer()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Tracer` (retrieved 2026-07-31, oldid=53146) + verified against the Zandronum source's `src/g_doom/a_revenant.cpp:52`.
**Bucket:** action function (defined on `AActor` in `src/g_doom/a_revenant.cpp`).

A homing function for seeking missiles, typically the Revenant's tracer projectile. The missile steers aggressively toward its `tracer` target, spawning both a visual puff and trailing smoke.

**Only works for missiles with the `SEEKERMISSILE` flag.**

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

1. **Smoke spawning** — spawns a `BulletPuff` puff at the missile's current position, and a `RevenantTracerSmoke` actor offset by `-velx, -vely` (behind the missile).
2. **Smoke properties** — the smoke actor's vertical velocity is set to 1 (in fixed-point units) and its tic count is reduced by 0–3 (random); if this would drop it to 0 or below, it's forced to 1.
3. **Steering** (server-side only; returns early in client mode after smoke spawning):
   - If the missile has no tracer target, or the target is dead, or the missile's speed is 0, or the missile's `CanSeek()` check fails for the target, returns without steering.
   - Otherwise, computes the angle to the target and adjusts the missile's angle by up to `0xc000000` (binary angle units) per tic, turning toward it.
   - Updates the missile's `velx` and `vely` based on the new angle and its `Speed` property.
   - If the missile is not flagged as a floor-hugger or ceiling-hugger, computes and adjusts the vertical velocity (`velz`) to steer toward the target's Z position, changing it by up to `±FRACUNIT/8` per tic.

## See also

- `A_Tracer2` — a simpler steering function used by Strife's projectiles (exists in Zandronum but accepts only the turn rate).
- `A_SeekerMissile` — a different homing implementation.
- `SEEKERMISSILE` actor flag — required for this function to work correctly.
