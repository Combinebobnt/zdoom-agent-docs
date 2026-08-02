# Units and encodings

**Tier:** B (wiki-sourced concept page; the two claims that actually matter for this fork — tic precision and the `speed`/8 scaling — were traced to source; the Boom speed-constant table and the general "every `SPEED()`-using special behaves the same" extrapolation were not).
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — a `3.3-alpha` development snapshot ahead of the 3.2.1 target; the tic-precision and `SPEED()` macro findings here are core/stable ACS-engine behavior unlikely to differ across that gap — see "Engine scope" in `../../shared/AUTHORING.md`).
**Provenance:** wiki page `Definitions - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28, `oldid=49529`) + verified against the Zandronum source (`doomdef.h`, `win32/i_system.cpp`, `p_lnspec.cpp`) for the TICRATE/precision and `speed`-scaling claims (2026-07-28). Fixed-point/ angle/pitch encoding definitions are language-level facts, not independently re-derived from engine source (there is no fork-specific behavior to diverge here). The Boom door/platform/stair speed table is wiki-sourced background, not source-verified.

Fixed-point numbers, byte/fixed-point angles and pitches, tic/octic time units, and the
`speed`-argument scaling used across ZDoom-family action specials. Earns its place per the
authoring rule in `../../shared/AUTHORING.md` because these are exactly the "units beyond the type" facts a
signature-only doc can't carry — e.g. `fixed speed` tells you nothing about *what* fixed-point
value a given function expects.

## Fixed point numbers

A 32-bit int with the integer part in the top 16 bits and the fractional part (65536ths) in the
low 16 bits: `fixed_value = real_number * 65536`. This is what the `fixed` type means everywhere
in BCS/ACS (`GetActorX`, `FixedMul`, etc.) — not independently re-derived from source here since
it's the language's own type definition, not fork-specific behavior.

## Byte angles vs fixed-point angles

- **Byte angle**: 0-255, one full turn per 256. `0` = East, `64` = North, `128` = West,
  `192` = South (each 90° step is 64 units).
- **Fixed-point angle**: a `fixed` value between `0` and `65536` representing `0.0`-`1.0` of a
  turn (so `0.25` = North, `0.5` = West). Convert between them with `byte = fixed >> 8` and
  `fixed = byte << 8`.
- Only multiples of 45° convert to/from degrees without rounding loss in either representation
  (GCD of 360 and 256 is 8) — if a function takes a byte angle and you're computing it from a
  degree value, expect off-by-fractional-unit rounding for anything not a multiple of 45°.

## Pitches

- **Byte pitch**: signed, `-90`..`90` in degrees; **negative is up, positive is down**, `0` is
  level — this sign convention is the opposite of what "positive angle" intuition suggests and is
  worth double-checking against whichever pitch-taking function you're calling.
- **Fixed-point pitch**: same fixed-point-angle encoding as above but the useful range is only
  `-0.25` (90° up) to `0.25` (90° down), since pitch is limited to a half-turn.

## Units of time: tic vs octic — and the GZDoom-only precision fix does NOT apply here

- **Tic**: nominally 1/35 second; actor/state logic runs on tics.
- **Octic**: nominally 1/8 second (= 35/8 tics); sector movers (doors, lifts, crushers, stairs)
  and camera/actor-mover interpolation run on octics.
- **The wiki's "Precision" section describes a fix specific to GZDoom v3.2.2** that makes 35 tics
  last exactly one real second. **Verified this fix is not present in Zandronum**: `TICRATE` is
  `35` (`doomdef.h:60`), and the per-tic delay computation in the Windows timer backend is plain
  truncating integer division, `delay = 1000/TICRATE` (`win32/i_system.cpp:281`, evaluates to
  `28`, not `28.5714...`) — the same older/imprecise behavior the wiki attributes to "all official
  versions of parent port ZDoom." Zandronum is a ZDoom-family fork, not a GZDoom build, and this
  checkout shows no sign of having backported GZDoom's later precision fix. **Practical
  consequence: under Zandronum, 35 tics measurably take ~0.98 real seconds, not exactly 1 second**
  — don't assume tic-based timers (`Delay(35 * N)`) drift-correct to real wall-clock time over
  long durations.

## Sector movement speed (the `speed` argument pattern)

Many action specials take a `speed` argument in **eighths of a map unit per tic** — i.e. the raw
integer you pass gets divided by 8 before being used as units/tic (so `8` → 1.0 units/tic,
`35 * 8` → 35 units/sec). This is exactly the `SPEED(a)` macro
(`#define SPEED(a) ((a)*(FRACUNIT/8))`, `p_lnspec.cpp:76`) already confirmed for
`Floor_MoveToValue` in [Floor_MoveToValue](../functions/floor_movetovalue.md) — that function doc
is the concrete, fork-verified instance of the general pattern this page documents. Not
independently re-checked against every other speed-taking special using `SPEED()` in this pass,
but the macro is shared, not per-function, so the scaling is expected to hold wherever `SPEED()`
is used — check the target function's own doc (or `p_lnspec.cpp`) if it doesn't call `SPEED()`.

The standard Boom door/platform/stair speed constants (`2`/`4`/`8`/`16`/`32`/`64`/`128` = slow
through turbo, varying meaning per special family) are wiki-sourced background, not independently
re-derived from source in this pass — useful context for reading old Boom-compat maps/specials,
not a claim verified against any specific project's own scripts.
