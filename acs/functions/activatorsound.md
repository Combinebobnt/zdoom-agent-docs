# `void ActivatorSound(str sound, int volume)`

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked out source reports 3.3-alpha; `PCD_ACTIVATORSOUND` and the `bSoundOnClient` addition are long-standing, not netcode-gated additions postdating 3.2.1, so this is not expected to be version-sensitive).
**Provenance:** `ActivatorSound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=ActivatorSound&oldid=37264), verified 2026-07-29 against fork source.
**Bucket:** compiler builtin.

Plays a sound from whoever/whatever activated the script. Compiler builtin (`PCD_ACTIVATORSOUND`,
the zt-bcc source's `src/builtin.c:57,205`), implementation in `p_acs.cpp:11395-11413`.

- `sound` — looked up via `FBehavior::StaticLookupString` (`p_acs.cpp:11396`); a bad/unregistered
  string index makes `lookup` stay `NULL` and the whole block is skipped — a silent no-op, not an
  error, same pattern as other sound builtins in this fork.
- `volume` — matches the wiki's 0-127 int range; the engine divides by 127 to get the float
  `0.0`-`1.0` scale `S_Sound` expects (`(float)(STACK(1)) / 127.f`, `p_acs.cpp:11403/11409`).
- **The wiki's one-line description ("plays from whoever activated the script") glosses over a
  real activator-null branch that changes both positioning and audibility:**
  - If `activator != NULL` (`p_acs.cpp:11399-11404`): `S_Sound(activator, CHAN_AUTO, lookup,
    volume/127, ATTN_NORM, true)` — positioned at the activator, subject to normal distance
    attenuation (`ATTN_NORM`), so players far from the activator may not hear it at all.
  - If `activator == NULL` (`p_acs.cpp:11405-11410`) — e.g. called from a script with no activator
    such as an `OPEN` script — falls back to `S_Sound(CHAN_AUTO, lookup, volume/127, ATTN_NONE,
    true)`: unpositioned and **heard everywhere regardless of distance** (`ATTN_NONE`). This
    fallback isn't mentioned by the wiki at all.
- **Silent-sector suppression:** the activator-present path calls the `AActor*` overload of
  `S_Sound`, which returns immediately with no sound if `activator->Sector->Flags & SECF_SILENT`
  (`s_sound.cpp:1285-1289`) — a Zandronum/ZDoom engine behavior the wiki doesn't call out for this
  function specifically. The activator-absent path (unpositioned `S_Sound`) has no such check.
- **Zandronum netcode addition not in the ZDoom wiki's model:** both branches pass a trailing
  `true` for the fork-added `bSoundOnClient` parameter (`s_sound.h:228-229`, `// [EP] Added
  bSoundOnClient`). When the engine is running as a network server, this makes it additionally
  replicate the sound to clients — `SERVERCOMMANDS_SoundActor` for the activator-present case,
  `SERVERCOMMANDS_Sound` for the activator-absent case (`s_sound.cpp:1273-1276`, `1289-1292`).
  Vanilla ZDoom's `S_Sound` has no such parameter or replication step, so this is purely a
  Zandronum-fork concern, not something the wiki page could describe.
- The wiki's own top-of-page note — "superseded by `PlaySound`, which duplicates and extends its
  functionality" — checks out structurally: `PlaySound` (see `functions/playsound.md`) exposes
  channel/looping/attenuation/local as explicit parameters instead of the two hardcoded
  attenuation modes and always-`CHAN_AUTO` channel this function is locked into.
