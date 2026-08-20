# CustomInventory

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `Classes:CustomInventory` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3ACustomInventory&oldid=53783) + verified against the Zandronum source's `src/g_shared/a_pickups.h:226`, `src/g_shared/a_pickups.cpp:1816-1851`, `src/thingdef/thingdef_codeptr.cpp:128-190`, and `src/p_mobj.cpp:879-914`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

### `+INVENTORY.ALWAYSPICKUP` is a second, independent backstop above `TryPickup`'s own result

A `false` from `ACustomInventory::TryPickup` (i.e. `CallStateChain` on `Pickup:` ultimately
returning false) is not necessarily the end of the story: the caller is `AInventory::
CallTryPickup` (`src/g_shared/a_pickups.cpp`), which is not overridden by `CustomInventory` and
wraps *every* inventory subclass's `TryPickup`, not just this one:

```c
if (!res && (ItemFlags & IF_ALWAYSPICKUP) && !ShouldStay())
{
    res = true;
    GoAwayAndDie();
}
```

If the `CustomInventory` actor itself carries `+INVENTORY.ALWAYSPICKUP` (`ShouldStay()` returns
`false` unconditionally for plain, non-map-persistent inventory), the item is consumed and the
overall pickup reports success even when its entire `Pickup:` chain returned false — independent
of, and in addition to, the OR-based chain-result mechanics above. A concrete case where this
matters: a `Pickup:` chain that gives a `Powerup` subclass whose own `HandlePickup` discards a
re-give while significant duration remains (see [`Powerup`'s re-pickup
semantics](powerup.md#re-pickup-and-refresh-semantics)) still contributes `false` to that one
`A_GiveInventory` call — but on an `+INVENTORY.ALWAYSPICKUP` item like vanilla `Berserk`, neither
that nor the chain's overall OR result affects whether the world item is actually picked up.

Confirmed on UZDoom: the same backstop exists, moved into ZScript as `Inventory::CallTryPickup` (the UZDoom source's `wadsrc/static/zscript/actors/inventory/inventory.zs:697-701`) — `if (!res && (bAlwaysPickup) && !ShouldStay()) { res = true; GoAwayAndDie(); }`, functionally identical to Zandronum's C++ version quoted above with `IF_ALWAYSPICKUP`/`ALWAYSPICKUP` renamed to the ZScript flag field `bAlwaysPickup`.

### Note: `A_GiveInventory`'s own failure path is self-cleaning, not an example of missing rollback

It's tempting to reach for an `A_GiveInventory` call that hits a `MaxAmount` cap as a "no rollback" example, but tracing it end-to-end shows the opposite: `DoGiveInventory` (backing `A_GiveInventory`) spawns a temporary item and calls `item->CallTryPickup(receiver)`; if that fails (e.g. `AInventory::HandlePickup` finds the receiver already at `MaxAmount` and never sets `IF_PICKUPGOOD`, so `AInventory::TryPickup` returns false), `DoGiveInventory` immediately calls `item->Destroy()` and sets `ACTION_SET_RESULT(false)` — src/thingdef/thingdef_codeptr.cpp:2120-2180. No inventory amount changed, no item persists; a single action function's own internal failure is fully self-contained. This is *not* where the "no rollback" risk lives.

Confirmed on UZDoom: the ZScript `DoGiveInventory` (`wadsrc/static/zscript/actors/inventory_util.zs:407-461`) is structurally identical — it spawns the temporary item, calls `item.CallTryPickup(receiver)`, and on failure runs `item.Destroy(); return false;` in the same tic. Same self-contained, non-leaking failure path, just written in ZScript instead of C++.

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

Confirmed on UZDoom: `TryPickup`, `Use`, and `SpecialDropAction` are structurally identical, now written as ZScript overrides on `CustomInventory` (`wadsrc/static/zscript/actors/inventory/stateprovider.zs:497-532`) instead of C++ methods — same `CallStateChain` call per state label, same `Super.TryPickup`/`GoAwayAndDie` branching in `TryPickup`, same "never placed in the world" behavior for `SpecialDropAction`. Syntax differs (ZScript `override bool` methods calling a `native bool CallStateChain(...)` declared on the class), behavior does not.

## Engine-family divergence: GZDoom/UZDoom-only StateProvider features

The wiki's ZScript definition (shown for reference) describes a GZDoom/UZDoom implementation with several features absent from Zandronum's DECORATE-only codebase. All five bullets below are now confirmed directly against the current UZDoom source (not just inferred from the wiki text):

- **`StateProvider` parent class:** Zandronum's CustomInventory is `class ACustomInventory : public AInventory` only; there is no `StateProvider` base class. Confirmed on UZDoom: `class CustomInventory : StateProvider` (`wadsrc/static/zscript/actors/inventory/stateprovider.zs:471`), and `StateProvider` itself extends `Inventory` and supplies the weapon-flavored action functions (`A_FireBullets`, `A_CustomPunch`, `A_RailAttack`, `A_ReFire`, etc.) that `CustomInventory` inherits alongside the deprecated stubs below.
- **`DefaultStateUsage SUF_*` property:** This GZDoom-era property and its flags do not exist in Zandronum. Confirmed on UZDoom: `CustomInventory`'s `Default` block sets `DefaultStateUsage SUF_ACTOR|SUF_OVERLAY|SUF_ITEM` (`stateprovider.zs:473-476`), and this isn't just declarative — see "Engine-family divergence: `SUF_ITEM` enforcement" below for the runtime check it backs.
- **`A_GunFlash`, `A_Lower`, `A_Raise`, `A_CheckReload`, `A_WeaponReady` as deprecated methods:** These are Weapon-only in Zandronum and are not available on CustomInventory (the ZScript code marks them deprecated for this reason). Confirmed on UZDoom: all five are declared as empty `deprecated(...)` stubs directly on `CustomInventory` (`stateprovider.zs:484-488`), e.g. `deprecated("2.3", "must be called from Weapon") action void A_GunFlash(...) {}` — present only so old mods calling them through CustomInventory don't hard-error, not because they do anything.
- **Anonymous functions with `return int`/`return bool`:** ZScript's ability to return explicit success/failure from action blocks does not exist in Zandronum DECORATE — side effects run and the result is determined by which actions set `StateCall.Result`. Confirmed on UZDoom, with a correction to the underlying mechanism: it isn't that a return statement inside a state's inline action block is special-cased — UZDoom's `CallStateChain` decides how to interpret *any* called action function's return value generically, from its VM return-type prototype (`state`, `int`/`bool`, both, or neither). See the new "Engine-family divergence" section below for exactly how.
- **`return bool`/`return int` from action functions:** Specific ACS/call-result functions like `ACS_NamedExecuteWithResult` can signal success/failure; general action functions cannot. Still accurate on UZDoom as far as *named* functions in this file's scope go, though the generic prototype-based dispatch above means any action function declared with an `int`/`bool` return type can signal success/failure this way, not just a fixed list of ACS call-result functions.

## Zandronum-specific: client-side prediction bypass in `CallStateChain`

Zandronum's `CallStateChain` (quoted in full above) checks `NETWORK_InClientMode()` at two points and returns `true` unconditionally to a client at both: once inside the self-jump abort branch (a client that reaches the `Fail`/self-jump case is told it succeeded, on the theory the server already decided and will broadcast the real result), and once at the very end regardless of the accumulated `result`. This lets a Zandronum client keep an item's pickup/use looking successful even when its own local execution diverges from what the server actually decided — the server is authoritative and its result arrives separately over the network.

UZDoom's `CallStateChain` (the native function backing `ACustomInventory.CallStateChain`, UZDoom source `src/playsim/p_actionfunctions.cpp:86-220`) has no equivalent check anywhere in the function, and grepping the entire UZDoom `src/` tree for `InClientMode` turns up nothing at all — the concept doesn't exist there. UZDoom returns the accumulated `result` as computed, unconditionally, on every peer. Worth keeping for future porting work: code (or a mod) that leans on Zandronum's "a client always sees its own pickup/use as successful" leniency will behave differently — visibly failing locally instead — if ported to UZDoom.

## Engine-family divergence: how `CallStateChain` determines per-state success (UZDoom)

UZDoom's `CallStateChain` is native code backing a ZScript method declaration (`native bool CallStateChain(Actor actor, State state);` on `CustomInventory`, `stateprovider.zs:489`), not Zandronum's free-standing DECORATE code-pointer dispatch built on `StateCallData`/`ACTION_SET_RESULT`. Rather than each action function calling `ACTION_SET_RESULT(true/false)` explicitly, UZDoom inspects the called function's VM return-type *prototype* generically (`src/playsim/p_actionfunctions.cpp:134-152`):

- A function whose prototype returns only `state` is treated as a pure jump; its `retval` is forced `false` and never counted, regardless of whether it actually jumps. Confirmed: `A_JumpIf`, `A_JumpIfCloser`, and `A_JumpIfInventory` are all declared `action state ...(...)` (`wadsrc/static/zscript/actors/checks.zs:29,64,113`) — a pure-`state` prototype, matching this file's existing description of their Zandronum behavior (contributing nothing to the OR accumulation despite jumping).
- A function whose prototype returns `state` plus `int`/`bool` (the doc comment in UZDoom's source names `A_Warp` and `A_Teleport` as the intended beneficiaries) has its bool/int result counted only when it did **not** jump that tic — if it jumps, the bool is computed but discarded, same as a pure-jump function.
- A function whose prototype returns only `int`/`bool` is treated as a plain success/fail action, and a function returning nothing leaves the pre-set `retval = true` untouched (see the `A_RailWait` note below).

Two runtime safety checks exist in UZDoom's `CallStateChain` with **no Zandronum equivalent at all** (Zandronum's `StateCallData` model performs neither check):

- **`SUF_ITEM` enforcement:** every state in the chain is checked against `state->UseFlags & SUF_ITEM` before it runs; a state not flagged for item/state-chain use prints an error to the console and aborts the *entire* chain immediately with `false` (`p_actionfunctions.cpp:103-107`). This is the runtime enforcement side of the `DefaultStateUsage SUF_*` property noted above as absent from Zandronum — on UZDoom it isn't just a declarative property, a state lacking the flag hard-fails the whole `Pickup:`/`Use:`/`Drop:` chain at the point it's reached, discarding any already-accumulated success the same way the `Fail`/self-jump abort does.
- **`Unsafe` action-function stripping:** if a state's action function is flagged `Unsafe` (a compile-time property for functions that access custom/user Actor fields — see `src/common/scripting/backend/codegen.cpp:6754`), `CallStateChain` prints a one-time warning and clears `state->ActionFunc` before attempting the call, rather than invoking it and risking a crash (`p_actionfunctions.cpp:114-120`). This backs the "Known behavior notes" section's closing claim below that CustomInventory items "lose access to their own variables" after pickup — on UZDoom that's an actively compiled-and-enforced check, not just documented guidance.

## Known behavior notes

- **A_RailWait as a success signal:** The wiki recommends ending a `Pickup:` or `Use:` chain with `A_RailWait` to guarantee success. This works, but not as a deliberate success marker — `A_RailWait` is an empty stub function. It contributes success because `CallAction` returns true (the function exists), triggering the default-true `StateCall.Result` to be OR'd in. Functionally equivalent to any bare action with no explicit result setting; relying on this is fragile and not recommended. Confirmed on UZDoom: `A_RailWait` is still an empty `action void A_RailWait() {}` stub kept "only here to satisfy old Dehacked patches" (`wadsrc/static/zscript/actors/doom/doomweapons.zs:78-81`) — same accidental-success outcome, reached through the generic return-type mechanism described above (a `void`-returning function leaves the pre-set `retval = true` untouched) rather than Zandronum's per-function `ACTION_SET_RESULT` call.

- **Frame durations ignored in state chains:** The `Pickup:`, `Use:`, and `Drop:` state chains run at no frame cost (all states execute in the same tic). Frame durations in these chains are parsed but have no effect at runtime (states are not subject to tic countdown). Attempting to loop within these states (e.g., `TROO AB 4 Loop`) will trigger the self-jump abort after the loop target is reached, failing the entire chain.

- **Player/Owner semantics:** In `Pickup:` and `Use:`, the `Owner` pointer is the entity being given the item (the toucher during pickup, the item's current owner during use). Actions in these chains can modify the owner's inventory, properties, or state, but CustomInventory items themselves cannot access their own variables after being picked up (they "lose access to their variables, gaining direct access to the owner's variables instead," per the wiki).
