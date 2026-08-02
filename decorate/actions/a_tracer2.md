# `A_Tracer2`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Tracer2` (retrieved 2026-07-31, oldid=34282) + verified against the Zandronum source's `src/g_strife/a_spectral.cpp:99-173` and `src/g_doom/a_revenant.cpp:50-149` (for comparison with `A_Tracer`).
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
