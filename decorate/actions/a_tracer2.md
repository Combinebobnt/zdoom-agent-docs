# `A_Tracer2`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_Tracer2` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Tracer2&oldid=34282) + verified against the Zandronum source's `src/g_strife/a_spectral.cpp:99-173` and `src/g_doom/a_revenant.cpp:50-149` (for comparison with `A_Tracer`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_Tracer2)` in `src/g_strife/a_spectral.cpp`.

Seeks toward the calling actor's `tracer` target, adjusting angle and velocity to home in. Designed for Strife homing missiles. Unlike the similar `A_Tracer` (Revenant homing missile), this function acts on **every call** (no gametic gate) and does **not spawn puffs** behind the missile.

## Signature

```decorate
void A_Tracer2()
```

(No parameters.)

## Behavior

When called, `A_Tracer2` performs the following on the server side (clients are bypassed entirely):

1. **Target validation**: Checks that the actor has a valid `tracer` field, the target is alive (`dest->health > 0`), the actor has a non-zero speed, and the target passes `CanSeek()` checks (which reject invisible or `CANTSEEK`-flagged targets). Returns early if any check fails.

2. **Angle adjustment**: Calculates the exact angle toward the target. If the target is not directly in front of the missile, applies a turning rate of approximately **19.69 degrees per call** (defined as `TRACEANGLE = 0xe000000` in the source). The missile turns left or right as needed to close the angle, but never overshoots the target.

3. **Velocity update**: Updates `velx` and `vely` based on the new angle and the actor's `Speed` property.

4. **Pitch adjustment** (if the actor is not using the `MF3_FLOORHUGGER` or `MF3_CEILINGHUGGER` flags): Calculates a slope toward the target and adjusts `velz` by ±0.125 FRACUNIT per call to home vertically as well.

5. **Network broadcast** (server only): Sends a full position, angle, and velocity update to all clients via `SERVERCOMMANDS_MoveThingExact(...)`, broadcasting `CM_X|CM_Y|CM_Z|CM_ANGLE|CM_VELX|CM_VELY|CM_VELZ`. This happens **on every call**, so rapid homing missiles generate significant netcode traffic.

## Comparison with A_Tracer

