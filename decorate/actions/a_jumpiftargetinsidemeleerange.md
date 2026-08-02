# `A_JumpIfTargetInsideMeleeRange (str state)` / `A_JumpIfTargetInsideMeleeRange (int offset)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_JumpIfTargetInsideMeleeRange` (retrieved 2026-08-01, oldid=42383) + verified against Zandronum source `src/thingdef/thingdef_codeptr.cpp:836-850`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIfTargetInsideMeleeRange)` (callable from any actor's state table).

Jumps to a target state if the calling actor's target is within melee range.

## Parameters

**state / offset** — Target state (by name string or relative frame offset) to jump to if the condition is met.

## Behavior

The jump occurs if all of the following conditions are true:

1. **Target exists:** The actor has a non-NULL `target` pointer. If target is NULL, the function returns without jumping.

2. **Distance check:** The actor's `meleerange` field (typically the actor's bounding-radius value for combat purposes) plus the target's radius is greater than the approximate XY distance between the actors. Distance uses octagonal approximation (`P_AproxDistance`), not true Euclidean distance.

3. **Vertical check:** Unless the target has the `MF5_NOVERTICALMELEERANGE` flag set, the target's Z position must fall within the actor's vertical bounds (not above the actor's ceiling or below the actor's floor).

4. **Friendship check:** The target must not be a friend (determined via `IsFriend(target)`, which checks team/species relationships and the `MF3_FRIENDLY` flag).

5. **Line of sight:** The actor must be able to see the target via `P_CheckSight`. This is the key semantic difference from `A_CheckRange` — melee attacks typically require line of sight.

## Network Synchronization

This function is server-authoritative in multiplayer. On a client, the function returns immediately if `NETWORK_InClientModeAndActorNotClientHandled()` is true (the standard gate for actions that require server authority). If the actor has `+CLIENTSIDEONLY`, the check is bypassed and the jump evaluates locally.

## Wiki/engine divergence

The ZDoom wiki page includes a note that "Jump functions perform differently inside of anonymous functions." **This note does not apply to Zandronum** — anonymous action blocks are a ZScript feature not available in Zandronum's DECORATE language.

## Companion and related functions

- `A_JumpIfTargetOutsideMeleeRange` — The inverse condition: jumps if the target is **outside** melee range (does not require line of sight when outside melee range).
- `A_CheckRange` — Distance-only check without line-of-sight requirement or melee-specific semantics.
