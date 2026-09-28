# `void A_Look2()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Look2` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Look2&oldid=35060) + verified against Zandronum source `src/p_enemy.cpp:2351-2423`, `src/p_sight.cpp:262-287` (`SF_SEEPASTBLOCKEVERYTHING`), `src/p_mobj.cpp:502-603` (`SetState`), `src/cl_main.cpp:5722-5761` (client `SetThingFrame`) and the stock Strife actors in `wadsrc/static/actors/strife/`. Also present in UZDoom 4.15pre (`src/playsim/p_enemy.cpp:2306`) with identical target-acquisition logic but without the Zandronum network-specific divergence documented below.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/p_enemy.cpp:2351` (`DEFINE_ACTION_FUNCTION(AActor, A_Look2)`).

Sound-based target-acquisition action for monsters: wakes on a sound heard from a shootable actor (`LastHeard`). If no target is acquired, it randomly moves the actor to one of three fixed states after its `SpawnState` (see below). Used by the stock Strife humans (Peasant, Rebel, Acolyte, Templar, Macil, merchants).

## Target acquisition

`threshold` is reset to 0 on every call. Then, if `self->LastHeard` is non-null, alive (`health > 0`; a dead `LastHeard` is treated as `NULL`) and `+SHOOTABLE`:

- **If the heard actor is hostile** (its `+FRIENDLY` flag differs from this actor's, or the map sets `LEVEL_NOALLIES`): sets `self->target` to it, sets `threshold` to 10 and jumps to `SeeState`. If `+AMBUSH` is set, it first needs line of sight to the heard actor, checked with `SF_SEEPASTBLOCKEVERYTHING`; if sight fails it falls through to the idle branch below. That flag does not let sight pass closed doors or solid walls. It only lets sight cross a block-everything line that is impact-activated and runs `ACS_Execute`/`ACS_ExecuteAlways` on the current map (a scripted breakable line such as Strife glass).
- **If the heard actor is on the same side**: runs the regular `P_LookForPlayers` search (the one `A_Look` uses), all-around if `+LOOKALLAROUND` is set. That search picks its own target and needs sight in most modes. This contradicts the wiki's claim that A_Look2 "only reacts to sound": `LastHeard` only gates entry to this branch. If the search succeeds, jumps to `SeeState` and sets `+INCOMBAT`; `threshold` stays 0. If it fails, falls through to the idle branch.

**Early-outs:** If `+INCONVERSATION` is set, the function returns immediately with no other effect. On Zandronum it also returns immediately on clients; the whole action runs on the server.

## State animation when no target found

When no target is acquired (the `nosee:` fallback), two independent rolls run:

- **30/256 of calls (about 11.7%):** `SetState` to `SpawnState + 1` or `SpawnState + 2` with equal probability, chosen by `(pr_look2() & 1)`.
- **Then, if `+STANDSTILL` is not set, 40/256 of calls (about 15.6%):** `SetState` to `SpawnState + 3`. If `+STANDSTILL` is set, this roll is skipped and no RNG value is consumed.

Both can fire in one call. Each `SetState` runs the entered state's action immediately (and chains through any 0-tic states), so the `+1`/`+2` state's action runs and then the `+3` state's action runs, all in the same tic. The actor ends in the `+3` state.

## Wiki/engine divergence: "three states after this function call"

The wiki says "the three states after this function call are reserved". The code actually uses fixed offsets from the actor's `SpawnState` (the first state under `Spawn:`), not from the state that called A_Look2. The two only coincide when A_Look2 is on the first `Spawn:` state, as in every stock actor.

Offsets count states, not lines: `Loop`, `Wait`, `Goto` and labels are not states. So `SpawnState + 3` is the third real state after the first `Spawn:` state, wherever it sits in the actor's state list. The stock actors use this in two ways:

1. **Rebel, Templar, Macil, Acolyte, merchants:** `Spawn:` holds the A_Look2 state, then two unlabeled single-state idle blocks each ending in `Loop` (back to `Spawn:`), then a longer unlabeled sequence. So `+1`/`+2` are brief idle poses. `+3` starts an `A_Wander` sequence, except for merchants, where it is a longer idle animation.
2. **Peasant:** `Spawn:` is only `PEAS A 10 A_Look2` / `Loop`. `+1`, `+2` and `+3` are the first three states of its `See:` block (`A_Wander` frames), so an idle peasant randomly starts wandering. This is deliberate, not a mistake.

If you write your own A_Look2 user, put the three states you want right after the first `Spawn:` state. Otherwise the offsets land in whichever states happen to follow in the actor's state list.

## Zandronum-specific: multiple calls to SetState and RNG frame desync

On acquiring a target, the server sends clients `SetThingState` (`STATE_SEE`) before its own `SetState(SeeState)`. In the `nosee:` branch it sends `SetThingFrame` with the new state before each `SetState`, and the client runs that state's action on receipt.

For the first idle roll (lines 2411 and 2413), the frame sent to clients and the frame the server sets each call `pr_look2()` separately. They are two independent RNG results, so client and server pick different states (`+1` vs `+2`) about half the time this branch runs. If the `+3` roll also fires, a second `SetThingFrame` puts both sides on `SpawnState + 3`. The server stays authoritative, so the mismatch only affects what clients show.

## See also

- [A_Look](a_look.md) for the visual-line-of-sight variant.
- `A_TurretLook` (Strife-specific action) if you don't need idiomatic state animation — an alternative sound-detection action that doesn't require reserved animation states.
- `STANDSTILL` actor flag in [inventory/actor-flags.md](../inventory/actor-flags.md) for the flag check in the third-state branch.