The key differences between `A_Tracer2` and the functionally similar `A_Tracer` (used by the Revenant's homing rocket):

| Property | A_Tracer | A_Tracer2 |
|---|---|---|
| **Gametic gate** | 1-in-4 (runs only every 4 tics) | None (runs every call) |
| **Puff spawn** | Yes, spawns `RevenantTracerSmoke` trail | No puffs |
| **Turning rate** | ~16.88° per call | ~19.69° per call |
| **Game origin** | Doom (Revenant) | Strife (Spectral Projectile) |

Because `A_Tracer2` has no gametic gate, a 1-tic state will adjust angle every tic, whereas `A_Tracer` in a 1-tic state still only turns every 4 ticks. This makes `A_Tracer2` more responsive but also more network-expensive.

## SEEKERMISSILE flag semantics

The wiki states "this only works for missiles with the SEEKERMISSILE flag," which requires clarification: **`A_Tracer2` does not check the flag itself**. Instead, the flag is a convention; it controls whether missile-spawning actions populate the `tracer` field in the first place. The engine sets `tracer` when firing a missile with the `SEEKERMISSILE` flag (see `src/thingdef/thingdef_codeptr.cpp:1719-1720` and similar sites), and `A_Tracer2` only requires a valid `tracer` pointer — it can be set by any code, not just flag-based firing paths. If you manually set `tracer` on any actor, `A_Tracer2` will home toward it regardless of flags.

For conventional homing missiles, declaring `+SEEKERMISSILE` is the standard practice because it integrates with engine missile-spawning paths; omitting it is possible but non-standard.

## Network considerations

- **Server-side only**: The function returns immediately if `NETWORK_InClientMode()` is true, so homing calculations happen only on the server.
- **Broadcast traffic**: On the server, every call broadcasts a full position/angle/velocity update. A map with many simultaneous homing missiles can incur significant netcode overhead; consider state durations carefully when designing high-frequency homing sequences.
- **Position authority**: Clients receive missile positions from the server and cannot independently adjust homing behavior.

## Engine-family divergence: shared implementation, new `traceang` parameter

On UZDoom, `A_Tracer2` is no longer a Strife-only, parameterless native function. It is implemented as a general ZScript helper in the UZDoom source's `wadsrc/static/zscript/actors/doom/revenant.zs`, with the signature `void A_Tracer2(double traceang = 19.6875)` — an optional turn-rate parameter, in degrees, defaulting to the same ~19.69° Strife rate Zandronum hardcodes as `TRACEANGLE`. Callers can now pass a custom turn rate explicitly (e.g. `A_Tracer2(30.0)`), which has no equivalent on Zandronum, where the rate is fixed at compile time and the function takes no arguments at all.

More significantly, `A_Tracer` (the Revenant homing function) is no longer an independently-implemented function on UZDoom. Its ZScript body performs only the puff/smoke-spawn and the 1-in-4 gametic gate described above, then defers the actual homing math to a plain call to `A_Tracer2(16.875)` — the Revenant's own turn rate, passed as an explicit argument. So on UZDoom the two functions share one code path; the "Comparison with A_Tracer" table above (turning rate, puff spawn, gametic gate) still describes the observable behavioral difference correctly, but the underlying mechanism is now composition (`A_Tracer` calling `A_Tracer2`) rather than two independently-implemented functions as on Zandronum (the Strife-side `src/g_strife/a_spectral.cpp` versus the Doom-side `src/g_doom/a_revenant.cpp`).

## Engine-family divergence: floating-point steering math

Zandronum's `A_Tracer2` works in fixed-point `angle_t` BAM units and `finesine`/`finecosine` lookup tables, and derives its vertical-seek divisor from `P_AproxDistance` (an octagonal distance approximation, not true Euclidean distance). UZDoom's version is fully floating-point: `AngleTo`/`deltaangle` compute the facing delta as a `double` degree value directly (no BAM conversion), `VelFromAngle()` derives velocity from that angle and the actor's `Speed`, and the vertical-seek divisor comes from `AActor::DistanceBySpeed` — `max(1, Distance2D(dest) / speed)`, true 2D Euclidean distance rather than the octagonal table approximation. The two engines converge on the same turn-rate constants and the same ±1/8-unit-per-call vertical step, so trajectories track closely, but exact per-tic angle and pitch values can differ slightly, most noticeably at short range where the octagonal approximation's error from true distance is largest.

## Engine-family divergence: no client/server execution gate

The "Network considerations" section above describes Zandronum-specific behavior with no UZDoom equivalent: neither `NETWORK_InClientMode()` nor `SERVERCOMMANDS_MoveThingExact` (or any similarly-named broadcast mechanism) exists anywhere in the UZDoom source tree. UZDoom's `A_Tracer2` runs its full homing calculation unconditionally, every call, on every machine — there is no server-authoritative gate and no explicit per-call position/angle/velocity broadcast. This follows from UZDoom's GZDoom-family netcode model (every peer runs the same deterministic simulation) rather than Zandronum's explicit client/server split with server-authoritative position broadcasts, and it is the same divergence already documented for the sibling function `A_SeekerMissile` (`decorate/actions/a_seekermissile.md`).

## Related functions and cross-references

- **[Creating projectiles](../concepts/creating-projectiles.md)** — full guide to homing missiles, including state setup and `A_Tracer2` integration.
- **`A_Tracer`** — similar homing function for Doom-engine homing missiles; uses a slower turning rate and spawns puff trails.

## Example (Zandronum DECORATE)

```decorate
actor StriveHominMissile : Actor
{
  Projectile
  Damage 10
  Speed 20
  Height 8
  Radius 6
  Seesound "weapons/plasmaf"
  Deathsound "weapons/plasmax"
  +SEEKERMISSILE
  States
  {
  Spawn:
    PLSS A 3 Bright A_Tracer2
    Loop
  Death:
    PLSE AB 5 Bright
    Stop
  }
}
```

The `SEEKERMISSILE` flag allows action functions that fire this missile (such as `A_CustomMissile` or `A_SpawnProjectile`) to automatically set the `tracer` field. Each frame in `Spawn:` runs `A_Tracer2` to home toward the target.
