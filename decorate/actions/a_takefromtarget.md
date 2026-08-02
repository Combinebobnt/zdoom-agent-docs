# `bool A_TakeFromTarget(class<Inventory> itemtype, int amount = 0, int flags = 0, int forward_ptr = AAPTR_DEFAULT)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_TakeFromTarget` (retrieved 2026-08-01, oldid=43420) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp` lines 2335–2338 and the shared `DoTakeInventory` helper at lines 2253–2328.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:2335-2338` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_TakeFromTarget)`, dispatched via a thin wrapper that passes `self->target` to the shared `DoTakeInventory` helper).

Removes inventory items of a specified type from the calling actor's **current target**'s inventory (or from another actor relative to the target, via the `forward_ptr` parameter). The amount removed is clamped to the inventory item's current amount (zero is the minimum), and items with the `INVENTORY.KEEPDEPLETED` flag are reduced to zero rather than destroyed.

## Parameters

- **`itemtype`** — the inventory item class to remove. This must be a valid class derived from `Inventory`. If the item class is invalid, the function returns `false` without modifying the inventory.
- **`amount`** — the number of samples to remove. Default is `0`. If zero or greater than or equal to the current amount, the entire stack is removed (unless the item has the `INVENTORY.KEEPDEPLETED` flag, in which case only the `Amount` field is reduced to zero).
- **`flags`** — control flags. Currently only one flag is defined:
  - `TIF_NOTAKEINFINITE` — If set, the function skips removal if the target is a player with infinite ammo enabled (either via the `DF_INFINITE_AMMO` dmflag or the `CF_INFINITEAMMO` cheat) and the item is ammo. In this case, the function still returns the original `res` value (whether the item existed and had amount > 0 before the check).
- **`forward_ptr`** — an actor pointer selector determining which actor loses the item, with the calling actor's **target as the context** (not the calling actor itself). Default is `AAPTR_DEFAULT`, which corresponds to the calling actor's target. For example, `AAPTR_MASTER` here refers to the target's master, not the calling actor's master. See [Actor pointer selectors](../../acs/concepts/actor-pointers.md) for the full selector set.

## Success/failure and return value

The function returns `true` if the item was found and had an amount greater than zero **before the removal attempt**, or `false` if the item was not found or already had zero amount. **If the target is NULL**, the function returns early without modifying the result slot; any prior value persists, so a subsequent DECORATE `if` branch will use that prior value, not a guaranteed outcome.

Note that a return value of `true` indicates the item existed and had quantity; it does not guarantee the removal succeeded (e.g., if `TIF_NOTAKEINFINITE` blocked the removal, the return value is still `true`, but nothing was taken).

## Item cleanup behavior

- **Items without `INVENTORY.KEEPDEPLETED`**: When the amount reaches zero, the item object is destroyed (`Destroy()` called), and subsequent `FindInventory` lookups return NULL.
- **Items with `INVENTORY.KEEPDEPLETED`**: When the amount reaches zero, the item remains in the inventory with `Amount = 0`, and subsequent `FindInventory` lookups still return the item object.

## Zandronum-specific: client/server behavior

**This is server-authoritative.** On clients:

- **For client-handled actors** (where the target has `MF6_CLIENTSIDE` or similar engine-recognized flag), the function runs to completion and returns the actual result (true/false).
- **For all other actors**, the function **returns immediately without removing items or setting an explicit result** when the actor calling this function is not a player's weapon or flash state. The state-code result slot is not modified in this case (any prior value persists), so a DECORATE `if` branch off the return value will use that prior value, not the actual outcome. The server separately syncs inventory changes to clients via `SERVERCOMMANDS_TakeInventory`. This matches the general server-authoritative pattern for action functions in Zandronum's netcode.

## Related functions

Three other action functions share the same underlying implementation (`DoTakeInventory`):

- `A_TakeInventory` — remove from the calling actor itself
- `A_TakeFromChildren` — remove from all children (actors whose `master` is the calling actor)
- `A_TakeFromSiblings` — remove from all siblings (actors sharing the same `master`)

The give-family counterparts are:

- `A_GiveToTarget` — add to the calling actor's target
- `A_GiveInventory` — add to the calling actor itself
- `A_GiveToChildren` — add to all children
- `A_GiveToSiblings` — add to all siblings
