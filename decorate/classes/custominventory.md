# CustomInventory

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `Classes:CustomInventory` (retrieved 2026-08-01, oldid=53783) + verified against the Zandronum source's `src/g_shared/a_pickups.h:226`, `src/g_shared/a_pickups.cpp:1816-1851`, `src/thingdef/thingdef_codeptr.cpp:128-190`, and `src/p_mobj.cpp:879-914`.
**Bucket:** Built-in base class; native C++ class at `src/g_shared/a_pickups.h:226`; DECORATE declaration at `wadsrc/static/actors/shared/inventory.txt:135`.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

CustomInventory is a scripted inventory class that executes code in state chains during pickup, use, and drop events. It is an inventory base class designed to work around the lack of a scripting language before ZScript existed, and is best understood through its state-chain execution model: code runs immediately with side effects visible even if the state chain later fails, and the `Pickup:`/`Use:`/`Drop:` states determine success or failure through action-function results and state jumps.

## Core behavior: state-chain execution

CustomInventory defines three reserved states:
- **`Pickup:`** — state chain executed when the item is picked up; if it succeeds and there is no `Use:` state, the item is destroyed; if it succeeds and a `Use:` state exists, the item is placed in the actor's inventory.
- **`Use:`** — state chain executed when the item is activated (used); if it succeeds, the item is consumed from inventory; if it fails (e.g., ends with `Fail`), the item is retained.
- **`Drop:`** — state chain executed when a monster drops the item at death (not used for player-thrown drops or item-pool spawns); the item is never placed in the world after this state chain runs.

All three state chains execute **without frame delays** — every state in the chain executes within the same tic. The state-chain execution model is `CallStateChain`, described below.

## The CallStateChain execution model

The `Pickup:`, `Use:`, and `Drop:` state chains are not normal state machines — they execute via `ACustomInventory::CallStateChain`, which runs states in sequence and accumulates a success/failure result:

```cpp
bool ACustomInventory::CallStateChain (AActor *actor, FState * State)
{
	StateCallData StateCall;
	bool result = false;
	int counter = 0;

	while (State != NULL)
	{
		// Assume success. The code pointer will set this to false if necessary
		StateCall.State = State;
		StateCall.Result = true;
		if (State->CallAction(actor, this, &StateCall))
		{
			// collect all the results. Even one successful call signifies overall success.
			result |= StateCall.Result;
		}


		// Since there are no delays it is a good idea to check for infinite loops here!
		counter++;
		if (counter >= 10000)	break;

		if (StateCall.State == State) 
		{
			// Abort immediately if the state jumps to itself!
			if (State == State->GetNextState()) 
			{
				// [AK] The server handles state chain results, so if the client
				// reaches here, then it already succeeded on the server's end.
				// Thus, let it succeed on the client's end, even in this case,
				// because they likely didn't predict the result properly.
				if (NETWORK_InClientMode())
					return true;

				return false;
			}
			
			// If both variables are still the same there was no jump
			// so we must advance to the next state.
			State = State->GetNextState();
		}
		else 
		{
			State = StateCall.State;
		}
	}

	// [TP] The server handles state chain results. The client considers everything to succeed. This way, the client is
	// immune to state chain failure in event it cannot predict the result properly. Since the client is here, it has
	// already succeded on the server. Without this, clients would sometimes be unable to handle e.g. GiveInventory
	// messages properly for CustomInventory items with Pickup states that call ACS.
	if (NETWORK_InClientMode())
		return true;

	return result;
}
```

**Key execution properties:**

1. **Result accumulation via OR:** The result is built with `result |= StateCall.Result` — **only from states that have action functions**. A bare frame like `TNT1 A 0` with no trailing action contributes nothing. This means once any state with an action returns true, the chain result is locked to true for the remainder of execution (the OR operation only copies bits, never clears them).

2. **What action functions contribute:** 
   - Functions like `A_JumpIfInventory`, `A_JumpIf`, `A_JumpIfCloser` explicitly set `ACTION_SET_RESULT(false)` and contribute nothing to the OR accumulation, despite jumping (the jump alters `StateCall.State` but the result stays unaffected).
   - Functions like `A_GiveInventory`, `A_CallSpecial`, `ACS_NamedExecuteWithResult`, and other outcome-dependent actions set the result to true/false based on their success.
   - A function that doesn't explicitly set a result leaves `StateCall.Result` at its default (`true`), which is then OR'd in if the function exists. This is why `A_RailWait` — a stub function that does nothing — accidentally signals success: `CallAction` returns true (the function exists), so the default-true `StateCall.Result` is OR'd in.

