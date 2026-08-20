# ThrustThingZ

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** ZDoom Wiki `ThrustThingZ` (https://zdoom.org/w/index.php?title=ThrustThingZ&oldid=52807, retrieved 2026-07-29, re-verified 2026-08-06) + verified against Zandronum source's `src/p_lnspec.cpp:997-1047`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action special (index 128; `FUNC(LS_ThrustThingZ)` in `src/p_lnspec.cpp`)

**Classification:** Action special (index 128)

## Signature

```text
int ThrustThingZ(int tid, int force, int direction, int mode);
```

## Summary

Thrusts an actor vertically with a specified force. Can either set the actor's Z-velocity to zero and then apply the force, or add the force to the actor's current Z-velocity.

## Parameters

- **`tid`** — Thing ID of the actor to thrust. If `0`, thrusts the script's activator (typically the player who triggered the script).

- **`force`** — Vertical thrust magnitude, expressed in quarter map-units per tic (1 second = 35 tics). Internally computed as `arg1 * FRACUNIT / 4`, where `FRACUNIT = 65536`. For example, passing `force=4` yields 1 map-unit-per-tic of velocity; `force=1` yields 0.25 map-units-per-tic. Large force values (`> 32767`) wrap due to signed 32-bit arithmetic before the multiplication. The `direction` parameter modifies the sign of the result.

- **`direction`** — Thrust direction. `0` = upward (default), `1` = downward. If non-zero, the computed thrust value is negated before being applied to velocity.

- **`mode`** — Velocity handling. `0` = replace the actor's Z-velocity with the computed thrust value, `1` = add the thrust value to the actor's current Z-velocity.

## Return value

Returns `true` if the function applied thrust (either to one or more TID-matched actors, or to an existing activator). Returns `false` when `tid` is `0` and there is no activator (e.g., in an `OPEN` script with no triggering actor).

## Behavior notes

- **Activator vs. TID:** When `tid` is 0, the function applies to the script's activator via the `it` pointer (the player or actor that triggered the script). When `tid` is non-zero, the function iterates through all actors with that TID and applies the thrust to each one independently. Note: when `tid` is non-zero, the function returns `true` even if no actors match (the TID-iterator loop is empty).

- **Netcode (multiplayer):** Two distinct code paths with asymmetric client-side behavior:
  - **TID path (`tid != 0`):** Server applies the thrust; clients never apply it locally. The server then broadcasts the new position and Z-velocity via `SERVERCOMMANDS_MoveThingExact`.
  - **Activator path (`tid == 0`):** Implements client-side prediction. If the activator is a player and the local machine is not in pure-client mode, the client applies the thrust to its own console player immediately (prediction). The server then confirms with `SERVER_UpdateThingVelocity` (velocity only, no position resync). This asymmetry is a Zandronum-specific optimization documented in commit `b335d4cde`.

- **Gravity:** This function manipulates Z-velocity directly; it does not disable gravity. Actors affected by gravity will continue to fall, with the initial Z-velocity set/modified by this function.

## Engine-family divergence

- **Force-value overflow quirk is Zandronum-only.** Zandronum computes the thrust as a 32-bit
  fixed-point value, `fixed_t thrust = arg1*FRACUNIT/4` (`src/p_lnspec.cpp`'s `FUNC(LS_ThrustThingZ)`),
  so large `force` arguments (`> 32767`) overflow the intermediate multiplication before the divide,
  as described above. UZDoom stores actor velocity as a `double` and computes the thrust directly as
  `double thrust = arg1/4.` (UZDoom source's `src/playsim/p_lnspec.cpp`, `FUNC(LS_ThrustThingZ)`) —
  there is no `FRACUNIT` multiplication and therefore no equivalent overflow at that range. A script
  passing `force` values near or above 32767 for vertical thrust behaves differently in magnitude
  between the two engines; everything else about the function (TID vs. activator targeting,
  `direction`/`mode` semantics, the `false`-on-no-activator return, and gravity being left alone)
  is otherwise identical.
- The documented netcode/client-prediction behavior above is already scoped as Zandronum-specific
  in the text; UZDoom's `FUNC(LS_ThrustThingZ)` has no equivalent client/server split at all — it
  applies the velocity change unconditionally in both the TID and activator branches.

## Related

- **`ThrustThing`** — similar function that applies *horizontal* thrust instead of vertical. Can be combined with `ThrustThingZ` to produce diagonal or arbitrary-direction forces.

## Example

Repeatedly thrust the activator upward and downward (ACS):

```acs
script "BobPlayer" ENTER
{
  while (true) {
    ThrustThingZ(0, 4, 0, 1);  // Add upward thrust (1 map-unit/tic) to console player
    Delay(35);                  // Wait one second
    ThrustThingZ(0, 4, 1, 1);  // Add downward thrust
    Delay(35);                  // Wait one second
  }
}
```

**Note on the wiki example:** The wiki page's example is written in ZScript (`class FloatingStimpack : Health { States { Spawn: STIM A 25 ThrustThingZ(...); ... } }`), which does not exist in Zandronum. The action-special pattern itself transfers via DECORATE state actions (e.g., `States { Spawn: ITEM A 1 A_LineSpecial(128, 0, 4, 0, 1); ... }`), but the class syntax does not.
