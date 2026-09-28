# `fixed GetActorViewHeight(int tid)`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** written from the Zandronum source's `src/p_acs.cpp:5984-5997` (`ACSF_GetActorViewHeight`
dispatch) and `src/p_user.cpp:2820-2963` (`P_CalcHeight`, showing what this function's return value
actually is relative to the live per-tic state it does *not* expose); no wiki page covers this.
**Bucket:** extension function (index -14; dispatched as `ACSF_GetActorViewHeight`).

Returns an actor's *static, target* eye-height — not the live, per-tic camera height the engine
actually renders from. For a player actor, this is `player->mo->ViewHeight + player->crouchviewdelta`
(the DECORATE `Player.ViewHeight` class property, defaulting to 41 map units, plus the live crouch
offset). For a non-player actor, it instead returns that class's `AMETA_CameraHeight` metadata
(falling back to `actor->height / 2` if the class never set one) — a completely different property
from the player branch, sharing only the function name. Returns `0` if `tid` resolves to no actor.

## Parameters

- `tid` — actor to query. `SingleActorFromTID` semantics: `tid = 0` reads the activator; nonzero
  `tid` resolves to the first matching actor if several share it. Returns `0` if the activator is
  NULL (e.g. an `OPEN` script with `tid = 0`) or no actor matches a nonzero `tid` — indistinguishable
  from a genuine `0` return, though `0` never occurs for a real player or a class with a positive
  camera-height metadata/half-height.

## What this does and doesn't include

This function **does** fold in the live crouch offset (`crouchviewdelta`) for a player actor — a
crouched player's `GetActorViewHeight` reading drops accordingly. It does **not** reflect:

- **Camera bob.** The `bob` term added into the engine's actual render height (`viewz`) is entirely
  separate and never factored in here.
- **The landing squat, or any other live deviation of the per-tic `viewheight` integrator.** A
  player who just landed hard, is mid-recovery from a landing, is stepping up a ledge, or has an
  active floor-clip adjustment has a live `viewheight` measurably different from what this function
  returns — this function always reports the integrator's *recovery target*, never its current
  value. See [`../concepts/viewheight-integrator.md`](../concepts/viewheight-integrator.md) for the
  full state machine (`P_CalcHeight`, `deltaviewheight`, the landing-squat seed, and why none of it
  has any other ACS read path either).

In short: this is the number `player->viewheight` is *converging toward* on any given tic, not the
number actually feeding the render camera.

## No read path exists for the live value

Confirmed by an exhaustive grep of `p_acs.cpp`: there is no ACS function, compiler builtin, or
`APROP_*` selector that reads the live `player->viewheight`, `deltaviewheight`, or `viewz`.
`GetActorProperty`/`CheckActorProperty`'s `APROP_ViewHeight` case (`p_acs.cpp:4987-4994`,
`:5057-5060`) is a *different*, even more static value than this function: it returns bare
`actor->ViewHeight` with **no** `crouchviewdelta` added, so it disagrees with `GetActorViewHeight`
for any actively-crouching player. `SetActorProperty`'s `APROP_ViewHeight` case (`:4878-4896`) is
write-only and, incidentally, also assigns the live `viewheight` field to the new value — but that
only moves what the integrator's clamps target next tic, not a way to observe the current one.

A script that needs to detect a landing squat or reconstruct the integrator's live state has to do
so indirectly, from `GetActorVelZ`/`GetActorFloorZ`/`GetActorZ` — see
[`../concepts/viewheight-integrator.md`](../concepts/viewheight-integrator.md)'s "Not readable from
ACS" section for the exact reconstruction and its limits.

## See also

- [`../concepts/viewheight-integrator.md`](../concepts/viewheight-integrator.md) — the full
  `viewheight`/`deltaviewheight`/`viewz` state machine this function's return value is one static
  snapshot of.
- [`GetActorFloorZ`](getactorfloorz.md), [`GetActorZ`](../families/actor-position-getters.md) — used
  together to detect ground contact, the precondition for a landing-squat seed.
- [`GetActorVelZ`](../families/actor-velocity-getters.md) — the impact-velocity term the landing
  squat's seed is directly derived from (`velz >> 3`).
