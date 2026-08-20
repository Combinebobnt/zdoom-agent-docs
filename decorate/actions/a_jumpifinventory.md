# `A_JumpIfInventory` (state action)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_JumpIfInventory` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_JumpIfInventory&oldid=55324) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:913-971`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIfInventory)` in `src/thingdef/thingdef_codeptr.cpp` — callable from any actor's state table.

Checks an actor's inventory and conditionally jumps to a state if a certain amount of an item is present. The same logic applies to checking the inventory of a different actor via an actor pointer.

## Signatures

```decorate
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

## Engine-family divergence: network synchronization

The "Network and client-side behavior" section above is Zandronum-specific and does not apply to
UZDoom. `A_JumpIfInventory` on UZDoom is a two-line ZScript wrapper
(`action state A_JumpIfInventory(...)` in `wadsrc/static/zscript/actors/checks.zs`) around
`Actor.CheckInventory()` (`wadsrc/static/zscript/actors/inventory_util.zs`) — neither contains a
`NETWORK_InClientMode()`-style gate, a `+CLIENTSIDEONLY`-equivalent check, or a `consoleplayer`
check. UZDoom has no client/server authority split anywhere in its source tree for this function:
it simply evaluates the inventory-amount condition and jumps (or doesn't), identically whether
called from a weapon/flash psprite or any other actor's state table — there is no networking
consideration at all.

## Engine-family divergence: unresolvable class name is not silent

The "Parameters" and "Failure modes and edge cases" sections above state that an unresolvable or
misspelled `inventorytype` name causes a silent no-jump with no error logged — true for Zandronum,
which resolves the class name at runtime via `EvalExpressionClass` (the `ACTION_PARAM_CLASS` macro
in `src/thingdef/thingdef.h`). **UZDoom resolves the class name at DECORATE parse time instead**,
via `FxClassTypeCast::Resolve()` (`src/common/scripting/backend/codegen.cpp`): an unknown class
name triggers a script message ("Unknown class name '...' of type '...'") printed as a load-time
warning by default (`MSG_OPTERROR`, which `FScriptPosition::Message` downgrades to `MSG_WARNING`
unless the `strictdecorate` cvar — `CVAR_GLOBALCONFIG | CVAR_ARCHIVE`, default `false` — is
enabled, in which case it becomes a hard, load-aborting `MSG_ERROR` instead). This is not silent:
the message appears in the console/log once, at map or WAD load, for each misspelled call site in
DECORATE source — not deferred to when the state actually executes. At runtime the resolved class
reference is still `null`, and `CheckInventory()`'s own `if (itemtype == null) return false;` guard
still means no jump occurs, matching Zandronum's runtime outcome — but a modder relying on the typo
going unnoticed will not get the same silence on UZDoom.

## Shared implementation

`A_JumpIfInventory` delegates to the internal `DoJumpIfInventory` helper, which is also used by `A_JumpIfInTargetInventory` (identical logic but checks the actor's `target` field instead of accepting an actor pointer).

## Failure modes and edge cases

- **Unresolvable class name:** Silently returns without jumping. No error is logged.
- **NULL actor pointer:** Returns without jumping (the `COPY_AAPTR_NOT_NULL` guard in the source ensures this).
- **Missing inventory item:** Returns without jumping — having zero of an item is not the same as having the item at zero amount; the item object must exist in the inventory.

## See also

- `A_JumpIfInTargetInventory` — same logic applied to the actor's `target` field instead of an
  explicit actor pointer.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) —
  detailed coverage of how state jumps interact with client/server in multiplayer
  (Zandronum-specific; see the divergence note above for UZDoom).
