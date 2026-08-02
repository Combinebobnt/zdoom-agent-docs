# `A_JumpIfTargetOutsideMeleeRange (state label)` / `A_JumpIfTargetOutsideMeleeRange (int offset)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_JumpIfTargetOutsideMeleeRange` (retrieved 2026-08-01, oldid=42382) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:815-829` and `src/p_enemy.cpp:245-280` (`CheckMeleeRange` function).
**Bucket:** AActor — callable from any actor's state table.

Jumps to a target state (or forward by an offset) if the calling actor's target is **not** within melee range. Note that this includes the cases where the target is null, blocked by line of sight, outside vertical range, or considered a friendly.

## Parameters

- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. Two overloads: pass a string (quoted in DECORATE) to jump to a named state, or an integer offset to jump forward by that many frame states from the current one.

## Behavior and range calculation

The jump condition inverts the result of `CheckMeleeRange()`, which evaluates several constraints:

1. **Null target** — If the calling actor has no target (`target` field is null), the function jumps. The jump occurs regardless of the actor's current position or any other state.
2. **Distance check** — The distance between the caller and target is calculated using octagonal approximation (not true Euclidean). The jump occurs if distance >= `meleerange + target->radius`. Note that the **caller's own radius is not included** in this calculation — only the target's radius is added. This asymmetry can produce surprising results for very wide actors (e.g., a wide monster may be unable to reach a target that is theoretically overlapping it).
3. **Vertical range** — Unless the target has the `MF5_NOVERTICALMELEERANGE` flag set, the function checks whether the target is within the calling actor's vertical reach (target's `z` and `z + height` must be within the caller's `z` to `z + height` range). If the target fails this check, the function jumps.
4. **Friendly fire** — If the target is considered a friend of the caller (determined by `IsFriend(self, target)`), the function jumps.
5. **Line of sight** — The function performs a `P_CheckSight` test. If no line of sight exists between the caller and target, the function jumps.
6. **Special case: master as goal** — If the target is the same actor as the caller's `goal` field, melee range is immediately considered "in range" and no jump occurs. This short-circuit happens before the vertical and friendly checks.

The default melee range (`MELEERANGE`) is `64 * FRACUNIT` (64 fixed-point units, or approximately 1 map unit in standard Doom dimensions), but this is configurable per actor via its `meleerange` property. Many monster classes override this default.

## Wiki/engine divergence

The ZDoom wiki's description — "when the target of the calling actor is beyond melee range" — presupposes that the target exists. **In Zandronum, this function jumps when there is no target at all** (null target), before any distance or range checks. This is a divergence from the wiki's framing rather than a contradiction — the wiki's language focuses on the distance-based semantics, while the null-target case is an important practical consequence of how `CheckMeleeRange()` is implemented.

## Network synchronization

In multiplayer, the melee-range check is server-authoritative. If the calling actor does not have the `NETFL_CLIENTSIDEONLY` flag, the function returns immediately in client mode without evaluating the condition — the server's decision is broadcast to the client via a position/frame synchronization update (`CLIENTUPDATE_FRAME | CLIENTUPDATE_POSITION`). This synchronization is necessary because clients do not have access to the calling actor's target pointer in network-latent actors.

For `+CLIENTSIDEONLY` actors (spawned only on the client and having no network authority), the range check runs on both server and client independently, with each maintaining its own copy of the actor's state.

## See also

- `A_JumpIfTargetInsideMeleeRange` — the inverse condition; does not jump if the target is outside melee range.
- `A_JumpIfCloser` — similar conditional jump based on a custom distance threshold instead of actor melee range.
- `A_CheckSight` — checks only line-of-sight visibility, without distance or vertical range constraints.
