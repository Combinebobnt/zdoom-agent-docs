# `A_SkullAttack(fixed speed)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki A_SkullAttack (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SkullAttack&oldid=47234) + verified against Zandronum source `src/g_doom/a_lostsoul.cpp:64-71` and impact behavior in `src/p_mobj.cpp:3748-3799`; charge setup and broadcasts `src/g_doom/a_lostsoul.cpp:22-62`, damage formula `src/p_mobj.cpp:3715-3733`, actor-collision hook `src/p_map.cpp:1028-1034`, wall stop `src/p_mobj.cpp:2143-2185`, floor/ceiling bounce `src/p_mobj.cpp:3189-3192` and `3239-3242`, damage-while-charging `src/p_interaction.cpp:1250-1258`, client-side-only spawn gating `src/thingdef/thingdef_codeptr.cpp:105-124` and `src/p_mobj.cpp:6195-6199`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SkullAttack)`, callable from any actor's state table.

Initiates a charging attack at the calling actor's current target, setting the `MF_SKULLFLY` flag and velocity vectors to move toward the target in a straight line. **On Zandronum the charge is computed server-side only.** Clients return immediately and receive the flag, position and velocity from the server instead. A `+CLIENTSIDEONLY` actor using this action never charges in a network game: the server never spawns such an actor, and on a client the action does nothing.

## Parameters

- **`speed`** — fixed-point velocity magnitude for the charge. Default (when `speed <= 0`): `SKULLSPEED` (20 map units per tic). The parameter is actually passed as a fixed-point value, not integer — the wiki's `int speed` is imprecise, and a caller can pass fractional values (e.g. `A_SkullAttack(20.5)`).

## Behavior

Requires a valid target (`self->target` must be non-NULL; returns silently if not). Sets `MF_SKULLFLY` and calculates velocity to move the charging actor toward the target:

- **Horizontal direction:** `angle` is set to face the target; velocity is derived as `(speed * cos(angle), speed * sin(angle))`. On Zandronum the facing goes through `A_FaceTarget`, so against a `+SHADOW` target (without `+SEEINVISIBLE` on the charger) the angle gets a random offset and the charge can head off-line.
- **Vertical direction:** velocity is the height difference to the target's vertical center (`z + height/2`) divided by the estimated horizontal time-to-impact (at least 1 tic), so the actor aims to arrive at the target's mid-height as it reaches the horizontal position. It is a timed climb or fall.
- **Velocity is set once:** the charge is a straight line with no re-steering toward a moving target.

The charging actor plays its `AttackSound` once at the start.

## Impact and aftermath

When the charging actor's movement is blocked by another actor while `MF_SKULLFLY` is set, the impact is handled by the charger's `Slam()` virtual method:

- **Clears `MF_SKULLFLY`** and sets all velocities to 0.
- **Deals melee damage** (damage type `Melee`) to the actor it collided with, which need not be its target. The amount comes from `GetMissileDamage(7, 1)`: a random 1 to 8 multiplied by the charger's `Damage` property, or the evaluated expression if `Damage` is an expression. It is rolled once per collision.
- **State transition (if the charger survives):** goes to its `SeeState` (normally the `See` state) if defined, or `Idle` otherwise. From `See`, the monster's chase logic can pick its Missile state again for another charge.
- **If dormant (`MF2_DORMANT`):** deals no damage and goes directly to `Idle` with `tics = -1`.

When the charging actor's horizontal movement stops (for example, blocked by a wall), `MF_SKULLFLY` is cleared on its next movement tic without damage, velocity is zeroed, and it transitions to `SeeState` or `Idle` the same way (or `Idle` with `tics = -1` if dormant). Hitting the floor or ceiling does not end the charge: it only reverses the vertical velocity, so the charger bounces and keeps flying.

**Damage taken while charging ends the charge.** When a charging actor is damaged, its velocity is zeroed while `MF_SKULLFLY` stays set, and the next movement tic treats the zero horizontal movement as a stop: the flag is cleared and the actor goes to `SeeState` or `Idle`. (This happens only for damage that gets past the invulnerability early-outs; `MF_SKULLFLY` also suppresses the pain state.) On UZDoom, an actor with `+NOAUTOOFFSKULLFLY` (a flag Zandronum lacks) skips this automatic stop, both here and after a wall block.

## Network synchronization

Server-side only: on a client (or during client demo playback) `NETWORK_InClientMode()` makes the action return immediately without effect. The check does not look at the actor, so a `+CLIENTSIDEONLY` actor, which exists only on clients in a network game, never charges.

