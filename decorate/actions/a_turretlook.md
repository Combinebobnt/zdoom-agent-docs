# `void A_TurretLook()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_TurretLook` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_TurretLook&oldid=36244) + verified against Zandronum source `src/g_strife/a_strifestuff.cpp:476-503`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/g_strife/a_strifestuff.cpp:476` (`DEFINE_ACTION_FUNCTION(AActor, A_TurretLook)`).

Sound-based target-acquisition action for monsters: wakes on detected sound from a shootable actor, ignoring visual contact. Unlike `A_Look2`, does not perform random state animation jumps when no target is found — intended as a simpler alternative for actors that don't require the reserved-state-offset animation convention. Strife-specific; documented in the ZDoom wiki and present on both engines — on UZDoom it is implemented as a ZScript `Actor` method in `wadsrc/static/zscript/actors/strife/klaxon.zs`, used by the `KlaxonWarningLight` and `CeilingTurret` Spawn states.

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

## Engine-family divergence: friendliness check

On UZDoom, the friendly-flag comparison described above is not a simple flag XOR — the ZScript
implementation calls the actor's full `IsFriend()` method instead, the same check `A_Look` uses.
This changes the acquisition outcome in two cases the Zandronum flag-XOR check treats differently:

- **Two non-`FRIENDLY` actors** (an ordinary hostile monster hearing another ordinary hostile
  monster): the Zandronum XOR is false (equal flags), so no acquisition occurs. On UZDoom,
  `IsFriend()` between two non-friendly actors also returns false, and the calling code negates
  it — so the acquisition condition is satisfied and the turret can acquire the other hostile
  monster as a target.
- **Two `FRIENDLY` actors on opposing teams, in deathmatch with teamplay enabled:** the Zandronum
  XOR is still false (equal flags), so no acquisition occurs regardless of team. On UZDoom,
  `IsFriend()` additionally checks team membership in this mode and returns false for
  opposing-team friendlies, so the negated condition again allows acquisition.

Friendly-vs-hostile pairs, and same-team friendly pairs outside deathmatch+teamplay, resolve the
same way on both engines. The bullet above noting this check "replaces the full `IsFriend()` check
used by `A_Look`" no longer holds on UZDoom, where `A_TurretLook` and `A_Look` use the same
friendliness check.

Because `target` is assigned before the `+AMBUSH` sight gate on both engines (see above), the
first case has a concrete consequence: a hostile `+AMBUSH` turret on UZDoom can end up with
`target` set to another hostile monster it merely heard and cannot see — a state a Zandronum
turret with the same setup never reaches.

Separately, the documented `+AMBUSH` sight check itself is only accurate for UZDoom, not as
written above: UZDoom's `CheckSight(target)` call passes no sight flags (equivalent to
`P_CheckSight`'s default, unflagged behavior), not the `SF_SEEPASTBLOCKEVERYTHING` variant this
file's "Target acquisition from sound" section describes.

## Comparison with `A_Look2`

- `A_Look2` performs **random state jumps** (approximately 11.7% and 15.6% of calls) to fixed offsets from `SpawnState` when no target is found; `A_TurretLook` does not animate or jump states on failure.
- `A_Look2` is server-authoritative (returns on client mode); `A_TurretLook` runs on both sides.
- `A_Look2` falls back to visual player-seeking for friendly targets; `A_TurretLook` does not (it checks only the `LastHeard` sound target).

## See also

- [A_Look](a_look.md) for the visual-line-of-sight variant with full server-side gating.
- [A_Look2](a_look2.md) for the Strife variant that includes random-animation state jumping.
- [A_LookEx](a_lookex.md) for parameterized target acquisition with customizable range and field-of-view.
