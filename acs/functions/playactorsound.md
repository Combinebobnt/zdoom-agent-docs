# `void PlayActorSound(int tid, int sound [, int channel, fixed volume, bool looping, fixed attenuation])`

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked out source reports 3.3-alpha; `ACSF_PlayActorSound` shares long-standing Hexen-era ACS plumbing with `ACSF_PlaySound`, not a netcode-gated addition, so this is not expected to be version-sensitive).
**Provenance:** `PlayActorSound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=PlayActorSound&oldid=50241), verified 2026-07-29 against fork source.
**Bucket:** extension function.

Plays one of an actor's built-in DECORATE sound properties (SeeSound, AttackSound, etc.) as
identified by a `SOUND_*` constant, rather than an explicit sound lump name. Extension function
(`ACSF_PlayActorSound`, index `-71` in the zt-bcc source's `lib/zcommon.bcs:1700`), implementation
shared with `PlaySound` in the same switch case: the Zandronum source's `src/p_acs.cpp:6477-6554`
(the `funcIndex == ACSF_PlayActorSound` branches are at lines 6478, 6491, 6508-6511). See
`functions/playsound.md` for the shared activator/fan-out/looping plumbing — this file only
covers what's specific to `PlayActorSound`.

- `tid` — **`0` does mean "the activator"**, exactly as for `PlaySound`: the `if (args[0] == 0)
  { spot = activator; goto doplaysound; }` check at `p_acs.cpp:6501-6505` sits outside any
  `funcIndex` branch, so it applies identically to both functions. (Worth stating explicitly:
  nothing about `PlayActorSound` changes this — the tid-0-means-activator rule is not
  `PlaySound`-specific.) Nonzero `tid` fans out to every actor matching that TID via
  `FActorIterator`, same as `PlaySound`.
- **Real crash bug: `PlayActorSound(0, <valid SOUND_* constant>, ...)` from a script with no
  activator crashes the engine — unlike `PlaySound`, nothing guards this.** When `args[0] == 0`,
  `spot = activator` (`p_acs.cpp:6501-6505`) with no check that `activator` is non-`NULL`;
  execution then falls straight into `sid = GetActorSound(spot, args[1])`
  (`p_acs.cpp:6508-6511`), unconditionally, whenever `funcIndex == ACSF_PlayActorSound` — there is
  no equivalent to `PlaySound`'s later `S_Sound(AActor*, ...)` NULL check ahead of this call.
  `GetActorSound` itself (`p_acs.cpp:5332-5348`) does not guard `actor` either: every case except
  `default` dereferences it directly (`actor->SeeSound`, `actor->AttackSound`, ...,
  `actor->GetClass()->Meta.GetMetaInt(...)` for `SOUND_Howl`). So calling this with `tid=0` from a
  script that has no activator — `OPEN`/`ENTER`/`RESPAWN`, a `DISCONNECT` script, or any other
  context where `activator == NULL` — **null-pointer-dereferences and crashes the engine**, for
  *any* real `SOUND_*` constant. (The one case that doesn't crash: an out-of-range/invalid `sound`
  value hits `default: return 0;` without ever touching `actor`, so misusing the `sound` param
  happens to be safe — but that's not something to rely on, since every intentional use passes a
  real constant.) `PlaySound` does **not** share this bug — its `S_Sound(AActor*, ...)` overload
  explicitly checks `ent == NULL` before dereferencing (`s_sound.cpp:1287`), so `PlaySound(0, ...)`
  from a no-activator script is a safe no-op; see `functions/playsound.md`. **Callers must guard
  this call themselves.** Real-world callers typically do this at every call site, with
  `if (!IsPointerEqual(AAPTR_DEFAULT, AAPTR_NULL, 0, 0)) { PlayActorSound(0, ...); }` —
  verified correct: it resolves the `tid=0`/`AAPTR_DEFAULT` pointer (the activator) and compares it
  against `AAPTR_NULL`, so the guard only lets the call through when the activator is a real,
  non-null actor. See [IsPointerEqual](ispointerequal.md).
- `sound` — unlike `PlaySound`'s `sound` (a string looked up via `StaticLookupString`), this is
  an **integer sound-identifier constant**, resolved per-actor by `GetActorSound(spot, args[1])`
  (`p_acs.cpp:5332-5348`) into one of that actor's DECORATE sound properties:
  `SOUND_See`→`SeeSound`, `SOUND_Attack`→`AttackSound`, `SOUND_Pain`→`PainSound`,
  `SOUND_Death`→`DeathSound`, `SOUND_Active`→`ActiveSound`, `SOUND_Use`→`UseSound`,
  `SOUND_Bounce`→`BounceSound`, `SOUND_WallBounce`→`WallBounceSound`,
  `SOUND_CrushPain`→`CrushPainSound`, `SOUND_Howl`→the class's `HowlSound` meta property.
  Because `GetActorSound` is called once per matched actor (not once for the whole call), the
  actual sound played can differ per actor if the fan-out (nonzero `tid` matching multiple
  actors of different classes) is in play.
  - **Wiki/fork divergence: `SOUND_Push` does not exist in this fork.** The wiki lists an 11th
    identifier, `SOUND_Push`, but `zt-bcc/lib/zcommon.bcs:736-746`'s anonymous `SOUND_*` enum
    only defines 10 values (`SOUND_SEE` through `SOUND_HOWL`, i.e. 0-9), and `GetActorSound`'s
    `switch` (`p_acs.cpp:5334-5347`) has no `case` for a value of 10 — it falls through to
    `default: return 0`. There is no compile-time constant for it and no runtime support; passing
    a literal `10` (or any value not in the switch) is a **silent no-op** (see below), not an
    error.
  - The wiki flags `SOUND_Use` with "(Verification needed)" over whether it plays
    `Inventory.UseSound`. Verified: it does not — `GetActorSound` returns the actor's own generic
    `UseSound` field (`actor.h:1120`, "`Sound to play when an actor is used`", set via DECORATE's
    plain `UseSound` actor property), not the `Inventory`-class-specific `UseSound` property.
    Those are two different DECORATE properties on different classes; this function only ever
    reads the generic `AActor::UseSound`.
- **Invalid/unmatched `sound` values are a silent no-op, end to end.** For `PlaySound`, an
  invalid string index leaves `sid == 0` and the `if (sid != 0 || funcIndex ==
  ACSF_PlayActorSound)` guard at `p_acs.cpp:6491` skips the whole block for that funcIndex. For
  `PlayActorSound` that same guard is always true (short-circuited by the `funcIndex ==
  ACSF_PlayActorSound` half), so the loop body always runs — but `GetActorSound` returning `0`
  for an unmatched `sound` value means the later `if (sid != 0)` at `p_acs.cpp:6512` is false, so
  neither the immediate-play nor the looping-play branch executes. Net effect is identical to
  `PlaySound`'s bad-string case: no sound, no error.
- `channel`, `volume`, `looping`, `attenuation` — read exactly as for `PlaySound`
  (`p_acs.cpp:6496-6499`, gated on `argCount`), same defaults (`CHAN_BODY`, `1.0`, `false`,
  `ATTN_NORM`).
- **No `PlaySound`-style dead trailing parameter here.** `PlaySound` declares an unread 7th
  `local` bool that the engine never reads. `PlayActorSound`'s compiler signature
  (`zcommon.bcs:1700`: `PlayActorSound(int,int;int,fixed,bool,fixed):void`) has only 6 params
  total, matching the wiki's own signature exactly, and the engine reads `args[0]` through
  `args[5]` — no gap between declared and read params for this function.
- Looping/server-channel bookkeeping (`SERVER_IsChannelLooping`/`SERVER_UpdateLoopingChannels`)
  is identical to `PlaySound`'s — see that doc, not repeated here.
