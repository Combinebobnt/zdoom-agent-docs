# `A_SkullAttack(fixed speed)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki A_SkullAttack (retrieved 2026-08-01, oldid=47234) + verified against Zandronum source `src/g_doom/a_lostsoul.cpp:64-71` and impact behavior in `src/p_mobj.cpp:3748-3799`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SkullAttack)`, callable from any actor's state table.

Initiates a charging attack at the calling actor's current target, setting the `MF_SKULLFLY` flag and velocity vectors to move toward the target in a straight line. **The charge is server-side only and will not execute on clients in multiplayer** — a `+CLIENTSIDEONLY` actor using this action will charge exclusively on the server, creating desyncs.

## Parameters

- **`speed`** — fixed-point velocity magnitude for the charge. Default (when `speed <= 0`): `SKULLSPEED` (20 map units per tic). The parameter is actually passed as a fixed-point value, not integer — the wiki's `int speed` is imprecise, and a caller can pass fractional values (e.g. `A_SkullAttack(20.5)`).

## Behavior

Requires a valid target (`self->target` must be non-NULL; returns silently if not). Sets `MF_SKULLFLY` and calculates velocity to move the charging actor toward the target:

- **Horizontal direction:** `angle` is set to face the target; velocity is derived as `(speed * cos(angle), speed * sin(angle))`.
- **Vertical direction:** velocity is the altitude difference divided by horizontal time-to-impact, so the actor arrives at the target's height at the same time it reaches the horizontal position — a timed climb or fall.
- **Velocity is set once:** the charge is a straight line with no re-steering toward a moving target.

The charging actor plays its `AttackSound` once at the start.

## Impact and aftermath

When the charging actor collides with another actor while `MF_SKULLFLY` is set, the impact is handled by the charger's `Slam()` virtual method:

- **Clears `MF_SKULLFLY`** and sets all velocities to 0.
- **Deals melee damage:** calculated via `GetMissileDamage(7, 1)` (a random 1–7 multiplied by the charger's `Damage` property) to the target, rolled once per collision.
- **State transition (if the charger survives):** goes to its `SeeState` (normally the `See` state) if defined, or `Idle` otherwise — this handles the Lost Soul's `goto Missile+2` loop, allowing re-entry to a Missile state for another charge.
- **State transition (if dormant):** goes directly to `Idle` with `tics = -1`.

When the charging actor hits a wall or ceiling (no horizontal/vertical movement occurs), `MF_SKULLFLY` is cleared without damage, and it transitions to `SeeState` or `Idle` the same way. **Damage taken while charging does not cancel the charge** — the flag remains set until impact or death.

## Network synchronization

Server-side only: `NETWORK_InClientMode()` returns immediately without effect. A lost soul charging from a `+CLIENTSIDEONLY` context creates a desync — the client performs no action while the server charges.

**Consequence:** because the whole charge — angle lock, velocity vectors, and the timed climb/fall — is computed once on the server with no client-side prediction, players commonly perceive charging actors as laggy or rubber-banding online, especially at higher latency: the charger appears to snap or warp toward its landing position as ordinary position-sync catches up, rather than visibly traveling the straight line the server calculated. This is more noticeable than for a walking monster because the whole trajectory is committed instantly at the start of the charge instead of being resolved incrementally tic-by-tic.

## Examples

Lost Soul's missile attack state (from Doom):

```
Missile:
  SKUL C 10 bright A_FaceTarget
  SKUL D 4 bright A_SkullAttack
  SKUL CD 4 bright
  goto Missile+2
```

The `SKUL D` frame runs `A_SkullAttack(20)` (default speed), setting the charge. The `SKUL CD 4 bright` frames loop until impact, which calls `Slam()` and transitions the actor to `SeeState` (another run to the Missile label). The charge is a straight-line vector calculated from the initial `A_SkullAttack()` call, ignoring any movement of the target during the charge.

## See also

- [`Slam()` virtual method](../concepts/actor-definition-syntax.md) — overrideable method called on actor-to-actor collision; the default implementation deals damage and transitions state.
- [Creating monsters](../concepts/creating-monsters.md) — recommended states and properties for charge-capable monsters.
