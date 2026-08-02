# Actor position-getter family

`GetActorX`, `GetActorY`, `GetActorZ` — three compiler builtins sharing one C++ `case` block
almost verbatim (`p_acs.cpp:11998-12016`), which picks the returned field via pointer arithmetic
on the actor's own `x`/`y`/`z` members. Neither requires the others to be useful — this isn't a
mandatory-sequence family like [Lump I/O](lump-io.md) — but nearly every finding below applies
to all three identically, and `GetActorZ`'s one real behavioral divergence (bob offset) only
makes sense stated as a contrast against its two siblings, so one file avoids maintaining three
near-duplicate `functions/*.md` pages (same precedent as the [plane-trigger family](plane-trigger.md)).

**Bucket:** all three compiler builtins (`PCD_GETACTORX`/`PCD_GETACTORY`/`PCD_GETACTORZ`,
`p_acs.cpp:11998-12016`, one shared `case` block). The implementation is
`(&actor->x)[pcd - PCD_GETACTORX]` — `AActor` declares `fixed_t x, y, z;` as consecutive members
(`actor.h:970`) and the three `PCD_GETACTOR*` enum values are consecutive in the same order
(`p_acs.h:763-765`), so the offset trick reads exactly the intended field. All three resolve the
target actor via the file-local `SingleActorFromTID(int, AActor*)` helper (`p_acs.cpp:4445-4456`).
`zt-bcc/src/builtin.c` registers `getactorx`/`getactory`/`getactorz`, each `fixed GetActor*(int)`.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master`/`3.3-alpha`
HEAD — see "Engine scope" in `../../shared/AUTHORING.md`).

---

## `fixed GetActorX(int tid)`
## `fixed GetActorY(int tid)`
## `fixed GetActorZ(int tid)`

Gets one coordinate of an actor by TID, as a signed 16.16 fixed-point map-unit value — see
[units-and-encodings.md](../concepts/units-and-encodings.md). Unlike the normalized `[0.0, 1.0)`
return of [GetActorAngle](../functions/getactorangle.md), position coordinates can be negative,
zero, or any positive value depending on where the actor sits on the map.

- `tid` — **`0` means "the activator"** (`SingleActorFromTID`'s `tid == 0` fallback,
  `p_acs.cpp:4448`); guarded against a NULL activator (e.g. called from a script with no
  activator), which returns `0` silently rather than crashing — the safe pattern that
  [PlayActorSound](../functions/playactorsound.md) violates (see
  [crash-and-bug-checklist.md](../concepts/crash-and-bug-checklist.md)).
- **`tid != 0`: reads only the first actor matching that TID**, via `FActorIterator` wrapped in a
  single `Next()` call (`p_acs.cpp:4449`). In projects where a TID is deliberately shared across
  many actors, reading position on a shared TID yields only one actor's coordinates, never a sum
  or average across all matches.
- **Symmetric with `SetActorPosition`, unlike the angle functions.**
  [SetActorPosition](../functions/setactorposition.md) also resolves through
  `SingleActorFromTID` and therefore only moves the *first* matching actor for a nonzero TID —
  the same first-match-only rule these getters use. This is a real contrast with
  [GetActorAngle](../functions/getactorangle.md)/[SetActorAngle](../functions/setactorangle.md),
  where the getter reads only the first match but the *setter* mutates every actor sharing the
  TID. Get/Set position pairs don't have that asymmetry; Get/Set angle pairs do — worth checking
  explicitly when porting logic between the two.
- **Silent `0` conflation: bad TID, no activator, and a genuinely-zero coordinate are
  indistinguishable.** The function returns `0` when `actor == NULL` (bad TID, or `tid == 0`
  with no activator), and also returns `0` when an actor legitimately sits at that coordinate —
  the same NULL/zero-value conflation already documented for
  [ActivatorTID](../functions/activatortid.md)/[GetSectorFloorZ](../functions/getsectorfloorz.md)/
  [GetActorAngle](../functions/getactorangle.md). Y=0 and X=0 are ordinary (origin-adjacent) map
  coordinates, not rare like a zero angle, so the conflation bites more often here. Safe guard:
  check `IsPointerEqual(AAPTR_DEFAULT, AAPTR_NULL, tid, 0)` before a high-trust read (real-world
  callers typically pattern this at multi-TID call sites).
- **`GetActorZ` alone adds a floating bob offset — the one real behavioral divergence among the
  three.** `GetActorZ` returns `actor->z + actor->GetBobOffset()` (`p_acs.cpp:12009`);
  `GetActorX`/`GetActorY` are raw member reads with no equivalent addition. `GetBobOffset()` is a
  time-varying vertical oscillation, non-zero only for actors with the `MF2_FLOATBOB` flag set
  (floating decorations like torches/barrels), computed from the actor's `FloatBobPhase` and map
  time; it's `0` for everything else. **This creates a round-trip problem specific to Z:**
  `SetActorPosition(tid, GetActorX(0), GetActorY(0), GetActorZ(0), false)` is exact in X and Y
  (raw member in, raw member out via `SetOrigin`), but for a `MF2_FLOATBOB` actor the Z argument
  already includes the bob offset, which `SetOrigin` then stores as the new raw `z` — baking the
  bob into the base position, which the *next* `GetActorZ` read adds another bob term on top of.
  Each round-trip increments the stored Z by the current bob value. Non-floating actors round-trip
  exactly in all three dimensions. To get height above the floor rather than absolute Z, subtract
  [GetActorFloorZ](../functions/getactorfloorz.md)`(tid)` from `GetActorZ(tid)`.
- **No angle interpolation, no netcode replication.** All three are raw synchronous reads with no
  smoothing and no client/server replication path — unlike
  [SetActorPosition](../functions/setactorposition.md), which replicates a successful move to
  clients via `SERVERCOMMANDS_MoveThing`, these getters just read whatever's currently in memory.

## Example (adapted from the wiki)

```c
script 1 (int count)
{
    // Rains health potions on the player from above
    while (count-- > 0)
    {
        Delay(random(5, 15));
        Spawn("HealthBonus", GetActorX(0), GetActorY(0), GetActorZ(0) + 256.0, 0, 0);
    }
}

