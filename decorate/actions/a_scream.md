# `void A_Scream()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Scream` (retrieved 2026-08-01, oldid=52947) + verified against the Zandronum source's `src/p_enemy.cpp:3329-3344`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_Scream)` in `src/p_enemy.cpp` — defined on `AActor`, callable from any actor's state table.

Plays the actor's death sound (`DeathSound` property) on the voice channel. No parameters.

## Behavior

When called:

1. **Silent if no death sound**: If the actor has no `DeathSound` property set (or it's empty), the function returns without playing anything.

2. **Boss flag handling**: If the actor has the `+BOSS` flag set, the sound plays at full volume (`ATTN_NONE`). Otherwise, the sound plays with normal distance attenuation (`ATTN_NORM`).

3. **Channel and cutoff**: The sound is played on `CHAN_VOICE` (the voice channel). Any other sound on the voice channel from the same actor will be cut off by this one.

4. **Network behavior**: No Zandronum-specific network handling — the function body contains no client-mode early return or replication gates (unlike `A_NoBlocking`, which does have one). `A_XScream` shares this same lack of a gate. The sound propagates server-side; client-side behavior depends on the netcode's sound-replication layer.

## Wiki divergence

The ZDoom Wiki claims: "If the actor has either the BOSS or FULLVOLDEATH flags, the sound is heard at full volume regardless of distance."

**This does not hold in Zandronum.** The `+FULLVOLDEATH` flag exists (an `MF3` flag) and is honored in the engine's default death-sound mechanism (when a projectile explodes via `P_ExplodeMissile`), but `A_Scream` checks only the `+BOSS` flag. Setting `+FULLVOLDEATH` alone does not cause `A_Scream` to play at full volume.

## Related

- **`A_ScreamAndUnblock`** — composite action that calls `A_Scream` followed by `A_NoBlocking`, commonly used in death states to play the death sound and then unblock the actor and drop items.
- **`A_XScream`** — plays a gibbed sound instead, hardcoded to `*gibbed` (player) or `misc/gibbed` (non-player), ignoring `DeathSound`.
- **`A_NoBlocking` / `A_Fall`** — unblocks the actor and spawns drop items; see its doc for network synchronization caveats.
