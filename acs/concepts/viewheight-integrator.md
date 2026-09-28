# The player eye-height integrator (`viewheight`, `deltaviewheight`, `viewz`)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/p_user.cpp:2820-2963` (`P_CalcHeight`) and
`:3321-3358` (`P_DeathThink`'s death-state ramp), `src/p_mobj.cpp:2895-2913` (smooth step-up and the
gravity-application gate), `:3047-3188` (the floor-hit branch and `PlayerLandedOnThing` call site),
`:3352-3413` (`PlayerLandedOnThing` itself), `:4403-4434` (the landing-on-another-actor variant),
`:5346-5376` (`AActor::AdjustFloorClip`), `src/d_player.h:833-836` (`player_t::GetDeltaViewHeight`),
`src/p_acs.cpp:5984-5997` (`ACSF_GetActorViewHeight`) and `:4878-4896`/`:4987-4994`/`:5057-5060`
(`SetActorProperty`/`GetActorProperty`/`CheckActorProperty`'s `APROP_ViewHeight` cases), and
`src/p_tick.cpp:369-411` (per-tic ordering of `P_PlayerThink` against `DThinker::RunThinkers`); no
wiki page covers this. UZDoom's presence is confirmed only by grep (`deltaviewheight` is a
ZScript-exposed `PlayerInfo` field in `src/playsim/p_user.cpp`, and the integrator itself has moved
to an overridable ZScript virtual, `PlayerPawn.CalcHeight()`, in
`wadsrc/static/zscript/actors/player/player.zs`) — its own algorithm was not read line-by-line for
this entry; see "Engine-family divergence" below before assuming any Zandronum-specific claim here
carries over.

Every tic, the engine recomputes a player actor's eye height from three cooperating pieces of
per-tic state, none of which is the DECORATE `Player.ViewHeight` property (that property is only
the *static default*, and it never changes at runtime — see "The name collision" below). The
render camera's actual height is:

```text
viewz = mo.z + viewheight + (cl_viewbob ? bob : 0)
```

`bob` is the ordinary movement/breathing sway term (unrelated to this file, computed earlier in the
same function from player velocity and `userinfo`'s move-bob/still-bob settings) and is gated
entirely by `cl_viewbob` — it never affects `viewheight` itself. `viewheight` is the live, per-tic
eye height this file is about: a `fixed_t` on `player_t` that recovers toward a target and gets
knocked below it by several distinct events, most prominently landing hard.

## The name collision

Four different things share almost the same name, and mixing them up is easy:

- `Player.ViewHeight` — the DECORATE actor property (`AActor::ViewHeight` in the class metadata,
  defaults to 41 map units for a standard player). Static. Set once from the actor's class
  definition (or by an explicit `SetActorProperty(tid, APROP_ViewHeight, n)` ACS call), never
  adjusted by movement, bobbing, crouching, or landing.
- `player->crouchviewdelta` — a separate live offset applied while crouching (maintained by the
  crouch state machine, not by the integrator below).
- **`defaultviewheight`** — a local computed each time `P_CalcHeight` runs:
  `player->mo->ViewHeight + player->crouchviewdelta`. This is the integrator's *recovery target*,
  not a stored field. It is exactly the value `GetActorViewHeight` (see
  [`../functions/getactorviewheight.md`](../functions/getactorviewheight.md)) returns — that
  function returns the target the integrator is chasing, never the live value below.
- **`player->viewheight`** — the live, per-tic integrator state this file documents. This is the
  value that actually feeds `viewz`. Confusingly, it is a `player_t` field with almost the same
  name as the DECORATE `Player.ViewHeight` class property above, and the two are read from
  completely different places.

None of `player->viewheight`, `player->deltaviewheight`, or `player->viewz` have an ACS getter —
confirmed by an exhaustive grep of `p_acs.cpp` (see "Not readable from ACS" below).

**Unrelated homonym:** `console/concepts/view-window-geometry.md` documents a completely different
`viewheight` — the renderer's global screen-pixel view-window height (`SCREENWIDTH`/`viewwidth`/
`viewwindowx` territory, driven by the `screenblocks` cvar). That one has nothing to do with player
eye height; don't conflate the two just because they share a field name.

## The recovery integrator

Gated on `player->playerstate == PST_LIVE` — it does not run at all while dead (see "Death" below).
Each tic, in this order:

1. **Accumulate:** `viewheight += deltaviewheight`.
2. **Clamp high:** if `viewheight` has recovered past `defaultviewheight`, snap it back down to
   exactly `defaultviewheight` and zero `deltaviewheight` — this is the only place `deltaviewheight`
   is set to a literal `0` by the integrator itself, and it means "fully recovered, stop."