3. **Fail/Wait/Stop behavior:** If a state's `NextState` points back to itself (the parser's internal representation of `Fail`/`Wait`), `CallStateChain` detects this condition at `if (State == State->GetNextState())` and returns hard `false` immediately, **discarding any accumulated result** that may have been built by earlier states in the chain. This is the atomic abort mechanism for `Fail`.

4. **Infinite-loop limit:** If the state chain loops more than 10,000 times, `CallStateChain` breaks and falls through to return the accumulated result. This is a safety limit, not the same as the `Fail`-abort above — an accumulated success survives the break.

5. **Network behavior:** In multiplayer, clients receive a broadcast of the chain result from the server and return `true` unconditionally (`NETWORK_InClientMode()` checks), allowing clients to continue even if their local prediction diverged from the server's decision. The server decides success/failure authoritatively.

## Pickup flow: success vs. failure and rollback semantics

### Success path (Pickup returns true, no Use state)

```cpp
bool ACustomInventory::TryPickup (AActor *&toucher)
{
	FState *pickupstate = FindState(NAME_Pickup);
	bool useok = CallStateChain (toucher, pickupstate);
	if ((useok || pickupstate == NULL) && FindState(NAME_Use) != NULL)
	{
		useok = Super::TryPickup (toucher);
	}
	else if (useok)
	{
		GoAwayAndDie();
	}
	return useok;
}
```

If `Pickup:` returns true and there is NO `Use:` state, `GoAwayAndDie()` is called and the item is removed from the world. This is the "pickup and consume" path.

### Success path (Pickup returns true, Use state exists)

If `Pickup:` returns true and a `Use:` state exists, `Super::TryPickup` (the parent `AInventory::TryPickup`) is called. This performs the normal inventory pickup logic (amount capping, pickup messages, etc.) and places the item in the actor's inventory. At this point, the item is available for the player to activate later via the `Use:` state chain.

### Failure path (Pickup returns false)

If `Pickup:` returns false (or `pickupstate == NULL` is the only state executed), the item remains in the world. **No side effects are rolled back.** If an earlier state in the `Pickup:` chain already ran an action function like `A_GiveInventory`, that item is now in the toucher's inventory even though the overall pickup is reported failed. This is a critical asymmetry: **side effects execute immediately with no save/restore mechanism**; only the overall success/failure result is affected.

### Note: `A_GiveInventory`'s own failure path is self-cleaning, not an example of missing rollback

It's tempting to reach for an `A_GiveInventory` call that hits a `MaxAmount` cap as a "no rollback" example, but tracing it end-to-end shows the opposite: `DoGiveInventory` (backing `A_GiveInventory`) spawns a temporary item and calls `item->CallTryPickup(receiver)`; if that fails (e.g. `AInventory::HandlePickup` finds the receiver already at `MaxAmount` and never sets `IF_PICKUPGOOD`, so `AInventory::TryPickup` returns false), `DoGiveInventory` immediately calls `item->Destroy()` and sets `ACTION_SET_RESULT(false)` — src/thingdef/thingdef_codeptr.cpp:2120-2180. No inventory amount changed, no item persists; a single action function's own internal failure is fully self-contained. This is *not* where the "no rollback" risk lives.

### Where the no-rollback risk actually lives: state-order, not single-action failure

The real risk is across **multiple states in the same chain**, because `CallStateChain` has no concept of undo — it just runs states in sequence (see above) and OR's their results together. If an *earlier* state in a `Pickup:` or `Use:` chain runs an action with an irreversible external effect, and a *later* state in the same chain fails (via a jump function or `Fail`), the earlier effect already happened and is not undone even though the chain's overall result is false:

1. `Pickup:` first calls `ACS_NamedExecuteWithResult("GiveBonus")`. This runs `P_ExecuteSpecial(ACS_ExecuteWithResult, ...)` synchronously — the ACS script runs to completion (e.g. it awards the player some currency, opens a door, or otherwise mutates world/player state) before this action function returns. `ACTION_SET_RESULT` is then set to whatever the script itself returned (src/thingdef/thingdef_codeptr.cpp:5717-5734).
2. A later state in the same `Pickup:` chain calls `A_JumpIfInventory` (or similar), which explicitly sets `ACTION_SET_RESULT(false)` and jumps — contributing nothing to the OR.
3. If no other state in the chain sets the result true, `CallStateChain` returns false and `CustomInventory::TryPickup` reports failure — the world item is not picked up, and (with a `Use:` state present) never even reaches `Super::TryPickup`.
4. **But the ACS script from step 1 already ran to completion.** There is no mechanism anywhere in `CallStateChain`, `TryPickup`, or the ACS call specials to detect "the chain ultimately failed" and revert what the script did — once `ACS_ExecuteWithResult` returns, its side effects are as permanent as any other ACS script's.

