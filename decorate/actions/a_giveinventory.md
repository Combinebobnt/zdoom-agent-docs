# `bool A_GiveInventory(class<Inventory> itemtype, int amount = 0, int giveto = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_GiveInventory` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_GiveInventory&oldid=52121) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp` (`DoGiveInventory`) and `wadsrc/static/actors/actor.txt:217` (action native declaration).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:2120-2180` (`static void DoGiveInventory`; dispatched via `A_GiveInventory` macro at `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_GiveInventory)` line 2182 and related thin wrappers).

Adds inventory items of a specified type to an actor's inventory. The function will not add more items than the inventory item's `MaxAmount` property permits.

## Parameters

- **`itemtype`** — the inventory item class to give. This must be a valid class derived from `Inventory`.
- **`amount`** — the number of samples to give. Default is `0`, which is internally converted to `1` (see "Health items" below). For non-health items, the spawned item's `Amount` field is directly set to this value; if the item's `MaxAmount` is lower, `CallTryPickup` (see "Success/failure" below) will reject it.
- **`giveto`** — an actor pointer selector determining which actor receives the item. Default is `AAPTR_DEFAULT`, which corresponds to the calling actor (the calling action function's `self`). See [Actor pointer selectors](../../acs/concepts/actor-pointers.md) for the full selector set.

## Health items: special amount handling

If the item class derives from `Health`, the `amount` parameter is multiplied by the item's own `Amount` property. For example, giving a `Medikit` (Health subclass with `Amount = 25`) with `A_GiveInventory("Medikit", 2)` results in the actor receiving `50` health points, not `2`.

## Success/failure and return value

The function returns `true` if the item was successfully added to the actor's inventory, or `false` if the pickup failed (e.g., the item's `MaxAmount` was exceeded and `CallTryPickup` rejected it, or the item class was invalid).

## Zandronum-specific: client/server behavior

**This is server-authoritative.** On clients:

- **For client-handled actors** (where the calling actor has `MF6_CLIENTSIDE` or similar engine-recognized flag), the function runs to completion and returns the actual result (true/false).
- **For all other actors**, the function **returns immediately without giving items or setting an explicit result**. The state-code result slot is not modified in this case (any prior value persists), so a DECORATE `if` branch off the return value will use that prior value, not the actual outcome. The server separately syncs inventory changes to clients via `SERVERCOMMANDS_GiveInventoryNotOverwritingAmount`. This matches the general server-authoritative pattern for action functions in Zandronum's netcode.

## Inventory-limit enforcement

The actual pickup attempt is delegated to `CallTryPickup`, which enforces the item's `MaxAmount` inventory limit and any item-specific pickup rules defined in the item's own `TryPickup` override.

## Related functions

Three related action functions share the same underlying implementation (`DoGiveInventory`):

- `A_GiveToTarget` — give to the actor's target instead of the actor itself
- `A_GiveToChildren` — give to all children (actors whose `master` is the calling actor)
- `A_GiveToSiblings` — give to all siblings (actors sharing the same `master`)