3. **Clamp low:** if `viewheight` has dropped below `defaultviewheight >> 1` (half the target),
   floor it there. If `deltaviewheight` isn't already positive, re-arm it to `1` so recovery can
   begin even if nothing else seeded a delta this tic.
4. **Advance the recovery rate:** if `deltaviewheight` is nonzero, add a flat `FRACUNIT/4` to it
   (a constant per-tic acceleration, not a fixed step) — and if that addition would leave it at
   exactly `0`, re-arm it to `1` instead. This is why `deltaviewheight == 0` is only ever a
   legitimate "fully recovered" state (set on purpose in step 2); it never reads as "stuck" partway
   through recovery.

The order matters: the high/low clamps run *before* the rate advances, so a delta that would
overshoot on this tic gets clamped to the target in the same tic it arrives, not one tic later.

Nothing above is directly readable from ACS — a script can reconstruct the shape of this state
machine (see "Not readable from ACS" below) but cannot poll `viewheight`/`deltaviewheight`
themselves.

## What seeds `deltaviewheight`

Four distinct mechanisms write into `deltaviewheight` (or `viewheight` directly); all but the first
are worth knowing about even though this file doesn't trace them in the same depth.

### Landing squat (the main case)

`PlayerLandedOnThing` (`p_mobj.cpp:3352`), called from the actor's per-tic Z-movement handling
(`P_ZMovement`) when the actor's floor-hit branch is taken (`mo->z <= mo->floorz`, guarded by
`CLIENT_CanClipMovement`) and `mo->velz < minvel` (`minvel = -8*FRACUNIT`, strictly less than) with
`MF_NOGRAVITY` clear, sets:

```text
player->deltaviewheight = mo->velz >> 3
```

an arithmetic (sign-preserving) shift on a negative value, so a harder landing produces a larger
negative seed. `mo->velz` is zeroed in the *same* tic, immediately after this call.

**Gravity is not double-counted in the seed.** Z-movement for the tic runs `mo->z += mo->velz`
first, then a separate gate `if (mo->z > mo->floorz && !NOGRAVITY)` decides whether to subtract
gravity from `velz` for the *next* tic. On the tic where the actor's advanced `z` already lands at
or below `floorz` — which is exactly what routes execution into the floor-hit branch that snaps
`mo->z` to `mo->floorz` and calls `PlayerLandedOnThing` — that gate's `mo->z > mo->floorz` test is
already false, so gravity was never subtracted from `velz` this tic. The `velz` the seed reads is
the same impact velocity that was used to move the actor into the floor, with no extra
correction needed.

**One-tic lag between the seed and its visible effect.** Within one game tic, `P_PlayerThink`
(which calls `P_CalcHeight`, running the integrator above) executes for every player *before*
`DThinker::RunThinkers()` ticks the actor list (which is what runs `P_ZMovement`/
`PlayerLandedOnThing` for that tic) — confirmed at `p_tick.cpp:369-411`. So a landing detected
during tic `N`'s actor-thinking pass seeds `deltaviewheight` too late for that same tic's already-run
integrator call; the seed is consumed for the first time on tic `N+1`. The landing tic itself shows
no visible dip yet.

### Landing on another actor

A separate, structurally similar path (`p_mobj.cpp:4403-4434`) fires when a player's `z`-movement
resolves onto another actor's top (`P_CheckOnmobj`) rather than a floor plane. It uses a different
velocity gate (`velz < level.gravity * Sector->gravity * -655.36f`, not the flat `-8*FRACUNIT` used
for floor landings) and, if the actor being landed on is short enough to step up onto
(`onmo->z + onmo->height - z <= MaxStepHeight`), additionally applies a step-down term to
`viewheight` directly and takes the *larger* of the freshly computed
`player->GetDeltaViewHeight()` (`(ViewHeight + crouchviewdelta - viewheight) >> 3`, `d_player.h:833`)
against whatever `deltaviewheight` already held, rather than overwriting it outright.

### Smooth step-up

When a player's `z` is below `floorz` (walking up a stair or ledge shorter than a full step, rather
than landing from a fall), `p_mobj.cpp:2899-2903` directly decrements `viewheight` by the exact gap
(`floorz - z`) and reseeds `deltaviewheight` via the same `GetDeltaViewHeight()` helper above,
producing a smoothed climb rather than the floor-landing squat's sharper impact-velocity-scaled dip.

### Floor-clip changes

