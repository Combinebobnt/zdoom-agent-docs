# `A_CheckSight`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_CheckSight` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_CheckSight&oldid=45585) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3286-3329`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in `src/thingdef/thingdef_codeptr.cpp`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; see [LICENSE](../../LICENSE) §3 for Zandronum's license terms.

Jumps to a target state if no player can see the calling actor. Unlike `A_JumpIf*` conditional jumps, this is a **sight-based check** that polls all active players' line-of-sight to the actor, accounting for player cameras and co-op spy.

## Signature

```decorate
state A_CheckSight (state target)
state A_CheckSight (int offset)
```

## Parameters

**`target`** (state label or frame offset)  
The jump destination. If a state label (e.g., `"Death"`, `"DeathFade"`), the name is resolved in the calling actor's derived class's state table (virtual resolution). If an integer, the offset counts **frames in the current state line**, not instruction lines.

## Behavior

- Checks whether **any** non-spectating player can see the calling actor from their viewpoint.
- If **at least one player has line of sight** to the actor, returns without jumping. Execution continues to the next action or frame in the current state.
- If **no player has line of sight** to the actor, performs the jump to the target state.
- The sight check uses `P_CheckSight(..., SF_IGNOREVISIBILITY)`, which means **the player does not have to be facing the actor** — only a potential line of sight must exist. If a player is positioned where they *could* see the actor if they turned, the check returns true.
- The jump does not set any result value for inventory-pickup state chains (`ACTION_SET_RESULT(false)` is always called, per the source).

## Network considerations

```c
DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CheckSight)
{
	ACTION_PARAM_START(1);
	ACTION_PARAM_STATE(jump, 0);

	ACTION_SET_RESULT(false);	// Jumps should never set the result for inventory state chains!

	// [BB] If this is a CLIENTSIDEONLY actor, a client only checks whether the consoleplayer sees it.
	// [Dusk] If the actor does NOT have CLIENTSIDEONLY, the client does nothing.
	if ( NETWORK_InClientMode() )
	{
		if ( !( self->NetworkFlags & NETFL_CLIENTSIDEONLY ) ||
			P_CheckSight( players[consoleplayer].camera, self, SF_IGNOREVISIBILITY ) )
		{
			return;
		}
	}
	else
	{
		for (int i = 0; i < MAXPLAYERS; i++) 
		{
			if (playeringame[i])
			{
				// [TP] Spectators do not count.
				if (players[i].bSpectating)
					continue;

				// Always check sight from each player.
				if (P_CheckSight(players[i].mo, self, SF_IGNOREVISIBILITY))
				{
					return;
				}
				// If a player is viewing from a non-player, then check that too.
				if (players[i].camera != NULL && players[i].camera->player == NULL &&
					P_CheckSight(players[i].camera, self, SF_IGNOREVISIBILITY))
				{
					return;
				}
			}
		}
	}

	ACTION_JUMP(jump, CLIENTUPDATE_FRAME);	// [BB] Inform the clients about the jump.
}
```

On network-authoritative actors (those without the `NETFL_CLIENTSIDEONLY` flag), the client-mode check returns *before* checking sight, so a client performs **no sight tests** for these actors at all — it only receives the server's already-decided outcome via the `CLIENTUPDATE_FRAME` state-change flag.

