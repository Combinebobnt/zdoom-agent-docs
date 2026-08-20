# `void A_LoopActiveSound()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_LoopActiveSound` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_LoopActiveSound&oldid=49051) + verified against the Zandronum source's `src/g_strife/a_strifestuff.cpp:639-645`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_LoopActiveSound)` — callable from any actor's state table.

Plays the actor's `ActiveSound` property, if defined, as a looped sound that runs continuously until explicitly stopped. The looped sound is tied to the `CHAN_VOICE` channel, which is also used for monster pain/death sounds, activation sounds, and other voice-like effects.

## Behavior

When called, the function:

1. Checks whether the actor has an `ActiveSound` defined (not zero).
2. Checks whether any sound is already playing on the `CHAN_VOICE` channel for this actor. If a sound is already playing — **any sound**, not just the `ActiveSound` — the function returns without starting the loop.
3. If both conditions are met, plays the `ActiveSound` on `CHAN_VOICE` with the `CHAN_LOOP` flag set, causing it to restart seamlessly when it finishes.

Because of the second check, an `ActiveSound` loop will not restart if another sound (such as a pain sound, death sound, or a manually-triggered sound via `A_PlaySound`) is playing on that channel. This means the loop can be interrupted by other game events but will not double-up or conflict.

## Stopping the loop

The looped sound can be stopped by calling `A_StopSound()` with no parameters (defaults to stopping `CHAN_VOICE`). Alternatively, any other sound triggered on `CHAN_VOICE` will implicitly displace the loop.

## Relation to other functions

- **`A_FLoopActiveSound`** — a separate, distinct function (not a variant) that plays the `ActiveSound` every 8 tics without the `CHAN_LOOP` flag; creates a repeating effect rather than a seamless loop. This is useful for periodic activation sounds rather than continuous ambient ones.
- **`A_PlaySound`** — a general-purpose alternative for looping arbitrary sounds (not just `ActiveSound`) with explicit volume/attenuation control; recommended for new code when more flexibility is needed.

## Zandronum-specific: multiplayer loop replication

In multiplayer, looping sounds are replicated via the server's internal looping-channels list (`g_LoopingChannelList`), allowing late-joining clients to inherit active loops from actors already on the map.

## Engine-family divergence: A_StartSound availability

The ZDoom Wiki notes that this function has been "superseded by `A_StartSound`" and recommends using the newer function for "maximum flexibility." **`A_StartSound` does not exist in Zandronum** — it is a GZDoom/UZDoom feature added after Zandronum's codebase diverged. `A_LoopActiveSound` remains the only option on Zandronum for looping an actor's `ActiveSound` property. On UZDoom, `A_LoopActiveSound` itself is now just a thin ZScript wrapper around `A_StartSound` — see the next section for how that changes its channel-busy check.

## Engine-family divergence: what counts as "busy" before restarting the loop

On UZDoom, `A_LoopActiveSound` is a ZScript method (`wadsrc/static/zscript/actors/strife/strifefunctions.zs`) that calls `A_StartSound(ActiveSound, CHAN_VOICE, CHANF_LOOPING)`. `CHANF_LOOPING` is a convenience alias for `CHANF_LOOP | CHANF_NOSTOP`. The `CHANF_NOSTOP` flag makes the underlying sound-engine "already playing" check (`SoundEngine::IsSourcePlayingSomething`) skip (re)starting the sound only when *the same sound ID* (`ActiveSound` itself) is already playing on `CHAN_VOICE` for this actor — the sound ID is passed through as an exact-match filter, not a wildcard. A *different* sound already playing on that channel (a pain sound, a death sound, a manually-triggered `A_PlaySound`) does **not** block the call: UZDoom starts the `ActiveSound` loop anyway, cutting off whatever was playing.

This is the opposite of the documented Zandronum behavior above. Zandronum's `A_LoopActiveSound` calls its channel-busy check (`S_IsActorPlayingSomething`) with a wildcard sound ID (`-1`), so *any* sound already playing on `CHAN_VOICE` — not just a previous instance of `ActiveSound` — blocks the loop from (re)starting; other channel activity is never interrupted. On UZDoom, only an already-looping copy of the same `ActiveSound` blocks a restart, so a mod relying on the Zandronum "won't double-up or conflict" guarantee documented above will instead see `A_LoopActiveSound` interrupt pain/death/other `CHAN_VOICE` sounds on UZDoom.

## Weapons and inventory items

Although this function is technically callable from a weapon or `CustomInventory` state, it will not produce the expected result. In weapon/item states, the `self` pointer is redirected to the owning player or receiving actor rather than the weapon/item itself. Consequently, `A_LoopActiveSound` reads and plays the owner's `ActiveSound` (if defined), not the weapon's — which typically means no sound, since `ActiveSound` is primarily defined on monsters. This is why the wiki notes it "doesn't work on weapons." For weapon/item audio, use `A_PlaySound` instead with an explicit sound path.
