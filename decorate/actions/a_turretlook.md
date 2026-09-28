# `void A_TurretLook()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_TurretLook` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_TurretLook&oldid=36244) + verified against Zandronum source `src/g_strife/a_strifestuff.cpp:476-503`, `src/s_sound.cpp:1285-1294`, `src/p_enemy.cpp:2351-2423`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/g_strife/a_strifestuff.cpp:476` (`DEFINE_ACTION_FUNCTION(AActor, A_TurretLook)`).

Sound-based target-acquisition action for monsters: wakes on detected sound from a shootable actor and never scans for players by sight (a `+AMBUSH` caller still needs line of sight to the heard actor, see below). Unlike `A_Look2`, does not perform random state animation jumps when no target is found — intended as a simpler alternative for actors that don't require the reserved-state-offset animation convention. Strife-specific; documented in the ZDoom wiki and present on both engines — on UZDoom it is implemented as a ZScript `Actor` method in `wadsrc/static/zscript/actors/strife/klaxon.zs`, used by the `KlaxonWarningLight` and `CeilingTurret` Spawn states.

## Target acquisition from sound

Acquires a target from `self->LastHeard` (the last actor to make noise near this actor):

- **Target must exist, be alive, and shootable** (`MF_SHOOTABLE` flag).
- **Friendly-flag XOR check:** The target's `MF_FRIENDLY` flag must differ from the calling actor's — hostile actors trigger this function on enemy sounds but not ally sounds, and vice versa for friendly actors. This replaces the full `IsFriend()` check used by `A_Look`.
- **`+AMBUSH` flag gate:** Once the three checks above pass, `self->target` is set to the heard actor. Only then, if the calling actor has the `AMBUSH` flag set, is line of sight required: a plain `P_CheckSight(self, target)` with no sight flags, so `ML_BLOCKEVERYTHING` lines block it (unlike `A_Look2`, which passes `SF_SEEPASTBLOCKEVERYTHING`). Without line of sight the function returns and the actor stays in its current state, but `target` stays set and `LastHeard` is not cleared, so the next call retries the same actor. Actors without `AMBUSH` wake immediately. Both vanilla users (`KlaxonWarningLight`, `CeilingTurret`) are `+AMBUSH`.

On successful acquisition, in this order:
- Plays the actor's `SeeSound` (if non-zero) on the voice channel with normal attenuation.
- **Clears `self->LastHeard` to NULL**, so consecutive calls do not re-acquire the same actor.
- Sets `self->threshold` to 10 (the counter that keeps a monster chasing its current target).
- Transitions to `self->SeeState`.

## Early-return conditions

- **`MF5_INCONVERSATION` early-out:** If the calling actor has the `INCONVERSATION` flag set, the function returns immediately without any acquisition logic.
- **No target found:** If `LastHeard` is NULL or fails the health, shootable or friendliness checks, the function returns without changing state or playing sounds. A `+AMBUSH` sight failure also returns this way, but after `target` was already set (see above).

## `threshold` and state initialization

- `self->threshold` is set to 0 on every call that gets past the `INCONVERSATION` early-out, before `LastHeard` is examined. This clears the counter that makes a monster keep chasing its current target.
- `self->threshold` is set to 10 when a target is successfully acquired.

## Zandronum-specific: not server-authoritative in multiplayer

Unlike `A_Look` and `A_Look2`, **`A_TurretLook` has no `NETWORK_InClientMode()` guard** and runs its full target-acquisition logic on both server and client. Nothing it does is sent to clients: `SetState(SeeState)` is local with no `SERVERCOMMANDS_SetThingState` call, and the `SeeSound` uses `S_Sound` without its inform-clients argument, so no `SERVERCOMMANDS_SoundActor` goes out either. `LastHeard` itself is not part of the network protocol; each side fills it from its own noise alerts. A client therefore wakes the actor (and plays its `SeeSound`) only if its own `LastHeard` passes the checks, which can differ from the server's result.

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

The `+AMBUSH` sight check itself is the same on both engines: an unflagged sight check
(Zandronum `P_CheckSight(self, target)`, UZDoom `CheckSight(target)`), not `SF_SEEPASTBLOCKEVERYTHING`.

## Comparison with `A_Look2`

- `A_Look2` performs **random state jumps** (approximately 11.7% and 15.6% of calls) to fixed offsets from `SpawnState` when no target is found; `A_TurretLook` does not animate or jump states on failure.
- `A_Look2` is server-authoritative (returns on client mode); `A_TurretLook` runs on both sides.
- `A_Look2` falls back to visual player-seeking when the heard actor is on the caller's own side; `A_TurretLook` does not (it checks only the `LastHeard` sound target).
- `A_Look2`'s `+AMBUSH` sight check passes `SF_SEEPASTBLOCKEVERYTHING` and runs before `target` is set; `A_TurretLook`'s is unflagged and runs after.

## See also

- [A_Look](a_look.md) for the visual-line-of-sight variant with full server-side gating.
- [A_Look2](a_look2.md) for the Strife variant that includes random-animation state jumping.
- [A_LookEx](a_lookex.md) for parameterized target acquisition with customizable range and field-of-view.
