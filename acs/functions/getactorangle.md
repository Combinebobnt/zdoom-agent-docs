# `fixed GetActorAngle(int tid)`

**Tier:** A.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master`/`3.3-alpha` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`).
**Provenance:** wiki page `GetActorAngle - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=40295`) + source-verified against `p_acs.cpp:12032-12037, 4445-4453`, `doomtype.h` for `angle_t` signedness, and `zt-bcc/src/builtin.c:133`. The fixed-point angle encoding, `fixed` return type, and nonzero-TID read-only-first-match asymmetry with `SetActorAngle` all verified; no wiki/fork divergence found (the `GetActorAngle`/`SetActorAngle` asymmetry is unmentioned on the wiki but is real in the fork and documented in `SetActorAngle`'s own entry).
**Bucket:** compiler builtin.

Gets the facing angle of an actor by TID. Compiler builtin (`PCD_GETACTORANGLE`,
the Zandronum source's `src/p_acs.cpp:12032-12037`), implementation via the file-local
`SingleActorFromTID(int, AActor*)` helper (`p_acs.cpp:4445-4453`), which the ACS case calls to
resolve the actor and then extracts its angle member.

- `angle` (return value) — a **fixed-point fraction of a full turn** (`[0.0, 1.0)`), the same
  encoding as `SetActorAngle`/`Sin`/`Cos`/`VectorAngle` — see
  [units-and-encodings.md](../concepts/units-and-encodings.md). The wiki's `East=0.0`,
  `North=0.25`, `West=0.5`, `South=0.75` table checks out against source: the actor's angle is
  stored as `angle_t` (32-bit BAM, full turn = `2^32`), right-shifted by 16 to convert to the
  16.16 fixed-point ACS return value — `0.25` (North, `0x40000000` in BAM) becomes `16384`, which
  is `0.25` in ACS fixed point. The return is **always unsigned** (`angle_t` is `uint32`), so
  angles are always in the normalized `[0.0, 1.0)` range, never negative. No divergence from the
  wiki here — the wiki already declares `fixed` return, and `zt-bcc/src/builtin.c:133`
  (`{ "getactorangle", "f;i" }`, fixed return, one int param) agrees.
- `tid` — **`0` means "the activator"** (`SingleActorFromTID`'s `tid == 0` fallback, line 4448);
  guarded against NULL activator (e.g. called from a script with no activator), which returns `0`
  silently rather than crashing.
- **`tid == 0` (activator): symmetric with `SetActorAngle`**. Both functions read/write the
  activator alone when `tid == 0`.
- **`tid != 0` (by TID): asymmetric read behavior vs `SetActorAngle`.** This getter reads only the
  *first* actor matching that TID (`SingleActorFromTID` wraps the iterator in a single
  `Next()` call, line 4449), while `SetActorAngle` with the same nonzero TID mutates *every*
  actor sharing that TID in one call (wraps the iterator in a `while` loop). This is a real
  asymmetry to keep in mind in projects where a TID is deliberately shared across many actors —
  a Get on a shared TID doesn't see every actor, but a Set touches every one.
- **Silent `0` conflation: bad TID, no activator, and genuine East angle (`0.0`) are
  indistinguishable.** The function returns `0` when `actor == NULL` (either bad TID passed or
  `tid == 0` with no activator), and also returns `0` when an actor legitimately faces East.
  This is the same pattern already documented for `ActivatorTID`/`GetSectorFloorZ` — all three
  have the same NULL/zero-value conflation at their root.
- **No angle interpolation.** Unlike `SetActorAngle` (which supports smooth player-view panning
  via a per-actor `interpolate` flag), the getter is straightforward: read the current angle,
  no smoothing or filtering involved. Get→Set round-trips are also **lossy below 1/65536 turn**
  (the internal `angle_t >> 16` operation truncates the low 16 BAM bits), so an angle set with
  fixed-point precision finer than that will drift on read-back.

## Example (adapted from the wiki)

```c
script 10 ENTER
{
    // Thrust the activator (a player) in the direction it's facing
    ThrustThing(GetActorAngle(0) >> 8, 50, 1, 0);
}

script 15 (int monsterid)
{
    // Get a monster's angle, convert from fixed-point to byte angle
    int angle = GetActorAngle(monsterid) >> 8;
    
    // Reverse the angle (180 degrees): add 128 (half a byte-angle circle)
    if (angle < 128)
        angle = angle + 128;
    else
        angle = angle - 128;
    
    Print(d:angle);
}
```
