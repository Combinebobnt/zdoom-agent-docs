# ThrustThing

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki (https://zdoom.org/w/index.php?title=ThrustThing&oldid=46771, retrieved 2026-08-06), verified against Zandronum source (p_lnspec.cpp, LS_ThrustThing)
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Signature

```acs
int ThrustThing(int angle, int force [, int nolimit, int tid])
```

Action special (index 72).

## Description

Applies an instantaneous velocity impulse to one or more actors in a given direction.

- **angle**: Direction vector as a byte angle (0–255, representing 0–360 degrees). Encoded via `BYTEANGLE(angle)` before use; converting from a 0–360 degree value requires `angle * 256 / 360`.
- **force**: Velocity change in units per tic. Added directly to the actor's `velx` and `vely` components.
- **nolimit**: If 0 (default), clamped to ±30 units per tic after addition. If 1, no clamping applied; use this for forces > 30 to allow higher impulse magnitude.
- **tid**: Thing ID of actor(s) to thrust. If 0 (default), affects the line special's activator.

## Return Value

`int`: 1 (true) if the thrust was applied to at least one actor, 0 (false) if the activator is null and tid was 0, or if tid was non-zero but no actors matched.

## Multiplayer Caveats

**Server-side only** (with exceptions): on network maps, the thrust is only applied if the actor is controlled by the console player (single-player host) OR if the actor is flagged `NETFL_CLIENTSIDEONLY`. The velocity update is then broadcast to all clients via `SERVER_UpdateThingVelocity()`. In single-player or non-networked modes, this has no effect.

## Engine-family divergence: server-side gating and velocity broadcast are Zandronum-only

The core thrust math is identical between the two engines: UZDoom's `FUNC(LS_ThrustThing)`
(`src/playsim/p_lnspec.cpp:1215-1237`) resolves the `tid`/activator target the same way, converts
`angle` via the same `BYTEANGLE` macro (`(a) * (360./256.)`, `p_lnspec.cpp:68`), applies the same
Hexen-format backside-activation guard (`LEVEL2_HEXENHACK && backSide` on the no-`tid` activator
path), and adds the force to `Vel.X`/`Vel.Y` via `AActor::Thrust(DAngle angle, double speed)`
(`src/playsim/actor.h:1675-1679`, `Vel.X += speed * angle.Cos(); Vel.Y += speed * angle.Sin();`)
— the same trig-based instantaneous velocity add as Zandronum's `velx`/`vely` update. The
`nolimit`-gated clamp is also identical: `ThrustThingHelper` (`p_lnspec.cpp:1205-1213`) clamps to
`±MAXMOVE`, and `MAXMOVE` is `30.` (`src/playsim/p_local.h:52`), matching Zandronum's ±30.

The entire "Multiplayer Caveats" section above is Zandronum-specific and does not apply to
UZDoom. UZDoom's `LS_ThrustThing` has no console-player/`NETFL_CLIENTSIDEONLY` gating check at
all — it applies the thrust unconditionally to every resolved actor — and there is no
`SERVER_UpdateThingVelocity()`-style broadcast call anywhere in its call path. More broadly,
`SERVERCOMMANDS_*` and `SERVER_Update*` (the families of functions Zandronum's split
client-server netcode uses to replicate state) do not exist anywhere in the UZDoom source tree at
all — it uses a GZDoom-family unified/deterministic simulation model instead of Zandronum's
explicit server-authoritative broadcast model. So on UZDoom, `ThrustThing` simply always applies
the thrust to every matching actor, with no server/client distinction to reason about.

## Examples

Impart a 10-unit-per-tic impulse to the east to actor TID 143:
```acs
ThrustThing(0, 10, 1, 143);
```

Thrust the line special's activator in the direction they're facing:
```acs
ThrustThing(GetActorAngle(0) * 256 / 360, 15, 1, 0);
```

Combine with `ThrustThingZ` for a 3D impulse (e.g., spawn a creature and launch it):
```acs
Script "Arachnotron jump" (void)
{
    SpawnSpotFacingForced("Arachnotron", 142, 143);
    Delay(1);
    ThrustThingZ(143, 115, 0, 0);  // Vertical impulse: 115 units/4 = ~28.75 units/tic upward
    Delay(18);
    ThrustThing(0, 10, 1, 143);    // Horizontal impulse: 10 units/tic eastward
}
```

## See Also

- `ThrustThingZ` — vertical velocity impulse (action special 128).
- `GetActorAngle` — retrieve an actor's current facing direction.