What the server sends: at the start of the charge it broadcasts the actor's angle (from `A_FaceTarget`), the attack sound, the `MF_SKULLFLY` flag, and the exact position plus all three velocity components. Clients then move the charger along that velocity themselves. The stop is also server-driven: the wall-stop branch in the movement code and `Slam()` are skipped on clients, and the server sends the cleared flag, the zeroed velocity and the `See`/`Idle` state change (plus the tics for the dormant case). Velocity zeroing from damage is likewise server-only and broadcast.

## Engine-family divergence: client/server authority

UZDoom's `A_SkullAttack` and its `Slam()` impact handler carry no equivalent of Zandronum's `NETWORK_InClientMode()` early-return gate, and no `SERVERCOMMANDS_*` broadcast afterward. That whole client/server authority split does not exist anywhere in UZDoom's source tree. The charge (angle lock, velocity vectors, vertical-climb divisor) and the slam impact both run unconditionally wherever the actor's state machine executes, instead of being computed once on an authoritative server and replicated to clients. The doc's "server-side only" framing and the "Network synchronization" section above both describe Zandronum-specific behavior; on UZDoom there is no separate client path to desync from.

## Engine-family divergence: distance and velocity math

Zandronum derives the charge's horizontal velocity from fixed-point trig lookup tables (`finecosine`/`finesine`, indexed by the actor's `angle_t`), and derives the vertical-velocity divisor from `P_AproxDistance`, an octagonal approximation of 2D distance rather than a true Euclidean one. UZDoom's `A_SkullAttack` computes horizontal velocity via `VelFromAngle()` (floating-point `cos`/`sin`, also pitch-scaled), and derives the vertical-velocity divisor from `AActor::DistanceBySpeed()` (true floating-point 2D distance divided by speed, floored at 1). Both engines aim at the same target position, but the exact climb/fall rate and horizontal speed components can differ slightly between them. On Zandronum, `P_AproxDistance` is `max + min/2`: exact along the axes, never an under-estimate, and up to about 11.8% too long near 26.6 degrees off an axis, which makes the computed climb/fall slower than needed there.

## Engine-family divergence: post-slam state transition

The wall-hit case (no target actor involved, handled in the movement code that clears `MF_SKULLFLY` when the actor's horizontal move resolves to zero; floor and ceiling hits only reverse vertical velocity on both engines) transitions the same way on both engines: clear `MF_SKULLFLY`, zero velocity, then `SeeState` if defined else `Idle` (or straight to `Idle` with `tics = -1` if `MF2_DORMANT`).

The actor-to-actor collision case (`AActor::Slam`, still native C++ on both engines, not migrated to ZScript) differs. Zandronum's `Slam` always goes to `SeeState` if defined, else `Idle`, after a surviving non-lethal hit, with no other check. UZDoom's `Slam` first looks for a state labeled `Slam` on the actor and jumps there if one is found; only when no such label exists does it fall back to `SeeState`, and even then only if the actor's `RETARGETAFTERSLAM` flag (`flags8`, documented in UZDoom as "forces jumping to the idle state after slamming into something") is *not* set — otherwise it goes straight to `Idle`. `RETARGETAFTERSLAM` doesn't exist in Zandronum at all. UZDoom's own `LostSoul` class sets `+RETARGETAFTERSLAM` by default, so on UZDoom a Lost Soul that survives a non-lethal charge goes to `Idle` rather than back into its `See`/Missile loop. The return to `See` (and from there possibly another charge) described above in "Impact and aftermath" is accurate for Zandronum, but does not hold for UZDoom's stock Lost Soul.

## Examples

A charging monster built like Doom's Lost Soul (only the relevant states shown):

```text
ACTOR ChargingSkull
{
  Monster
  +FLOAT +NOGRAVITY
  Damage 3
  AttackSound "skull/melee"
  States
  {
  Spawn:
    SKUL AB 10 bright A_Look
    Loop
  See:
    SKUL AB 6 bright A_Chase
    Loop
  Missile:
    SKUL C 10 bright A_FaceTarget
    SKUL D 4 bright A_SkullAttack
    SKUL CD 4 bright
    goto Missile+2
  }
}
```

The `SKUL D` frame runs `A_SkullAttack` with the default speed of 20, setting the charge. The `SKUL CD 4 bright` frames loop until the charge ends (impact, wall stop or damage), which moves the actor to its `See` state. `A_Chase` there may later choose the Missile state again for another charge. The charge is a straight-line vector calculated from the initial `A_SkullAttack` call, ignoring any movement of the target during the charge.

## See also

- [`Slam()` virtual method](../concepts/actor-definition-syntax.md) — engine-side virtual called on actor-to-actor collision, not overridable from DECORATE; the default implementation deals damage and transitions state.
- [Creating monsters](../concepts/creating-monsters.md) — recommended states and properties for charge-capable monsters.
