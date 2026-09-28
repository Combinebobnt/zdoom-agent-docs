# `A_JumpIfInventory` (state action)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_JumpIfInventory` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_JumpIfInventory&oldid=55324) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:913-971`; jump network updates from `src/thingdef/thingdef_codeptr.cpp:695-750`; `A_JumpIfInTargetInventory`'s pointer parameter from `wadsrc/static/actors/actor.txt:258`; load-time class-name resolution from `src/thingdef/thingdef_parse.cpp:929-933` and `src/thingdef/thingdef_expression.cpp:2538-2587,2863-2881`.
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
| `inventorytype` | `string` (resolves to class) | The name of the inventory item class to check — e.g. `"Clip"`, `"Shell"`, `"HealthPack"`. Must resolve to a valid `Inventory`-derived class. An unresolvable or misspelled name never jumps at runtime, but it is not silent: an `Unknown class name` message is printed when DECORATE loads (see the divergence note below). |
| `amount` | `int` | The threshold to check: if positive, jump when the actor has *at least* that many. If zero or negative, jump when the actor is carrying the *maximum possible* amount of that item (determined by the item's own `MaxAmount` property). This zero-and-max logic is useful for checking whether a player has a full magazine or ammo reserve without the amount varying based on backpack pickups. |
| `offset` / `label` | `int` or state label | The frame offset to jump (if integer) or the state label to jump to (if string). |
| `owner` | `int` (optional, defaults to `AAPTR_DEFAULT`) | An actor pointer constant (such as `AAPTR_DEFAULT`, `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER`) selecting which actor's inventory to check. If unspecified, defaults to `AAPTR_DEFAULT`, which refers to the calling actor itself. If the pointer resolves to `NULL`, no jump occurs. |

## Behavior

The function searches for the specified inventory item in the actor's (or the pointed-to actor's) inventory:

- If the item is **not found**, no jump occurs.
- If the item **is found**:
  - **When `amount > 0`:** Jump if `item->Amount >= amount`. Note that if you request more items than the item's `MaxAmount`, the actor normally can never accumulate that many, and the jump will never fire even if the actor is carrying the maximum. The wiki's own "Armor Addon" example demonstrates this pitfall: a request for 150 armor against a `BasicArmor` with `MaxAmount` of 100 will always fail, and you must work around it by creating an intermediate armor class with a higher `MaxAmount`.
- **When `amount <= 0`:** Jump if `item->Amount >= item->MaxAmount`. This is the "at max capacity" check mentioned above. Both zero and negative amounts trigger this branch.

## Network and client-side behavior

In network multiplayer (Zandronum):

- **Weapon and flash states** (player's weapon (`ps_weapon`) and flash (`ps_flash`) psprites) execute the check on both server and client. Each side evaluates it against its own copy of the inventory and jumps independently. The server sends no state-jump update for these, so a client whose inventory view differs from the server's can take a different branch.
- **All other states** on server-authoritative actors return early in client mode without checking or jumping, unless one of these conditions holds:
  - The actor is flagged `+CLIENTSIDEONLY` (visuals-only; doesn't require server sync), **or**
  - The actor is the console player's own body (its player number equals `consoleplayer`).
- **Server-side jumps in other states are pushed to clients.** When the server takes the jump, it sends the new frame to clients. For a player body it skips that player's own client. For any other actor it also sends a position update.
- **`CustomInventory` state chains** (`Pickup`, `Use` and the like): the call sets its action result to `false`, so it never counts as a success for the chain. A chain made only of jump calls therefore fails; some other action in it must succeed.

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

## Engine-family divergence: unresolvable class name severity

Neither engine is silent about an unresolvable or misspelled `inventorytype` name. Both resolve
the class name when DECORATE loads, not when the state executes, and print an `Unknown class name`
script message once per misspelled call site. At runtime the class reference is null and no jump
occurs on either engine. They differ only in whether the message can be escalated.

- **Zandronum** parses a `class<...>` parameter as an actor-name cast (`FxClassTypeCast`,
  `src/thingdef/thingdef_parse.cpp`). `FStateExpressions::ResolveAll()` resolves every state
  parameter in lax mode, so `FxClassTypeCast::Resolve()` (`src/thingdef/thingdef_expression.cpp`)
  prints the unknown name as a yellow script warning and substitutes a null class. The action's
  `if (!Type) return;` guard then skips the check. Zandronum has no `strictdecorate` cvar, so this
  is always a warning, never a load error.
- **UZDoom** resolves it in `FxClassTypeCast::Resolve()` (`src/common/scripting/backend/codegen.cpp`)
  with the message "Unknown class name '...' of type '...'" at `MSG_OPTERROR`, which
  `FScriptPosition::Message` downgrades to `MSG_WARNING` unless the `strictdecorate` cvar
  (`CVAR_GLOBALCONFIG | CVAR_ARCHIVE`, default `false`) is enabled. With it enabled the message is
  a hard, load-aborting `MSG_ERROR`. At runtime `CheckInventory()`'s `if (itemtype == null) return
  false;` guard means no jump occurs.

## Shared implementation

On Zandronum, `A_JumpIfInventory` delegates to the internal `DoJumpIfInventory` helper, which is also used by `A_JumpIfInTargetInventory`. That function runs identical logic but starts from the caller's `target` instead of the caller. It still takes a fourth actor-pointer parameter (`forward_ptr`, default `AAPTR_DEFAULT`), resolved relative to that target.

## Failure modes and edge cases

- **Unresolvable class name:** Returns without jumping at runtime. It is not silent: an `Unknown class name` message is printed when DECORATE loads (see the divergence note above).
- **NULL actor pointer:** Returns without jumping (the `COPY_AAPTR_NOT_NULL` guard in the source ensures this).
- **Missing inventory item:** Returns without jumping — having zero of an item is not the same as having the item at zero amount; the item object must exist in the inventory.

## See also

- `A_JumpIfInTargetInventory`: same logic starting from the actor's `target`, with its pointer
  parameter resolved relative to that target.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) —
  detailed coverage of how state jumps interact with client/server in multiplayer
  (Zandronum-specific; see the divergence note above for UZDoom).
