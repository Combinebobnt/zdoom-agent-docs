# `A_JumpIfTargetInsideMeleeRange (str state)` / `A_JumpIfTargetInsideMeleeRange (int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_JumpIfTargetInsideMeleeRange` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfTargetInsideMeleeRange&oldid=42383) + verified against Zandronum source `src/thingdef/thingdef_codeptr.cpp:836-850`, `src/p_enemy.cpp:245-280`, `src/p_maputl.cpp:59-64`, `src/p_mobj.cpp:7663-7681`, `src/network.cpp:1598-1612`, `src/thingdef/thingdef_codeptr.cpp:695-753`, `src/thingdef/thingdef_states.cpp:377-397`, `wadsrc/static/actors/actor.txt:12`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIfTargetInsideMeleeRange)` (callable from any actor's state table).

Jumps to a target state if the calling actor's target is within melee range.

## Parameters

**state / offset** — Target state (by name string or relative frame offset) to jump to if the condition is met. On Zandronum an offset must be a non-negative integer literal: negative is a parse error, 0 means no jump, and a positive offset on a multi-frame line is a parse error.

## Behavior

The check is `AActor::CheckMeleeRange()` (the Zandronum source's `src/p_enemy.cpp:245-280`). It runs these steps in order:

1. **Target exists:** The actor has a non-NULL `target` pointer. If target is NULL, the function returns without jumping.

2. **Distance check:** The actor's `meleerange` field (the `MeleeRange` property, 44 map units by default) plus the target's radius must be greater than the approximate XY distance between the actors. Distance uses the `P_AproxDistance` approximation, not true Euclidean distance.

3. **Goal shortcut:** If the target is also the actor's `goal`, the check succeeds here. Steps 4 to 6 are skipped.

4. **Vertical check:** Unless the calling actor has the `MF5_NOVERTICALMELEERANGE` flag set, the two actors' bodies must overlap vertically. The check fails if the target's bottom is above the caller's top, or the target's top is below the caller's bottom.

5. **Friendship check:** The target must not be a friend (`IsFriend(target)`). On Zandronum this is only ever true when both actors are `+FRIENDLY`. In cooperative play that alone makes them friends; in deathmatch or team games it also depends on the owning players being teammates.

6. **Line of sight:** The actor must be able to see the target via `P_CheckSight`.

## Network Synchronization

This function is server-authoritative in multiplayer. On a client, the function returns immediately if `NETWORK_InClientModeAndActorNotClientHandled()` is true (the standard gate for actions that require server authority). The check runs locally instead when the actor is client-handled: it has `+CLIENTSIDEONLY`, or it has no network ID. When the server takes the jump from the actor's own state, it sends clients the new frame and the actor's position.

## Wiki/engine divergence

The ZDoom wiki page includes a note that "Jump functions perform differently inside of anonymous functions." **This note does not apply to Zandronum.** Anonymous action blocks (`{ ... }` in place of a single action call) are a later ZDoom-lineage addition that UZDoom accepts in DECORATE as well as ZScript, but Zandronum's DECORATE parser does not support them.

## Engine-family divergence: distance calculation

The "Distance check" condition above describes Zandronum's `P_AproxDistance`, a
(Doom-classic) approximation of 2D distance. **UZDoom's `A_JumpIfTargetInsideMeleeRange` uses true
Euclidean distance instead** — its native `P_CheckMeleeRange()` (`src/playsim/p_enemy.cpp`) calls
`actor->Distance2D(pl)`, which computes an exact `sqrt(dx*dx + dy*dy)` rather than Zandronum's
`max + min/2` estimate. The two engines' melee-range thresholds therefore don't line up exactly
at all angles. `P_AproxDistance` never under-estimates true distance and over-estimates it by up
to about 11.8% (near a 26.6° angle), so a target near the boundary can read as "outside melee
range" on Zandronum while UZDoom reads it as "inside" for an off-axis approach. The other conditions
(goal shortcut, vertical check, friend check, line-of-sight) use the same logic and thresholds on
both engines.

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

- `A_JumpIfTargetOutsideMeleeRange` — The exact inverse: jumps whenever the check above fails, including when there is no target, the target is out of vertical reach, is a friend, or is not in sight.
- `A_CheckRange` — Checks distance to players rather than to `target`, and jumps when the caller is out of range of every player.
