# `A_JumpIfTargetOutsideMeleeRange (state label)` / `A_JumpIfTargetOutsideMeleeRange (int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_JumpIfTargetOutsideMeleeRange` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfTargetOutsideMeleeRange&oldid=42382) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:815-829` and `src/p_enemy.cpp:245-280` (`CheckMeleeRange` function).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

## Engine-family divergence: distance calculation

UZDoom's melee-range check (`Actor.CheckMeleeRange()`, declared in the ZScript stdlib's `actors/actor.zs` and backed natively by `P_CheckMeleeRange` in `src/playsim/p_enemy.cpp`) computes the caller-to-target distance with a true 2D Euclidean measurement (`Actor.Distance2D`, i.e. the length of the `(dx, dy)` vector), not Zandronum's octagonal approximation (`P_AproxDistance`, `max(|dx|,|dy|) + min(|dx|,|dy|)/2`). The Euclidean distance is always less than or equal to the octagonal approximation for the same `(dx, dy)` pair (equal only along the axes, increasingly smaller as the angle approaches 45 degrees), so for the same numeric `meleerange`, a target near the boundary along a diagonal approach can be judged in range on UZDoom while Zandronum's approximation would judge it out of range and take the jump.

## Engine-family divergence: sector-based attack blocking

UZDoom's `P_CheckMeleeRange` adds a check with no Zandronum equivalent: if the calling actor's current sector has the `SECF_NOATTACK` flag set (`src/gamedata/r_defs.h`; a MAPINFO/UDMF sector flag meaning monsters cannot start attacks in that sector), the function returns false immediately, so the jump fires, regardless of the target's distance, vertical position, friendliness, or line of sight. This check runs immediately after the goal short-circuit (so it's skipped, same as the vertical/friendly/sight checks, when the target is also the actor's move-goal) but before the vertical-range check. Zandronum's `AActor::CheckMeleeRange` has no equivalent flag check at all, so a monster standing in a sector that would suppress its melee attack on UZDoom is unaffected on Zandronum.

## Wiki/engine divergence

The ZDoom wiki's description — "when the target of the calling actor is beyond melee range" — presupposes that the target exists. **In Zandronum, this function jumps when there is no target at all** (null target), before any distance or range checks. This is a divergence from the wiki's framing rather than a contradiction — the wiki's language focuses on the distance-based semantics, while the null-target case is an important practical consequence of how `CheckMeleeRange()` is implemented.

## Network synchronization

In multiplayer, the melee-range check is server-authoritative. If the calling actor does not have the `NETFL_CLIENTSIDEONLY` flag, the function returns immediately in client mode without evaluating the condition — the server's decision is broadcast to the client via a position/frame synchronization update (`CLIENTUPDATE_FRAME | CLIENTUPDATE_POSITION`). This synchronization is necessary because clients do not have access to the calling actor's target pointer in network-latent actors.

For `+CLIENTSIDEONLY` actors (spawned only on the client and having no network authority), the range check runs on both server and client independently, with each maintaining its own copy of the actor's state.

## Engine-family divergence: no client/server authority split

UZDoom has no client/server authority split anywhere in its source tree — no `NETWORK_InClientMode`-style gate, no `SERVERCOMMANDS_*`-style broadcast, no `CLIENTUPDATE_*` flags. `A_JumpIfTargetOutsideMeleeRange`/`A_JumpIfTargetInsideMeleeRange` are declared directly as ZScript `action state` functions (`wadsrc/static/zscript/actors/checks.zs`) that call the natively-implemented `CheckMeleeRange()` unconditionally on whichever machine runs the state — there is no separate client-side code path, no server-authoritative decision, and no explicit position/frame synchronization step. The entire "Network synchronization" section above describes machinery that is specific to Zandronum and does not exist on UZDoom at all.

## See also

- `A_JumpIfTargetInsideMeleeRange` — the inverse condition; does not jump if the target is outside melee range.
- `A_JumpIfCloser` — similar conditional jump based on a custom distance threshold instead of actor melee range.
- `A_CheckSight` — checks only line-of-sight visibility, without distance or vertical range constraints.
