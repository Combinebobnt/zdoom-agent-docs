# `A_Stop`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Stop` (retrieved 2026-08-01, oldid=40682) + verified against the
Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3741-3749` and `wadsrc/static/actors/actor.txt`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_Stop)`, `src/thingdef/thingdef_codeptr.cpp:3741`.

Stops all movement by zeroing the actor's velocity components (`velx`, `vely`, `velz`).

For players, if the actor is currently in its `See` state sequence, transitions to the `Spawn`
state; otherwise does nothing. This is more restrictive than the wiki's description of
transitioning to an "idle state if it exists, otherwise spawn state" — the actual implementation
only conditionally transitions from `See` state and does not check for a separate `Idle` label.

## Remarks

- For non-player actors, this function only zeros velocity and returns.
- For players, the `Spawn` state transition (when in `See` state) happens via `PlayIdle()`, which
  wraps network synchronization on servers (`SERVERCOMMANDS_SetPlayerState`).
- Player velocity (`player->velx`, `player->vely`) is zeroed independently of actor velocity — the
  actor's `velz` component is zeroed, but the player struct carries only `velx` and `vely`.
- Unlike the wiki's reference to "acceleration," this function does not modify any `accel_*`
  fields; it only affects velocity (`vel_*`). The actor's `Speed` property (if set) is untouched.
- **Zandronum fork note:** The player check includes a commented-out guard against
  `CF_PREDICTING` (`/*&& !(self->player->cheats & CF_PREDICTING)*/`), with a code comment
  indicating Zandronum handles netcode prediction differently than upstream ZDoom.

## See also

- `PlayIdle()` (`p_user.cpp:1566`) — the player-state-transition helper called internally.
- `A_StopSound` / `A_StopSoundEx` — unrelated sound-channel functions despite the name prefix.
