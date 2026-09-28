# The rendered 3D view is one tic behind every actor position ACS can read

**Tier:** B — the source chain below is read end to end and the behavior is directly measured
in-engine, but only against Zandronum, and the equivalent UZDoom call order has not been checked.
**Applies to:** UZDoom=unknown, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-03)
**Provenance:** Source reading plus direct in-engine measurement — a stationary target with an
ACS-drawn HUD overlay on it, captured frame by frame through a jump with `currentpos` recorded at
every frame. No wiki page.

Read in `p_tick.cpp`, `p_user.cpp`, `r_utility.cpp` and `statnums.h`. The functions involved
(`P_Ticker`, `P_PlayerThink`, `P_CalcHeight`, `DThinker::RunThinkers`) are old shared ZDoom lineage,
so the same ordering is *likely* to hold family-wide — but that is an expectation, not a
measurement. Repeat the check before relying on it on another engine.

## The behavior

Within a single game tic, the view the renderer draws from is computed **before** actors move, while
ACS reads actor positions **after** they move. So for the whole duration of that tic:

> Any ACS read of an actor's position (`GetActorZ`, `GetActorX`/`Y`, `GetActorVelZ`, ...) is one tic
> **newer** than the position the 3D view is being rendered from.

This is invisible while an actor is still or moving slowly, and grows with speed. It matters most on
the vertical axis, because jumping and landing produce the fastest position changes a player
normally experiences.

**The practical consequence** is for anything that draws world-anchored HUD content — an overlay,
marker, outline or box positioned by projecting a world point through the viewer's reconstructed eye.
Such an overlay is positioned from ACS-read coordinates, so it **leads the rendered world by one
tic** and visibly detaches during fast vertical motion, snapping back the moment motion stops. The
overlay is not wrong; it is simply a tic ahead of the frame it is composited onto.

Measured magnitude, for scale: on a landing where the final tic moved the viewer's eye 10 map units,
an overlay on a target 150 units away sat 39 screen pixels off at 1280x960 / fov 105 — about 3.9
px per map unit of eye travel at that depth. A tic that moves the eye 20 units doubles it.

## Why: P_Ticker's ordering

`P_Ticker` does two separate passes, in this order:

1. **Player thinking.** It loops over players calling `P_PlayerThink`, which calls `P_CalcHeight`.
   That is where the view height is resolved: `player->viewz = player->mo->z + player->viewheight +
   bob` (`p_user.cpp:2948`). Critically, `player->mo->z` at this moment is still the position the
   actor held at the *end of the previous tic* — nothing has moved it yet this tic.
2. **Thinkers.** Only afterwards does `P_Ticker` call `DThinker::RunThinkers()`, which ticks the
   main lists in ascending statnum order (see [single-threaded-execution](single-threaded-execution.md)).
   `STAT_PLAYER` (52) is where `P_ZMovement` actually advances `mo->z` for this tic; `STAT_SCRIPTS`
   (65) is where the ACS VM runs (`statnums.h`).

So `viewz` is derived from the pre-move `z`, and ACS — running 13 statnums later, after
`STAT_PLAYER` — reads the post-move `z`. The offset is structural, not a race, and is stable at
exactly one tic.

Note the same ordering is what produces the one-tic delay between a landing being detected and the
eye-height dip becoming visible; that consequence is written up separately in
[viewheight-integrator](viewheight-integrator.md). This file is the general form: the ordering
affects *every* position read, not just the landing-squat seed.

## Pausing does not expose a fresher frame, and does not interpolate

Worth knowing when measuring this, because the natural instinct — pause, single-step, screenshot,
and assume the offset is the capture pipeline failing to present a fresh frame — is wrong in both
directions.

`P_Ticker` sets `r_NoInterpolate = true` near its top and returns early if the game is paused, so
that flag stays set for a paused frame. `R_SetupFrame` then takes the `r_NoInterpolate` branch:
it calls `R_ResetViewInterpolation()` and forces `r_TicFrac = FRACUNIT` (`r_utility.cpp:846-856`),
and `R_InterpolateView`'s `NoInterpolateView` branch copies `nview*` over `oview*`. Two results:

- **A paused frame has no fractional-tic view interpolation at all** — it shows exactly the last
  completed tic's `viewz`, not a blend. So a paused capture cannot be "mid-tic".
- **The one-tic offset survives pausing unchanged.** It is upstream of interpolation entirely.

Measured confirmation: three screenshots taken at one paused tic with no step between them are
byte-identical and all equally offset, and a capture taken three tics after the previous one shows
the *same* one-tic offset, not a three-tic one. The lag does not scale with how long the renderer
was left alone, because it is not a presentation delay.

## Consequences for testing

- To check whether ACS-side position math is correct, compare it against **the actor position ACS
  itself reads on that same tic** (e.g. a `currentpos`-style console readout), never against the
  rendered sprite. The sprite will always disagree during motion, at any step size, and that
  disagreement is the engine, not the code under test.
- If a rendered-image comparison is wanted anyway, compare it against the **previous** tic's read
  position, and capture a constant-velocity stretch as a control so a genuine error can be told
  apart from this offset.
- Stepping more tics between captures does not help and is not a workaround; there is nothing to
  settle.
