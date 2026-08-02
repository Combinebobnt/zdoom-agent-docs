# `void ThingSound(int tid, str sound, int volume)`

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked out source reports 3.3-alpha; `PCD_THINGSOUND` and the `bSoundOnClient` addition are long-standing, not netcode-gated additions postdating 3.2.1, so this is not expected to be version-sensitive).
**Provenance:** `ThingSound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=ThingSound&oldid=37263), verified 2026-07-29 against fork source.
**Bucket:** compiler builtin.

Plays a sound positioned at every actor matching `tid`. Compiler builtin (`PCD_THINGSOUND`,
the zt-bcc source's `src/builtin.c:56,204`), implementation in `p_acs.cpp:11583-11598`.

- `tid` — **not just one actor.** The engine runs a full `FActorIterator(tid)` and calls `S_Sound`
  once for *every* matching actor (`p_acs.cpp:11587-11595`), not just the first hit. If multiple
  actors share the same `tid`, the sound plays from each of them. `tid == 0` follows the standard
  ZDoom `FActorIterator` convention of matching actors that have no TID assigned (untagged
  actors) — it is not a special-case for "no actor"/"activator" the way some other TID-taking
  specials treat 0.
- `sound` — looked up via `FBehavior::StaticLookupString` (`p_acs.cpp:11584`); if the string index
  doesn't resolve, `lookup` stays `NULL` and the whole loop is skipped — a silent no-op, same
  pattern as the other sound builtins in this fork (`ActivatorSound`, `AmbientSound`, etc.), not
  an error.
- `volume` — matches the wiki's 0-127 int range; the engine divides by 127 to get the float
  `0.0`-`1.0` scale `S_Sound` expects (`(float)(STACK(1))/127.f`, `p_acs.cpp:11594`). No clamping
  is done here, so a value outside 0-127 is passed straight through as a proportionally
  out-of-range float.
- Always calls the `AActor*` overload of `S_Sound` with `CHAN_AUTO` and `ATTN_NORM`
  (`p_acs.cpp:11592-11594`) — i.e. always a positioned, distance-attenuated point sound as the
  wiki states ("anyone far away will not hear it as loudly"); there is no unpositioned/global
  fallback branch the way `ActivatorSound` has for a null activator.
- **Silent-sector suppression:** the `AActor*` overload of `S_Sound` returns immediately with no
  sound at all if the actor's `Sector->Flags & SECF_SILENT` (`s_sound.cpp:1287-1289`) — an
  engine behavior the wiki doesn't mention for this function. With multiple matching actors, each
  one is checked independently, so actors in a silent sector are skipped while others matching the
  same `tid` elsewhere still play.
- **Zandronum netcode addition not in the ZDoom wiki's model:** the call passes a trailing `true`
  for the fork-added `bSoundOnClient` parameter (`s_sound.h:229`, `// [EP] Added bSoundOnClient`).
  When running as a network server this additionally replicates the sound to clients via
  `SERVERCOMMANDS_SoundActor` (`s_sound.cpp:1291-1293`). Vanilla ZDoom's `S_Sound` has no such
  parameter or replication step, so this is purely a Zandronum-fork concern the wiki page
  couldn't describe.
- The wiki's top-of-page note — "superseded by `PlaySound`, which duplicates and extends its
  functionality" — checks out structurally: `PlaySound` (extension function, index -61; see
  `INDEX.md`'s flat tier-C entry) exposes channel, attenuation mode, and locality as explicit
  parameters instead of the single hardcoded `CHAN_AUTO`/`ATTN_NORM` pairing this function is
  locked into, and it operates on a single activator/TID rather than iterating every actor
  sharing a TID.
