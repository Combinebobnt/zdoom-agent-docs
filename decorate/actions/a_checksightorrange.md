# `state A_CheckSightOrRange(float distance, state label)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_CheckSightOrRange` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_CheckSightOrRange&oldid=44212) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3330-3401`; corrections backed by `src/thingdef/thingdef_codeptr.cpp:695-753` (`DoJump`), `src/thingdef/thingdef_states.cpp:377-397` (integer jump offsets), `src/p_sight.cpp:686` (`SF_IGNOREVISIBILITY`), `src/g_game.cpp:1183` (co-op spy camera) and `src/p_lnspec.cpp:2899-2912` (`ChangeCamera`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CheckSightOrRange)` in `src/thingdef/thingdef_codeptr.cpp:3374`.

Jumps to a target state if the calling actor is **both** out of range **and** out of sight of all players. Returns (continues to next state) if at least one player satisfies either the distance check or the sight check. Useful for toggling behavior of actors in complex maps with many simultaneous effects.

## Signature and Parameters

**`distance`** (float, required)  
The maximum distance at which the actor should be considered "in range" of a player. Measured in map units, squared internally to avoid a square-root computation. The distance is compared to all active players and their camera viewpoints.

**`state label`** (state, required)  
The jump destination when both distance and sight checks fail (actor is far away and not visible). Resolved as a state label in the calling actor's derived class, with fallback to ancestor states via virtual inheritance (same resolution as other state-jump actions).

## Behavior: range and sight checks

The function iterates through all active players in the game. For each player:

1. **Distance check (performed first, cheaper than sight tests):** Calculates the distance from the actor to the player's pawn and separately to the player's camera viewpoint (only if that camera is a non-player actor, e.g. a map camera set by `ChangeCamera`). If the actor is within the specified distance of either viewpoint, the check returns true ("in range").

2. **Sight check (only if distance fails):** If distance check is false, calls `P_CheckSight(camera, self, SF_IGNOREVISIBILITY)` to test line of sight. See "Line of sight semantics" below.

3. **Early return:** As soon as any player satisfies either the distance check or the sight check, the function returns immediately without jumping — execution continues to the next state-line action.

4. **Jump condition:** If no player passes either check, the function jumps to the specified state label.

## Line of sight semantics

The sight check uses `P_CheckSight(..., SF_IGNOREVISIBILITY)`, which:

- Ignores `RF_INVISIBLE` and a `RenderStyle`/alpha combination that makes the actor invisible. `+SHADOW` is never consulted by `P_CheckSight`, with or without this flag.
- Ignores whether the player is actually **facing** the actor — only whether a potential line of sight exists. If a player is positioned where they could see the actor if they turned, the check returns true.
- Uses the same 3/4-height eye position as `P_CheckSight`, not the player pawn's center.

## Wiki/engine divergence: distance and visibility measurement

The wiki states the check measures "between the center of the calling actor and that of any player pawn." This is **not accurate** in Zandronum:

- **On the viewer side:** The distance is measured from the player's eye position (3/4 of the viewer's height above its base), not from the viewer's center.
- **On the actor side:** The distance to the actor is clamped to the actor's vertical extent (`z` to `z + height`). If the viewer's eye height falls within this range, the vertical component (`dz`) is **zero**, making the check effectively 2D (horizontal distance only). Otherwise, the distance is measured to the nearest vertical edge of the actor's bounds.

The check is therefore effectively 2D only when the actor's vertical extent spans the viewer's eye height. Standing on the same floor as a default 56-unit-tall player (eye reference 42 units up), an actor must be at least 42 units tall for the vertical component to be zero. A shorter actor, such as a small effect sprite, still gets a vertical component equal to the gap between its top and the player's eye height.

## Engine-family divergence: reference point for the vertical clamp

Zandronum and UZDoom both clamp the vertical component of the distance check to the target actor's vertical extent (as described above), but they anchor that clamp from a different point on the *player/camera* side:

- **Zandronum** anchors from the player/camera's **eye height**, 3/4 of the actor's height above its base, the same formula the source comments as matching `P_CheckSight`'s eye height (see above).
- **UZDoom** anchors from the player/camera's **vertical center**, via the shared `AActor::Center()` helper (`Z() + Height / 2`) — the midpoint of the actor's height, not its eye/view height. UZDoom's `DoCheckSightOrRange` helper (`src/playsim/p_actionfunctions.cpp:1762-1797`, shared by both `A_CheckSightOrRange` and `A_CheckRange`) still names the local variable `eyez`, but the value it holds is the mid-height center, not an eye position.

