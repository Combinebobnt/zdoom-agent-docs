# `A_JumpIfTargetInsideMeleeRange (str state)` / `A_JumpIfTargetInsideMeleeRange (int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_JumpIfTargetInsideMeleeRange` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfTargetInsideMeleeRange&oldid=42383) + verified against Zandronum source `src/thingdef/thingdef_codeptr.cpp:836-850`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

## Engine-family divergence: distance calculation

The "Distance check" condition above describes Zandronum's `P_AproxDistance`, an octagonal
(Doom-classic) approximation of 2D distance. **UZDoom's `A_JumpIfTargetInsideMeleeRange` uses true
Euclidean distance instead** — its native `P_CheckMeleeRange()` (`src/playsim/p_enemy.cpp`) calls
`actor->Distance2D(pl)`, which computes an exact `sqrt(dx*dx + dy*dy)` rather than the octagonal
`max + 3*min/8` estimate. The two engines' melee-range thresholds therefore don't line up exactly
at all angles — `P_AproxDistance` over-estimates true distance by up to ~6% at a 45° angle, so a
target near the boundary can read as "inside melee range" on one engine and "outside" on the other
for a diagonal approach. The other conditions (vertical check, friend check, line-of-sight) use
the same logic and thresholds on both engines.

UZDoom's `P_CheckMeleeRange()` also has one additional early-out not present in Zandronum's
`CheckMeleeRange()`: if the calling actor's sector has the `SECF_NOATTACK` flag set (`monsters
cannot start attacks in this sector`, `src/gamedata/r_defs.h`), the check fails immediately
regardless of distance, vertical bounds, friendship, or sight. Zandronum has no equivalent sector
flag, so a monster standing in a would-be `SECF_NOATTACK` sector on UZDoom can still trigger this
jump on Zandronum.

## Engine-family divergence: network synchronization

The "Network Synchronization" section above is Zandronum-specific and does not apply to UZDoom.
UZDoom has no client/server authority split anywhere in its source tree for this function — no
`NETWORK_InClientModeAndActorNotClientHandled()`-style gate, and no `+CLIENTSIDEONLY` bypass
check. `A_JumpIfTargetInsideMeleeRange` is a plain ZScript `action state` method
(`wadsrc/static/zscript/actors/checks.zs`) that evaluates `CheckMeleeRange()` and resolves the
jump unconditionally — there is no networking consideration at all.

## Companion and related functions

- `A_JumpIfTargetOutsideMeleeRange` — The inverse condition: jumps if the target is **outside** melee range (does not require line of sight when outside melee range).
- `A_CheckRange` — Distance-only check without line-of-sight requirement or melee-specific semantics.
