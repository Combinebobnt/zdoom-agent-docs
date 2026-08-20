# `void LocalAmbientSound(str sound, int volume)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `LocalAmbientSound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=LocalAmbientSound&oldid=35966), verified 2026-07-29 against fork source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Plays a sound at world volume (no distance attenuation), audible only to the script's activator —
not broadcast to every player like `AmbientSound`. Compiler builtin (`PCD_LOCALAMBIENTSOUND`,
the zt-bcc source's `src/builtin.c:58,206`), implementation in `p_acs.cpp:11375-11393`.

- `sound` — looked up via `FBehavior::StaticLookupString` (`p_acs.cpp:11379`); a bad/unregistered
  string index leaves `lookup` as `NULL` and the whole block is skipped — a silent no-op, same
  pattern as the other sound builtins in the Zandronum engine fork (see `functions/activatorsound.md`).
- `volume` — matches the wiki's 0-127 int range; divided by 127 to get the `0.0`-`1.0` float scale
  `S_Sound` expects (`(float)(STACK(1)) / 127.f`, `p_acs.cpp:11384`).
- **"World volume" = `ATTN_NONE`** (`s_sound.h:277`, `// full volume the entire level`) — same
  attenuation mode `AmbientSound` uses (`p_acs.cpp:11366`). The only behavioral difference between
  the two builtins is *who* hears it, not how loud/positioned it is — both are unpositioned and
  distance-independent.
- **"Only heard by the activator" is not a simple identity check — it's `activator->CheckLocalView
  (consoleplayer)`** (`p_acs.cpp:11380`, defined at `p_mobj.cpp:1257-1273`): true when the executing
  machine's `consoleplayer` is currently *viewing through* the activator — i.e. the activator is
  that player's camera, or the activator *is* that player's body and their camera is a non-sentient
  chase/spectator object. This matters for spynext/spectator/chasecam views: if the activating
  player's view has been swapped away from their own body (e.g. spying another player, or a
  non-owned camera actor), the local playback check can fail even though "the activator" in the
  ACS sense hasn't changed. The wiki's plain "only heard by the activator" phrasing doesn't capture
  this.
- **`activator == NULL` is a documented no-op in the Zandronum engine fork, not a crash** — a comment right above
  the case (`p_acs.cpp:11376`, `// [BB] With Skulltag's in game joining / leaving, it's possible
  that activator is NULL`) guards the whole block; if there's no activator (e.g. called from an
  `OPEN` script, or during Skulltag/ST-legacy join/leave transitions), nothing plays and nothing is
  networked. The wiki doesn't mention this case at all.
- **Zandronum netcode addition not in the ZDoom wiki's model:** when running as a network server,
  the local `S_Sound` call is followed by `SERVERCOMMANDS_Sound(..., activator->player - players,
  SVCF_ONLYTHISCLIENT)` (`p_acs.cpp:11388-11389`; `SVCF_ONLYTHISCLIENT`, `sv_commands.h:73`) — the
  server explicitly targets the replication packet at the activator's own client only, so other
  clients never receive the sound command. This send is additionally gated on `activator->player`
  being non-null (bots/non-player activators never get a network send, only the potential local
  `S_Sound` on whichever machine is actually running that activator's view). Vanilla ZDoom has no
  such per-client targeting concept; this is purely a Zandronum-fork mechanism for keeping the
  sound genuinely single-player-audible in multiplayer, and it depends on the same fork-specific
  `bSoundOnClient`-adjacent server-command plumbing seen in `functions/activatorsound.md`.
- **Sibling comparison:** `AmbientSound` (`p_acs.cpp:11360-11373`) always plays unconditionally and
  replicates to all clients (`SERVERCOMMANDS_Sound` with no `SVCF_ONLYTHISCLIENT` flag) — it has no
  activator-null guard and no local-view check. `LocalAmbientSound` is not a variant that reuses
  `AmbientSound`'s case internally; the two are fully separate `case` blocks with independent logic,
  despite sharing the attenuation mode and volume scaling.

**Example:**

```text
script 1 ENTER
{
    LocalAmbientSound("QTalk", 127); // full volume, heard only by this script's activator
    Print(s: "Welcome to Hell");
}
```