script 2 (int count, int dist)
{
    // Ring of imps around the activator
    int basex = GetActorX(0);
    int basey = GetActorY(0);
    int angle, n;

    for (n = 0; n < count; n++)
    {
        angle = 1.0 * n / count;  // Fraction of a full turn; 1.0 = 360 degrees

        Spawn("DoomImp", basex + dist * cos(angle), basey + dist * sin(angle), GetActorZ(0),
            0, (angle + 0.5) >> 8);
    }
}
```

The `angle = 1.0 * n / count` trick forces fixed-point division: `n / count` would truncate to
`0` under integer division before multiplying by `1.0`, so the multiply is done first.

**Provenance:** wiki pages `GetActorX - ZDoom Wiki.html` (`oldid=38555`),
`GetActorY - ZDoom Wiki.html` (`oldid=35874`), `GetActorZ - ZDoom Wiki.html` (`oldid=35809`)
(all `_intake/`, retrieved 2026-07-29) + source-verified against `p_acs.cpp:11998-12016`
(shared `case` block), `p_acs.cpp:4445-4456` (`SingleActorFromTID`), `actor.h:970` (consecutive
`x,y,z` members), `actor.h:885-892` (`GetBobOffset`/`MF2_FLOATBOB`), and `p_acs.h:763-765` (PCD
enum order). The fixed-point return type, `tid=0`→activator convention, first-match-only
semantics on nonzero TID, symmetric Get/Set pair (contrast with the
`GetActorAngle`/`SetActorAngle` asymmetry), and the Z-only bob offset all verified; no
wiki/fork divergence found for X or Y — each wiki page is simply minimal, omitting failure
behavior and the setter-symmetry point. **Wiki divergence for Z:** the wiki describes
`GetActorZ` as returning "the Z coordinate of the actor" without mentioning the bob-offset
addition at all; that's a source-only finding, not documented anywhere on the wiki.
**Engine:** Zandronum 3.2.1. **Tier:** A.
