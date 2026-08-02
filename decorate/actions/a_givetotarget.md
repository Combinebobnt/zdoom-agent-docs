# `bool A_GiveToTarget(class<Inventory> itemtype, int amount = 0, int giveto = AAPTR_DEFAULT)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_GiveToTarget` (retrieved 2026-07-31, oldid=43419) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp` lines 2187–2190 and the shared `DoGiveInventory` helper at lines 2120–2180.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:2187-2190` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_GiveToTarget)`, dispatched via a thin wrapper that passes `self->target` to the shared `DoGiveInventory` helper).

Adds inventory items of a specified type to the calling actor's **current target**'s inventory. The function will not add more items than the inventory item's `MaxAmount` property permits.

## Parameters

- **`itemtype`** — the inventory item class to give. This must be a valid class derived from `Inventory`.
- **`amount`** — the number of samples to give. Default is `0`, which is internally converted to `1` (see "Health items" below). For non-health items, the spawned item's `Amount` field is directly set to this value; if the item's `MaxAmount` is lower, `CallTryPickup` (see "Success/failure" below) will reject it.
- **`giveto`** — an actor pointer selector determining which actor receives the item, with the calling actor's **target as the context** (not the calling actor itself). Default is `AAPTR_DEFAULT`, which corresponds to the calling actor's target. For example, `AAPTR_MASTER` here refers to the target's master, not the calling actor's master. See [Actor pointer selectors](../../acs/concepts/actor-pointers.md) for the full selector set.

## Health items: special amount handling

If the item class derives from `Health`, the `amount` parameter is multiplied by the item's own `Amount` property. For example, giving a `Medikit` (Health subclass with `Amount = 25`) to a target with `A_GiveToTarget("Medikit", 2)` results in the target receiving `50` health points, not `2`.

## Success/failure and return value

The function returns `true` if the item was successfully added to the target's inventory, or `false` if the pickup failed (e.g., the item's `MaxAmount` was exceeded and `CallTryPickup` rejected it, or the item class was invalid). **If the target is NULL**, the function returns early without calling the action-result-setting mechanism; the state-code result slot is not modified in this case, so a subsequent DECORATE `if` branch will use any prior value, not the actual outcome.

## Zandronum-specific: client/server behavior

**This is server-authoritative.** On clients:

- **For client-handled actors** (where the calling actor has `MF6_CLIENTSIDE` or similar engine-recognized flag), the function runs to completion and returns the actual result (true/false).
- **For all other actors**, the function **returns immediately without giving items or setting an explicit result**. The state-code result slot is not modified in this case (any prior value persists), so a DECORATE `if` branch off the return value will use that prior value, not the actual outcome. The server separately syncs inventory changes to clients via `SERVERCOMMANDS_GiveInventoryNotOverwritingAmount`. This matches the general server-authoritative pattern for action functions in Zandronum's netcode.

## Inventory-limit enforcement

The actual pickup attempt is delegated to `CallTryPickup`, which enforces the item's `MaxAmount` inventory limit and any item-specific pickup rules defined in the item's own `TryPickup` override.

## Use cases

A common use case is rewarding the player (stored as the `target` of a dying monster after the engine calls `Die` and sets `target = killer`) with items or points on the monster's death. A monster can also use the `giveto` parameter to give items to other actors relative to its target — for example, `A_GiveToTarget("BlurSphere", 1, AAPTR_MASTER)` on a monster's death gives a blur sphere to the target's master, not the target itself.

## Related functions

Three other action functions share the same underlying implementation (`DoGiveInventory`):

- `A_GiveInventory` — give to the calling actor itself
- `A_GiveToChildren` — give to all children (actors whose `master` is the calling actor)
- `A_GiveToSiblings` — give to all siblings (actors sharing the same `master`)
