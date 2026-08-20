# `void PlaySound(int tid, str sound [, int channel, fixed volume, bool looping, fixed attenuation, bool local])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `PlaySound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=PlaySound&oldid=47607), verified 2026-07-29 against fork source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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
- **`local` (the wiki's 7th parameter) is accepted by the compiler but never read by Zandronum's
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

## Engine-family divergence: `local` parameter is live on UZDoom

UZDoom's `case ACSF_PlaySound:` (`src/playsim/p_acs.cpp:5999-6046`, shared with `ACSF_PlayActorSound`
the same way as Zandronum) does read the 7th argument: `INTBOOL local = argCount > 6 ? args[6] :
false;`. When set, it ORs a `CHANF_LOCAL` flag into the channel value passed to `S_PlaySound`
(`p_acs.cpp:6039/6041`). `S_PlaySound`/`S_PlaySoundPitch` (`src/sound/s_doomsound.cpp:609-630`)
branch on that flag: with `CHANF_LOCAL` set, the sound only plays if `a->CheckLocalView()` is true
for the source actor (i.e. only for the client whose view is attached to that actor), and it's
played via the listener-relative path with `ATTN_NONE` instead of the passed-in attenuation. This
matches the wiki's description of `local` almost exactly ("played with `ATTN_NONE`" when looking
through the source actor's eyes) — so on UZDoom, `local` is **not** a dead parameter the way it is
on Zandronum; omitting it (or passing `false`) reproduces the Zandronum-documented behavior above,
but explicitly passing `true` has a real, wiki-matching effect on UZDoom that it does not have on
Zandronum.

The NULL-safety property documented above for `tid=0` with no activator still holds on UZDoom:
`S_PlaySoundPitch` starts with `if (a == nullptr || a->Sector->Flags & SECF_SILENT || a->Level !=
primaryLevel) return;` (`s_doomsound.cpp:611-612`), so a NULL `spot` is a safe no-op there too.
Everything else (tid-0-means-activator, TID-nonzero fan-out to every matching actor, bad-sound-name
silent no-op via `argCount`-gated defaults for `channel`/`volume`/`looping`/`attenuation`) matches
the Zandronum behavior described above; UZDoom naturally has no
`SERVER_IsChannelLooping`/`SERVER_UpdateLoopingChannels` server bookkeeping since that's
Zandronum-specific multiplayer plumbing, not a vanilla-ZDoom-family concept, and UZDoom's looping
instead goes through the ordinary `CHANF_LOOP | CHANF_NOSTOP` channel flags on the same
`S_PlaySound` call.