For `+CLIENTSIDEONLY` actors, the client does check sight independently (using its own player's camera or pawn), and the server checks all active players. Since the client's world state and camera position may lag, there is a potential for divergence: a `+CLIENTSIDEONLY` actor might jump on one machine and not the other if the client's knowledge of actor position or camera state differs from the server's. This is acceptable because `NETFL_CLIENTSIDEONLY` is documented as "only spawned by the clients... don't affect the game in any way (visuals aside)" — each machine owns and simulates its own private copy of the actor with no cross-machine consistency requirement.

## Engine-family divergence: network execution model

The client/server authority split described above (the `NETWORK_InClientMode()` branch, the `NETFL_CLIENTSIDEONLY` special case, and the `CLIENTUPDATE_FRAME` cross-machine sync flag) is specific to Zandronum's netcode. UZDoom has no equivalent concept anywhere: a search of UZDoom's entire source tree turns up zero occurrences of `NETWORK_InClientMode`/`SERVERCOMMANDS_*`. UZDoom's `A_CheckSight` (`wadsrc/static/zscript/actors/checks.zs:151`, calling the native `CheckIfSeen()` in `src/playsim/p_actionfunctions.cpp:1729`) contains no client-mode branch, no server-authoritative early return, and no cross-machine state-sync flag — it is a single plain loop over all in-game players, evaluated identically regardless of network role. The entire "Network considerations" topology described above, including the source excerpt, does not apply to UZDoom.

**Player cameras and co-op spy:** The sight check looks at both `players[i].mo` (each player's pawn) and `players[i].camera` if it is non-NULL and not a player pawn itself (e.g., a camera actor spawned by `Chasecam`/`Spectate` or other camera-switching mechanism). This means the check accounts for actors being viewed through free-floating cameras and co-op spy viewpoints.

**Spectators excluded:** Spectating players are skipped (the `bSpectating` check), so they do not block a jump.

## Engine-family divergence: spectator exclusion

UZDoom's implementation (`CheckIfSeen()`, `src/playsim/p_actionfunctions.cpp:1729`) has **no spectator exclusion at all**. It loops over every in-game player (`Level->PlayerInGame(i)`) and checks sight from each one's pawn and camera, with no equivalent of Zandronum's `bSpectating` check.

This isn't a narrower check that happens to produce the same result — the concept itself is gone: `player_t` and the rest of the UZDoom source tree have no `bSpectating` field or "spectating" notion anywhere. The only trace of it is a comment block in `src/playsim/p_acs.cpp` listing `PlayerIsSpectator` as one of "Zandronum's [ACS special functions] - these must be skipped" when UZDoom's ACS interpreter reaches the corresponding function-index range — i.e. UZDoom explicitly does not implement it, rather than having ported it under a different name.

Practical effect: on UZDoom, a player who would be "spectating" on Zandronum (freely observing without being part of the round) still counts as a full player for this check, and their line of sight to the actor **will** suppress the jump. On Zandronum, such a player is skipped and cannot block the jump. Mods relying on `A_CheckSight` to detect "no player is watching" for despawn/optimization purposes (see Examples below) should account for this: on UZDoom there is no in-engine spectator state to exclude, so any such filtering would need to be implemented at the mod level if still desired.

## Examples

The following actor fades out and disappears from the map once killed, but will not do so until out of sight of all players. Useful for open maps with a high body count, to reduce possible lag:

```decorate
actor FadingZombie : Zombieman
{
  States
  {
  Death:
    POSS H 5
    POSS I 5 A_Scream
    POSS J 5 A_NoBlocking
    POSS K 5
    // intentional fallthrough
  DeathWait:
    POSS L 1 A_CheckSight("DeathFade")
    loop
  DeathFade:
    POSS L 1 A_FadeOut(0.02)
    loop
  XDeath:
    POSS M 5
    POSS N 5 A_XScream
    POSS O 5 A_NoBlocking
    POSS PQRST 5
    // intentional fallthrough
  XDeathWait:
    POSS U 1 A_CheckSight("XDeathFade")
    loop
  XDeathFade:
    POSS U 1 A_FadeOut(0.02)
    loop
  Raise:
    stop    // not fair to have the monster revivable just because it's in LOS
  }
}
```

## See also

- `A_CheckSightOrRange` — checks both sight *and* distance to a target range, useful for toggling actor behavior only when sufficiently far and out of sight.
- `A_JumpIfInTargetLOS` — conditional jump when the *target* is in line of sight *from* the actor.
- `CheckSight` (ACS) — the underlying Zandronum engine function for general line-of-sight queries.
