# `A_CheckRange`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_CheckRange` (retrieved 2026-08-01, oldid=46727) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3409-3463`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CheckRange)` in `src/thingdef/thingdef_codeptr.cpp:3436`.

Jumps to a target state if the calling actor is beyond a specified distance range from all active players. Returns (continues to next state) if at least one player is within the distance.

## Signature and Parameters

**`distance`** (float, required)  
The maximum distance at which the actor should be considered "in range" of a player, measured in map units. Internally squared to avoid a square-root computation. The distance comparison is 3D: it includes the vertical component and is measured from each player's eye position to the actor's nearest vertical point.

**`state label`** (state, required)  
The jump destination when all players are beyond the distance range. Resolved as a state label in the calling actor's derived class, with fallback to ancestor states via virtual inheritance.

## Behavior: distance calculation

The function iterates through all active players. For each player:

1. **Sight-independent check:** Calculates the 3D distance from the calling actor to the player's pawn and separately to the player's camera viewpoint (if they are viewing through a non-player camera, e.g., co-op spy or a free camera).

2. **Distance measurement:** The distance is measured from the **player's eye position** (3/4 of the viewer's height above its base, the same eye height as `P_CheckSight` uses) to the actor. On the actor side, the distance is clamped to the actor's vertical extent (`z` to `z + height`). If the player's eye height falls within the actor's vertical range, the vertical component (`dz`) is zero, making the check effectively 2D in that scenario.

3. **Early return:** As soon as any player is within the specified distance of either their pawn or their camera viewpoint, the function returns immediately without jumping — execution continues to the next state-line action.

4. **Jump condition:** If all players are beyond the distance, the function jumps to the specified state label.

## Player cameras and co-op spy

The function checks distance to both:

- Each active player's pawn (`players[i].mo`).
- Each active player's camera viewpoint, **if non-NULL and not a player pawn itself** (e.g., a free-floating camera spawned by Chasecam, Spectate, or custom camera-switching logic).

The check accounts for actors being viewed through free-floating cameras and co-op spy viewpoints.

## Network considerations

**This function runs on both server and client**, similar to `A_CheckSightOrRange`. The source code comment `[BB] Let's hope that the clients know enough.` indicates the original implementation expected clients to infer the correct outcome independently.

This means:

- On the server, the function evaluates each player's true position and makes the jump decision.
- On a client, the function uses the client's local world state, based on potentially out-of-sync player positions.
- For actors without `NETFL_CLIENTSIDEONLY`, this client-side evaluation is **not sent to other machines** — the jump parameter `0` means no cross-machine state-sync signal is sent (unlike `A_CheckSight`'s `CLIENTUPDATE_FRAME`).
- For `+CLIENTSIDEONLY` actors, each client simulates its own copy and divergence is acceptable.

## Wiki/fork divergence: parameters

The ZDoom wiki page describes optional and alternate parameters that **do not exist in Zandronum**:

- **`int offset` variant:** The wiki suggests a variant accepting an integer offset instead of a state label. Zandronum has only the `state label` variant (see `wadsrc/static/actors/actor.txt`), and passing an integer will likely be interpreted as a frame offset if the parameter macro supports it, not as a second overload.
- **`bool 2d_check` parameter:** The wiki describes an optional third boolean parameter for forcing a 2D distance check (ignoring z-coordinates). **This parameter does not exist in Zandronum.** The Zandronum implementation (`ACTION_PARAM_START(2)`) accepts only two parameters: the distance and the jump state. Passing a third argument will cause a compile error in Zandronum DECORATE.

The reason the wiki's 2D-vs-3D distinction may have seemed important is that in practice, when an actor and viewer are at roughly the same height, the distance check already degenerates to 2D (vertical component becomes zero) due to the eye-height clamping described above. There is no need for an explicit 2D mode.

## See also

- `A_CheckSight` — checks whether **any** player can see the actor (no distance component).
- `A_CheckSightOrRange` — checks both sight *and* distance to a target range.
- `A_JumpIfInTargetLOS` — checks whether the **target** is in line of sight *from* the actor.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) — detailed coverage of how state jumps interact with client/server in multiplayer.
