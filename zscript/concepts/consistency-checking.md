# Consistency checking and `CalculateConsistency`'s actual coverage

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=unknown — Zandronum has its own separate consistency-check
implementation; it was not read for this entry, so nothing here should be assumed to carry over.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-13)
**Provenance:** written from the UZDoom source's `src/d_net.cpp`; no wiki page covers this.

[Multiplayer-safe ZScript](multiplayer-safe-zscript.md) says UZDoom "marks the affected client as
inconsistent" once two clients' game states diverge. `CalculateConsistency` is the function that
check is built on, and it is the citation any argument about "will a state divergence actually get
caught" rests on — so it's worth knowing exactly what it sums, since that is also exactly what it
*doesn't* sum.

## What actually goes into the sum

`CalculateConsistency` sums four RNG seed states — the seeds behind actor spawning, general ACS
random calls, monster chase-target selection, and damage rolls — via a small helper that just adds
seed values together. On top of that it adds each in-game player's position and their yaw and
pitch orientation (**roll is not included**), and their health. That's the entire input to the
per-tic consistency value. Nothing else is part of it.

## What this means for arbitrary ZScript state

Any field a ZScript class holds beyond the values above — inventory counts, custom AI state,
anything defined by mod code rather than by the engine's own player/RNG bookkeeping — is invisible
to this check. If two clients' copies of such a field diverge, the game keeps reporting them as
consistent until (and unless) the divergence eventually perturbs one of the covered values: a
position, a health total, or one of the four RNG streams. A ZScript object can be desynced for an
arbitrary length of time with no detection at all.

## On mismatch: no resync

When a mismatch is detected, the affected player is flagged inconsistent inside the engine's
broader per-tic consistency-check routine. That flag drives the on-screen "out of sync" indicator
[Multiplayer-safe ZScript](multiplayer-safe-zscript.md) describes — but nothing beyond the
indicator happens. There is no state-transfer mechanism and no automatic recovery path triggered
by it; a detected desync is reported, not fixed.

## The flag doesn't stay set

The inconsistent flag is cleared the next time that player spawns, which makes it less useful as a
persistent indicator than it first appears: checking resumes silently after a spawn, against game
state that may still be desynced from before, with nothing left on screen to show it was ever
wrong for that player. A UI that only checks the flag once, or only right after it's first raised,
can miss that the underlying divergence is still there.

## See also

- [Multiplayer-safe ZScript](multiplayer-safe-zscript.md) — the desync model and "out of sync"
  indicator this page's coverage detail applies to.
