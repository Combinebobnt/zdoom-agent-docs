# Units and encodings

**Tier:** B (wiki-sourced concept page; tic counting, fixed-point/angle encodings, and the `speed`/8 scaling were traced to source; the Boom speed-constant table and the general "every `SPEED()`-using special behaves the same" extrapolation were not; engine-family SPEED() macro divergence is source-verified).
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `Definitions - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28, `https://zdoom.org/w/index.php?title=Definitions&oldid=49529`) + verified against the Zandronum source (`doomdef.h`, `win32/i_system.cpp`, `p_lnspec.cpp`) for the TICRATE/precision and `speed`-scaling claims (2026-07-28). Fixed-point/ angle/pitch encoding definitions are language-level facts, not independently re-derived from engine source (there is no fork-specific behavior to diverge here). The Boom door/platform/stair speed table is wiki-sourced background, not source-verified. Octic users and tic-clock backends checked 2026-09-27 against Zandronum `p_lnspec.cpp:76-78,250,290,844`, `g_shared/a_movingcamera.cpp:368,394`, `g_shared/a_camera.cpp:78`, `win32/i_system.cpp:289-302,345-371`, `sdl/i_system.cpp:178-197,269-308` and `sv_main.cpp:651-699`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Fixed-point numbers, byte/fixed-point angles and pitches, tic/octic time units, and the
`speed`-argument scaling used across ZDoom-family action specials. Earns its place per the
authoring rule in `../../shared/AUTHORING.md` because these are exactly the "units beyond the type" facts a
signature-only doc can't carry — e.g. `fixed speed` tells you nothing about *what* fixed-point
value a given function expects. Includes engine-family differences in how the Zandronum engine fork and UZDoom implement the internal mechanics of these encodings, while preserving the caller-visible semantics.

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

## Units of time: tic vs octic

- **Tic**: nominally 1/35 second; actor/state logic runs on tics.
- **Octic**: nominally 1/8 second. Only a few time arguments use it: the delay of
  `Door_CloseWaitOpen`, `Generic_Door` and `Generic_Lift`, and the travel and hold times on
  camera/actor-mover path nodes (`InterpolationPoint` args 1 and 2), and a `SecurityCamera`'s
sweep cycle time (arg 2). Most other sector-mover
  delays (`Door_Raise`, the `Plat_*` and `Stairs_Build*` specials) are in tics, and every mover
  steps once per tic at its `speed`. *Note:* the `OCTICS(a)` macro those specials use
  (`((a)*TICRATE)/8`, identical on both engines) uses integer division, so `OCTICS(1)` = 4 tics
  (not 4.375), representing exactly 4/35 ≈ 114 milliseconds.

## Sector movement speed (the `speed` argument pattern)

Many action specials take a `speed` argument in **eighths of a map unit per tic** — i.e. the raw
integer you pass is divided by 8 to get map-units-per-tic (so `8` → 1.0 units/tic,
`35 * 8` → 35 units/sec). Both engines implement this via a `SPEED()` macro in `p_lnspec.cpp`
that converts the eighths-of-units representation to the engine's internal speed type, though
the implementation differs: Zandronum multiplies by a fixed-point constant (`(a)*(FRACUNIT/8)`,
resulting in a fixed-point `int`), while UZDoom divides as a floating-point literal
(`(a) / 8.`, resulting in a `double`). The semantic input/output is identical — pass `8` for
1.0 units/tic on both engines — but the downstream movement functions expect different types.
This macro is shared across all action specials that take `speed`, not per-function, so the
eighths-of-units scaling holds wherever `SPEED()` is used. See [Floor_MoveToValue](../functions/floor_movetovalue.md)
for a concrete, source-verified instance of this pattern.

The standard Boom door/platform/stair speed constants (`2`/`4`/`8`/`16`/`32`/`64`/`128` = slow
through turbo, varying meaning per special family) are wiki-sourced background, not independently
re-derived from source in this pass — useful context for reading old Boom-compat maps/specials,
not a claim verified against any specific project's own scripts.

## Engine-family divergence

The fixed-point number format, byte/fixed-point angle/pitch encodings, and the tic/octic time units are identical on both engines. The `SPEED()` macro semantic (divide raw argument by 8 to get map-units-per-tic) is also identical, but the implementation differs: Zandronum's macro multiplies by a fixed-point constant and passes an `int` to movement functions, while UZDoom's macro divides as a floating-point literal and passes a `double`. Callers observe no difference — pass the same value on both engines and get the same movement-per-tic behavior. Both engines' `OCTICS()` macro uses integer division and truncates identically. The tic clock differs by build. UZDoom derives the tic count from elapsed clock time. Zandronum's dedicated server and its Windows client do too (the Windows timer-event mode is disabled for a consistent tic rate). Zandronum's SDL (Linux/macOS) client instead counts `SIGALRM` signals from an interval timer set to `1000000/TICRATE` microseconds, and falls back to elapsed time only if that timer can't be set, so its tic count is not directly tied to elapsed time.
