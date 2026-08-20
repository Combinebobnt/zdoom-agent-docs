# `A_SentinelBob`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_SentinelBob` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SentinelBob&oldid=34311) + verified against the Zandronum source's `src/g_strife/a_sentinel.cpp:12-52`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_SentinelBob)` in `src/g_strife/a_sentinel.cpp` — callable on any actor class, not restricted to Sentinel despite the name.

Applies upward or downward vertical acceleration to smoothly bob an actor. This is an **accelerator**, not a position setter — `velz` is adjusted by ±1 unit/tic (`FRACUNIT` each call), so the function must be called repeatedly in a loop for continuous effect.

## Signature

```text
void A_SentinelBob()
```

## Behavior

When called, the action performs these steps:

1. **Network mode check**: In client mode, returns immediately without effect. On the server, continues to step 2.

2. **`MF_INFLOAT` early-out**: If the actor has the `MF_INFLOAT` flag set, zeroes `velz`, does not execute steps 3–6 below, and broadcasts `SERVERCOMMANDS_MoveThing(self, CM_VELZ)` to clients.

3. **Threshold gate**: If the actor's `threshold` field is nonzero (indicating an active post-attack window or other countdown), returns without change. This means monsters in their attack recovery period stop bobbing.

4. **Bob envelope calculation**: Computes vertical bounds:
   - `maxz = ceilingz - height - 16*FRACUNIT` (16 map units below ceiling)
   - `minz = floorz + 96*FRACUNIT` (96 map units above floor)
   - If `minz > maxz` (ceiling too low), clamps `minz = maxz` — the actor sits pinned and unable to bob in low-ceilinged rooms.

5. **Vertical acceleration**: Adjusts `velz`:
   - If `z < minz` (below the target range), increments `velz` by `FRACUNIT` (upward acceleration).
   - If `z >= minz` (at or above the target range), decrements `velz` by `FRACUNIT` (downward acceleration).

6. **Reaction time side effect**: Sets `reactiontime = 4` if `minz >= self->z` (within bob range), else `reactiontime = 0`. This clobbers any existing `reactiontime` — note this interaction if using `reactiontime` for other state timings.

7. **Server broadcast**: Broadcasts `SERVERCOMMANDS_MoveThingExact(self, CM_VELZ)` to clients to replicate the velocity change (note this differs from step 2's `SERVERCOMMANDS_MoveThing`).

## Comparison to `FLOATBOB` flag

The wiki states this action is "not the same as using the FLOATBOB flag." Mechanically: `FLOATBOB` applies a fixed sine-wave `z` offset table indexed by game tic; `A_SentinelBob` integrates a velocity (`velz`), causing smooth acceleration bounded by floor/ceiling constraints. The velocity approach means **momentum is preserved between calls** — if other forces apply vertical velocity, `A_SentinelBob` adds or subtracts from that accumulated velocity rather than overwriting it. The position envelope also respects the actor's height and has a 96-unit floor clearance, unlike the fixed `FLOATBOB` offset.

## Threshold interruption caveat

**`threshold`-driven interruption can leave bobbing incomplete.** If an actor's state chain sets `threshold` during bobbing (e.g., a monster that enters an attack recovery), the next call to `A_SentinelBob` silently returns without integrating velocity. On recovery (when `threshold` counts back to 0), bobbing resumes. Actors that bob and attack should account for this pause in vertical motion or use separate velocity-management logic.

## Network behavior (Zandronum multiplayer)

- **Server-side only**: Clients return immediately without effect (step 1).
- **Velocity replication**: The server broadcasts velocity changes to clients via `SERVERCOMMANDS_MoveThing` or `SERVERCOMMANDS_MoveThingExact` on each call (though clients do not perform the bobbing calculation themselves).

## Engine-family divergence: no client/server broadcast

UZDoom's `A_SentinelBob` is now implemented in ZScript (`extend class Actor` in the UZDoom source's `wadsrc/static/zscript/actors/strife/sentinel.zs`, not a native `DEFINE_ACTION_FUNCTION`), and carries none of Zandronum's network-authority machinery: there is no client-mode early return (step 1), no replication call in the `MF_INFLOAT`/`bInFloat` branch (step 2), and no replication call at the end of the function (step 7) — nothing in the UZDoom source tree corresponds to `SERVERCOMMANDS_MoveThing`/`SERVERCOMMANDS_MoveThingExact`. The bob math itself carries over unchanged: the same `bInFloat` zero-out, the same `threshold != 0` gate, the same `ceilingz`/`floorz` envelope calculation (in double map units rather than Zandronum's `fixed_t`, with no behavioral difference), and the same `reactiontime` side effect. In short, UZDoom's version is Zandronum's steps 3–6 with no client/server split wrapped around them.

## Example (Zandronum DECORATE)

```text
ACTOR Sentinel 3006
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

In this Strife-native example, the Sentinel bobs while chasing its target. Each call to `A_SentinelBob` adjusts vertical velocity; each call to `A_Chase` handles horizontal movement and target logic. Both actions are called once per 6 tics (every two animation frames).

## Related

- **`FLOATBOB` actor flag** — fixed sine-wave vertical offset; does not integrate velocity.
- **`MF_INFLOAT` flag** — special actor state that zero-outs `velz` and bypasses the bob calculation.
- **`A_SentinelAttack`, `A_SentinelRefire`** — companion actions for Strife's Sentinel actor (distinct from bobbing; not related to this action).