The two reference heights are 1/4 of the viewer's height apart, and the vertical component differs between engines whenever either reference height falls outside the checked actor's extent. That includes the same-floor case. Against a default 56-unit player on the same floor, Zandronum's component is zero only for an actor at least 42 units tall, UZDoom's for one at least 28 units tall. A 16-unit actor gets a 26-unit vertical component on Zandronum but a 12-unit one on UZDoom. Both engines agree on a zero component only when the actor spans both reference heights. This affects the distance check only; the sight-check branch (`P_CheckSight`) is unaffected since it does not use this clamped vertical value.

## Engine-family divergence: parameters

The ZDoom wiki shows an optional third parameter, `bool 2d_check`, which does **not exist in Zandronum**. Passing a third argument is a fatal DECORATE parse error in Zandronum (`Expected ')', got ','.`). (See above for when the eye-height clamping already yields a 2D result.)

The wiki also lists `int offset` and `state label` variants. In Zandronum both are the same `state` parameter (`wadsrc/static/actors/actor.txt:313`), which accepts either a state label or an integer offset literal (`src/thingdef/thingdef_states.cpp:377-397`). Offset N targets the state N after the calling one, and 0 means no jump. A negative offset is a parse error ("Negative jump offsets are not allowed"), and so is a positive offset on a multi-frame state line.

**UZDoom does implement the `2d_check`-equivalent parameter.** UZDoom's `A_CheckSightOrRange(double distance, statelabel label, bool two_dimension = false)` (`wadsrc/static/zscript/actors/checks.zs:156`) accepts a third boolean matching the wiki's description; when `true`, the vertical component of the distance check is forced to zero regardless of the clamping logic above, giving an explicit pure-2D check rather than relying on same-height degeneration.

## Network considerations

**This function runs on both server and client**, unlike `A_Look` or `A_CheckSight` which have explicit client-mode branches. The source code comment `[BB] This is hopefully okay.` indicates uncertainty in the original implementation.

This means:
- On the server, the function evaluates each player's position and camera state and makes its own jump decision.
- On a client, the function uses the client's local world state to make the same decision independently, based on potentially out-of-sync player positions or camera state.
- **Neither decision is sent to other machines.** The jump is `ACTION_JUMP(jump, 0)`, and without `CLIENTUPDATE_FRAME` (which `A_CheckSight` passes), `DoJump` sends clients no state update even when the server takes the jump (`src/thingdef/thingdef_codeptr.cpp:695-753`). For actors without `NETFL_CLIENTSIDEONLY`, a client can therefore take a different branch than the server.
- For `+CLIENTSIDEONLY` actors, each client simulates its own copy and this divergence is acceptable (the flag documents such actors as visuals-only with no cross-machine consistency requirement).

The practical risk is low for typical use cases (defensive checks where a false-negative result does not cause game-breaking behavior), but code using this for high-stakes decisions should be aware of this network topology.

## Engine-family divergence: network execution model

The client/server authority split described above is specific to Zandronum's netcode. UZDoom has no equivalent concept for this function: a search of UZDoom's entire source tree turns up zero occurrences of `NETWORK_InClientMode`/`SERVERCOMMANDS_*` anywhere — not just for this function, the mechanism doesn't exist in UZDoom at all. UZDoom's `A_CheckSightOrRange` (`wadsrc/static/zscript/actors/checks.zs:156`, calling the native `CheckSightOrRange` in `src/playsim/p_actionfunctions.cpp:1799-1826`) contains no client-mode branch, no server-authoritative early return, and no cross-machine state-sync flag comparable to Zandronum's `ACTION_JUMP` parameter (`0` vs. `CLIENTUPDATE_FRAME`). It is a plain function call evaluated identically regardless of network role, so the entire "Network considerations" topology above does not apply to UZDoom.

## Player cameras and co-op spy

The function checks line of sight and distance to both:

- Each active player's pawn (`players[i].mo`).
- Each active player's camera viewpoint, **if non-NULL and not a player pawn itself** (e.g. a map camera actor set by `ChangeCamera`). Co-op spying points the camera at another player's pawn, so it adds no extra check, and chasecam is a player cheat flag rather than a camera change.

Camera textures are **not** checked — the actor does not know whether it is being viewed through a camera texture portal.

Spectating players are **not** explicitly excluded (unlike `A_CheckSight`'s `bSpectating` check), so spectators will be treated as normal players for the purpose of this check.

## Null pointer safety

The helper function `DoCheckSightOrRange` guards against `camera == NULL` with an early return (returning false if the camera pointer is null), so the main loop's `MAXPLAYERS` iteration is safe — even if a player's `mo` or `camera` is uninitialized, no null dereference occurs.

## See also

- `A_CheckSight` — checks whether **any** player can see the actor (no distance component).
- `A_CheckRange` — checks only distance to players (no line of sight component).
- `A_JumpIfTargetInLOS` — jumps if the actor can see its **target**.
- `A_JumpIfInTargetLOS` — the reverse direction: jumps if the actor is within its target's line of sight and field of view.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) — detailed coverage of how state jumps interact with client/server in multiplayer.
