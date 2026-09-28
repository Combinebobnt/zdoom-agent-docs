# `A_SentinelBob`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_SentinelBob` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SentinelBob&oldid=34311) + verified against the Zandronum source's `src/g_strife/a_sentinel.cpp:12-52`; `threshold` setters and countdown at `src/p_interaction.cpp:1846,1871`, `src/p_enemy.cpp:2383,2477-2487`; client-mode test at `src/network.cpp:1552-1555`; stock Sentinel `See` state at `wadsrc/static/actors/strife/sentinel.txt:37-40`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_SentinelBob)` in `src/g_strife/a_sentinel.cpp` — callable on any actor class, not restricted to Sentinel despite the name.

Applies upward or downward vertical acceleration to smoothly bob an actor. This is an **accelerator**, not a position setter — `velz` is adjusted by ±1 unit/tic (`FRACUNIT` each call), so the function must be called repeatedly in a loop for continuous effect.

## Signature

```text
void A_SentinelBob()
```

## Behavior

When called, the action performs these steps:

1. **Network mode check**: In client mode (a network client, or client-side demo playback), returns immediately without effect. Otherwise (server or single player), continues to step 2.

2. **`MF_INFLOAT` early-out**: If the actor has the `MF_INFLOAT` flag set, zeroes `velz` and returns without executing steps 3-7. On a server it first sends `SERVERCOMMANDS_MoveThing(self, CM_VELZ)` to clients.

3. **Threshold gate**: If the actor's `threshold` field is nonzero, returns without change. `threshold` is the monster's target-lock countdown, not an attack-recovery timer. Among other engine setters, taking damage sets it to 100 (`BASETHRESHOLD`) when the victim keeps or switches to its attacker as target, Strife's `A_Look2` sets it to 10, and each `A_Chase` call counts it down by 1 (or zeroes it if the target is gone or dead). So a monster that was just hurt stops bobbing for a while.

4. **Target height**: Computes the height the actor bobs around:
   - `maxz = ceilingz - height - 16*FRACUNIT` (top of the actor 16 map units below the ceiling)
   - `minz = floorz + 96*FRACUNIT` (96 map units above the floor)
   - If `minz > maxz` (ceiling too low), `minz` is lowered to `maxz`. `maxz` is only this cap, not an upper bound on movement. In a low room the actor still oscillates, just around the lower target height.

5. **Vertical acceleration**: Adjusts `velz`:
   - If `z <= minz` (at or below the target height), increments `velz` by `FRACUNIT` (upward acceleration).
   - If `z > minz` (above the target height), decrements `velz` by `FRACUNIT` (downward acceleration).

6. **Reaction time side effect**: Sets `reactiontime = 4` if `minz >= self->z` (at or below the target height, the same condition as the upward branch), else `reactiontime = 0`. This clobbers any existing `reactiontime` — note this interaction if using `reactiontime` for other state timings.

7. **Server broadcast**: On a server only, sends `SERVERCOMMANDS_MoveThingExact(self, CM_VELZ)` to clients to replicate the velocity change (note this differs from step 2's `SERVERCOMMANDS_MoveThing`).

## Comparison to `FLOATBOB` flag

The wiki states this action is "not the same as using the FLOATBOB flag." Mechanically: `FLOATBOB` applies a fixed sine-wave `z` offset table indexed by game tic; `A_SentinelBob` integrates a velocity (`velz`), causing smooth acceleration around a target height derived from the floor and ceiling. The velocity approach means **momentum is preserved between calls** — if other forces apply vertical velocity, `A_SentinelBob` adds or subtracts from that accumulated velocity rather than overwriting it. The target height sits 96 units above the floor, capped so the actor's top stays 16 units below the ceiling, unlike the fixed `FLOATBOB` offset.

## Threshold interruption caveat

**`threshold`-driven interruption can leave bobbing incomplete.** DECORATE has no property or action that sets `threshold` directly. The engine sets it, most commonly to 100 when the monster takes damage and targets its attacker (step 3). While it is nonzero, every call to `A_SentinelBob` silently returns without integrating velocity, so any existing `velz` keeps carrying the actor. Bobbing resumes once `A_Chase` calls have counted `threshold` back to 0, or immediately if the target dies or is lost. Actors that bob and get hurt should account for this pause in vertical motion or use separate velocity-management logic.

## Network behavior (Zandronum multiplayer)

- **Server-side only**: Clients return immediately without effect (step 1).
- **Velocity replication**: The server sends the new `velz` to clients via `SERVERCOMMANDS_MoveThing` (the `MF_INFLOAT` branch) or `SERVERCOMMANDS_MoveThingExact` (the normal path). A call that returns at the `threshold` gate sends nothing. Clients never perform the bobbing calculation themselves.

## Engine-family divergence: no client/server broadcast

UZDoom's `A_SentinelBob` is now implemented in ZScript (`extend class Actor` in the UZDoom source's `wadsrc/static/zscript/actors/strife/sentinel.zs`, not a native `DEFINE_ACTION_FUNCTION`), and carries none of Zandronum's network-authority machinery: there is no client-mode early return (step 1), no replication call in the `MF_INFLOAT`/`bInFloat` branch (step 2), and no replication call at the end of the function (step 7) — nothing in the UZDoom source tree corresponds to `SERVERCOMMANDS_MoveThing`/`SERVERCOMMANDS_MoveThingExact`. The bob math itself carries over unchanged: the same `bInFloat` zero-out, the same `threshold != 0` gate, the same `ceilingz`/`floorz` envelope calculation (in double map units rather than Zandronum's `fixed_t`, with no behavioral difference), and the same `reactiontime` side effect. In short, UZDoom's version is Zandronum's steps 3–6 with no client/server split wrapped around them.

## Example (Zandronum DECORATE)

```text
ACTOR BobbingSentinel : Sentinel
{
    States
    {
    See:
        SEWR A 6 A_SentinelBob
        SEWR A 6 A_Chase
        Loop
    }
}
```

This subclass restates the stock Strife Sentinel's `See` state, so it bobs while chasing its target. Each call to `A_SentinelBob` adjusts vertical velocity; each call to `A_Chase` handles horizontal movement and target logic. The two frames alternate every 6 tics, so each action runs once per 12-tic loop. The `SEWR` sprites ship only with Strife.

## Related

- **`FLOATBOB` actor flag** — fixed sine-wave vertical offset; does not integrate velocity.
- **`MF_INFLOAT` flag** (DECORATE name `INFLOAT`): set by monster movement when a floating monster's step is blocked and it rises or sinks to fit the opening instead, cleared when a step succeeds. While it is set, `A_SentinelBob` zeroes `velz` and skips the bob calculation.
- **`A_SentinelAttack`, `A_SentinelRefire`** — companion actions for Strife's Sentinel actor (distinct from bobbing; not related to this action).
