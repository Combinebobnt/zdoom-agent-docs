# Face pointer actions

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_FaceTarget` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_FaceTarget&oldid=54149) + verified against
the Zandronum source's `src/p_enemy.cpp:3107-3231`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Shared implementation — Zandronum: single static `A_Face()` helper (`src/p_enemy.cpp`) called by three action-function wrappers. UZDoom: non-static exported native `A_Face()` (declared `src/playsim/p_enemy.h:95`, defined `src/playsim/p_enemy.cpp:2999-3093`) called by three plain-ZScript wrapper functions in `wadsrc/static/zscript/actors/actor.zs`, dispatched through `src/scripting/vmthunks_actors.cpp`.
**Family rationale:** Shared implementation — three thin wrappers around one underlying engine function.

Adjusts an actor's angle and/or pitch to face a specified target. The three variants differ only in which actor pointer they follow:

- `A_FaceTarget` follows `self->target`
- `A_FaceTracer` follows `self->tracer`
- `A_FaceMaster` follows `self->master`

If the specified pointer is null, the function returns without modifying the actor.

The per-member signatures below (`## `) are Zandronum's two-parameter form. On UZDoom, all three members take four additional parameters — `ang_offset`, `pitch_offset`, `flags`, `z_ofs` — see "Engine-family divergence: extended six-parameter form" below for the full UZDoom signature.

## `void A_FaceTarget(double max_turn = 0, double max_pitch = 270)`

Changes the calling actor's angle to face their current target.

## `void A_FaceTracer(double max_turn = 0, double max_pitch = 270)`

Changes the calling actor's angle to face their current tracer (usually set by `A_Tracer2` or assignment).

## `void A_FaceMaster(double max_turn = 0, double max_pitch = 270)`

Changes the calling actor's angle to face their master (usually set by spawning as a summoned actor or explicit assignment).

## Parameters

### `max_turn`

Maximum angle turn in degrees. Controls how much the actor can rotate per call. A value of `0` means no limit — turn directly to face the target in a single call. For non-zero limits, the actor rotates towards the target angle but cannot exceed this per-call increment.

**Zandronum-specific note:** The `SHADOW` flag interaction described in some documentation (where `SHADOW` would disregard `max_turn`) does not manifest as coded in Zandronum; the maximum turn limit is always applied. The same holds on UZDoom — its jitter-application code is likewise gated on `max_turn == 0` (see the jitter mechanism described in "Engine-family divergence: invisible-target aim jitter" below).

Default: `0`.

### `max_pitch`

Maximum pitch angle adjustment in degrees. Controls how much the actor's up/down aim can change per call. A value of `0` means no limit — aim directly at the target in a single call. Any value greater than `180` disables pitch adjustment entirely (the default `270` has this effect).

When pitch adjustment is enabled (`<= 180`), the function aims at a point 32 units above the target's feet, falling back to the target's vertical center if that overshoots the target's head. There is no way to change this aim point in Zandronum — that customization exists only in the UZDoom/GZDoom-family engines.

**Engine-family divergence, minor:** UZDoom applies the same "overshoots the top" fallback to the *source* actor's own aim-origin height, not just the target's — if `self`'s computed source point (`self->Z() + 32 + bob offset`) is at or above `self->Top()`, UZDoom repositions it to `self->Center()` as well. Zandronum's `A_Face` only performs this correction for the target side; the source side always uses the raw `self->z + 32*FRACUNIT + bob offset` value uncorrected. This only matters for actors shorter than 32 map units.

Default: `270` (pitch adjustment disabled).

## Behavior

All three functions perform the following:

- **Server-authoritative in multiplayer — Zandronum only.** In networked play, the function performs angle/pitch calculations only on the server. Client-side actors early-return immediately (except for `+STEALTH` monsters, which set `visdir = 1` on both client and server). The angle is replicated to clients via `SERVERCOMMANDS_SetThingAngle()`. Pitch changes are **not replicated** — this is a server-only internal state in multiplayer. This client/server split does not exist on UZDoom at all — see "Engine-family divergence: multiplayer authority model" below.
- **Clears `MF_AMBUSH`** as a side effect, regardless of success or failure. This flag-clearing is not optional. Confirmed identical on UZDoom (`self->flags &= ~MF_AMBUSH;` in `A_Face`, unconditional on both engines).
- **SHADOW monster handling — Zandronum's simpler form.** For `self->target == self->tracer == some actor with MF_SHADOW`, if `max_turn == 0` (unlimited turn) *and* the actor doesn't have `MF6_SEEINVISIBLE`, a small random angle jitter is applied to the final angle. This prevents the actor from appearing to aim perfectly at an invisible target. UZDoom implements the same underlying idea through a substantially more elaborate mechanism — see "Engine-family divergence: invisible-target aim jitter" below.

## Engine-family divergence: extended six-parameter form

The ZDoom Wiki source (oldid=54149) describes an extended six-parameter form with angle offset, pitch offset, and a flags word controlling the aim point (`FAF_BOTTOM`, `FAF_MIDDLE`, `FAF_TOP`). This extended form does not exist in Zandronum 3.2.1 — Zandronum's functions accept only `max_turn` and `max_pitch`. The extended parameters exist in UZDoom/GZDoom-family engines, which allow customizing the aim point and applying additional angle/pitch offsets post-calculation.

