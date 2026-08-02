# `state A_CheckSightOrRange(float distance, state label)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_CheckSightOrRange` (retrieved 2026-07-31, oldid=44212) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3330-3401`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CheckSightOrRange)` in `src/thingdef/thingdef_codeptr.cpp:3374`.

Jumps to a target state if the calling actor is **both** out of range **and** out of sight of all players. Returns (continues to next state) if at least one player satisfies either the distance check or the sight check. Useful for toggling behavior of actors in complex maps with many simultaneous effects.

## Signature and Parameters

**`distance`** (float, required)  
The maximum distance at which the actor should be considered "in range" of a player. Measured in map units, squared internally to avoid a square-root computation. The distance is compared to all active players and their camera viewpoints.

**`state label`** (state, required)  
The jump destination when both distance and sight checks fail (actor is far away and not visible). Resolved as a state label in the calling actor's derived class, with fallback to ancestor states via virtual inheritance (same resolution as other state-jump actions).

## Behavior: range and sight checks

The function iterates through all active players in the game. For each player:

1. **Distance check (performed first, cheaper than sight tests):** Calculates the distance from the actor to the player's pawn and separately to the player's camera viewpoint (if they are viewing through a non-player camera, e.g., co-op spy or a free camera). If the actor is within the specified distance of either viewpoint, the check returns true ("in range").

2. **Sight check (only if distance fails):** If distance check is false, calls `P_CheckSight(camera, self, SF_IGNOREVISIBILITY)` to test line of sight. See "Line of sight semantics" below.

3. **Early return:** As soon as any player satisfies either the distance check or the sight check, the function returns immediately without jumping — execution continues to the next state-line action.

4. **Jump condition:** If no player passes either check, the function jumps to the specified state label.

## Line of sight semantics

The sight check uses `P_CheckSight(..., SF_IGNOREVISIBILITY)`, which:

- Ignores invisibility flags (`MF_SHADOW`, `RF_INVISIBLE`) and alpha (`RenderStyle` with zero alpha).
- Ignores whether the player is actually **facing** the actor — only whether a potential line of sight exists. If a player is positioned where they could see the actor if they turned, the check returns true.
- Uses the same 3/4-height eye position as `P_CheckSight`, not the player pawn's center.

## Wiki divergence: distance and visibility measurement

The wiki states the check measures "between the center of the calling actor and that of any player pawn." This is **not accurate** in Zandronum:

- **On the viewer side:** The distance is measured from the player's eye position (3/4 of the viewer's height above its base), not from the viewer's center.
- **On the actor side:** The distance to the actor is clamped to the actor's vertical extent (`z` to `z + height`). If the viewer's eye height falls within this range, the vertical component (`dz`) is **zero**, making the check effectively 2D (horizontal distance only). Otherwise, the distance is measured to the nearest vertical edge of the actor's bounds.

This means the distance behavior varies depending on whether the actor and viewer are on the same floor or at different elevations — in the common case where they are roughly at the same height, the check degenerates to a 2D distance check even without an explicit parameter.

## Parameter differences from ZDoom wiki

The ZDoom wiki shows an optional third parameter, `bool 2d_check`, which does **not exist in Zandronum**. Passing a third argument will cause a parse error in Zandronum. (See above for why the 2D-vs-3D behavior is less relevant in practice due to the eye-height clamping.)

The wiki also suggests both `int offset` and `state label` variants; Zandronum has only the `state label` variant (see `wadsrc/static/actors/actor.txt:313`), though `ACTION_PARAM_STATE` may handle both spellings internally.

## Network considerations

**This function runs on both server and client**, unlike `A_Look` or `A_CheckSight` which have explicit client-mode early-returns. The source code comment `[BB] This is hopefully okay.` indicates uncertainty in the original implementation.

This means:
- On a network-authoritative server, the function evaluates each player's true position and camera state and makes the jump decision.
- On a client, the function uses the client's local world state to make the same decision independently, based on potentially out-of-sync player positions or camera state.
- For actors without `NETFL_CLIENTSIDEONLY`, this client-side evaluation is **not sent to other machines** — only the server's decision propagates via state changes (the `ACTION_JUMP` call with `0` parameter, which differs from `A_CheckSight`'s `CLIENTUPDATE_FRAME`).
- For `+CLIENTSIDEONLY` actors, each client simulates its own copy and this divergence is acceptable (the flag documents such actors as visuals-only with no cross-machine consistency requirement).

The practical risk is low for typical use cases (defensive checks where a false-negative result does not cause game-breaking behavior), but code using this for high-stakes decisions should be aware of this network topology.

## Player cameras and co-op spy

The function checks line of sight and distance to both:

- Each active player's pawn (`players[i].mo`).
- Each active player's camera viewpoint, **if non-NULL and not a player pawn itself** (e.g., a free-floating camera spawned by Chasecam, Spectate, or custom camera-switching logic).

Camera textures are **not** checked — the actor does not know whether it is being viewed through a camera texture portal.

Spectating players are **not** explicitly excluded (unlike `A_CheckSight`'s `bSpectating` check), so spectators will be treated as normal players for the purpose of this check.

## Null pointer safety

The helper function `DoCheckSightOrRange` guards against `camera == NULL` with an early return (returning false if the camera pointer is null), so the main loop's `MAXPLAYERS` iteration is safe — even if a player's `mo` or `camera` is uninitialized, no null dereference occurs.

## See also

- `A_CheckSight` — checks whether **any** player can see the actor (no distance component).
- `A_CheckRange` — checks only distance to players (no line of sight component).
- `A_JumpIfInTargetLOS` — checks whether the **target** is in line of sight *from* the actor.
- `A_JumpIfTargetInLOS` — similar, alternate naming.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) — detailed coverage of how state jumps interact with client/server in multiplayer.
