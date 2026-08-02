# `void PlaySound(int tid, str sound [, int channel, fixed volume, bool looping, fixed attenuation, bool local])`

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked out source reports 3.3-alpha; `ACSF_PlaySound` is long-standing Hexen-era ACS, not a netcode-gated addition, so this is not expected to be version-sensitive).
**Provenance:** `PlaySound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=PlaySound&oldid=47607), verified 2026-07-29 against fork source.
**Bucket:** extension function.

Plays a sound as if it originated from the actor(s) matching `tid`. Extension function
(`ACSF_PlaySound`, index `-61` in the zt-bcc source's `lib/zcommon.bcs:1689`), implementation shared
with `PlayActorSound` in one switch case: the Zandronum source's `src/p_acs.cpp:6477-6554`.

- `tid` — TID of the actor(s) to play the sound from. **`0` means "the activator"**
  (`p_acs.cpp:6501-6505`: `if (args[0] == 0) { spot = activator; goto doplaysound; }`), matching
  the wiki. If `tid` is nonzero it plays on **every** actor matching that TID (`FActorIterator`
  loop, `p_acs.cpp:6493/6506`), not just the first one — the wiki doesn't mention this fan-out.
- **`tid=0` with no activator is a verified-safe no-op — no NULL guard needed, unlike
  `PlayActorSound`.** `spot = activator` (`p_acs.cpp:6501-6505`) is assigned with no NULL check,
  same as `PlayActorSound`, but `PlaySound` never dereferences `spot` before `S_Sound(spot, chan,
  sid, vol, atten, true)` (`p_acs.cpp:6530`/`6548`), and that `AActor*` overload explicitly checks
  `ent == NULL` before touching the pointer (`s_sound.cpp:1287`: `if (ent == NULL || ent->Sector->
  Flags & SECF_SILENT) return;`). The other functions on this path with a possibly-NULL `spot` —
  `S_IsActorPlayingSomething`, `SERVER_IsChannelLooping`, `SERVER_UpdateLoopingChannels` — only
  ever compare the pointer for identity, never dereference it. `PlayActorSound` (sharing this same
  `case`) is **not** safe the same way, because its extra `GetActorSound(spot, ...)` call
  (`p_acs.cpp:6510`) dereferences `spot` unconditionally with no NULL guard at all — see
  `functions/playactorsound.md` for the crash this causes.
- `sound`: looked up via `FBehavior::StaticLookupString` (`p_acs.cpp:6485`) — a bad/unregistered
  string index makes `sid` stay `0`, and the whole block at `p_acs.cpp:6491` is skipped, so the
  call is a silent no-op rather than an error.
- `channel`, `volume`, `looping`, `attenuation` — read straight through as documented by the
  wiki, defaulting to `CHAN_BODY`, `1.0`, `false`, `ATTN_NORM` respectively when omitted
  (`p_acs.cpp:6496-6499`, gated on `argCount`). No surprises here.
- **`local` (the wiki's 7th parameter) is accepted by the compiler but never read by this fork's
  engine code — it is a silent no-op, not a fork-vs-wiki behavior difference in the visible
  effect, just a dead parameter.** `zcommon.bcs:1689`'s signature
  (`PlaySound(int,str;int,fixed,bound,fixed,bool)`) does declare a 5th optional `bool` after
  `attenuation`, matching the wiki's `local` slot positionally, and it compiles fine with 7
  arguments passed. But `p_acs.cpp`'s `case ACSF_PlaySound:` handler (lines 6477-6554) only ever
  indexes `args[0]` through `args[5]` (`tid`, `sound`, `channel`, `volume`, `looping`,
  `attenuation`) — there is no `argCount > 6` / `args[6]` read anywhere in the case, and no
  `ATTN_NONE`-forcing or listener-relative logic corresponding to the wiki's description of what
  `local` should do ("played with `ATTN_NONE`" when the player is looking through the source
  actor's eyes). Passing a 7th argument compiles and is silently ignored at runtime.
- Looping sounds go through Zandronum's own server/looping-channel bookkeping
  (`SERVER_IsChannelLooping`/`SERVER_UpdateLoopingChannels`, `p_acs.cpp:6516-6527` and
  `6534-6546`) not present in vanilla ZDoom — a Zandronum-specific addition the wiki (written for
  upstream ZDoom) doesn't and can't describe. Notably, the engine also treats the `channel`
  argument's `CHAN_LOOP` bit as an alternate way to request looping (`chan & CHAN_LOOP` checks
  alongside the explicit `looping` bool at `p_acs.cpp:6520`/`6538`) — this is engine-internal
  plumbing, not something the ACS caller needs to set, but explains why `channel` is passed
  through raw rather than masked.