This is why the risk is specifically about **chain ordering of irreversible external actions** (ACS scripts, `A_CallSpecial`, giving *other* actors items, `A_GiveToTarget`, etc.) relative to a later fail-capable state — not about a single action function's own well-behaved internal failure path.

### A `SetActorPosition` call on the toucher from `Pickup:` gets silently discarded, for a different reason than the above

The "no rollback" behavior above means an already-fired side effect isn't undone. A position
change is a distinct, separate trap with the opposite shape: it fires, but then gets **overwritten
by the caller's own code**, not by anything in `CallStateChain`/`TryPickup`. When `Pickup:` is
reached by the toucher walking into the item (not by `Use:`, and not by an item granted directly
with no intervening movement), the whole touch happens nested inside the toucher's own `P_TryMove`
call, which caches its destination coordinates as locals *before* the touch runs and unconditionally
reassigns `thing->x`/`thing->y` back to that destination once the touch returns — silently
discarding any `SetActorPosition` (or other position-setting call) made on the toucher mid-chain,
independent of whether the chain ultimately succeeds or fails. See
[Position change during pickup touch](../concepts/position-change-during-pickup-touch.md) for the
full verified call-stack trace and avoidance options — this is a `P_TryMove`-level mechanism, not
specific to `CustomInventory` beyond it being the easiest way to get arbitrary ACS to run from a
pickup's touch.

## Use/Drop flow

`Use` is called when the item is activated:

```cpp
bool ACustomInventory::Use (bool pickup)
{
	return CallStateChain (Owner, FindState(NAME_Use));
}
```

If `Use:` returns true, the item is consumed from the inventory (the item's amount is decremented, and destroyed if amount reaches 0). If `Use:` returns false (typically by ending with `Fail` instead of `Stop`), the item is retained.

Like `Pickup:`, **side effects in `Use:` are not rolled back.** If a `Use:` state chain calls `ACS_NamedExecuteWithResult` which fires an ACS script, and a later action in the same chain fails, the ACS script's side effects persist — the script has already run.

`SpecialDropAction` calls `CallStateChain` on the `Drop:` state and never places the resulting item in the world, regardless of success or failure.

## Wiki divergences in GZDoom/UZDoom

The wiki's ZScript definition (shown for reference) describes a GZDoom/UZDoom implementation with several features absent from Zandronum's DECORATE-only codebase:

- **`StateProvider` parent class:** Zandronum's CustomInventory is `class ACustomInventory : public AInventory` only; there is no `StateProvider` base class.
- **`DefaultStateUsage SUF_*` property:** This GZDoom-era property and its flags do not exist in Zandronum.
- **`A_GunFlash`, `A_Lower`, `A_Raise`, `A_CheckReload`, `A_WeaponReady` as deprecated methods:** These are Weapon-only in Zandronum and are not available on CustomInventory (the ZScript code marks them deprecated for this reason).
- **Anonymous functions with `return int`/`return bool`:** ZScript's ability to return explicit success/failure from action blocks does not exist in Zandronum DECORATE — side effects run and the result is determined by which actions set `StateCall.Result`.
- **`return bool`/`return int` from action functions:** Specific ACS/call-result functions like `ACS_NamedExecuteWithResult` can signal success/failure; general action functions cannot.

## Known behavior notes

- **A_RailWait as a success signal:** The wiki recommends ending a `Pickup:` or `Use:` chain with `A_RailWait` to guarantee success. This works, but not as a deliberate success marker — `A_RailWait` is an empty stub function. It contributes success because `CallAction` returns true (the function exists), triggering the default-true `StateCall.Result` to be OR'd in. Functionally equivalent to any bare action with no explicit result setting; relying on this is fragile and not recommended.

- **Frame durations ignored in state chains:** The `Pickup:`, `Use:`, and `Drop:` state chains run at no frame cost (all states execute in the same tic). Frame durations in these chains are parsed but have no effect at runtime (states are not subject to tic countdown). Attempting to loop within these states (e.g., `TROO AB 4 Loop`) will trigger the self-jump abort after the loop target is reached, failing the entire chain.

- **Player/Owner semantics:** In `Pickup:` and `Use:`, the `Owner` pointer is the entity being given the item (the toucher during pickup, the item's current owner during use). Actions in these chains can modify the owner's inventory, properties, or state, but CustomInventory items themselves cannot access their own variables after being picked up (they "lose access to their variables, gaining direct access to the owner's variables instead," per the wiki).
