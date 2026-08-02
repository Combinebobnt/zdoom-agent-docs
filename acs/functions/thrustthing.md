# ThrustThing

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki, verified against Zandronum source (p_lnspec.cpp, LS_ThrustThing)

## Signature

```c
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

## Examples

Impart a 10-unit-per-tic impulse to the east to actor TID 143:
```c
ThrustThing(0, 10, 1, 143);
```

Thrust the line special's activator in the direction they're facing:
```c
ThrustThing(GetActorAngle(0) * 256 / 360, 15, 1, 0);
```

Combine with `ThrustThingZ` for a 3D impulse (e.g., spawn a creature and launch it):
```c
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
