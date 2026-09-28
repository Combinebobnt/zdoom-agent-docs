# `void A_Look()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki A_Look (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Look&oldid=53797) + verified against the
Zandronum source's `src/p_enemy.cpp:1931-2058` (`DEFINE_ACTION_FUNCTION(AActor, A_Look)`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/p_enemy.cpp:1931` (`DEFINE_ACTION_FUNCTION(AActor, A_Look)`).

The default `Spawn`-state action for most monsters: idles until it detects a target (a player, or
whatever last made noise nearby), then transitions to the actor's `See` state. `A_LookEx` is the
parameterized version (search distance, field of view, wake state); `A_Look2` is a separate
Strife-derived variant used by Strife's peasants, acolytes and similar actors.

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
- **`CF_NOTARGET` early-out.** If the heard target (`LastHeard`, or the sector's `SoundTarget`
  under `COMPATF_SOUNDTARGET`/`MF_NOSECTOR`; only consulted when `TIDtoHate` is 0) is a player with
  the `CF_NOTARGET` cheat flag set, `A_Look` returns at once for that call. This skips everything
  after it, including the sight search for other players, so a monster that last heard a notarget
  player won't wake that tic even if another player is in view. `P_NoiseAlert` already ignores
  noise made by a notarget player, so this mostly arises when the cheat is turned on after the
  noise. UZDoom adds a second condition
  here; see the divergence section below.
- **`Thing_SetGoal`-on-spawn special case.** If the actor's map `special` is `Thing_SetGoal` with
  `args[0] == 0`, `A_Look` consumes the special on its first call (`self->special = 0`) and sets up
  a patrol goal from `args[1]` (PatrolPoint TID), `args[2]` (delay in seconds before chasing the
  goal) and `args[3]` (nonzero sets `CHASEGOAL`). `A_LookEx` carries the same special case;
  `A_Look2` does not.
- **Heard-an-ally path.** If the heard target is shootable and `self->IsFriend(targ)` is true
  (both carry `MF_FRIENDLY`, plus team checks in deathmatch/teamgame; e.g. a friendly monster that
  heard a player), `A_Look` doesn't target
  it. It runs the normal search (`P_LookForPlayers`, with `MF4_LOOKALLAROUND` respected; for a
  friendly actor that search looks for enemies first) and goes to `See` if that finds something.
  Otherwise it enters its `See` state anyway, without a new target, to wander looking for a fight.
  A monster with no `SeeState` calls `A_Wander` instead of erroring or staying idle.

## Engine-family divergence: CF_NOTARGET early-out also requires the FRIENDLY flag

Zandronum's heard-target early-out (the `CF_NOTARGET` bullet above) checks only
`targ->player->cheats & CF_NOTARGET`. UZDoom's `A_Look` (`src/playsim/p_enemy.cpp:1949`) checks
`(targ->player->cheats & CF_NOTARGET) || !(targ->flags & MF_FRIENDLY)` — an extra condition
requiring the candidate player to carry the `FRIENDLY` flag, added by an upstream GZDoom commit
("Monsters no longer search for players who are unfriendly.", 2017) and, after a 2024 attempt to
replace it with an `IsHostile()`-based check was reverted, still present in this raw-flag form.

In ordinary play this extra condition is a no-op: both engines' `PlayerPawn` base class carries
`+FRIENDLY` by default (Zandronum's `wadsrc/static/actors/shared/player.txt:14`; UZDoom's
`wadsrc/static/zscript/actors/player/player.zs:134`), so a normal player always satisfies it. It
only matters when something has stripped a player pawn's `FRIENDLY` flag (a DECORATE/ZScript flag
change, or a replacement `PlayerPawn` definition that omits it) — in that case UZDoom's `A_Look`
silently declines to react to that player via the `LastHeard`/`SoundTarget` path (returns without a
`See`-state transition that tic), where Zandronum's would still acquire them, gated only by
`CF_NOTARGET`.

This divergence is specific to `A_Look`'s own heard-target check — `P_LookForPlayers`'s
player-filtering (`isTargetablePlayer` on UZDoom; the inline loop body on Zandronum) already uses
an `IsFriend()`-based check on both engines that requires *both* the looking actor and the
candidate player to carry `MF_FRIENDLY` before excluding them, so that path is unaffected.

## Target acquisition gates based on actor flags

- **`MF_AMBUSH` flag gate.** This gate applies to the heard target only. A non-`AMBUSH` actor
  that hears a shootable non-ally takes it as `target` and enters `See` with no sight check at
  all. An `AMBUSH` actor also stores it as `target`, but only goes to `See` if `P_CheckSight`
  (with `SF_SEEPASTBLOCKEVERYTHING`) passes. If that fails, it falls through to the normal sight
  search (`P_LookForPlayers`) and stays in its current state unless that search finds someone.
  So an ambush monster uses noise only to pick whom to sight-check. A heard target in line of
  sight wakes it from any direction, while an unheard player must be inside its 180-degree field
  of view (unless it has `LOOKALLAROUND`) or within melee range.

## See also

- [Actor pointers](../../acs/concepts/actor-pointers.md) for the general `AAPTR_*`/pointer
  resolution model this function's own `self`/`targ` handling doesn't otherwise interact with.
