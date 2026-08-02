# `fixed GetActorPitch(int tid)`

**Tier:** A.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master`/`3.3-alpha` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`).
**Provenance:** wiki page `GetActorPitch - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=42689`) + source-verified against `p_acs.cpp:12039-12044, 4445-4453`, `r_swrenderer.cpp:182-185` for pitch-limit derivation, and `zt-bcc/src/builtin.c:149`. The fixed-point pitch encoding, `fixed` return type, and nonzero-TID read-only-first-match asymmetry with `SetActorPitch` all verified. **Wiki/fork divergence noted:** the wiki describes pitch bounds as renderer-dependent (software vs GL), but this fork's source shows renderer-specific `GetMaxViewPitch()` implementation only in the software renderer path; GL implementation was not traced to completion, so the actual GL bounds in this fork remain unverified. Documented as a known gap. The `GetActorPitch`/`SetActorPitch` asymmetry is unmentioned on the wiki but is real in the fork and documented in `SetActorPitch`'s own entry.
**Bucket:** compiler builtin.

Gets an actor's view/aim pitch. Compiler builtin (`PCD_GETACTORPITCH`,
the Zandronum source's `src/p_acs.cpp:12039-12044`), implementation via the file-local
`SingleActorFromTID(int, AActor*)` helper (`p_acs.cpp:4445-4453`), which the ACS case calls to
resolve the actor and then extracts its pitch member, right-shifted by 16 bits to convert from
the internal BAM representation to ACS fixed-point.

- `pitch` (return value) — a **fixed-point angle in the pitch plane** as documented in
  [Units and encodings](../concepts/units-and-encodings.md#pitches), constructed by dividing the
  internal `AActor::pitch` value (a `fixed_t` BAM-style signed integer) by 65536. **Negative
  values mean looking up, positive values mean looking down, 0 means level.** The wiki describes
  pitch bounds as renderer-dependent: software renderer bounded to approximately `-0.0888977`
  (about `-32°`) to `0.155548` (about `+56°`), GL renderer to `-0.25` to `0.25` (`-90°` to
  `+90°`). This fork's implementation uses `GetMaxViewPitch()` (`r_swrenderer.cpp:182-185`) which
  returns 32 degrees (looking up) or 56 degrees (looking down) as the default pitch limits;
  whether GL enforces different limits was not traced in source. No clamping is enforced by the
  getter itself — an actor can have an out-of-normal-range pitch set via `SetActorPitch` and will
  be read back verbatim. See the `SetActorPitch` doc for the actual range limits enforced by
  player-input code.
- `tid` — **`0` means "the activator"** (`SingleActorFromTID`'s `tid == 0` fallback, line 4448);
  guarded against NULL activator (e.g. called from an `OPEN` script with no activator), which
  returns `0` silently rather than crashing.
- **`tid == 0` (activator): symmetric with `SetActorPitch`.** Both functions read/write the
  activator alone when `tid == 0`.
- **`tid != 0` (by TID): reads only the *first* actor with that TID — asymmetric vs `SetActorPitch`.** This getter reads only the first actor matching that TID (`SingleActorFromTID` wraps the iterator
  in a single `Next()` call, line 4449), while `SetActorPitch` with the same nonzero TID mutates
  *every* actor sharing that TID in one call (wraps the iterator in a `while` loop). This is a real
  asymmetry to keep in mind in projects where a TID is deliberately shared across many actors —
  a Get on a shared TID doesn't see every actor, but a Set touches every one.
- **Silent `0` conflation: bad TID, no activator, and genuine level pitch (`0.0`) are
  indistinguishable.** The function returns `0` when `actor == NULL` (either bad TID passed or
  `tid == 0` with no activator), and also returns `0` when an actor legitimately has level pitch.
  This is the same pattern already documented for `ActivatorTID`/`GetSectorFloorZ` — all three
  have the same NULL/zero-value conflation at their root.
- **No pitch interpolation.** Unlike `SetActorPitch` (which supports smooth player-view panning
  via a per-actor `interpolate` flag), the getter is straightforward: read the current pitch,
  no smoothing or filtering involved. Get→Set round-trips are also **lossy below 1/65536 turn**
  (the internal `pitch >> 16` operation truncates the low 16 BAM bits), so a pitch set with
  fixed-point precision finer than that will drift on read-back.

## Example (from the wiki)

This script will modify a projectile's trajectory based on the activator's pitch:

```c
script 1 (void)
{
    int speed, vspeed;
    speed = cos(GetActorPitch(0)) * 64 >> 16;
    vspeed = -sin(GetActorPitch(0)) * 64 >> 16;
    SpawnProjectile(1, "DoomImpBall", 0, speed, vspeed, 1, 0);
}
```