Confirmed against UZDoom source: `wadsrc/static/zscript/actors/actor.zs` exposes `native void A_Face(Actor faceto, double max_turn = 0, double max_pitch = 270, double ang_offset = 0, double pitch_offset = 0, int flags = 0, double z_ofs = 0)`, and `A_FaceTarget`/`A_FaceTracer`/`A_FaceMaster` are themselves plain ZScript wrappers (not natives) in the same file, each forwarding all six parameters — `A_FaceTarget(double max_turn = 0, double max_pitch = 270, double ang_offset = 0, double pitch_offset = 0, int flags = 0, double z_ofs = 0)` calling `A_Face(target, max_turn, max_pitch, ang_offset, pitch_offset, flags, z_ofs)`, and correspondingly for `tracer`/`master`. The native `A_Face` C++ implementation (UZDoom source's `src/playsim/p_enemy.cpp:2999-3093`) defines the `FAF_Flags` enum (`FAF_BOTTOM = 1`, `FAF_MIDDLE = 2`, `FAF_TOP = 4`, `FAF_NODISTFACTOR = 8` — the last documented in-source as deprecated) and takes the offset/flags/`z_add` parameters exactly as the wiki describes: `ang_offset` is added to the computed yaw, `pitch_offset` is added to the computed pitch, `flags` overrides which point on the target (`FAF_BOTTOM`/`FAF_MIDDLE`/`FAF_TOP`) is aimed at instead of the default "32 units above feet, falling back to center" point, and `z_add` is added to the final target aim-point height after any `FAF_*` override.

## Engine-family divergence: multiplayer authority model

Zandronum's `A_Face` is client/server-split (see "Server-authoritative in multiplayer" above): a Zandronum client executing this action does no angle/pitch math at all except the `+STEALTH` `visdir` set, and the server-computed yaw is pushed to clients via `SERVERCOMMANDS_SetThingAngle()`.

UZDoom's `A_Face` (UZDoom source's `src/playsim/p_enemy.cpp:2999-3093`) has no such split — there is no `NETWORK_InClientMode()`-equivalent early-return, and no `SERVERCOMMANDS_*` call of any kind. UZDoom's multiplayer model does not distinguish an authoritative server simulation from a predicting client simulation the way Zandronum's does, so every peer runs the identical full angle/pitch calculation locally rather than one side computing and the other side receiving a network update. Any port pulling this function from a Zandronum-derived mod into a UZDoom-family target should drop the client/server branching entirely, not attempt to translate it into an equivalent UZDoom networking primitive — there isn't one for this function.

## Engine-family divergence: invisible-target aim jitter

Zandronum's angle jitter (described above) is a single inline check at the end of `A_Face`: `other->flags & MF_SHADOW && !(self->flags6 & MF6_SEEINVISIBLE)`, gated on `max_turn == 0` and the actor already being exactly angle-aligned, applying `pr_facetarget.Random2() << 21` to `self->angle`. It never touches pitch.

UZDoom replaces this with a general "shadow" subsystem (UZDoom source's `src/playsim/shadowinlines.h`), shared with several other aim-related functions (`P_SpawnMissileXYZ`, `A_MonsterRail`, `A_CustomRailgun`, etc.), not something private to `A_Face`:

- `AffectedByShadows(self)` gates the whole mechanism on `!(self->flags6 & MF6_SEEINVISIBLE) || self->flags9 & MF9_SHADOWAIM` — so, unlike Zandronum, a `MF9_SHADOWAIM`-flagged actor can be jittered even when it *does* have `MF6_SEEINVISIBLE`.
- `CheckForShadows`/`P_CheckForShadowBlock` extend "is the target a shadow" beyond `other->flags & MF_SHADOW` to also cover invisibility imposed by an intervening **shadow-blocking actor** hit by a trace between `self` and `other` (a UZDoom-only actor category with no Zandronum equivalent), each with its own `ShadowPenaltyFactor` scaling the jitter strength.
- The base jitter range is the same on both engines — Zandronum's `pr_facetarget.Random2() << 21` (a BAM shift, ±255 × 2²¹⁄2³² × 360° ≈ ±44.8°) and UZDoom's `pr_facetarget.Random2() * (45 / 256.)` degrees (±255 × 45/256 ≈ ±44.8°) resolve to the same span. The real divergence is that UZDoom then *scales* that raw value — `DAngle::fromDeg(pr_facetarget.Random2() * (45 / 256.)) * self->ShadowAimFactor * penaltyFactor` — by the per-actor `ShadowAimFactor` (default `1`, so a no-op unless a DECORATE/ZScript actor overrides it) and the resolved `penaltyFactor` from any shadow-blocking actor in the trace, neither of which Zandronum's fixed shift has any equivalent for. Applied to yaw in the `max_turn == 0` / angle-already-aligned case (`A_Face_ShadowHandling(..., vertical=false)`), same gating as Zandronum.
- UZDoom additionally jitters **pitch** when `self->flags9 & MF9_SHADOWAIMVERT` is set — `A_Face_ShadowHandling(..., vertical=true)`, gated on `max_turn == nullAngle` (reusing the turn-limit parameter as the gate for both axes) and the pitch already being aligned. Zandronum's `A_Face` has no pitch-jitter path at all.

Net effect: the "small random jitter so a monster doesn't aim perfectly at an invisible target" behavior exists on both engines and is directly comparable for the default case (`MF_SHADOW` target, no `MF6_SEEINVISIBLE`, `max_turn == 0`), but UZDoom's version is a tunable, extensible framework (per-actor jitter strength, shadow-blocking geometry, optional pitch jitter) rather than Zandronum's fixed single-purpose check. Worth keeping in mind for any future porting work that assumes the two are behaviorally identical beyond that base case.

## Examples

Monster turns to face its target before attacking:

```text
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

```text
SKUL C 10 A_FaceTarget(45);
```

Projectile homes on its target by repeatedly facing and moving toward it:

```text
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
