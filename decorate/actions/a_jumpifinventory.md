# `A_JumpIfInventory` (state action)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_JumpIfInventory` (retrieved 2026-07-31, oldid=55324) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:913-971`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIfInventory)` in `src/thingdef/thingdef_codeptr.cpp` — callable from any actor's state table.

Checks an actor's inventory and conditionally jumps to a state if a certain amount of an item is present. The same logic applies to checking the inventory of a different actor via an actor pointer.

## Signatures

```c
state A_JumpIfInventory(string "inventorytype", int amount, int offset[, int owner])
state A_JumpIfInventory(string "inventorytype", int amount, state "label"[, int owner])
```

The third parameter can be either an integer frame offset or a state label — DECORATE resolves both forms via the parser.

## Parameters

| Parameter | Type | Meaning |
|-----------|------|---------|
| `inventorytype` | `string` (resolves to class) | The name of the inventory item class to check — e.g. `"Clip"`, `"Shell"`, `"HealthPack"`. Must resolve to a valid `Inventory`-derived class; an unresolvable or misspelled name silently causes no jump without error. |
| `amount` | `int` | The threshold to check: if positive, jump when the actor has *at least* that many. If zero or negative, jump when the actor is carrying the *maximum possible* amount of that item (determined by the item's own `MaxAmount` property). This zero-and-max logic is useful for checking whether a player has a full magazine or ammo reserve without the amount varying based on backpack pickups. |
| `offset` / `label` | `int` or state label | The frame offset to jump (if integer) or the state label to jump to (if string). |
| `owner` | `int` (optional, defaults to `AAPTR_DEFAULT`) | An actor pointer constant (`AAPTR_DEFAULT`, `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER`) selecting which actor's inventory to check. If unspecified, defaults to `AAPTR_DEFAULT`, which refers to the calling actor itself. If the pointer resolves to `NULL`, no jump occurs. |

## Behavior

The function searches for the specified inventory item in the actor's (or the pointed-to actor's) inventory:

- If the item is **not found**, no jump occurs.
- If the item **is found**:
  - **When `amount > 0`:** Jump if `item->Amount >= amount`. Note that if you request more items than the item's `MaxAmount`, the actor can never accumulate that many, and the jump will never fire even if the actor is carrying the maximum. The wiki's own "Armor Addon" example demonstrates this pitfall: a request for 150 armor against a `BasicArmor` with `MaxAmount` of 100 will always fail, and you must work around it by creating an intermediate armor class with a higher `MaxAmount`.
- **When `amount <= 0`:** Jump if `item->Amount >= item->MaxAmount`. This is the "at max capacity" check mentioned above. Both zero and negative amounts trigger this branch.

## Network and client-side behavior

In network multiplayer (Zandronum):

- **Weapon and flash states** (player's weapon (`ps_weapon`) and flash (`ps_flash`) psprites) execute the check on both server and client, and always jump synchronously.
- **All other states** on server-authoritative actors return early in client mode without checking or jumping, unless one of these conditions holds:
  - The actor is flagged `+CLIENTSIDEONLY` (visuals-only; doesn't require server sync), **or**
  - The actor is the console player's own body (`self->player && consoleplayer`).
- **Inventory state chains in `CustomInventory` `Pickup` states** should not rely on the return value — `A_JumpIfInventory` explicitly sets the action result to `false` to avoid breaking inventory state flow.

## Shared implementation

`A_JumpIfInventory` delegates to the internal `DoJumpIfInventory` helper, which is also used by `A_JumpIfInTargetInventory` (identical logic but checks the actor's `target` field instead of accepting an actor pointer).

## Failure modes and edge cases

- **Unresolvable class name:** Silently returns without jumping. No error is logged.
- **NULL actor pointer:** Returns without jumping (the `COPY_AAPTR_NOT_NULL` guard in the source ensures this).
- **Missing inventory item:** Returns without jumping — having zero of an item is not the same as having the item at zero amount; the item object must exist in the inventory.