`AActor::AdjustFloorClip` (`p_mobj.cpp:5346-5376`, triggered by standing in shallow liquid whose
effective clip depth just changed) adjusts `viewheight` by the clip delta and reseeds
`deltaviewheight` through the same `GetDeltaViewHeight()` helper — a third, independent call site
for that one shared helper.

None of the three secondary mechanisms above are traced in the same depth as the landing-squat case;
treat them as "also real, also worth checking" rather than as fully documented here.

## Amplitude and recovery time

For a standard, non-crouching player (`defaultviewheight` = 41 map units, `ViewHeight`'s DECORATE
default), the low clamp floors `viewheight` at `defaultviewheight >> 1` ≈ 20.5 map units below
target — larger than ordinary view-bob's amplitude, but transient: recovery accelerates at a flat
`FRACUNIT/4` per tic, reaching full recovery within roughly a second at the engine's 35 tics/second.

## Death

The integrator above only runs while `player->playerstate == PST_LIVE` — it is skipped entirely on
death, per the gate at the top of `P_CalcHeight`. A dead player's `viewheight` instead ramps toward
a flat `6 * FRACUNIT` (6 map units) at a constant `FRACUNIT` per tic, driven by `P_DeathThink`
(`p_user.cpp:3321-3358`) rather than by `deltaviewheight` at all — a distinct state machine, not
another seed into the same one. A flying bloody-skull/ice-chunk death chunk snaps `viewheight`
straight to `6 * FRACUNIT` with no ramp. Either way, `6` map units is a far larger deviation from a
standard player's `defaultviewheight` (41) than any of the live-player mechanisms above produce.

## Not readable from ACS

Confirmed by an exhaustive grep of `p_acs.cpp`: `player->viewheight` (the live per-tic value, as
opposed to the static `Player.ViewHeight` property) appears exactly once, and it's a **write** path
(`SetActorProperty`'s `APROP_ViewHeight` case, `p_acs.cpp:4878-4896` — sets both the static
`ViewHeight` property and, for a player actor, the live `viewheight` field to the same new value,
which only moves what the integrator's clamps target next tic; not usable as a read-back).
`deltaviewheight` and `viewz` appear zero times in `p_acs.cpp`. `GetActorProperty`/
`CheckActorProperty`'s `APROP_ViewHeight` cases (`:4987-4994`, `:5057-5060`) return only the static
`actor->ViewHeight` class property — **not** even `crouchviewdelta`-adjusted, so this is a third,
even-more-static value than [`GetActorViewHeight`](../functions/getactorviewheight.md)'s
`ViewHeight + crouchviewdelta`. Neither read path ever surfaces the live integrator state, the
current `deltaviewheight`, or the actual rendered `viewz`.

A script that needs to detect or reconstruct this state machine itself has no direct read-back —
only the pieces to derive it from: `GetActorVelZ` (real ACS builtin, extension function index -11,
engine-side `p_acs.cpp:5934`) and `GetActorFloorZ` (compiler builtin, see
[`../functions/getactorfloorz.md`](../functions/getactorfloorz.md)) can reconstruct *when* a
landing-squat seed would fire (watch for `GetActorVelZ(tid) < 0` combined with
`GetActorZ(tid) == GetActorFloorZ(tid)` on consecutive tics), but nothing hands back the resulting
`deltaviewheight`/`viewheight` values themselves.

Also **not gated by `cl_viewbob`** — that cvar only silences the separate `bob` term in the `viewz`
formula at the top of this file, never the squat/step/clip integrator above.

## Engine-family divergence

UZDoom has moved this entire mechanism into ZScript: `PlayerPawn.CalcHeight()`
(`wadsrc/static/zscript/actors/player/player.zs`) is an overridable virtual method, not a hardcoded
engine function, and `deltaviewheight`/`viewheight` are ZScript-visible `PlayerInfo` fields
(`DEFINE_FIELD_X` entries in `src/playsim/p_user.cpp`). This means a UZDoom-side mod can override
the whole state machine per player class, something Zandronum's fixed C++ implementation has no
equivalent for. The UZDoom implementation was not read line-by-line for this entry (and, being
ZScript stdlib, cannot be quoted verbatim here even if it had been — see
`../../shared/AUTHORING.md`'s GPL-3.0 rule) — treat the mechanism shape (recovery integrator,
landing-squat seed, low/high clamps) as a reasonable prior for UZDoom given the shared ancestry, not
as independently verified UZDoom behavior. Re-check `CalcHeight()` directly before relying on any
specific clamp value, gate condition, or seed formula on UZDoom.
