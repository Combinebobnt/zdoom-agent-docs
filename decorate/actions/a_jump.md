# `A_Jump`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Jump` (retrieved 2026-07-31, oldid=46792) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:765-785`, `src/m_random.h`/`src/m_random.cpp` (the `FRandom` PRNG), and `src/d_net.cpp`/`src/d_main.cpp`/`src/sdl/i_system.cpp` (RNG-seed lifecycle across the server/client connection).
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in `src/thingdef/thingdef_codeptr.cpp`).
**Source excerpt:** Quotes Zandronum engine source; see [LICENSE](../../LICENSE) §3 for Zandronum's license terms.

Randomly advances to one of several target states with a specified probability. Virtual jumps resolve the target state in the derived (calling) actor's state table, not the base class where the action is defined.

## Signature

```decorate
state A_Jump (int chance, state target1, [state target2, ...])
state A_Jump (int chance, int offset1, [int offset2, ...])
```

## Parameters

**`chance`** (int, 0–256)  
Probability of jumping, expressed as a value 0–256. A value of 0 never jumps; 256 always jumps. Intermediate values represent the probability as `chance/256` (e.g., 128 ≈ 50% chance). When a jump occurs and multiple targets are provided, one is selected uniformly at random.

**`target1, target2, ...`** (state labels or frame offsets)  
One or more jump destinations. If using state labels (e.g., `"Melee"`, `"Death"`), the names are resolved in the calling actor's derived class's state table (virtual resolution). If using frame offsets (integers), the offset counts **frames in the current state line**, not instruction lines — this is a common source of confusion when combining `A_Jump` offsets with `goto` labels (which cannot be jumped to directly via offset). When multiple destinations are provided, one is chosen uniformly at random among them.

## Behavior

- If the probability check fails (random outcome ≤ `chance`), the action returns without jumping. Execution continues to the next action or frame in the current state.
- If the probability check succeeds and at least one target is provided, one target is selected at random with equal probability among all provided targets.
- The resulting jump does not set any result value for inventory-pickup state chains (`ACTION_SET_RESULT(false)` is always called, per the source).
- A_Jump with `chance = 0` and any targets present compiles successfully but never jumps — it is harmless but pointless.
- A_Jump with `chance = 256` always jumps, so if only one target is provided it is a deterministic branch.

## Network considerations

```c
DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Jump)
{
	ACTION_PARAM_START(3);
	ACTION_PARAM_INT(count, 0);
	ACTION_PARAM_INT(maxchance, 1);

	// [BC] Don't jump here in client mode.
	if ( NETWORK_InClientMode() )
	{
		if (( self->NetworkFlags & NETFL_CLIENTSIDEONLY ) == false )
			return;
	}

	if (count >= 2 && (maxchance >= 256 || pr_cajump() < maxchance))
	{
		int jumps = 2 + (count == 2? 0 : (pr_cajump() % (count - 1)));
		ACTION_PARAM_STATE(jumpto, jumps);
		ACTION_JUMP(jumpto, CLIENTUPDATE_FRAME ); // [BC] Random state changes shouldn't be client-side.
	}
	ACTION_SET_RESULT(false);	// Jumps should never set the result for inventory state chains!
}
```

On network-authoritative actors (those without the `NETFL_CLIENTSIDEONLY` flag), the client-mode check returns *before* either `pr_cajump()` call, so a client never rolls the dice for these actors at all — it only ever receives the server's already-decided outcome via the `CLIENTUPDATE_FRAME` state-change flag. There is no RNG-alignment requirement in this path because the client-side RNG stream is never touched.

For `+CLIENTSIDEONLY` actors, both server and client do execute the jump logic — and independently roll `pr_cajump()`, a private `FRandom` instance (`static FRandom pr_cajump("CustomJump")`) declared and consumed *only* inside this one function (verified: no other file in the source tree references `pr_cajump`, so there is no cross-consumer stream-sharing to worry about). Whether the two rolls line up depends entirely on whether `rngseed` (the value each machine's named `FRandom`s are (re-)seeded from, via `FRandom::Init`/`StaticClearRandom`) matches between server and client — and it does **not**, by design:

- Each process sets its own `rngseed` at startup from `I_MakeRNGSeed()` (`src/sdl/i_system.cpp`), which reads `/dev/urandom`/`/dev/random` (falling back to `time(NULL)`) — independent entropy per machine, not a shared value.
- The one mechanism that *would* transmit a `rngseed` between peers — the legacy `NCMD_SETUP` handshake's game-info packet (`src/d_net.cpp`, `D_ArbitrateNetStart`) — is dead code in Zandronum: its only call site, in `D_CheckNetGame` (`src/d_net.cpp`), is commented out (`//		D_ArbitrateNetStart ();`). No other file writes or reads `rngseed` as part of the live server/client connection or in-game protocol (`sv_main.cpp`, `cl_main.cpp`, `sv_commands.cpp`, and `cl_commands.cpp` contain no reference to it at all); the remaining `rngseed` read/write sites are demo record/playback (`cl_demo.cpp`, `g_game.cpp`) and per-level increment (`g_level.cpp`, `rngseed = rngseed + 1`), neither of which crosses the network.

So `+CLIENTSIDEONLY` actors' `A_Jump` rolls are **not** expected to align between machines — each one free-runs its own independent sequence. This is inconsequential rather than a bug: `NETFL_CLIENTSIDEONLY` is documented at its declaration (`src/actor.h`) as "only spawned by the clients... don't affect the game in any way (visuals aside)" — i.e. every machine already owns and simulates its own private copy of the actor, with no cross-machine consistency requirement to begin with. There is accordingly no synchronization gap to close for `A_Jump` in either code path.

## Virtual vs. static jumps

A jump via `A_Jump` resolves the target state in the calling actor's **derived** class's state table. Contrast this with the `goto` keyword, which is static — execution does not leave the base class and does not see overridden states. This matters when an action function defined on a base class jumps to a state label: the jump will use the derived class's version of that label if it exists.

## Parser quirk: multi-frame single-line states

Due to the way DECORATE's state parser handles frame-offset jumps, a limitation exists when using multiple state labels on one line with offsets: the parser cannot correctly parse `A_Jump(chance, offset1, offset2, ...)` syntax on a single line if the line includes multiple frame definitions (e.g., `SPRITE ABC 5 A_Jump(127, 2, 3)`). The workaround is to either (a) use state labels instead of offsets, or (b) place each `A_Jump` on its own line in separate states.

## Examples

Always jump to the "Melee" state:
```decorate
States
{
Spawn:
  POSS A 10 A_Look
  POSS A 0 A_Jump(256, "Melee")
  // Never reached
  Stop

Melee:
  POSS C 8 A_MeleeAttack
  Goto Spawn
}
```

Jump to one of three states with equal probability:
```decorate
States
{
Attack:
  POSS E 8 Bright A_FaceTarget
  POSS E 0 A_Jump(256, "Attack1", "Attack2", "Attack3")
  Stop

Attack1:
  POSS F 12 A_CustomMissile("Projectile1")
  Goto Spawn

Attack2:
  POSS G 12 A_CustomMissile("Projectile2")
  Goto Spawn

Attack3:
  POSS H 12 A_CustomMissile("Projectile3")
  Goto Spawn
}
```

Jump with 50% probability (offset-based; not recommended due to frame-count brittleness):
```decorate
States
{
Decide:
  POSS A 0 A_Jump(128, 2)
  POSS A 10 // 50% chance of skipping this
  Goto See
  POSS A 20 // Alternative path
  Goto See
}
```
