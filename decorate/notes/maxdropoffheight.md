# `MaxDropOffHeight <float>`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Source-derived (no wiki page consulted) — verified against the Zandronum source's
`src/thingdef/thingdef_properties.cpp:1221-1224` (property parsing, stores into
`AActor::MaxDropOffHeight`), `src/p_enemy.cpp` (`P_Move`'s `dropoff` parameter), `src/p_map.cpp`
(`P_TryMove`'s dropoff-height check block), and `src/p_mobj.cpp` (`P_XYMovement`'s calls into
`P_TryMove`).
**Bucket:** `DEFINE_PROPERTY(maxdropoffheight, F, Actor)` in `src/thingdef/thingdef_properties.cpp`;
stores directly into `AActor::MaxDropOffHeight` (`src/actor.h`).

Limits how tall a ledge an actor will voluntarily step off, by gating a height check inside
`P_TryMove`. Default `24` map units on both engines (Zandronum: `wadsrc/static/actors/actor.txt`;
UZDoom: `wadsrc/static/zscript/actors/actor.zs`'s base `Actor` default block). Confirmed identical
in mechanism on UZDoom, whose native `MaxDropOffHeight` field (`src/playsim/actor.h:1359`) is
consulted from the same `P_Move` (`src/playsim/p_enemy.cpp`) and `P_TryMove`
(`src/playsim/p_map.cpp`) call sites described below — see "Engine-family divergence" below for two
additional consumers that exist only on UZDoom.

## The gating condition is narrower than "only `P_Move`'s call path", but not as blanket as "ignores momentum entirely"

`P_TryMove` takes a `dropoff` parameter (`int`, tri-state `0`/`1`/`2`), but the `MaxDropOffHeight`
comparison is not simply gated on `!dropoff`. The actual gating condition (identical in structure on
both engines) is an OR of two terms: the first is true when `dropoff` is falsy *and* the actor
carries none of `MF_DROPOFF`, `MF_FLOAT`, or `MF_MISSILE`; the second, independent of `dropoff`
entirely, is true whenever the actor carries `MF5_NODROPOFF`. Either term being true is enough to
run the `MaxDropOffHeight` comparison.

For an ordinary walking monster (no `MF_DROPOFF`/`MF_FLOAT`/`MF_MISSILE`/`MF5_NODROPOFF` flags) this
reduces to the simple `!dropoff` case, so `P_Move` (`src/p_enemy.cpp`/`src/playsim/p_enemy.cpp`, the
function behind ordinary monster AI "walk toward my target/wander" stepping) is indeed the one call
path that constrains a typical monster: its local `dropoff` variable starts at `0` and is only ever
raised to `2` for the unrelated `MF6_JUMPDOWN` "dogs jump off ledges to chase" special case. But the
`MF5_NODROPOFF` half of the `||` is an unconditional override — an actor carrying that flag is
checked against `MaxDropOffHeight` **regardless of the `dropoff` argument**, including when the
caller is momentum-driven movement (see below). A second branch of the same `if` block, gated on
`MF5_AVOIDINGDROPOFF`, is used by `P_NewChaseDir`'s "move away from a dropoff" logic (temporarily
set while a monster already standing at a dropoff's edge is fleeing it) and applies a slightly
different pair of comparisons; it is not itself an exception to the gating above.

## Momentum-driven movement ignores it, unless the actor is flagged `MF5_NODROPOFF`

`P_XYMovement` (the function that applies an actor's velocity each tic, i.e. ordinary
physics-driven movement) calls `P_TryMove(mo, ..., true, ...)` with a **hardcoded literal `true`**
for the `dropoff` argument at every one of its call sites, on both engines. For any actor *without*
`MF5_NODROPOFF`, this makes the first term of the condition above false, unconditionally skipping
the `MaxDropOffHeight` check for anything moving under momentum rather than under `P_Move`'s
deliberate AI stepping — including:

- **Knockback/thrust** from taking damage (`P_DamageMobj`'s thrust application feeds into velocity,
  consumed here).
- **Explosions and radius attacks** that impart velocity (`A_Explode`, `A_RadiusThrust`, and
  similar).
- **Any other action function or ACS call** that sets an actor's velocity directly (`A_ChangeVelocity`,
  `SetActorVelocity`, etc.) and lets ordinary tic-by-tic movement carry it forward.

A monster pushed off a tall ledge by any of the above will fall off it regardless of
`MaxDropOffHeight`'s configured value — **unless it carries `MF5_NODROPOFF`** ("cannot drop off
under any circumstances"), in which case the `||` in the gating condition makes the check apply
anyway, blocking the momentum-driven move outright rather than merely letting the actor fall.
`MaxDropOffHeight` is not a blanket "keep monsters away from ledges" guarantee for ordinary actors;
it only reliably stops them from choosing to step off one on their own, unless the actor opts in to
the stricter behavior via `MF5_NODROPOFF`.

## Engine-family divergence: ACS `GetActorProperty`/`SetActorProperty` support

UZDoom's ACS exposes `MaxDropOffHeight` as `APROP_MaxDropOffHeight` (value `45`,
`src/playsim/p_acs.cpp`), readable and writable at runtime via `GetActorProperty`/
`SetActorProperty`/`CheckActorProperty`. Zandronum's ACS has no equivalent: its `APROP_*` enum in
`src/p_acs.cpp` tops out at `APROP_StencilColor` (`41`) and never defines a `MaxDropOffHeight`
property at all, so it cannot be read or changed from ACS on Zandronum — only from the DECORATE
property at actor-definition time.

## Engine-family divergence: UZDoom's respawn safe-position tracking

UZDoom maintains a `FSafePosition`/`LastSafePos` cache on each player (`src/playsim/d_player.h`,
consulted and updated in `src/playsim/p_user.cpp` and `src/playsim/p_mobj.cpp`) with no Zandronum
equivalent. One of its validity criteria is exactly the `MaxDropOffHeight` comparison — a cached
position only counts as "safe" if the player isn't hanging more than `MaxDropOffHeight` above the
nearest lower floor (compares the player's height above `dropoffz` against `MaxDropOffHeight`,
`src/playsim/p_user.cpp`), alongside a deep-water alternative. `PlayerSpawnPickClass`'s respawn
logic consults this cache when the `dmflags2` cvar's `DF2_SAME_SPAWN_SPOT` bit is set, to decide
whether to respawn the player at their last safe position instead of a normal spawn spot
(`src/playsim/p_mobj.cpp`). This is a second, independent consumer of `MaxDropOffHeight` that
exists only on UZDoom — Zandronum's `p_user.cpp` has no comparable position-safety cache at all.

## See also

- [Monster and player falling damage](../concepts/falling-damage.md) — a common reason to reach
  for `MaxDropOffHeight` as a mitigation ("if it can't fall off a ledge, it can't take the fall") —
  this gap is exactly what defeats that approach whenever the fall is knockback-driven rather than
  AI-chosen.
