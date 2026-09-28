# `A_CheckSight`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_CheckSight` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_CheckSight&oldid=45585) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3286-3329`, `DoJump` (`thingdef_codeptr.cpp:695-753`), jump-offset parsing (`src/thingdef/thingdef_states.cpp:377-397`), `SF_IGNOREVISIBILITY` (`src/p_sight.cpp:686`), and server-side CLIENTSIDEONLY suppression (`thingdef_codeptr.cpp:105-121`, `src/p_mobj.cpp:6195-6199`, `src/sv_main.cpp:5653-5668`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in `src/thingdef/thingdef_codeptr.cpp`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; see [LICENSE](../../LICENSE) §3 for Zandronum's license terms.

Jumps to a target state if no player can see the calling actor. Unlike `A_JumpIf*` conditional jumps, this is a **sight-based check** that polls all active players' line-of-sight to the actor, from each player's pawn and from any non-player camera they are viewing through.

## Signature

```decorate
state A_CheckSight (state target)
state A_CheckSight (int offset)
```

## Parameters

**`target`** (state label or frame offset)  
The jump destination. If a state label (e.g., `"Death"`, `"DeathFade"`), the name is resolved in the calling actor's derived class's state table (virtual resolution). If an integer, offset N targets the state N after the calling one. `0` means no jump. A negative offset is a parse error ("Negative jump offsets are not allowed"), and so is a positive offset on a multi-frame line such as `POSS AB 4 A_CheckSight(2)`.

## Behavior

- Checks whether **any** non-spectating player can see the calling actor from their viewpoint.
- If **at least one player has line of sight** to the actor, returns without jumping. Execution continues to the next action or frame in the current state.
- If **no player has line of sight** to the actor, performs the jump to the target state.
- The sight check is `P_CheckSight`, which is pure line of sight with no facing or FOV test. **The player does not have to be facing the actor.** If a player is positioned where they *could* see the actor if they turned, the actor counts as seen.
- The `SF_IGNOREVISIBILITY` flag makes the check ignore the actor's own visibility. An actor that is `RF_INVISIBLE` or whose render style and alpha make it invisible (e.g. fully faded out) still counts as seen.
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

On network-authoritative actors (those without the `NETFL_CLIENTSIDEONLY` flag), the client-mode check returns *before* checking sight, so a client performs **no sight tests** for these actors at all. The server decides, and `DoJump` (`thingdef_codeptr.cpp:695-753`) tells clients only in some cases. A jump from the actor's own current state sends a thing-frame update. A jump from a player's weapon or flash psprite state sends a weapon state jump. A jump inside a `CustomInventory` state chain sends nothing.

For `+CLIENTSIDEONLY` actors, each client checks sight alone, from `players[consoleplayer].camera` only. That camera is normally the local pawn. There is no separate pawn test and no spectator test on this path. The server never runs this branch for such actors, because it does not hold them: it refuses to spawn them from map things and action functions, and destroys any it spawns for summon or ACS relay (`thingdef_codeptr.cpp:105-121`, `p_mobj.cpp:6195-6199`, `sv_main.cpp:5653-5668`). Each client simulates its own private copy, so the outcome can differ between clients.

## Engine-family divergence: network execution model

The client/server authority split described above (the `NETWORK_InClientMode()` branch, the `NETFL_CLIENTSIDEONLY` special case, and the `CLIENTUPDATE_FRAME` cross-machine sync flag) is specific to Zandronum's netcode. UZDoom has no equivalent concept anywhere: a search of UZDoom's entire source tree turns up zero occurrences of `NETWORK_InClientMode`/`SERVERCOMMANDS_*`. UZDoom's `A_CheckSight` (`wadsrc/static/zscript/actors/checks.zs:151`, calling the native `CheckIfSeen()` in `src/playsim/p_actionfunctions.cpp:1729`) contains no client-mode branch, no server-authoritative early return, and no cross-machine state-sync flag — it is a single plain loop over all in-game players, evaluated identically regardless of network role. The entire "Network considerations" topology described above, including the source excerpt, does not apply to UZDoom.

**Player cameras and co-op spy:** The sight check looks at both `players[i].mo` (each player's pawn) and `players[i].camera` if it is non-NULL and not a player pawn itself (e.g. a camera actor switched to with `ChangeCamera` or a security camera). Co-op spy points the camera at another player's pawn, so the camera test skips it. That pawn is still checked in its own player's iteration. The `chase` command does not change the camera actor at all.

**Spectators excluded:** On the server and offline, spectating players are skipped (the `bSpectating` check), so they do not block a jump. The client-side path for `+CLIENTSIDEONLY` actors has no such test.

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
- `A_JumpIfInTargetLOS` — conditional jump when the calling actor is in its *target's* line of sight (FOV measured from the target's facing).
- `CheckSight` (ACS) — separate ACS function for line-of-sight queries between tagged actors. `A_CheckSight` does not call it.
