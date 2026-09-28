# Face pointer actions

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `A_FaceTarget` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_FaceTarget&oldid=54149) + verified against
the Zandronum source's `src/p_enemy.cpp:3107-3231`; network replication per `src/sv_commands.cpp:99-112,1742-1751`, `protocolspec/spec.things.txt:176-179`, `protocolspec/spec.txt:49` and `src/sv_main.cpp:2877-2878`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Shared implementation — Zandronum: one file-local (non-`static`, no header declaration) `A_Face()` helper (`src/p_enemy.cpp:3107`), wrapped by three C++ helpers that the three `DEFINE_ACTION_FUNCTION_PARAMS(AActor, ...)` action functions call (`src/p_enemy.cpp:3233-3258`). UZDoom: non-static exported native `A_Face()` (declared `src/playsim/p_enemy.h:95`, defined `src/playsim/p_enemy.cpp:2999-3093`) called by three plain-ZScript wrapper functions in `wadsrc/static/zscript/actors/actor.zs`, dispatched through `src/scripting/vmthunks_actors.cpp`.
**Family rationale:** Shared implementation — three thin wrappers around one underlying engine function.

Adjusts an actor's angle and/or pitch to face a specified target. The three variants differ only in which actor pointer they follow:

- `A_FaceTarget` follows `self->target`
- `A_FaceTracer` follows `self->tracer`
- `A_FaceMaster` follows `self->master`

If the specified pointer is null, the function returns without modifying the actor.

The per-member signatures below (`## `) are Zandronum's two-parameter form. On UZDoom, all three members take four additional parameters — `ang_offset`, `pitch_offset`, `flags`, `z_ofs` — see "Engine-family divergence: extended six-parameter form" below for the full UZDoom signature.

## `void A_FaceTarget(float max_turn = 0, float max_pitch = 270)`

Changes the calling actor's angle to face their current target.

## `void A_FaceTracer(float max_turn = 0, float max_pitch = 270)`

Changes the calling actor's angle to face their current tracer (usually set by `A_Tracer2` or assignment).

## `void A_FaceMaster(float max_turn = 0, float max_pitch = 270)`

Changes the calling actor's angle to face their master (usually set by spawning as a summoned actor or explicit assignment).

## Parameters

### `max_turn`

Maximum angle turn in degrees. Controls how much the actor can rotate per call. A value of `0` means no limit — turn directly to face the target in a single call. For non-zero limits, the actor rotates towards the target angle but cannot exceed this per-call increment.

**Zandronum-specific note:** The `SHADOW` flag interaction described in some documentation (where `SHADOW` would disregard `max_turn`) does not manifest as coded in Zandronum; the maximum turn limit is always applied. The same holds on UZDoom — its jitter-application code is likewise gated on `max_turn == 0` (see the jitter mechanism described in "Engine-family divergence: invisible-target aim jitter" below).

Default: `0`.

### `max_pitch`

Maximum pitch angle adjustment in degrees. Controls how much the actor's up/down aim can change per call. A value of `0` means no limit — aim directly at the target in a single call. Any value greater than `180` disables pitch adjustment entirely (the default `270` has this effect).

When pitch adjustment is enabled (`<= 180`), the function aims at a point 32 units above the target's feet, falling back to the target's vertical center if that overshoots the target's head. There is no way to change this aim point in Zandronum — that customization exists only in the UZDoom/GZDoom-family engines.

**Engine-family divergence, minor:** UZDoom applies the same "overshoots the top" fallback to the *source* actor's own aim-origin height, not just the target's. If the caller's source point (its feet plus 32 plus its bob offset) is at or above its own top, UZDoom moves it to the caller's vertical center as well. Zandronum's `A_Face` only performs this correction for the target side; the source side always uses the raw `self->z + 32*FRACUNIT + bob offset` value uncorrected. This only matters for actors shorter than 32 map units.

Default: `270` (pitch adjustment disabled).

## Behavior

All three functions perform the following:

- **Server-authoritative in multiplayer, Zandronum only.** The gate is `NETWORK_InClientMode()`: when the running process is a client (or is playing back a client demo), `A_Face` returns immediately for every actor, after only setting `visdir = 1` on a `+STEALTH` caller. Offline and on the server the full calculation runs. On the server the resulting angle is then sent to clients with `SERVERCOMMANDS_SetThingAngle()`, which sends nothing for an actor without a net ID and carries only the top 16 bits of the angle, so a client's copy is slightly quantized. `A_Face` sends no pitch update at all, so clients keep whatever pitch they last received (a client joining mid-game gets each actor's current pitch in its full update). This client/server split does not exist on UZDoom at all. See "Engine-family divergence: multiplayer authority model" below.
- **Clears `MF_AMBUSH`** as a side effect whenever the followed pointer is non-null. A null pointer returns before the flag is touched, and on Zandronum a client never clears it (the client-mode return comes first). UZDoom clears it at the same point, also only after its null check.
- **SHADOW monster handling, Zandronum's simpler form.** When the followed actor has `MF_SHADOW`, `max_turn` is `0` (unlimited turn) and the caller lacks `MF6_SEEINVISIBLE`, a random angle jitter of up to about 44.8 degrees either way is added to the final angle. The code also requires the caller to be exactly angle-aligned, which is always true with `max_turn == 0` since that path has just set the angle. This keeps the actor from aiming perfectly at an invisible target. UZDoom implements the same underlying idea through a substantially more elaborate mechanism — see "Engine-family divergence: invisible-target aim jitter" below.

## Engine-family divergence: extended six-parameter form

The ZDoom Wiki source (oldid=54149) describes an extended six-parameter form with angle offset, pitch offset, and a flags word controlling the aim point (`FAF_BOTTOM`, `FAF_MIDDLE`, `FAF_TOP`). This extended form does not exist in Zandronum 3.2.1 — Zandronum's functions accept only `max_turn` and `max_pitch`. The extended parameters exist in UZDoom/GZDoom-family engines, which allow customizing the aim point and applying additional angle/pitch offsets post-calculation.

Confirmed against UZDoom source: `wadsrc/static/zscript/actors/actor.zs` declares a native `A_Face` that takes the actor to face followed by six parameters: `max_turn` (default 0), `max_pitch` (default 270), `ang_offset`, `pitch_offset`, `flags` and `z_ofs` (all default 0). `A_FaceTarget`/`A_FaceTracer`/`A_FaceMaster` are themselves plain ZScript wrappers (not natives) in the same file. Each takes those same six parameters with the same defaults and forwards them unchanged to `A_Face` along with `target`, `tracer` or `master` respectively. The native `A_Face` C++ implementation (UZDoom source's `src/playsim/p_enemy.cpp:2999-3093`) defines the `FAF_Flags` enum (`FAF_BOTTOM = 1`, `FAF_MIDDLE = 2`, `FAF_TOP = 4`, `FAF_NODISTFACTOR = 8` — the last documented in-source as deprecated) and takes the offset/flags/`z_add` parameters exactly as the wiki describes: `ang_offset` is added to the computed yaw, `pitch_offset` is added to the computed pitch, `flags` overrides which point on the target (`FAF_BOTTOM`/`FAF_MIDDLE`/`FAF_TOP`) is aimed at instead of the default "32 units above feet, falling back to center" point, and `z_add` is added to the final target aim-point height after any `FAF_*` override.

## Engine-family divergence: multiplayer authority model

Zandronum's `A_Face` is client/server-split (see "Server-authoritative in multiplayer" above): a Zandronum client executing this action does no angle/pitch math at all except the `+STEALTH` `visdir` set, and the server-computed yaw is pushed to clients via `SERVERCOMMANDS_SetThingAngle()`.

UZDoom's `A_Face` (UZDoom source's `src/playsim/p_enemy.cpp:2999-3093`) has no such split — there is no `NETWORK_InClientMode()`-equivalent early-return, and no `SERVERCOMMANDS_*` call of any kind. UZDoom's multiplayer model does not distinguish an authoritative server simulation from a predicting client simulation the way Zandronum's does, so every peer runs the identical full angle/pitch calculation locally rather than one side computing and the other side receiving a network update. Any port pulling this function from a Zandronum-derived mod into a UZDoom-family target should drop the client/server branching entirely, not attempt to translate it into an equivalent UZDoom networking primitive — there isn't one for this function.

## Engine-family divergence: invisible-target aim jitter

