# `void SoundSequenceOnSector(int tag, string seqname, int location)`

**Tier:** A
**Engine:** Zandronum 3.2.1 (feature predates the fork; verified against the `3.3-alpha` local checkout, no version-gap concern for this one).
**Provenance:** `SoundSequenceOnSector - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SoundSequenceOnSector&oldid=27391`), verified 2026-07-29 against the Zandronum source's `src`.

## Bucket

Extension function, `ACSF_SoundSequenceOnSector` (index `-31` in `zt-bcc/lib/zcommon.bcs:1659`).
Implementation in `case ACSF_SoundSequenceOnSector:`, the Zandronum source's `src/p_acs.cpp:6240-6254`.

## Parameters

- `tag` — a sector tag, matched via `P_FindSectorFromTag` (`p_spec.cpp:270`, standard
  Boom-style chained-tag lookup). The call loops over **every** sector sharing that tag
  (`while ((secnum = P_FindSectorFromTag(args[0], secnum)) >= 0)`) and starts the sequence
  independently on each one — not just the first match. `tag` is an ordinary tag value here
  (no "0 means whole map" special-casing the way some line specials treat tag 0); if no sector
  has that tag, the loop body never runs and the call is a silent no-op.
- `seqname` — name of a sequence defined in the `SNDSEQ` lump, resolved via
  `FBehavior::StaticLookupString`. If the string index doesn't resolve, `seqname` comes back
  `NULL` and the whole function silently does nothing (no log, no error).
- `location` — which vertical "channel" of the sector the sequence attaches to. Use the
  `SECSEQ_*` constants already defined in `zt-bcc/lib/zcommon.bcs:705-708`:
  - `SECSEQ_FLOOR` (`1`) — from the floor and below
  - `SECSEQ_CEILING` (`2`) — from the ceiling and up
  - `SECSEQ_FULLHEIGHT` (`3`) — full height of the sector
  - `SECSEQ_INTERIOR` (`4`) — between floor and ceiling

  These numeric values are shared with (and identical to) the engine's own `CHAN_FLOOR`/
  `CHAN_CEILING`/`CHAN_FULLHEIGHT`/`CHAN_INTERIOR` macros (`s_sound.h:254-257`) — `SECSEQ_*` is
  just the ACS-facing name for the same channel numbering used internally.

## Fork-specific quirk: the out-of-range clamp is computed but never used

`p_acs.cpp:6243` computes a clamped channel value that is silently discarded:

```cpp
int space = args[2] < CHAN_FLOOR || args[2] > CHAN_INTERIOR ? CHAN_FULLHEIGHT : args[2];
...
SN_StartSequence(&sectors[secnum], args[2], seqname, 0);
```

`space` is assigned (clamping an out-of-range `location` to `SECSEQ_FULLHEIGHT`) but then the
raw, unclamped `args[2]` is passed to `SN_StartSequence` instead of `space`. This looks like a
leftover from a refactor — the clamping logic exists but doesn't actually take effect. In
practice this is not a crash risk: `SN_StartSequence(sector_t*, int chan, ...)` just stores
`chan` as an arbitrary tracking key on the resulting `DSeqSectorNode` (`s_sndseq.cpp:858-869`)
used later to target the same channel for `StopSequence`/`SN_StopSequence(sector, chan)`; it is
never used as an array index or otherwise bounds-checked downstream. So passing an out-of-range
`location` (e.g. `0` or `5`) does **not** get silently normalized to full-height as the dead
`space` variable would suggest — it starts a sequence tracked under that literal out-of-range
channel number, which simply won't collide with (or be stoppable via) any of the four named
`SECSEQ_*` channels. Stick to the four documented constants; nothing enforces it.

## Failure/no-op summary

- Bad/unmatched `tag`: silent no-op (loop never executes).
- Bad `seqname` string index: silent no-op (`seqname != NULL` check fails).
- Out-of-range `location`: not clamped despite dead code suggesting otherwise (see above) —
  starts the sequence on an untracked/uncoordinated channel number instead of erroring.
- No return value (`void`) and no activator/pointer semantics — this is a level-tag-targeted
  call, not actor-targeted.

## Fork/wiki notes

The wiki page itself is thin (no examples) and matches this fork's behavior for the documented,
in-range constants. The unused-clamp quirk above is not mentioned by the wiki at all — it's
purely a Zandronum/ZDoom-fork implementation detail found by reading `p_acs.cpp` directly.

## See also

- `SoundSequence` (actor-tid-or-global form)
- `SoundSequenceOnActor`
- `SoundSequenceOnPolyobj`
