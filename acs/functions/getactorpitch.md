# `fixed GetActorPitch(int tid)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `GetActorPitch - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=GetActorPitch&oldid=42689`) + source-verified against `p_acs.cpp:12039-12044, 4445-4456`, `r_swrenderer.cpp:182-185` for pitch-limit derivation, and `zt-bcc/src/builtin.c:149`. The fixed-point pitch encoding, `fixed` return type, and nonzero-TID read-only-first-match asymmetry with `SetActorPitch` all verified. **Wiki/fork divergence noted:** the wiki describes pitch bounds as renderer-dependent (software vs GL), but the Zandronum engine fork's source shows renderer-specific `GetMaxViewPitch()` implementation only in the software renderer path; GL implementation was not traced to completion, so the actual GL bounds in the Zandronum engine fork remain unverified. Documented as a known gap. GL `GetMaxViewPitch()` traced 2026-09-27 at `src/gl/scene/gl_scene.cpp:1222-1229` (cvar default at `src/gl/data/gl_data.cpp:76-80`), server limits at `p_user.cpp:767-768`; `ChangeActorPitch`'s `interpolate` argument at `p_acs.cpp:6862-6866`, `PCD_SETACTORPITCH` passing `false` at `p_acs.cpp:12599-12600`. The `GetActorPitch`/`SetActorPitch` asymmetry is unmentioned on the wiki but is real in the fork and documented in `SetActorPitch`'s own entry.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Gets an actor's view/aim pitch. Compiler builtin (`PCD_GETACTORPITCH`,
the Zandronum source's `src/p_acs.cpp:12039-12044`), implementation via the file-local
`SingleActorFromTID(int, AActor*)` helper (`p_acs.cpp:4445-4456`), which the ACS case calls to
resolve the actor and then extracts its pitch member, right-shifted by 16 bits to convert from
the internal BAM representation to ACS fixed-point.

- `pitch` (return value) — a **fixed-point angle in the pitch plane** as documented in
  [Units and encodings](../concepts/units-and-encodings.md#pitches), constructed by dividing the
  internal `AActor::pitch` value (a `fixed_t` BAM-style signed integer) by 65536. **Negative
  values mean looking up, positive values mean looking down, 0 means level.** The wiki describes
  pitch bounds as renderer-dependent: software renderer bounded to approximately `-0.0888977`
  (about `-32°`) to `0.155548` (about `+56°`), GL renderer to `-0.25` to `0.25` (`-90°` to
  `+90°`). On Zandronum these are player look limits taken from the renderer's
  `GetMaxViewPitch()`. The software renderer's (`r_swrenderer.cpp:182-185`) returns 56 degrees
  both up and down by default; looking up is limited to 32 degrees only with `cl_oldfreelooklimit`
  on. The GL renderer's (`src/gl/scene/gl_scene.cpp:1222-1229`) returns the `maxviewpitch` cvar
  (default 90, clamped to at most 90) unless `cl_disallowfullpitch` or the
  `ZADF_FORCE_SOFTWARE_PITCH_LIMITS` flag is set, which force the software values. A server sets
  fixed limits of 32 up and 56 down (`p_user.cpp:767-768`). No clamping is enforced by the
  getter itself — an actor can have an out-of-normal-range pitch set via `SetActorPitch` and will
  be read back verbatim. See the `SetActorPitch` doc for the actual range limits enforced by
  player-input code.
- `tid` — **`0` means "the activator"** (`SingleActorFromTID`'s `tid == 0` fallback, line 4447);
  guarded against NULL activator (e.g. called from an `OPEN` script with no activator), which
  returns `0` silently rather than crashing.
- **`tid == 0` (activator): symmetric with `SetActorPitch`.** Both functions read/write the
  activator alone when `tid == 0`.
- **`tid != 0` (by TID): reads only the *first* actor with that TID — asymmetric vs `SetActorPitch`.** This getter reads only the first actor matching that TID (`SingleActorFromTID` wraps the iterator
  in a single `Next()` call, line 4454), while `SetActorPitch` with the same nonzero TID mutates
  *every* actor sharing that TID in one call (wraps the iterator in a `while` loop). This is a real
  asymmetry to keep in mind in projects where a TID is deliberately shared across many actors —
  a Get on a shared TID doesn't see every actor, but a Set touches every one.
- **Silent `0` conflation: bad TID, no activator, and genuine level pitch (`0.0`) are
  indistinguishable.** The function returns `0` when `actor == NULL` (either bad TID passed or
  `tid == 0` with no activator), and also returns `0` when an actor legitimately has level pitch.
  This is the same pattern already documented for `ActivatorTID`/`GetSectorFloorZ` — all three
  have the same NULL/zero-value conflation at their root.
- **No pitch interpolation.** The getter just reads the current pitch, with no smoothing or
  filtering. On the setter side, smooth player-view panning is only available through
  `ChangeActorPitch`'s optional third `interpolate` argument, which only affects player actors.
  `SetActorPitch` from ACS always passes `false`.
- **Get→Set round-trips are lossy below 1/65536 turn on Zandronum.** The getter's `pitch >> 16`
  drops the low 16 bits of the internal pitch. `SetActorPitch` writes `value << 16`, so a pitch
  it set reads back exactly, but a pitch with nonzero low bits (e.g. from mouse input) comes back
  rounded down, and writing that value back changes the actor's pitch slightly.

## Example (from the wiki)

This script will modify a projectile's trajectory based on the activator's pitch:

```acs
script 1 (void)
{
    int speed, vspeed;
    speed = cos(GetActorPitch(0)) * 64 >> 16;
    vspeed = -sin(GetActorPitch(0)) * 64 >> 16;
    SpawnProjectile(1, "DoomImpBall", 0, speed, vspeed, 1, 0);
}
```
