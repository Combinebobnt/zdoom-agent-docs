# `void SoundSequenceOnActor(int tid, str sndseq)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `SoundSequenceOnActor - ZDoom Wiki` (https://zdoom.org/w/index.php?title=SoundSequenceOnActor&oldid=35963), verified 2026-07-29 against fork source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.

Starts a sound sequence (defined in a `SNDSEQ` lump, itself referencing sounds registered in
`SNDINFO`) attached to an actor. Extension function (`ACSF_SoundSequenceOnActor`, index `-30` in
the zt-bcc source's `lib/zcommon.bcs:1658`), implementation in `p_acs.cpp:6214-6238`.

- `tid == 0`: targets the activator directly (`p_acs.cpp:6219-6225`) instead of iterating actors.
  **If the script has no activator** (e.g. called from an `OPEN`/other activator-less script
  context), `activator == NULL` and the whole call is a silent no-op — nothing plays, no error.
  The wiki page doesn't mention this branch at all; it only shows the `tid != 0` case.
- `tid != 0`: iterates **every** actor matching that tid via `FActorIterator` and starts the
  sequence on **each one** (`p_acs.cpp:6227-6234`), not just the first match — if several actors
  share a tid, all of them start playing the sequence. The wiki's single "a thing on your map"
  phrasing understates this.
- `sndseq` name lookup is silent-fail: `SN_StartSequence(actor, seqname, modenum)` calls
  `FindSequence(seqname)` and simply returns `NULL` if the name isn't found in any loaded
  `SNDSEQ` lump (`s_sndseq.cpp:890-897`) — a typo'd or missing sequence name produces no sound and
  no log/error, same silent-failure pattern as this engine family's other sound builtins.
- **Replaces, does not stack:** the named-sequence overload calls the numbered overload with its
  `nostop` parameter defaulted to `false` (`s_sndseq.cpp:895`), which means `SN_StopSequence(actor)`
  runs first (`s_sndseq.cpp:847-850`) — calling `SoundSequenceOnActor` again on the same actor with
  a different (or the same) sequence stops whatever was already playing on it rather than layering
  sounds. Not mentioned by the wiki.
- The `modenum` argument of the underlying `SN_StartSequence(AActor*, const char*, int)` is always
  hardcoded to `0` by this ACS entry point (`p_acs.cpp:6223,6233`). A `SNDSEQ` choice block
  (e.g. lock-type-dependent door sequences, matched via `m_ModeNum` in `s_sndseq.cpp:1219`)
  therefore always resolves as mode 0. It jumps to the block's mode-0 entry if it lists one and
  otherwise falls through to the next command. Other modes are unreachable through this function.
- No transfer/translation is applied (`SEQ_NOTRANS` is passed at the numbered-overload level via
  the named overload, `s_sndseq.cpp:895`), consistent with the wiki not describing any translation
  behavior for this call.
- **Zandronum netcode:** nothing is sent to clients. Actor sequences play through `S_Sound`
  without its `bSoundOnClient` argument (`s_sndseq.cpp:110`), and Zandronum has a server command
  for sector sequences only (`SERVERCOMMANDS_StartSectorSequence`), none for actor sequences. A
  call from a server-side script is therefore inaudible to clients. To be heard online, the call
  must run on each client, e.g. from a `CLIENTSIDE` script.
