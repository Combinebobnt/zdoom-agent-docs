# `void SoundSequence(str sndseq)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `SoundSequence - ZDoom Wiki` (https://zdoom.org/w/index.php?title=SoundSequence&oldid=35964), verified 2026-07-29 against fork source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Plays a sound sequence (defined in the `SNDSEQ` lump) on the frontsector of the *linedef that
activated the current script*. Compiler builtin (`PCD_SOUNDSEQUENCE`,
the zt-bcc source's `src/builtin.c:52,200`), implementation in `p_acs.cpp:11415-11429`.

- `sndseq` — looked up via `FBehavior::StaticLookupString` (`p_acs.cpp:11416`); if the lookup
  fails, `lookup` stays `NULL` and the whole block (including the `activationline` check) is
  skipped — a silent no-op, same pattern as other string-arg sound builtins in Zandronum (see
  `functions/activatorsound.md`).
- **The wiki's one-line description ("plays a sound sequence defined in SNDSEQ") omits the real
  gating condition and hides what "plays" means mechanically:** the engine only does anything if
  `activationline != NULL` (`p_acs.cpp:11419`). `activationline` is the linedef whose special
  triggered the currently-running script — it is only non-`NULL` when the script was activated
  *through a line special* (e.g. the wiki's own example: a "Player Crosses Line" linedef with
  special 80/`ACS_Execute`). If the script instead runs from an `OPEN`/`ENTER` script, a puzzle
  item, a console command, `ACS_NamedExecute` called from another script, a net event, etc. —
  any path with no originating linedef — `activationline` is `NULL` and this function is a
  complete no-op with no error or log output. This is a materially different picture from what
  the wiki's terse description implies (it reads as if any script context works).
- When it does fire, it is implemented as `SN_StartSequence(activationline->frontsector,
  CHAN_FULLHEIGHT, lookup, 0)` — i.e. mechanically identical to starting a *sector* sound
  sequence (see `SN_StartSequence` sector-overload call sites, e.g. `p_acs.cpp:6250` for
  `ACSF_SoundSequenceOnSector`) on the activating line's front sector specifically, always on
  `CHAN_FULLHEIGHT` and always sequence "mode" `0`. There is no way to target the back sector, a
  different sector, an actor, or a polyobject with this function — for that, use
  `SoundSequenceOnSector`/`SoundSequenceOnActor`/`SoundSequenceOnPolyobj` instead, which take an
  explicit target argument and don't depend on how the script was activated.
- **Zandronum netcode addition not in the ZDoom wiki's model:** when the engine is running as a
  network server, a successful call also replicates via
  `SERVERCOMMANDS_StartSectorSequence(activationline->frontsector, CHAN_FULLHEIGHT, lookup, 0)`
  (`p_acs.cpp:11424-11425`, `// [BB] Tell the clients to play the sound.`) so clients start the
  same sequence locally. Vanilla ZDoom's `PCD_SOUNDSEQUENCE` has no such replication step — purely
  a Zandronum-fork concern.
- Confirmed to exist in the Zandronum engine fork essentially unchanged from the base engine (opcode, lookup
  pattern, and the `activationline`-gated sector call are all present with no version-gating
  markers around them) — not a newer feature subject to the 3.2.1-vs-3.3-alpha caveat.
