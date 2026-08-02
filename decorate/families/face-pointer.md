# Face pointer actions

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_FaceTarget` (retrieved 2026-07-31, oldid=54149) + verified against
the Zandronum source's `src/p_enemy.cpp:3107-3231`.
**Bucket:** Shared implementation (single static `A_Face()` helper called by three action wrappers).
**Family rationale:** Shared implementation — three thin wrappers around one underlying engine function.

Adjusts an actor's angle and/or pitch to face a specified target. The three variants differ only in which actor pointer they follow:

- `A_FaceTarget` follows `self->target`
- `A_FaceTracer` follows `self->tracer`
- `A_FaceMaster` follows `self->master`

If the specified pointer is null, the function returns without modifying the actor.

## `void A_FaceTarget(double max_turn = 0, double max_pitch = 270)`

Changes the calling actor's angle to face their current target.

## `void A_FaceTracer(double max_turn = 0, double max_pitch = 270)`

Changes the calling actor's angle to face their current tracer (usually set by `A_Tracer2` or assignment).

## `void A_FaceMaster(double max_turn = 0, double max_pitch = 270)`

Changes the calling actor's angle to face their master (usually set by spawning as a summoned actor or explicit assignment).

## Parameters

### `max_turn`

Maximum angle turn in degrees. Controls how much the actor can rotate per call. A value of `0` means no limit — turn directly to face the target in a single call. For non-zero limits, the actor rotates towards the target angle but cannot exceed this per-call increment.

**Zandronum-specific note:** The `SHADOW` flag interaction described in some documentation (where `SHADOW` would disregard `max_turn`) does not manifest as coded in this fork; the maximum turn limit is always applied.

Default: `0`.

### `max_pitch`

Maximum pitch angle adjustment in degrees. Controls how much the actor's up/down aim can change per call. A value of `0` means no limit — aim directly at the target in a single call. Any value greater than `180` disables pitch adjustment entirely (the default `270` has this effect).

When pitch adjustment is enabled (`<= 180`), the function aims at a point 32 units above the target's feet, falling back to the target's vertical center if that overshoots the target's head. There is no way to change this aim point in Zandronum — that customization exists only in the UZDoom/GZDoom-family engines.

Default: `270` (pitch adjustment disabled).

## Behavior

All three functions perform the following:

- **Server-authoritative in multiplayer.** In networked play, the function performs angle/pitch calculations only on the server. Client-side actors early-return immediately (except for `+STEALTH` monsters, which set `visdir = 1` on both client and server). The angle is replicated to clients via `SERVERCOMMANDS_SetThingAngle()`. Pitch changes are **not replicated** — this is a server-only internal state in multiplayer.
- **Clears `MF_AMBUSH`** as a side effect, regardless of success or failure. This flag-clearing is not optional.
- **SHADOW monster handling:** For `self->target == self->tracer == some actor with MF_SHADOW`, if `max_turn == 0` (unlimited turn) *and* the actor doesn't have `MF6_SEEINVISIBLE`, a small random angle jitter is applied to the final angle. This prevents the actor from appearing to aim perfectly at an invisible target.

## ZDoom/UZDoom/GZDoom family divergence

The ZDoom Wiki source (oldid=54149) describes an extended six-parameter form with angle offset, pitch offset, and a flags word controlling the aim point (`FAF_BOTTOM`, `FAF_MIDDLE`, `FAF_TOP`). This extended form does not exist in Zandronum 3.2.1 — Zandronum's functions accept only `max_turn` and `max_pitch`. The extended parameters exist in UZDoom/GZDoom-family engines, which allow customizing the aim point and applying additional angle/pitch offsets post-calculation.

## Examples

Monster turns to face its target before attacking:

```
actor DoomImp : Actor
{
  States
  {
  Attack:
    TROO E 8 A_FaceTarget;
    TROO G 6 A_TroopAttack;
    Goto See;
  }
}
```

Slowly turning monster (max 45-degree turn per tic):

```
SKUL C 10 A_FaceTarget(45);
```

Projectile homes on its target by repeatedly facing and moving toward it:

```
actor HomingSkull : LostSoul
{
  States
  {
  Missile:
    SKUL C 10 Bright A_FaceTarget;
    SKUL D 4 Bright A_SkullAttack;
    SKUL CD 4 Bright;
    Goto Missile;
  }
}
```
