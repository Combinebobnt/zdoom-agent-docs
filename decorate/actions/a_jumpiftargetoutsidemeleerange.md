# `A_JumpIfTargetOutsideMeleeRange (state label)` / `A_JumpIfTargetOutsideMeleeRange (int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_JumpIfTargetOutsideMeleeRange` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfTargetOutsideMeleeRange&oldid=42382) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:815-829` and `src/p_enemy.cpp:245-280` (`CheckMeleeRange` function), plus `wadsrc/static/actors/actor.txt:12` (default `MeleeRange`), `src/p_maputl.cpp:59-64` (`P_AproxDistance`), `src/thingdef/thingdef_states.cpp:377-397` (offset rules), `src/network.cpp:1598-1611` and `src/thingdef/thingdef_codeptr.cpp:695-753` (`DoJump`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** AActor — callable from any actor's state table.

Jumps to a target state (or forward by an offset) if the calling actor's target is **not** within melee range. Note that this includes the cases where the target is null, blocked by line of sight, outside vertical range, or considered a friendly.

## Parameters

- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. Two overloads: pass a string (quoted in DECORATE) to jump to a named state, or an integer offset to jump forward by that many frame states from the current one. On Zandronum the offset must be a non-negative integer literal. A negative offset is a parse error ("Negative jump offsets are not allowed"), 0 means no jump, and a positive offset on a line defining more than one frame is a parse error.

## Behavior and range calculation

The jump condition inverts the result of `CheckMeleeRange()`, which evaluates several constraints:

1. **Null target** — If the calling actor has no target (`target` field is null), the function jumps. The jump occurs regardless of the actor's current position or any other state.
2. **Distance check** — The distance between the caller and target is calculated using octagonal approximation (not true Euclidean). The jump occurs if distance >= `meleerange + target->radius`. Note that the **caller's own radius is not included** in this calculation — only the target's radius is added. This asymmetry can produce surprising results for very wide actors (e.g., a wide monster may be unable to reach a target that is theoretically overlapping it).
3. **Vertical range** — Unless the **calling actor** has the `NOVERTICALMELEERANGE` flag (`MF5_NOVERTICALMELEERANGE`) set, the function requires the two actors' vertical spans to overlap. This check fails (so the jump fires) when the target's bottom is above the caller's top (`target z > z + height`) or the target's top is below the caller's bottom (`target z + height < z`). The target's own flags play no part here.
4. **Friendly fire** — If the target is considered a friend of the caller (the caller's `IsFriend(target)`), the function jumps.
5. **Line of sight** — The function performs a `P_CheckSight` test. If no line of sight exists between the caller and target, the function jumps.
6. **Special case: target is the move goal** — If the target is the same actor as the caller's `goal` field (the actor it is walking toward, not its `master`), it counts as in range and no jump occurs. This short-circuit comes after the distance check (so a distant goal still jumps) but before the vertical, friendly and sight checks.

The range used is the caller's `MeleeRange` actor property, which the base `Actor` class defaults to 44 map units on both engines (Zandronum's `wadsrc/static/actors/actor.txt:12`; UZDoom writes it as `64 - MELEEDELTA`). No stock Zandronum actor definition overrides it. Zandronum's engine constant `MELEERANGE` (64 map units, `src/p_local.h:85`) is a different value used by other melee code (e.g. `A_CustomPunch`'s default range), not by this check.

## Engine-family divergence: distance calculation

UZDoom's melee-range check (`Actor.CheckMeleeRange()`, declared in the ZScript stdlib's `actors/actor.zs` and backed natively by `P_CheckMeleeRange` in `src/playsim/p_enemy.cpp`) computes the caller-to-target distance with a true 2D Euclidean measurement (`Actor.Distance2D`, i.e. the length of the `(dx, dy)` vector), not Zandronum's octagonal approximation (`P_AproxDistance`, `max(|dx|,|dy|) + min(|dx|,|dy|)/2`). The Euclidean distance is always less than or equal to the octagonal approximation for the same `(dx, dy)` pair. They are equal only along the axes, and the approximation over-estimates by up to about 11.8% (worst near 26.6 degrees off an axis, about 6% at 45 degrees). So for the same numeric `meleerange`, a target near the boundary along an off-axis approach can be judged in range on UZDoom while Zandronum's approximation would judge it out of range and take the jump.

## Engine-family divergence: sector-based attack blocking

UZDoom's `P_CheckMeleeRange` adds a check with no Zandronum equivalent: if the calling actor's current sector has the `SECF_NOATTACK` flag set (`src/gamedata/r_defs.h`; a MAPINFO/UDMF sector flag meaning monsters cannot start attacks in that sector), the function returns false immediately, so the jump fires, regardless of the target's distance, vertical position, friendliness, or line of sight. This check runs immediately after the goal short-circuit (so it's skipped, same as the vertical/friendly/sight checks, when the target is also the actor's move-goal) but before the vertical-range check. Zandronum's `AActor::CheckMeleeRange` has no equivalent flag check at all, so a monster standing in a sector that would suppress its melee attack on UZDoom is unaffected on Zandronum.

## Wiki/engine divergence

The ZDoom wiki's description — "when the target of the calling actor is beyond melee range" — presupposes that the target exists. **In Zandronum, this function jumps when there is no target at all** (null target), before any distance or range checks. This is a divergence from the wiki's framing rather than a contradiction — the wiki's language focuses on the distance-based semantics, while the null-target case is an important practical consequence of how `CheckMeleeRange()` is implemented.

## Network synchronization

In multiplayer, the melee-range check is server-authoritative. In client mode the function returns without evaluating the condition unless the client handles the actor itself, meaning it has `+CLIENTSIDEONLY` or has no network ID (`NETWORK_InClientModeAndActorNotClientHandled`, `src/network.cpp:1598-1611`). The engine's own comment gives the reason: monsters have no targets on the client end.

When the server takes the jump, what clients receive depends on where it was called from (`DoJump`). From the actor's own state, the server sends a set-frame command plus a position update (the `CLIENTUPDATE_FRAME | CLIENTUPDATE_POSITION` flags). From a player's weapon or flash psprite, it sends a weapon state jump instead. From a CustomInventory state chain, nothing is sent.

For client-handled actors, the client runs the check locally against its own copy of the actor and nothing is synchronized.

## Engine-family divergence: no client/server authority split

UZDoom has no client/server authority split anywhere in its source tree — no `NETWORK_InClientMode`-style gate, no `SERVERCOMMANDS_*`-style broadcast, no `CLIENTUPDATE_*` flags. `A_JumpIfTargetOutsideMeleeRange`/`A_JumpIfTargetInsideMeleeRange` are declared directly as ZScript `action state` functions (`wadsrc/static/zscript/actors/checks.zs`) that call the natively-implemented `CheckMeleeRange()` unconditionally on whichever machine runs the state — there is no separate client-side code path, no server-authoritative decision, and no explicit position/frame synchronization step. The entire "Network synchronization" section above describes machinery that is specific to Zandronum and does not exist on UZDoom at all.

## See also

- `A_JumpIfTargetInsideMeleeRange` — the inverse condition; does not jump if the target is outside melee range.
- `A_JumpIfCloser` — similar conditional jump based on a custom distance threshold instead of actor melee range.
- `A_CheckSight` — checks only line-of-sight visibility, without distance or vertical range constraints.
