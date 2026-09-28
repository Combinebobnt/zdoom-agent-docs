# `void ThingSound(int tid, str sound, int volume)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `ThingSound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=ThingSound&oldid=37263), verified 2026-07-29 against fork source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Plays a sound positioned at every actor matching `tid`. Compiler builtin (`PCD_THINGSOUND`,
the zt-bcc source's `src/builtin.c:56,204`), implementation in `p_acs.cpp:11583-11598`.

- `tid` — **not just one actor.** The engine runs a full `FActorIterator(tid)` and calls `S_Sound`
  once for *every* matching actor (`p_acs.cpp:11587-11595`), not just the first hit. If multiple
  actors share the same `tid`, the sound plays from each of them. **Correction (2026-08-15):**
  `tid == 0` does **not** match untagged actors — `FActorIterator::Next()` short-circuits to a
  null return immediately whenever `id == 0` (Zandronum `actor.h:1289-1290`; UZDoom
  `actor.h:1732-1733`; both engines return early on a zero id), so
  `ThingSound(0, sound, volume)` matches zero actors and is a silent no-op, the same outcome as an
  unresolved `sound` string. The prior text here claiming a "matches untagged actors" convention
  was wrong in both engines, not just newly wrong in UZDoom.
- `sound` — looked up via `FBehavior::StaticLookupString` (`p_acs.cpp:11584`); if the string index
  doesn't resolve, `lookup` stays `NULL` and the whole loop is skipped — a silent no-op, same
  pattern as the other sound builtins in the Zandronum fork (`ActivatorSound`, `AmbientSound`,
  etc.), not an error.
- `volume` — matches the wiki's 0-127 int range; the engine divides by 127 to get the float
  `0.0`-`1.0` scale `S_Sound` expects (`p_acs.cpp:11594`). This call site does no clamping, but
  the sound code does, in both engines. A volume of 0 or below plays nothing
  (`s_sound.cpp:901`). The value is then multiplied by the sound's SNDINFO `$volume` and capped
  at 1.0 (`s_sound.cpp:954`), so a value above 127 only makes a difference for a sound whose
  SNDINFO volume is below 1. On a Zandronum server, the copy broadcast to clients is clamped to
  0.0-2.0 and sent as a byte (`sv_commands.cpp:3678`), and the client caps it at 127
  (`cl_main.cpp:7222-7225`). Clients therefore never get more than 1.0 before their own SNDINFO
  scaling.
- Always calls the `AActor*` overload of `S_Sound` with `CHAN_AUTO` and `ATTN_NORM`
  (`p_acs.cpp:11592-11594`) — i.e. always a positioned, distance-attenuated point sound as the
  wiki states ("anyone far away will not hear it as loudly"); there is no unpositioned/global
  fallback branch the way `ActivatorSound` has for a null activator.
- **Silent-sector suppression:** the `AActor*` overload of `S_Sound` returns immediately with no
  sound at all if the actor's `Sector->Flags & SECF_SILENT` (`s_sound.cpp:1287-1289`) — an
  engine behavior the wiki doesn't mention for this function. With multiple matching actors, each
  one is checked independently, so actors in a silent sector are skipped while others matching the
  same `tid` elsewhere still play. On Zandronum the early return also skips the client broadcast
  below, so such an actor is silent for everyone.
- **Zandronum netcode addition not in the ZDoom wiki's model:** the call passes a trailing `true`
  for the fork-added `bSoundOnClient` parameter (`s_sound.h:229`, `// [EP] Added bSoundOnClient`).
  When running as a network server this additionally replicates the sound to clients via
  `SERVERCOMMANDS_SoundActor` (`s_sound.cpp:1291-1293`). An actor with no NetID is sent as a
  fixed-position point sound instead (`sv_commands.cpp:3666-3669`). Vanilla ZDoom's `S_Sound` has no such
  parameter or replication step, so this is purely a Zandronum-fork concern the wiki page
  couldn't describe.
- The wiki's top-of-page note — "superseded by `PlaySound`, which duplicates and extends its
  functionality" — checks out structurally. [`PlaySound`](playsound.md) (extension function,
  index -61) iterates every actor matching the TID just as this function does, but exposes
  channel, volume, looping and attenuation as explicit parameters instead of the hardcoded
  `CHAN_AUTO`/`ATTN_NORM` pairing here (Zandronum `p_acs.cpp:6477-6554`). UZDoom's handler also
  reads a seventh `local` parameter; Zandronum's has no such parameter. Unlike this function,
  `PlaySound` treats `tid == 0` as the activator rather than a no-op (`p_acs.cpp:6501-6505`).
