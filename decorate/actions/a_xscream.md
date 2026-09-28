# `void A_XScream()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_XScream` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_XScream&oldid=49049) + verified against the Zandronum source's `src/p_enemy.cpp:3346-3362`, `src/g_game.cpp:2705-2720` (`G_TransferPlayerFromCorpse`) and `src/g_game.cpp:2732-2758` (`G_DoReborn` queues the corpse unless single-player without respawn).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_XScream)` in `src/p_enemy.cpp` — defined on `AActor`, callable from any actor's state table.

Plays a hardcoded gibbed sound on the voice channel. The sound is `*gibbed` (the player's skin-specific gibbed sound) if the actor has a player pointer; otherwise `misc/gibbed` (the default non-player gibbed sound). No parameters.

Unlike `A_Scream`, which plays the actor's `DeathSound` property, `A_XScream` always plays one of two hardcoded sounds regardless of the actor's sound configuration. This is the correct choice for XDeath/gibbed states where you want a consistent "splat" sound, not a death speech.

## Behavior

When called:

1. **Player pointer handling**: If the actor has no player pointer but is in the body queue (a player corpse left behind when its player respawned or became a dead spectator), and that player is still in the game, `A_XScream` temporarily sets the player pointer back to that player (via `G_TransferPlayerFromCorpse`) so the gibbed sound uses that player's skin sound, then resets it to null. Corpses are queued in multiplayer and on single-player maps that allow respawning. In any other case this step does nothing.

2. **Sound selection**: If `self->player` is non-null, plays `*gibbed` (the player's sound-class alias, resolving per the player's skin). Otherwise plays `misc/gibbed` (a default non-player gibbed sound).

3. **Channel and attenuation**: The sound is played on `CHAN_VOICE` (the voice channel). Any other voice-channel sound from the same actor is cut off. The sound plays with normal distance attenuation (`ATTN_NORM`), not at full volume.

## Wiki note

The ZDoom Wiki's preamble states: "This function has been superseded by A_StartSound, which duplicates and extends its functionality."

`A_StartSound` does not exist in Zandronum — this is a GZDoom/UZDoom/ZScript-era function. The Zandronum equivalent for flexible sound-playing is `A_PlaySound` / `A_PlaySoundEx` (see the `A_PlaySound` doc for parameters and options).

## Contrast with A_Scream

Both functions play sounds in death states, but differ fundamentally:

- **`A_Scream`** plays the actor's `DeathSound` property if set (a per-actor configurable speech/howl), or nothing if `DeathSound` is empty. It checks the `+BOSS` flag for full-volume playback. Network behavior: implicit (no local gate).

- **`A_XScream`** plays a hardcoded gibbed sound (`*gibbed` or `misc/gibbed`), ignoring `DeathSound`. It checks the `player` pointer for sound selection, not flags. Multiplayer-aware: temporarily restores player pointers from the body queue. Network behavior: implicit (no local gate).

The choice between them depends on the death state: use `A_Scream` for death speeches, `A_XScream` for gibbed/explosive-death sound effects.

## Zandronum-specific: multiplayer player-pointer restoration

The "Player pointer handling" behavior described above — temporarily restoring a dead corpse's player pointer from the body queue via `G_TransferPlayerFromCorpse` so the gibbed sound uses the correct skin — is a Zandronum-only addition (marked `[AK]` in the Zandronum source, i.e. not inherited from upstream ZDoom). **UZDoom's `A_XScream` has no equivalent.** UZDoom's implementation (`Actor.A_XScream()`, defined natively in the ZScript stdlib's `actors/actor.zs`, not as a C++ `DEFINE_ACTION_FUNCTION`) is a one-line function that checks only the live `player` pointer and calls `A_StartSound` — there is no corpse-queue lookup or player-pointer restoration step at all. On UZDoom, a gibbed corpse whose player has already respawned plays `misc/gibbed` (falls to the non-player branch), not the departed player's skin-specific gibbed sound.

Sound selection (`*gibbed` vs `misc/gibbed`), channel (`CHAN_VOICE`), and attenuation (`ATTN_NORM`, the default) otherwise match between engines. UZDoom's call additionally passes `CHANF_NORUMBLE` (a controller-rumble suppression flag; Zandronum's `S_Sound` call has no flags parameter to carry an equivalent) — this doesn't change the audible sound, only controller haptics.

## Related

- **`A_Scream`** — plays the actor's configured `DeathSound` property.
- **`A_ScreamAndUnblock`** — composite that calls `A_Scream` followed by `A_NoBlocking`.
- **`A_PlaySound` / `A_PlaySoundEx`** — flexible sound-playing actions with channel/attenuation/volume control.
