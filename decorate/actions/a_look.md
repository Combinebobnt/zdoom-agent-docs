# `void A_Look()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki A_Look (retrieved 2026-07-31, oldid=53797) + verified against the
Zandronum source's `src/p_enemy.cpp:1931-2058` (`DEFINE_ACTION_FUNCTION(AActor, A_Look)`).
**Bucket:** `src/p_enemy.cpp:1931` (`DEFINE_ACTION_FUNCTION(AActor, A_Look)`).

The default `Spawn`-state action for most monsters: idles until it detects a target (a player, or
whatever last made noise nearby), then transitions to the actor's `See` state (or wanders, if it
has one and no target is found yet). This function has been extended by `A_LookEx` (which adds
parameterization for search distance and field-of-view control) and `A_Look2` — in new code,
consider using those for maximum flexibility.

## Zandronum-specific: server-authoritative, but not a pure no-op on clients

**This is handled server-side and returns almost immediately in client mode** — before any of the
target-finding logic runs, `A_Look` checks `NETWORK_InClientMode()` and, if true, does exactly one
thing (update `visdir` for a stealth monster, see below) and returns. On a listen/dedicated server,
or in a single-player game, the function runs its full target-acquisition logic every call, exactly
as in vanilla ZDoom-family behavior.

This is **not** a blanket "clients skip this function" caveat, though — the one line that *does*
run on both server and client is the Andy Baker stealth-monster `visdir` update
(`self->visdir = -1` when `MF_STEALTH` is set), duplicated in both the early client-mode branch and
the normal server-side path further down. A doc or review that assumes "client mode = full no-op"
would miss that stealth-monster facing state is intentionally still touched on clients.

## Early-return conditions before target acquisition

- **`MF5_INCONVERSATION` early-out.** If the actor has the `INCONVERSATION` flag set, `A_Look`
  returns immediately before any target acquisition logic — the actor won't look for or switch
  to targets while in a conversation state.
- **`CF_NOTARGET` early-out.** If the candidate target is a player with the `CF_NOTARGET` cheat
  flag set, `A_Look` returns without setting a `See` state — the monster stays idle against a
  noclip-style notarget player, same as base ZDoom.
- **`Thing_SetGoal`-on-spawn special case.** If the actor's map `special` is `Thing_SetGoal` with
  `args[0] == 0`, `A_Look` consumes the special on its first call (`self->special = 0`) and sets up
  a patrol goal from `args[1]`/`args[2]`/`args[3]` — a mapper-facing linedef-special convention
  that only fires from this one action function, not documented anywhere else in this fork's
  action-function set.
- **Friendly-monster path calls `P_LookForPlayers`, not the hostile path.** `self->IsFriend(targ)`
  branches to player-seeking (with `MF4_LOOKALLAROUND` respected) before falling back to
  `A_Wander` — a friendly monster with no `SeeState` at all silently calls `A_Wander` as a
  substitute rather than erroring or staying idle.

## Target acquisition gates based on actor flags

- **`MF_AMBUSH` flag gate.** If the actor has the `AMBUSH` flag set, even after acquiring a
  target, `A_Look` requires a direct line of sight (via `P_CheckSight` with
  `SF_SEEPASTBLOCKEVERYTHING` flags) before entering the `See` state — without it, the actor
  remains idle despite having a target. This allows ambush-style monsters to wait for the player
  to come into view before attacking. Actors without `AMBUSH` enter `See` immediately when a
  valid hostile target is found.

## See also

- [Actor pointers](../../acs/concepts/actor-pointers.md) for the general `AAPTR_*`/pointer
  resolution model this function's own `self`/`targ` handling doesn't otherwise interact with.
