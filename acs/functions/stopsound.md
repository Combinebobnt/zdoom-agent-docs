# `void StopSound(int tid, int channel)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `StopSound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=StopSound&oldid=40903), verified 2026-07-29 against fork source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.

Stops a currently-playing sound on a given channel for the actor(s) matching `tid`. Extension
function (`ACSF_StopSound`, index `-62` in the zt-bcc source's `lib/zcommon.bcs:1690`), implementation
in `DLevelScript::CallFunction`, the Zandronum source's `src/p_acs.cpp:6556-6591`.

- `tid` — **`0` means "the script's activator"** (`p_acs.cpp:6560`: `if (args[0] == 0) S_StopSound(activator, chan);`), same zero-means-activator convention as other actor-targeting functions across both engines.
- **`tid=0` with no activator is verified safe — no NULL guard needed.** `S_StopSound(activator,
  chan)` is called with no NULL check on `activator`, but `S_StopSound(AActor*, int)`
  (`s_sound.cpp:1582-1596`) only ever compares `chan->Actor == actor` for pointer identity — it
  never dereferences `actor` — so a `NULL` activator just means no channel matches and the call is
  a silent no-op. The two netcode follow-ups behave the same way for the same reason:
  `SERVER_UpdateLoopingChannels` (`sv_main.cpp:4437-4465`) only does pointer-identity comparisons
  against its channel list, and `SERVERCOMMANDS_StopSound` routes through `EnsureActorHasNetID`
  (`sv_commands.cpp:99-112`), which explicitly returns `false` on a `NULL` actor before anything is
  dereferenced. This is a real contrast with the sibling `PlayActorSound`
  (`functions/playactorsound.md`), which crashes on the same `tid=0`-with-no-activator input
  because its extra `GetActorSound(spot, ...)` call dereferences the pointer unconditionally with
  no equivalent guard anywhere in the chain.
- **Non-zero `tid` stops the sound on *every* actor matching that TID, not just one** — the engine
  walks an `FActorIterator` over all matches (`p_acs.cpp:6574-6588`), unlike `GetActorProperty`
  (`functions/getactorproperty.md`) which resolves only a single actor for a TID via
  `SingleActorFromTID`. Since multiple actors can share a TID in Doom, this is a real behavioral
  difference worth knowing before assuming "the actor" (singular, as the wiki phrases it) is
  literal.
- `channel` — optional; if the call omits it (`argCount == 1`), the engine defaults to
  `CHAN_BODY` (`p_acs.cpp:6558`: `int chan = argCount > 1 ? args[1] : CHAN_BODY;`), matching the
  wiki's stated default. `CHAN_BODY` is declared in the zt-bcc source's `lib/zcommon.bcs:716`.
- Both branches call `S_StopSound(actor, chan)` (`s_sound.cpp`), which is a no-op if nothing is
  currently playing on that channel for that actor — there's no error/failure return to check;
  this function's return type is `void`.
- **Zandronum netcode addition not in the ZDoom wiki's model:** when running as a network server
  (`NETWORK_GetState() == NETSTATE_SERVER`), both branches additionally call
  `SERVERCOMMANDS_StopSound(actor, chan)` to replicate the stop to clients, and
  `SERVER_UpdateLoopingChannels(actor, chan, 0, 0, 0, true)` to remove the channel from the
  server's tracked list of looping sounds for that actor (`p_acs.cpp:6564-6569` for the
  activator case, `6581-6587` for the TID-iterator case). Vanilla ZDoom has no server/client
  split, so the wiki page has no equivalent of this step — it's purely a Zandronum-fork concern.
