# `A_Stop`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_Stop` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_Stop&oldid=40682) + verified against the
Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3741-3749` and `wadsrc/static/actors/actor.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

## Zandronum-specific: PlayIdle networking and prediction handling

UZDoom implements `A_Stop` and its shared `CheckStopped()` helper entirely in ZScript
(`wadsrc/static/zscript/actors/actions.zs:39-44` and `:23-31`) rather than as a native/C++ action
function the way Zandronum does — an implementation-location change only, not a behavioral one:
the core zeroing and `See`-to-`Spawn` transition described above holds identically on both
engines. Two Zandronum-only details in the material above don't hold for UZDoom, though:

- **Network synchronization.** The "Remarks" section states `PlayIdle()` "wraps network
  synchronization on servers (`SERVERCOMMANDS_SetPlayerState`)" — true only for Zandronum's
  `APlayerPawn::PlayIdle` (`src/p_user.cpp:1566`), which checks `NETWORK_GetState() ==
  NETSTATE_SERVER` before transitioning state and broadcasting a `SERVERCOMMANDS_SetPlayerState`
  update. UZDoom's `PlayIdle()` (`wadsrc/static/zscript/actors/player/player.zs:257`) has no such
  gate — it evaluates the same `See`-state condition and transitions directly to `SpawnState`,
  with no client/server distinction or replication call anywhere in the function. UZDoom's source
  tree has no `SERVERCOMMANDS_*`-equivalent mechanism at all (zero occurrences tree-wide),
  consistent with UZDoom having no client/server authority split anywhere.
- **CF_PREDICTING guard.** The "Zandronum fork note" above describes this engine's
  `CF_PREDICTING` check as commented out (dead code) — the player-state sync always runs on
  Zandronum regardless of prediction state. UZDoom's equivalent guard, inside the shared
  `CheckStopped()` helper (also called by `A_ScaleVelocity`), is live: `!(player.cheats &
  CF_PREDICTING)` actually gates execution there. During a locally-predicted tic (client-side
  movement prediction ahead of server confirmation), UZDoom's `A_Stop` still unconditionally
  zeroes the calling actor's own `Vel`, but skips the `PlayIdle()` transition and the
  `player.Vel` zeroing.

## See also

- `PlayIdle()` (`p_user.cpp:1566`) — the player-state-transition helper called internally.
- `A_StopSound` / `A_StopSoundEx` — unrelated sound-channel functions despite the name prefix.