Zandronum's angle jitter (described above) is a single inline check at the end of `A_Face`: `other->flags & MF_SHADOW && !(self->flags6 & MF6_SEEINVISIBLE)`, gated on `max_turn == 0` and the actor already being exactly angle-aligned, applying `pr_facetarget.Random2() << 21` to `self->angle`. It never touches pitch.

UZDoom replaces this with a general "shadow" subsystem (UZDoom source's `src/playsim/shadowinlines.h`), shared with several other aim-related functions (`P_SpawnMissileXYZ`, `A_MonsterRail`, `A_CustomRailgun`, etc.), not something private to `A_Face`:

- `AffectedByShadows(self)` gates the whole mechanism: it passes when the caller lacks `MF6_SEEINVISIBLE` or has `MF9_SHADOWAIM`. So, unlike Zandronum, a `MF9_SHADOWAIM`-flagged actor can be jittered even when it *does* have `MF6_SEEINVISIBLE`.
- `CheckForShadows`/`P_CheckForShadowBlock` extend "is the target a shadow" beyond `other->flags & MF_SHADOW` to also cover invisibility imposed by an intervening **shadow-blocking actor** hit by a trace between `self` and `other` (a UZDoom-only actor category with no Zandronum equivalent), each with its own `ShadowPenaltyFactor` scaling the jitter strength.
- The base jitter range is the same on both engines. Zandronum's `pr_facetarget.Random2() << 21` (a BAM shift, ±255 × 2²¹⁄2³² × 360° ≈ ±44.8°) and UZDoom's conversion of the same `Random2()` roll to degrees at 45/256 of a degree per step (±255 × 45/256 ≈ ±44.8°) resolve to the same span. The real divergence is that UZDoom then *scales* that raw value by the per-actor `ShadowAimFactor` (default `1`, so a no-op unless a DECORATE/ZScript actor overrides it) and by the resolved penalty factor from any shadow-blocking actor in the trace. Zandronum's fixed shift has no equivalent for either. It is applied to yaw by `A_Face_ShadowHandling`'s horizontal path in the `max_turn == 0` / angle-already-aligned case, the same gating as Zandronum.
- UZDoom additionally jitters **pitch** when the caller has `MF9_SHADOWAIMVERT`, through `A_Face_ShadowHandling`'s vertical path. For that call `A_Face` passes its `max_pitch` (as left after the pitch-limiting step), so the pitch jitter is gated on `max_pitch` being `0` and the pitch already being aligned, not on `max_turn`. Zandronum's `A_Face` has no pitch-jitter path at all.

Net effect: the "small random jitter so a monster doesn't aim perfectly at an invisible target" behavior exists on both engines and is directly comparable for the default case (`MF_SHADOW` target, no `MF6_SEEINVISIBLE`, `max_turn == 0`), but UZDoom's version is a tunable, extensible framework (per-actor jitter strength, shadow-blocking geometry, optional pitch jitter) rather than Zandronum's fixed single-purpose check. Worth keeping in mind for any future porting work that assumes the two are behaviorally identical beyond that base case.

## Examples

Monster turns to face its target before attacking (this repeats the stock `DoomImp` `Missile` sequence in a subclass):

```decorate
actor FacingImp : DoomImp
{
  States
  {
  Missile:
    TROO EF 8 A_FaceTarget
    TROO G 6 A_TroopAttack
    Goto See
  }
}
```

Slowly turning monster: at most 15 degrees per `A_FaceTarget` call (per call, not per tic), then a shot straight ahead. `A_CustomMissile` with `CMF_AIMDIRECTION` fires along the actor's current angle, whereas `A_TroopAttack` would snap to face the target itself:

```decorate
actor SlowTurnImp : DoomImp
{
  States
  {
  Missile:
    TROO E 4 A_FaceTarget(15)
    TROO F 4 A_FaceTarget(15)
    TROO G 6 A_CustomMissile("DoomImpBall", 32, 0, 0, CMF_AIMDIRECTION)
    Goto See
  }
}
```

Lost Soul variant that re-aims and re-launches every cycle instead of flying straight until it hits something:

```decorate
actor HomingSkull : LostSoul
{
  States
  {
  Missile:
    SKUL C 10 Bright A_FaceTarget
    SKUL D 4 Bright A_SkullAttack
    SKUL CD 4 Bright
    Goto Missile
  }
}
```
