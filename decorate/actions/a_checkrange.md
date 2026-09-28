# `A_CheckRange`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_CheckRange` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CheckRange&oldid=46727) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3409-3463`, `src/thingdef/thingdef_states.cpp:377-397,430`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CheckRange)` in `src/thingdef/thingdef_codeptr.cpp:3436`.

Jumps to a target state if the calling actor is beyond a specified distance range from all active players. Returns (continues to next state) if at least one player is within the distance.

## Signature and Parameters

**`distance`** (float, required)  
The maximum distance at which the actor should be considered "in range" of a player, measured in map units. Internally squared to avoid a square-root computation. The distance comparison is 3D: it includes the vertical component and is measured from each player's eye position to the actor's nearest vertical point.

**`state label`** (state, required)  
The jump destination when all players are beyond the distance range. On Zandronum, an unscoped label is looked up at run time in the state owner's actual class, so a subclass that redefines the label jumps to its own version; a `Super::` or `Class::` scoped label is resolved at load time. If the label isn't found at run time, `Jump target '...' not found in <class>` prints to the console and no jump happens. A non-negative integer offset is also accepted (see "Engine-family divergence: parameters" below).

## Behavior: distance calculation

The function iterates through all active players. For each player:

1. **Sight-independent check:** Calculates the 3D distance from the calling actor to the player's pawn and separately to the player's camera viewpoint, if that camera is a non-player actor (e.g. one set with `ChangeCamera`). Co-op spy doesn't count as a separate viewpoint: its camera is another player's pawn, which that player's own pawn check already covers.

2. **Distance measurement:** The distance is measured from the **player's eye position** (3/4 of the viewer's height above its base, the same eye height as `P_CheckSight` uses) to the actor. On the actor side, the distance is clamped to the actor's vertical extent (`z` to `z + height`). If the player's eye height falls within the actor's vertical range, the vertical component (`dz`) is zero, making the check effectively 2D in that scenario.

3. **Early return:** As soon as any player is within the specified distance of either their pawn or their camera viewpoint, the function returns immediately without jumping — execution continues to the next state-line action.

4. **Jump condition:** If all players are beyond the distance, the function jumps to the specified state label.

## Player cameras and co-op spy

The function checks distance to both:

- Each active player's pawn (`players[i].mo`).
- Each active player's camera viewpoint, **if non-NULL and not a player pawn itself** (e.g. a camera actor set with the `ChangeCamera` special).

Co-op spy, chasecam and spectating don't add a viewpoint. Chasecam and spectating leave the camera on the player's own pawn, and co-op spy points it at another player's pawn, which the pawn check already covers.

On Zandronum, spectators are not skipped (unlike `A_CheckSight`, which skips them), and a spectator keeps a pawn, so a spectator's position keeps an actor in range.

## Network considerations

**This function runs on both server and client**, similar to `A_CheckSightOrRange`. The source code comment `[BB] Let's hope that the clients know enough.` indicates the original implementation expected clients to infer the correct outcome independently.

This means:

- On the server, the function evaluates each player's true position and makes the jump decision.
- On a client, the function uses the client's local world state, based on potentially out-of-sync player positions.
- The jump passes no client-update flags (`ACTION_JUMP(jump, 0)`), so even the server's jump is **not broadcast** to clients (unlike `A_CheckSight`, which jumps with `CLIENTUPDATE_FRAME`). Server and each client decide independently, and a client that decides differently stays out of step until some other state update for the actor arrives.
- For `+CLIENTSIDEONLY` actors, each client simulates its own copy and divergence is acceptable.

## Engine-family divergence: parameters

The ZDoom wiki page describes an integer-offset form and an optional third parameter. On Zandronum:

- **`int offset` form: supported.** Zandronum declares only `A_CheckRange(float distance, state label)` (`wadsrc/static/actors/actor.txt`), but every `state` parameter accepts either a quoted label or a non-negative integer literal (the Zandronum source's `src/thingdef/thingdef_states.cpp:377-397`). This is the general state-parameter mechanism, not a second overload. `0` means no jump; offset N targets the state N after the calling one; a negative offset is a parse error ("Negative jump offsets are not allowed"), and so is a positive offset on a line that defines more than one frame.
- **`bool 2d_check` parameter: does not exist.** The Zandronum implementation (`ACTION_PARAM_START(2)`) takes only the distance and the jump state. Passing a third argument is a fatal parse error at load (`Expected ')', got ','.`), because the parser requires `)` after the last declared parameter (`thingdef_states.cpp:430`).

Zandronum has no way to force a 2D check. Its 3D check degenerates to 2D only when the viewer's eye height (3/4 of its height) falls inside the checked actor's vertical extent. A short actor on the same floor as the player still gets a nonzero vertical component.

**UZDoom does implement this parameter.** UZDoom's `A_CheckRange(double distance, statelabel label, bool two_dimension = false)` accepts the third boolean, matching the wiki's description; when `true`, the vertical component of the distance check is forced to zero regardless of the clamping logic below, giving an explicit pure-2D check rather than relying on same-height degeneration.

## Engine-family divergence: reference point for the vertical clamp

Zandronum and UZDoom both clamp the vertical component of the distance check to the target actor's vertical extent (as described above), but they anchor that clamp from a different point on the *player/camera* side:

- **Zandronum** anchors from the player/camera's **eye height**, computed as `z + height - (height / 4)` — i.e. 3/4 of the actor's height above its base, the same formula the source comments as matching `P_CheckSight`'s eye height.
- **UZDoom** anchors from the player/camera's **vertical center**, via the shared `AActor::Center()` helper (`Z() + Height / 2`) — the midpoint of the actor's height, not its eye/view height. The local variable is still named `eyez` in the UZDoom source, but the value it holds is the mid-height center, not an eye position.

The two reference heights are 1/4 of the player/camera's height apart, so the computed vertical component can differ by up to that much. It differs whenever the checked actor's vertical extent doesn't contain both reference heights. That includes a short actor on the same floor as the player, not only setups where one stands on a ledge above the other. Only when the extent contains both (e.g. a tall actor on the same floor) is the vertical component 0 in both engines, so the divergence has no effect.

## See also

- `A_CheckSight` — checks whether **any** player can see the actor (no distance component).
- `A_CheckSightOrRange` — checks both sight *and* distance to a target range.
- `A_JumpIfInTargetLOS` — checks whether the **target** is in line of sight *from* the actor.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) — detailed coverage of how state jumps interact with client/server in multiplayer.
