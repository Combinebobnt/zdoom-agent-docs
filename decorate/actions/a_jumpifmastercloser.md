# `A_JumpIfMasterCloser (float distance, state label)` / `A_JumpIfMasterCloser (float distance, int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_JumpIfMasterCloser` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfMasterCloser&oldid=44215) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:903-906` and `src/thingdef/thingdef_codeptr.cpp:856-873` (`DoJumpIfCloser` helper).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** AActor — callable from any actor's state table. Shared implementation via the `DoJumpIfCloser()` helper, which also backs `A_JumpIfCloser` and `A_JumpIfTracerCloser`.

Jumps to a target state (or forward by an offset) if the calling actor's master is closer than a specified distance.

## Parameters

- **`distance`** (float, fixed-point units) — Threshold distance for the jump. The distance calculation uses octagonal approximation (via `P_AproxDistance`, not true Euclidean), so the actual "radius" of the test varies slightly with angle. Units match the actor radius convention (where Doom map units are `FRACUNIT` units internally).
- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. Two overloads: pass a string (quoted in DECORATE) to jump to a named state, or an integer offset to jump forward by that many frame states from the current one.

## Wiki/engine divergence

The source ZDoom wiki describes an optional third parameter, `noz` (boolean), to disable vertical distance checking. **This parameter does not exist in Zandronum 3.2.1** — attempting to pass it causes a parse error. Vertical distance is always checked in Zandronum's implementation.

## Engine-family divergence: `noz` parameter exists on UZDoom

Unlike Zandronum, **UZDoom does implement the wiki's `noz` parameter.** The UZDoom source's `wadsrc/static/zscript/actors/checks.zs` declares `action state A_JumpIfMasterCloser(double distance, statelabel label, bool noz = false)`, backed by a shared `CheckIfCloser(Actor targ, double dist, bool noz = false)` helper also used by `A_JumpIfCloser` and `A_JumpIfTracerCloser`. When `noz` is `true`, the vertical-gap check described below is skipped entirely and only the horizontal distance test applies. The wiki's third-parameter claim — which the "Wiki/engine divergence" section above rejects for Zandronum — is accurate for UZDoom; this is the feature-ahead-engine case where the ZDoom Wiki describes GZDoom-family lineage behavior that UZDoom inherited but Zandronum's older DECORATE-only codebase never received.

## Engine-family divergence: distance calculation uses true Euclidean distance, not octagonal approximation

UZDoom's `CheckIfCloser` tests horizontal distance via `Distance2D(targ) < dist`, where `Distance2D` (`src/playsim/actor.h`) computes `(Pos().XY() - otherpos.XY()).Length()` — a true Euclidean 2D distance (square root of the sum of squared axis deltas). This differs from Zandronum's `P_AproxDistance`-based octagonal approximation described in the Parameters section above: on UZDoom the threshold distance is the actual radius of a circular test region, with no angle-dependent variation. A distance value tuned against Zandronum's approximation (which over-estimates distance along diagonals) may produce a slightly different effective jump radius on UZDoom.

## Behavior notes

- **NULL master — no jump.** If the calling actor has no master, the condition is never true and the jump does not occur. There is no way to distinguish "master is far away" from "no master set" using only this function; combining with inventory checks or ACS lookups is necessary for master-presence detection.

- **Distance calculation does not account for actor radius.** Both the calling actor and its master are treated as points. If either or both actors are very wide (large radius), it's possible the jump condition can never be met. Workaround: increase the distance threshold to account for radii, e.g. `A_JumpIfMasterCloser(radius + desired_dist, "label")`.

- **Vertical distance is always checked, independent of horizontal distance.** The implementation compares the vertical gap between the actors' Z extents: if the calling actor is above the master, it measures the gap from the caller's Z to the top of the master's bounding box; if at or below, it measures from the top of the caller's bounding box to the master's Z. The applicable gap (one or the other) must be less than the specified distance threshold for the jump to occur. This means the test is strictly more permissive than a true spherical radius check (overlapping actors always pass the vertical component).

- **Network synchronization: client-side execution with no server gate.** Unlike `A_JumpIfCloser`, this function has **no early-return guard** preventing execution in client mode. Clients evaluate the jump condition locally using their own `self->master` pointer, which Zandronum does not reliably replicate across the network. This creates a server/client behavioral divergence: if the calling actor's master is known to the server but not to a client, the server and client may reach different jump decisions in the same tic. Effects of a server-side jump (e.g., state changes, subsequent action side effects) are broadcast to clients, but the divergence itself may cause out-of-sync windows on non-CLIENTSIDEONLY actors (where the client's local evaluation is not the intended behavior).

- **Client update on jump.** When the jump occurs, `ACTION_JUMP(..., CLIENTUPDATE_FRAME|CLIENTUPDATE_POSITION)` sends a frame and position update to keep clients synchronized.

## Engine-family divergence: no client/server authority split

The two "Network synchronization" and "Client update on jump" bullets above are Zandronum-specific. UZDoom's `CheckIfCloser`/`A_JumpIfMasterCloser` (`wadsrc/static/zscript/actors/checks.zs`) contain no network-role branch at all — no check for whether the calling actor belongs to the local client, and no equivalent of `CLIENTUPDATE_FRAME`/`CLIENTUPDATE_POSITION` (those constants, and `ACTION_JUMP`, do not exist anywhere in the UZDoom source tree). This matches the cohort-wide pattern: UZDoom has no `NETWORK_InClientMode`/`SERVERCOMMANDS_*` equivalents anywhere, confirmed by grep for this file. On UZDoom, every peer evaluates the master-distance check and resolves the jump identically and unconditionally — the server/client behavioral divergence described above for Zandronum does not exist as a concept on UZDoom.

## See also

- `A_JumpIfCloser` — same logic applied to the actor's `target` field; includes an early-return client-mode gate avoiding the network-sync caveat here.
- `A_JumpIfTracerCloser` — same logic applied to the actor's `tracer` field; also lacks a client-mode gate, same network-sync divergence as this function.
- [`network-jump-synchronization.md`](../concepts/network-jump-synchronization.md) — general reference on jump-function network behavior and patterns for avoiding desync.

## Example

```text
actor Minion : Actor
{
    Default
    {
        Health 20;
        Radius 12;
        Height 32;
    }

    States
    {
    Spawn:
        MINION A 10 A_Look;
        Loop;
    See:
        // If close to master, participate in melee
        MINION A 0 A_JumpIfMasterCloser(150, "Help");
        // Otherwise, wander independently
        MINION ABCD 4 A_Chase;
        Loop;
    Help:
        MINION E 5 A_CustomMeleeAttack(3);
        Goto See;
    Death:
        MINION F 5;
        MINION G -1;
        Stop;
    }
}
```
