# SoundSequenceOnPolyobj

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `SoundSequenceOnPolyobj - ZDoom Wiki.html` (zdoom.org, https://zdoom.org/w/index.php?title=SoundSequenceOnPolyobj&oldid=33052), verified against the Zandronum source on 2026-07-29. MoveTo exception: Zandronum `src/po_man.cpp:778-816` (`EV_MovePolyTo`, no `SN_StartSequence`).
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

The wiki's more specific claim, that a subsequent movement/rotation instruction on the same
polyobject overrides the sequence started here (even with a silent/undefined sound), holds for
most movement specials. On Zandronum, the starters `EV_RotatePoly`, `EV_MovePoly` and
`EV_OpenPolyDoor` (`po_man.cpp:622, 721, 1073, 1082`) start the polyobject's own `seqType`
sequence with the stop-previous default, and `DPolyDoor::Tick` does the same when a door begins
closing or reopens (`po_man.cpp:856, 936, 1019`). So calling `SoundSequenceOnPolyobj` and then
issuing one of those specials on the same polyobject will have the movement's own sequence (or
silence, if `seqType` is undefined) clobber the one just started. That matches the wiki's advice
to call `SoundSequenceOnPolyobj` *after* the movement special instead. A non-`OR_` special on a
polyobject that is already moving bails out before starting anything, so it clobbers nothing.

The exception is `Polyobj_MoveTo`/`Polyobj_MoveToSpot` and their `OR_` variants
(`p_lnspec.cpp:153, 162, 204, 213`). On Zandronum, `EV_MovePolyTo` (`po_man.cpp:778-816`) starts
no sequence at all, so a sequence started by this function before the move keeps playing through
it. On UZDoom, `EV_MovePolyTo` does start the `seqType` sequence like the other movers.

Every mover also calls `SN_StopSequence` when it finishes (e.g. `po_man.cpp:759` for
`DMovePolyTo`), and so does `Polyobj_Stop` (`po_man.cpp:291`). That ends whatever sequence is
playing on the polyobject, including one started by this function after the movement special.
This holds on both engines.

On Zandronum the function sends nothing to clients: the case has no `SERVERCOMMANDS_*` call, and
the only polyobject sound command (`client_PlayPolyobjSound`, `cl_main.cpp:9188-9204`) replays
the polyobject's `seqType`, not a named sequence. Called from a script that runs only on the
server, the sequence is never heard by clients.

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
  silent-failure behavior. Not documented as a `families/*.md` group here; see
  `maintainer/CLAUDE.md`'s "family-file collision guard" note if that changes later.
- Divergences from the ZDoom-wiki description on Zandronum: `Polyobj_MoveTo`/`MoveToSpot` don't
  override the sequence (see Behavior), and the function isn't networked. Beyond the wiki, the
  silent-no-op failure mode covers a bad string index, an unmatched polyobject tag and an unknown
  sequence name equally. An unknown name also leaves any sequence already playing untouched,
  since the stop only happens after the name resolves (`s_sndseq.cpp:930-938`).
