# `void A_XScream()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_XScream` (retrieved 2026-08-01, oldid=49049) + verified against the Zandronum source's `src/p_enemy.cpp:3346-3362`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_XScream)` in `src/p_enemy.cpp` — defined on `AActor`, callable from any actor's state table.

Plays a hardcoded gibbed sound on the voice channel. The sound is `*gibbed` (the player's skin-specific gibbed sound) if the actor has a player pointer; otherwise `misc/gibbed` (the default non-player gibbed sound). No parameters.

Unlike `A_Scream`, which plays the actor's `DeathSound` property, `A_XScream` always plays one of two hardcoded sounds regardless of the actor's sound configuration. This is the correct choice for XDeath/gibbed states where you want a consistent "splat" sound, not a death speech.

## Behavior

When called:

1. **Player pointer handling**: In multiplayer, if the actor is a dead corpse and its player has respawned, `A_XScream` temporarily restores the player pointer from the body queue (via `G_TransferPlayerFromCorpse`) so the gibbed sound plays with the correct player's skin sound, then restores it back to null. In single-player or if the player is not found in the queue, this is a no-op.

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

## Related

- **`A_Scream`** — plays the actor's configured `DeathSound` property.
- **`A_ScreamAndUnblock`** — composite that calls `A_Scream` followed by `A_NoBlocking`.
- **`A_PlaySound` / `A_PlaySoundEx`** — flexible sound-playing actions with channel/attenuation/volume control.
