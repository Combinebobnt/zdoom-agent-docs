# SoundSequenceOnPolyobj

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `SoundSequenceOnPolyobj - ZDoom Wiki.html` (zdoom.org, https://zdoom.org/w/index.php?title=SoundSequenceOnPolyobj&oldid=33052), verified against the Zandronum source on 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

```text
void SoundSequenceOnPolyobj(int polynum, str sndseq);
```

Extension function (`ACSF_SoundSequenceOnPolyobj`, index `-32` in `zt-bcc/lib/zcommon.bcs:1660`;
implementation `p_acs.cpp:6256-6268`, the Zandronum source's `src/p_acs.cpp`).

## Behavior

Looks up `sndseq` via `FBehavior::StaticLookupString`, and if that resolves, finds the polyobject
whose `tag` field equals `polynum` (`PO_GetPolyobj`, `po_man.cpp:1126-1138` — a straight linear
scan of `polyobjs[]` comparing `.tag`). If either lookup fails — bad string index, or no polyobject
with that tag — the whole call is a silent no-op: no sound, no log/console warning.

If the polyobject is found, `SN_StartSequence(poly, seqname, 0)` is called
(`s_sndseq.cpp:930-938`), which resolves the sequence name and starts it with `nostop` defaulted
to `false` (`s_sndseq.h:87`) — meaning any sequence already playing on that polyobject is stopped
first (`SN_StopSequence(poly)`, `s_sndseq.cpp:873-876`). This confirms the wiki's "a polyobject can
play only a single sequence at a time."

The wiki's more specific claim — that a subsequent movement/rotation instruction on the same
polyobject overrides the sequence started here (even with a silent/undefined sound) — also checks
out against Zandronum: every polyobject movement thinker (`PolyDoor`, `PolyMove`, `PolyRotate`,
etc. in `po_man.cpp`, e.g. lines 622, 721, 856, 936, 1019, 1073, 1082) itself calls
`SN_StartSequence(poly, poly->seqType, SEQ_DOOR, ...)` at the start of the move, again with the
stop-previous default. So calling `SoundSequenceOnPolyobj` and then immediately issuing a
`Polyobj_*` movement special on the same polyobject in the same script will have the movement's
own sequence (or silence, if `seqType` is undefined) clobber the one just started — matching the
wiki's advice to call `SoundSequenceOnPolyobj` *after* the movement special instead.

## Parameters

- `polynum` — the polyobject's **editor number/tag** (the id set on the polyobject anchor / used
  by `Polyobj_StartLine` etc.), not a TID and not a line tag on some other geometry — matched via
  a plain `polyobjs[i].tag == polynum` scan, so an invalid/unused number is simply "not found"
  (no error).
- `sndseq` — string-table index naming a sequence defined in the `SNDSEQ` lump. An unresolvable
  string index, or a name not present in `SNDSEQ` (`FindSequence` returns `< 0` inside
  `SN_StartSequence`), both fall through to no-op with no diagnostic.

## Notes

- Same-shape sibling extension functions exist for actors (`SoundSequenceOnActor`) and sectors
  (`SoundSequenceOnSector`, which additionally takes a channel argument) — each targets a
  different `SN_StartSequence` overload but shares the same stop-previous-then-start and
  silent-failure behavior. Not documented as a `families/*.md` group here; see this repo's
  `CLAUDE.md` "family-file collision guard" note if that changes later.
- No divergence found between Zandronum and the ZDoom-wiki description beyond the additional
  detail (confirmed here, not stated on the wiki) that the silent-no-op failure mode covers both
  a bad string index and an unmatched polyobject tag equally.
