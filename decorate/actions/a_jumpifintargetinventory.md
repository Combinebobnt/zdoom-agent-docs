# `A_JumpIfInTargetInventory` (state action)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_JumpIfInTargetInventory` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfInTargetInventory&oldid=42399) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:973-976` and the shared `DoJumpIfInventory` logic at lines 913–966.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIfInTargetInventory)` in `src/thingdef/thingdef_codeptr.cpp` — callable from any actor's state table.

Checks the calling actor's target for a specific inventory item and conditionally jumps to a state if a certain amount is present. This is equivalent to `A_JumpIfInventory` with the `AAPTR_TARGET` pointer parameter, but more concise.

## Signatures

```decorate
state A_JumpIfInTargetInventory(string "inventorytype", int amount, int offset[, int pointer])
state A_JumpIfInTargetInventory(string "inventorytype", int amount, state "label"[, int pointer])
```

The third parameter can be either an integer frame offset or a state label — DECORATE resolves both forms via the parser.

## Parameters

| Parameter | Type | Meaning |
|-----------|------|---------|
| `inventorytype` | `string` (resolves to class) | The name of the inventory item class to check — e.g. `"Clip"`, `"Shell"`, `"HealthPack"`. Must resolve to a valid `Inventory`-derived class; an unresolvable or misspelled name silently causes no jump without error. |
| `amount` | `int` | The threshold to check: if positive, jump when the actor has *at least* that many. If zero or negative, jump when the actor is carrying the *maximum possible* amount of that item (determined by the item's own `MaxAmount` property). This zero-and-max logic is useful for checking whether a player has a full magazine or ammo reserve without the amount varying based on backpack pickups. |
| `offset` / `label` | `int` or state label | The frame offset to jump (if integer) or the state label to jump to (if string). |
| `pointer` | `int` (optional, defaults to `AAPTR_DEFAULT`) | An actor pointer constant (`AAPTR_DEFAULT`, `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER`) selecting which actor's pointer to forward from the target. If unspecified, defaults to `AAPTR_DEFAULT`, which refers to the target itself. If the resulting pointer resolves to `NULL`, no jump occurs. |

## Behavior

The function searches for the specified inventory item in the target's (or the target's pointed-to actor's) inventory:

- If the actor has no target, no jump occurs.
- If the item is **not found**, no jump occurs.
- If the item **is found**:
  - **When `amount > 0`:** Jump if `item->Amount >= amount`. Note that if you request more items than the item's `MaxAmount`, the target can never accumulate that many, and the jump will never fire even if the target is carrying the maximum.
  - **When `amount <= 0`:** Jump if `item->Amount >= item->MaxAmount`. This is the "at max capacity" check. Both zero and negative amounts trigger this branch.

## Zandronum-specific: client/server behavior

In network multiplayer (Zandronum):

- **Weapon and flash states** (player's weapon (`ps_weapon`) and flash (`ps_flash`) psprites) execute the check on both server and client, and always jump synchronously.
- **All other states** on server-authoritative actors return early in client mode without checking or jumping, unless one of these conditions holds:
  - The target actor is flagged `+CLIENTSIDEONLY` (visuals-only; doesn't require server sync), **or**
  - The target actor is the console player's own body.
- **Inventory state chains in `CustomInventory` `Pickup` states** should not rely on the return value — `A_JumpIfInTargetInventory` explicitly sets the action result to `false` to avoid breaking inventory state flow.

## Engine-family divergence: no client/server split in UZDoom

UZDoom's `A_JumpIfInTargetInventory` (`wadsrc/static/zscript/actors/checks.zs`) has none of the
client/server machinery described above. Its source tree contains no `NETWORK_InClientMode` check
and no `SERVERCOMMANDS_*` equivalent anywhere — the weapon/flash-psprite exception and the
console-player/`+CLIENTSIDEONLY` carve-out for "all other states" are entirely Zandronum netcode
concepts with no UZDoom counterpart. The underlying check (via the shared `Actor.CheckInventory`
method — see "Shared implementation" below) always runs its full logic and jumps unconditionally
and locally, regardless of which state type called it.

The explicit "clear the action result" step also has no UZDoom equivalent. UZDoom's action
function is declared `action state A_JumpIfInTargetInventory(...)`, returning either `null` or a
resolved state directly as the jump target — there is no separate boolean "action result slot"
for it to set, unlike Zandronum's native `DEFINE_ACTION_FUNCTION_PARAMS`/`ACTION_SET_RESULT`
calling convention. The specific mechanism Zandronum uses to protect `CustomInventory` `Pickup`
state chains from an unintended result value is therefore absent on UZDoom, though the underlying
concern (an unrelated boolean leaking into Pickup-chain flow) is a property of the older calling
convention rather than something UZDoom needs a replacement for.

## Shared implementation

`A_JumpIfInTargetInventory` delegates to the same internal `DoJumpIfInventory` helper used by `A_JumpIfInventory`, with the calling actor's `target` field passed in place of the actor pointer parameter. The two functions are otherwise identical in behavior and restrictions.

## Failure modes and edge cases

- **No target:** Returns without jumping — the `COPY_AAPTR_NOT_NULL` guard in the source ensures this.
- **Unresolvable class name:** Silently returns without jumping. No error is logged.
- **NULL actor pointer:** Returns without jumping (when a `pointer` parameter forwards to a `NULL`).
- **Missing inventory item:** Returns without jumping — having zero of an item is not the same as having the item at zero amount; the item object must exist in the inventory.
