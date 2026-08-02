# `void A_TurretLook()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_TurretLook` (retrieved 2026-08-01, oldid=36244) + verified against Zandronum source `src/g_strife/a_strifestuff.cpp:476-503`.
**Bucket:** `src/g_strife/a_strifestuff.cpp:476` (`DEFINE_ACTION_FUNCTION(AActor, A_TurretLook)`).

Sound-based target-acquisition action for monsters: wakes on detected sound from a shootable actor, ignoring visual contact. Unlike `A_Look2`, does not perform random state animation jumps when no target is found — intended as a simpler alternative for actors that don't require the reserved-state-offset animation convention. Strife-specific; documented in the ZDoom wiki but **does not exist in UZDoom/GZDoom-family**.

## Target acquisition from sound

Acquires a target from `self->LastHeard` (the last actor to make noise near this actor):

- **Target must exist, be alive, and shootable** (`MF_SHOOTABLE` flag).
- **Friendly-flag XOR check:** The target's `MF_FRIENDLY` flag must differ from the calling actor's — hostile actors trigger this function on enemy sounds but not ally sounds, and vice versa for friendly actors. This replaces the full `IsFriend()` check used by `A_Look`.
- **`+AMBUSH` flag gate:** If the calling actor has the `AMBUSH` flag set, a line-of-sight check via `P_CheckSight(... SF_SEEPASTBLOCKEVERYTHING)` is required before waking, even though this is a sound-triggered action. Without line of sight, the function returns and the actor remains idle. Actors without `AMBUSH` wake immediately.

On successful acquisition:
- Sets `self->target` to the detected actor.
- **Clears `self->LastHeard` to NULL** — consecutive calls do not re-acquire the same actor.
- Sets `self->threshold` to 10 (monster combat timeout).
- Plays the actor's `SeeSound` (if non-zero) on the voice channel with normal attenuation.
- Transitions to `self->SeeState`.

## Early-return conditions

- **`MF5_INCONVERSATION` early-out:** If the calling actor has the `INCONVERSATION` flag set, the function returns immediately without any acquisition logic.
- **No target found:** If `LastHeard` is NULL or fails the acquisition gates, the function returns without changing state or playing sounds.

## `threshold` and state initialization

- `self->threshold` is set to 0 unconditionally on every call — clearing any in-progress melee timeout.
- `self->threshold` is set to 10 when a target is successfully acquired (conflict avoidance in multiple-hit melee sequences).

## Zandronum-specific: not server-authoritative in multiplayer

Unlike `A_Look` and `A_Look2`, **`A_TurretLook` has no `NETWORK_InClientMode()` guard** and runs its full target-acquisition and sound-playing logic on both server and client without explicit netcode synchronization. State changes via `SetState()` are applied locally; there is no `SERVERCOMMANDS_SetThingState` broadcast. This means clients may acquire targets or play sounds independent of the server in edge cases where `LastHeard` replication lags or diverges, creating a potential server/client perception gap. For vanilla Strife actors, this divergence is typically invisible (both sides waking on the same sound in short order), but custom monsters using `A_TurretLook` on a non-clientside actor should account for this.

## Comparison with `A_Look2`

- `A_Look2` performs **random state jumps** (approximately 11.7% and 15.6% of calls) to fixed offsets from `SpawnState` when no target is found; `A_TurretLook` does not animate or jump states on failure.
- `A_Look2` is server-authoritative (returns on client mode); `A_TurretLook` runs on both sides.
- `A_Look2` falls back to visual player-seeking for friendly targets; `A_TurretLook` does not (it checks only the `LastHeard` sound target).

## See also

- [A_Look](a_look.md) for the visual-line-of-sight variant with full server-side gating.
- [A_Look2](a_look2.md) for the Strife variant that includes random-animation state jumping.
- [A_LookEx](a_lookex.md) for parameterized target acquisition with customizable range and field-of-view.
