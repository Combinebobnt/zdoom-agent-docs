# `A_Jump`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `A_Jump` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Jump&oldid=46792) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:765-785` (and `DoJump`, `:695-753`), `src/thingdef/thingdef_states.cpp:377-397` (jump offsets), `src/thingdef/thingdef_expression.cpp:2673-2757` (state-label resolution), `src/m_random.h`/`src/m_random.cpp` (the `FRandom` PRNG), `src/actor.h:466-470`/`src/p_mobj.cpp:6195-6198` (the server never spawns `CLIENTSIDEONLY` actors), and `src/d_net.cpp`/`src/d_main.cpp`/`src/sdl/i_system.cpp` (RNG-seed lifecycle across the server/client connection).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in `src/thingdef/thingdef_codeptr.cpp`).
**Source excerpt:** Quotes Zandronum engine source; see [LICENSE](../../LICENSE) §3 for Zandronum's license terms.

Randomly advances to one of several target states with a specified probability. Unqualified state labels are resolved at run time in the state owner's actual class (virtual jumps), not in the base class where the state was written.

## Signature

```decorate
state A_Jump (int chance, state target1, [state target2, ...])
state A_Jump (int chance, int offset1, [int offset2, ...])
```

## Parameters

**`chance`** (int, 0–256)  
Probability of jumping, expressed as a value 0–256. A value of 0 (or less) never jumps; 256 (or more) always jumps. Intermediate values represent the probability as `chance/256` (e.g., 128 = 50% chance). When a jump occurs and multiple targets are provided, one is selected at random.

**`target1, target2, ...`** (state labels or frame offsets)  
One or more jump destinations; a parenthesized call needs at least one. Labels and offsets can be mixed in one call.

- State labels must be quoted strings (e.g. `"Melee"`, `"Death"`). An unqualified label is looked up at run time in the class of the state owner (the actor itself, or the weapon/`CustomInventory` item for those state tables), so a subclass's override of that label wins. A `Super::`- or `ClassName::`-qualified label is resolved once at load time instead. `""` or `"None"` means no jump. On Zandronum, an unqualified label missing at run time prints `Jump target '<label>' not found in <class>` and the actor does not jump (`thingdef_expression.cpp:2740-2757`).
- An integer offset N targets the Nth state after the calling one. Each frame letter is one state; labels and `Goto`/`Stop`/`Loop`/`Wait` lines occupy no state, so they are not counted. The offset must be a non-negative integer literal: a negative offset is a parse error (`Negative jump offsets are not allowed`), 0 means no jump, and a positive offset on a line that defines more than one frame is a parse error (see "Parser quirk" below). Zandronum: `thingdef_states.cpp:377-397`. A 0 in a multi-target list compiles to a null target, so when the random pick lands on it the actor simply doesn't jump (`DoJump` returns on a null target, `thingdef_codeptr.cpp:697`).

## Behavior

- The jump happens when `chance` is 256 or more (no roll is made) or when a random roll in 0–255 is strictly less than `chance`. When the roll is `chance` or higher, the action returns without jumping and execution continues to the next action or frame in the current state.
- If the probability check succeeds and more than one target is provided, one target is picked at random. On Zandronum the pick is a second 0–255 roll modulo the target count, which is uniform only when the count divides 256 (e.g. with 3 targets the first is very slightly favored). That second roll happens only after a successful chance check, and only when there are at least two targets.
- Zandronum: in a `CustomInventory` state chain, `A_Jump` always sets the chain's result to false, whether or not it jumps (`thingdef_codeptr.cpp:784`; `CallStateChain` presets it to true, `:145`). An `A_Jump` on its own therefore never counts as a successful pickup/use.
- A_Jump with `chance = 0` and any targets present compiles successfully but never jumps. It is harmless but pointless.
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

In client mode (`NETWORK_InClientMode()`: a connected client or client-demo playback), an actor without the `NETFL_CLIENTSIDEONLY` flag returns *before* either `pr_cajump()` call, so the client never rolls for it and never jumps on its own. Whether the server's outcome reaches the client depends on where the call ran (`DoJump`, `thingdef_codeptr.cpp:695-753`); `A_Jump` passes `CLIENTUPDATE_FRAME`, so on the server:

- From the actor's own state, the server sends `SERVERCOMMANDS_SetThingFrame` with the new state. An actor with no net ID (e.g. `+NONETID`) gets nothing, so on clients it never takes the jump.
- From a weapon or flash psprite state, the server calls `SERVER_HandleWeaponStateJump` (`sv_main.cpp:5517-5540`), which sends the player's new psprite state and also resends the weapon's ammo counts, since the client ignored the jump and may have mispredicted ammo meanwhile.
- From a `CustomInventory` state chain, nothing is sent.

The client-side RNG stream is never touched in this path, so there is no RNG-alignment requirement.

`+CLIENTSIDEONLY` actors are the other path. The server never spawns them (`actor.h:466-470`, `p_mobj.cpp:6195-6198`), so online only clients run their `A_Jump`, each rolling `pr_cajump()` locally; offline the game runs it as usual. `pr_cajump` is a private `FRandom` instance (`static FRandom pr_cajump("CustomJump")`) used only inside this function (`thingdef_codeptr.cpp:87,778,780`), so no other code shares its stream. The exception is the `compat_oldrandom` compat flag (`ZACOMPATF_OLD_RANDOM_GENERATOR`): with it set, every `FRandom` call returns Doom's `P_Random()` instead (`m_random.cpp:234-240`, cvar at `d_main.cpp:845`), which reads one global table index (`m_oldrandom.cpp:64-71`). Then `pr_cajump` shares that stream with every other random consumer and `rngseed` plays no part. Otherwise, whether two clients' rolls line up depends on whether their `rngseed` (the value each named `FRandom` is (re-)seeded from, via `FRandom::Init`/`StaticClearRandom`) matches, and normally it does **not**:

- Each process sets its own `rngseed` at startup from `I_MakeRNGSeed()` (`src/sdl/i_system.cpp`), which reads `/dev/urandom`/`/dev/random` (falling back to `time(NULL)`). That is independent entropy per machine, not a shared value. Only a `-rngseed <n>` command-line parameter (`d_main.cpp:2439-2448`) or `rngseed set` pins a static seed, and only locally.
- The one mechanism that *would* transmit a `rngseed` between peers, the legacy `NCMD_SETUP` handshake's game-info packet (`src/d_net.cpp`, `D_ArbitrateNetStart`), is dead code in Zandronum: its only call site, in `D_CheckNetGame` (`src/d_net.cpp:1651`), is commented out. The live server/client protocol (`sv_main.cpp`, `cl_main.cpp`, `sv_commands.cpp`, `cl_commands.cpp`) never touches `rngseed`; the remaining read/write sites are demo record/playback (`cl_demo.cpp`, `g_game.cpp`) and the per-level reseed (`g_level.cpp:575`, the static seed if set, else `rngseed + 1`), none of which crosses the network.

So `+CLIENTSIDEONLY` actors' `A_Jump` rolls are **not** expected to align between clients. Each one free-runs its own independent sequence. This is inconsequential rather than a bug: `NETFL_CLIENTSIDEONLY` is documented at its declaration (`src/actor.h:466-470`) as only for actors that don't affect the game in any way beyond visuals, so every client already simulates its own private copy with no cross-machine consistency requirement.

## Engine-family divergence: no client/server authority split

UZDoom's `A_Jump` (`src/playsim/p_actionfunctions.cpp:798-809`) has no client-mode gate at all: the native function only performs the chance check and returns either its single target state or no state. No `NETWORK_InClientMode()`/`CLIENTUPDATE_FRAME`/`SERVERCOMMANDS_*`-style construct exists anywhere in the UZDoom source tree (confirmed by a tree-wide search: zero occurrences). There is no `NETFL_CLIENTSIDEONLY`-style split between "network-authoritative" and "client-side-only" actors for this action — every actor's `A_Jump` call rolls and jumps identically wherever it runs. The entire "## Network considerations" section above — the client-mode early return, the `rngseed`-synchronization analysis, the `NCMD_SETUP` dead-code finding — is Zandronum-specific and does not apply to UZDoom: there is no split to reconcile because none exists in the engine.

## Engine-family divergence: multi-target selection happens in the compiler, not the native function

In Zandronum, target selection among multiple provided states lives inside the single native function shown above, and its `pr_cajump()` roll for picking a target only happens *after* the chance check succeeds (`ACTION_PARAM_STATE` reads the chosen target only inside the `if` block). UZDoom takes a structurally different path: the native `A_Jump` (`src/playsim/p_actionfunctions.cpp:798`) takes only `(int maxchance, statelabel jumpto)` — a single already-resolved target, no variadic list. When a call site passes more than one target, the compiler rewrites it before the native function ever sees it: `UnravelVarArgAJump`/`AJumpProcessing` (`src/scripting/backend/codegen_doom.cpp:360-413`) replaces the extra target arguments with a single `RandomPick[cajump](a, b, c, ...)` expression, evaluated as an ordinary function argument on *every* execution of that state — unconditionally, not gated on the chance check — drawing from the same `pr_cajump` `FRandom` stream (the one generator object is shared between `p_actionfunctions.cpp` and `codegen_doom.cpp`) to pick uniformly among the targets. The already-resolved single target is what actually reaches the native `A_Jump`, which then only performs the chance check. The observable outcome — probability of jumping, and a uniform distribution among targets when it does jump — is unchanged from Zandronum, but the RNG draw for target selection happens earlier and unconditionally (once per call regardless of whether the jump succeeds) rather than only after a successful chance roll — a difference in `pr_cajump` draw-sequence/count that matters for anyone relying on exact RNG-stream consumption (e.g. deterministic-replay or seeded-generation contexts), even though it has no effect on the probabilities documented above.

## Virtual vs. static jumps

A jump via `A_Jump` to an unqualified label resolves the target state in the state owner's actual (**derived**) class's state table. Contrast this with the `goto` keyword, which is static: execution does not leave the base class and does not see overridden states. This matters when a state written in a base class calls `A_Jump` with a label: the jump will use the derived class's version of that label if it exists. A `Super::` or `ClassName::` qualifier makes the `A_Jump` target static too.

## Parser quirk: multi-frame single-line states

A positive numeric offset is rejected on a state line that defines more than one frame (e.g. `SPRITE ABC 5 A_Jump(127, 2, 3)`). It is a fatal parse error: `You cannot use state jumps commands with a jump offset on multistate definitions`. An offset of 0 is still accepted on such a line, since the check is for a number greater than 0 (`thingdef_states.cpp:380`). The workaround is to either (a) use state labels instead of offsets, or (b) put the `A_Jump` on a line that defines a single frame.

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
