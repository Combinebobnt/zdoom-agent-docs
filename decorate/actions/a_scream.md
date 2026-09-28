# `void A_Scream()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Scream` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_Scream&oldid=52947) + verified against the Zandronum source's `src/p_enemy.cpp:3329-3344`, `src/s_sound.cpp:1285-1294`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_Scream)` in `src/p_enemy.cpp` — defined on `AActor`, callable from any actor's state table.

Plays the actor's death sound (`DeathSound` property) on the voice channel. No parameters.

## Behavior

When called:

1. **Silent if no death sound**: If the actor has no `DeathSound` property set (or it's empty), the function returns without playing anything.

2. **Boss flag handling**: If the actor has the `+BOSS` flag set, the sound plays at full volume (`ATTN_NONE`). Otherwise, the sound plays with normal distance attenuation (`ATTN_NORM`).

3. **Channel and cutoff**: The sound is played on `CHAN_VOICE` (the voice channel). Any other sound on the voice channel from the same actor will be cut off by this one.

4. **Network behavior**: No Zandronum-specific network handling. The function body contains no client-mode early return (unlike `A_NoBlocking`, which does have one). `A_XScream` shares this same lack of a gate. On Zandronum it calls `S_Sound` without the `bSoundOnClient` argument, which defaults to `false` (`src/s_sound.h:229`), so a server-side call sends clients no sound command (`src/s_sound.cpp:1285-1294`). Clients hear the death sound because they run the action themselves when their own copy of the actor enters the state (`AActor::SetState` calls state actions on clients too, `src/p_mobj.cpp:586`).

## Wiki/engine divergence: FULLVOLDEATH claim (Zandronum only)

The ZDoom Wiki claims: "If the actor has either the BOSS or FULLVOLDEATH flags, the sound is heard at full volume regardless of distance."

**This does not hold in Zandronum.** The `+FULLVOLDEATH` flag exists (an `MF3` flag) and is honored in the engine's default death-sound mechanism (when a projectile explodes via `P_ExplodeMissile`), but `A_Scream` checks only the `+BOSS` flag. Setting `+FULLVOLDEATH` alone does not cause `A_Scream` to play at full volume.

## Engine-family divergence: FULLVOLDEATH handling

UZDoom's `A_Scream` (`Actor.A_Scream()` in the ZScript stdlib's `actors/actor.zs`) plays `DeathSound` at full volume (`ATTN_NONE`) when the actor has **either** `+BOSS` **or** `+FULLVOLDEATH` set — the condition is `bBoss || bFullvolDeath`. Zandronum's `A_Scream`, described above, checks only `+BOSS`. The `+FULLVOLDEATH` flag (`MF3_FULLVOLDEATH`) exists on both engines and is honored by both engines' default missile-explosion death-sound path independent of `A_Scream`, but only UZDoom's `A_Scream` itself also checks it directly.

One consequence: the ZDoom Wiki claim quoted above, which the "Wiki/engine divergence: FULLVOLDEATH claim (Zandronum only)" section says does not hold on Zandronum, **is accurate for UZDoom** — it diverges from the wiki only on Zandronum, not on UZDoom.

## Related

- **`A_ScreamAndUnblock`** — composite action that calls `A_Scream` followed by `A_NoBlocking`, commonly used in death states to play the death sound and then unblock the actor and drop items.
- **`A_XScream`** — plays a gibbed sound instead, hardcoded to `*gibbed` (player) or `misc/gibbed` (non-player), ignoring `DeathSound`.
- **`A_NoBlocking` / `A_Fall`** — unblocks the actor and spawns drop items; see its doc for network synchronization caveats.
