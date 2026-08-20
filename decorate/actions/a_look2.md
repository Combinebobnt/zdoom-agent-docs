# `void A_Look2()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_Look2` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Look2&oldid=35060) + verified against Zandronum source `src/p_enemy.cpp:2351-2423`. Also present in UZDoom 4.15pre (`src/playsim/p_enemy.cpp:2306`) with identical target-acquisition logic but without the Zandronum network-specific divergence documented below.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/p_enemy.cpp:2351` (`DEFINE_ACTION_FUNCTION(AActor, A_Look2)`).

Sound-based target-acquisition action for monsters: wakes on detected sound from a shootable actor (`LastHeard`), ignoring visual contact. If no target is acquired, animates the actor through fixed state offsets (see below). Used in Strife and Strife-aligned actor definitions.

## Target acquisition

If `self->LastHeard` is non-null and its owning actor is shootable:

- **If the actor is an enemy** (aligned opposite to this actor, or `LEVEL_NOALLIES` flag set): sets `self->target` and jumps to `SeeState`. If the `+AMBUSH` flag is set, first checks line-of-sight with `SF_SEEPASTBLOCKEVERYTHING` (allowing sightlines through glass and closed doors); fails if sight fails.
- **If the actor is an ally** (same faction): calls `P_LookForPlayers(... MF4_LOOKALLAROUND ...)` to perform a **visual** search. This contradicts the wiki's claim that A_Look2 "only reacts to sound." The actual behavior is: `LastHeard` gates entry to the branch, but friendly targets fall through to a sight-based player lookup. If that succeeds, jumps to `SeeState`.

In either case, `threshold` is set to 10 on target acquisition. If `LastHeard` points to a dead actor, it's treated as `NULL`.

**Early-out:** If the `+INCONVERSATION` flag is set, the function returns immediately without any other behavior.

## State animation when no target found

When no target is acquired (the `nosee:` fallback):

- **Approximately 11.7% of calls** (RNG roll < 30/256): jumps to `SpawnState + 1` or `SpawnState + 2` with equal probability, controlled by `(pr_look2() & 1)`.
- **Independently, if the `+STANDSTILL` flag is not set, approximately 15.6% of calls** (RNG roll < 40/256): overrides to `SpawnState + 3`. If `+STANDSTILL` is set, this branch is skipped entirely, and the RNG is not consumed.

## Wiki/engine divergence: "three states after this function call"

**The wiki's language is ambiguous.** It says "the three states after this function call are reserved; the function jumps to the states following the call." The code actually uses hardcoded offsets from the actor's `SpawnState` — e.g. `SpawnState + 3` — not relative to the state that invoked A_Look2. This means:

1. If an actor's `Spawn:` state sequence has fewer than three states, `SpawnState + 3` lands in whatever states follow in the contiguous actor state table (typically the actor's `See:`, `Pain:`, or `Death:` state), producing undefined animation. This is a classic DECORATE footgun.
2. The wiki's own Peasant example (`Spawn: PEAS A 10 A_Look2 / Loop`) shows a non-idiomatic use case — the example doesn't visibly reserve three separate animation states, instead relying on `Loop` to control pacing. A proper use of A_Look2 requires three idle-animation state frames immediately following the call.

## Zandronum-specific: multiple calls to SetState and RNG frame desync

**When the animation `nosee:` path executes on a Zandronum server**, if the first condition (RNG < 30) fires:

- Line 2411 broadcasts `SERVERCOMMANDS_SetThingFrame(... SpawnState + (pr_look2() & 1) + 1)` with one RNG roll.
- Line 2413 calls `SetState(... SpawnState + (pr_look2() & 1) + 1)` with an **independent second RNG roll** ~50ms later on the same tic (in local server time).

The frame sent to clients and the frame the server actually sets are **independent RNG results** and disagree ~50% of the time this branch runs. This is a visual-only client/server desync; game state is unaffected.

**Further untraced:** both `SetState` calls (lines 2413 and 2354) run on the same tic, and ZDoom's `SetState` runs the new state's action by default — it's untraced whether this executes two state-action functions per tic (one per `SetState` call), or whether the second `SetState` overrides the first and only one runs.

## See also

- [A_Look](a_look.md) for the visual-line-of-sight variant.
- `A_TurretLook` (Strife-specific action) if you don't need idiomatic state animation — an alternative sound-detection action that doesn't require reserved animation states.
- `STANDSTILL` actor flag in [inventory/actor-flags.md](../inventory/actor-flags.md) for the flag check in the third-state branch.
