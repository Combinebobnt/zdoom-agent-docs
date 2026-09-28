# ThrustThing

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki (https://zdoom.org/w/index.php?title=ThrustThing&oldid=46771, retrieved 2026-08-06), verified against Zandronum source (p_lnspec.cpp, LS_ThrustThing; p_lnspec.cpp:960-995, network.cpp:1559-1563, sv_main.cpp:5563-5586)
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Signature

```acs
int ThrustThing(int angle, int force [, int nolimit, int tid])
```

Action special (index 72).

## Description

Applies an instantaneous horizontal velocity impulse to one or more actors in a given direction.

- **angle**: Direction as a byte angle (0–255, representing 0–360 degrees), converted via `BYTEANGLE(angle)` before use. On Zandronum `BYTEANGLE` shifts the value left 24 bits (`p_lnspec.cpp:79`), so only the low 8 bits count and out-of-range values wrap. Converting from a 0–360 degree value requires `angle * 256 / 360`; converting from a `GetActorAngle` result (a 0–65535 fraction of a full circle) requires `>> 8`.
- **force**: Impulse magnitude in map units per tic. `force` times the cosine and sine of the angle is added to the actor's X and Y velocity (`p_lnspec.cpp:983-985`).
- **nolimit**: If 0 (default), each of the actor's X and Y velocity components is clamped to ±30 units per tic after the addition (`MAXMOVE`, `p_local.h:81`). The clamp applies per axis and to the actor's total velocity, including what it already had, so a diagonal speed can reach about 42. If 1, no clamping is applied; use this for forces above 30.
- **tid**: Thing ID of actor(s) to thrust. If 0 (default), affects the activator (the script's activator when called from ACS).

## Return Value

`int`: 1 (true) whenever `tid` is non-zero, even if no actor matched, and when `tid` is 0 and there is an activator. 0 (false) only when `tid` is 0 and there is no activator (`p_lnspec.cpp:960-974`). UZDoom also returns 0 for the Hexen-format back-side case described below. On a Zandronum client the return is 1 even when the client-side gate below skipped the thrust.

## Multiplayer Caveats

Zandronum only (`ThrustThingHelper`, `p_lnspec.cpp:977-995`):

- Offline and on the server, the thrust is always applied to every resolved actor. `NETWORK_IsConsolePlayerOrNotInClientMode` returns true whenever not in client mode (`network.cpp:1559-1563`).
- In client mode (a client, or client-demo playback), the thrust is applied only to the console player's own player actor or to an actor flagged `NETFL_CLIENTSIDEONLY`. Other actors are skipped silently. This matters for `CLIENTSIDE` scripts.
- On the server, `SERVER_UpdateThingVelocity(it, false)` (`sv_main.cpp:5563-5586`) sends clients a `MoveThingExact` update carrying the new X/Y velocity, plus the X/Y position for non-player actors (players get velocity only). Nothing is sent for an actor without a net ID (`sv_commands.cpp:99-112,1646-1649`).

## Engine-family divergence: client gating, velocity broadcast and the Hexen back-side guard

The core thrust math is the same on both engines. UZDoom's `FUNC(LS_ThrustThing)`
(`src/playsim/p_lnspec.cpp:1215-1237`) resolves the `tid`/activator target the same way, converts
`angle` with its own `BYTEANGLE` macro (byte angle times 360/256, as degrees, `p_lnspec.cpp:68`),
and adds the force along that angle to the X/Y velocity via `AActor::Thrust(DAngle angle, double speed)`
(`src/playsim/actor.h:1675-1679`). That is the same trig-based instantaneous velocity add as
Zandronum's `velx`/`vely` update. The `nolimit`-gated clamp also matches: UZDoom's
`ThrustThingHelper` (`p_lnspec.cpp:1205-1213`) clamps each axis to `±MAXMOVE`, and UZDoom's
`MAXMOVE` is 30 (`src/playsim/p_local.h:52`), matching Zandronum's ±30.

One difference in the target resolution: on the no-`tid` activator path, UZDoom returns false
without thrusting when the map is Hexen-format (`LEVEL2_HEXENHACK`) and the special was activated
from a line's back side. Zandronum's `LS_ThrustThing` has no such check and thrusts the activator
regardless.

The "Multiplayer Caveats" section above is Zandronum-specific and does not apply to UZDoom.
UZDoom's `LS_ThrustThing` has no console-player/`NETFL_CLIENTSIDEONLY` gating check at all. It
applies the thrust unconditionally to every resolved actor, and there is no
`SERVER_UpdateThingVelocity()`-style broadcast call anywhere in its call path. More broadly,
`SERVERCOMMANDS_*` and `SERVER_Update*` (the families of functions Zandronum's split
client-server netcode uses to replicate state) do not exist anywhere in the UZDoom source tree.
It uses a GZDoom-family unified/deterministic simulation model instead of Zandronum's explicit
server-authoritative broadcast model. So on UZDoom, `ThrustThing` simply always applies the
thrust to every matching actor, with no server/client distinction to reason about.

## Examples

Impart a 10-unit-per-tic impulse to the east to actor TID 143:
```acs
ThrustThing(0, 10, 1, 143);
```

Thrust the activator in the direction they're facing (`GetActorAngle` returns a 0–65535 fraction of a circle, so `>> 8` gives a byte angle):
```acs
ThrustThing(GetActorAngle(0) >> 8, 15, 1, 0);
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
