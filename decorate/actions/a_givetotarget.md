# `bool A_GiveToTarget(class<Inventory> itemtype, int amount = 0, int giveto = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_GiveToTarget` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_GiveToTarget&oldid=43419) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp` lines 2187–2190 and the shared `DoGiveInventory` helper at lines 2120–2180.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

## Engine-family divergence: `DoGiveInventory` helper differences

- **NULL-target result behavior.** In UZDoom, `A_GiveToTarget` and the shared `DoGiveInventory` helper are real ZScript functions with a `bool` return type. Every code path — including both NULL-receiver cases (the calling actor has no target at all, or the `giveto` pointer selector resolves to NULL relative to the target) — explicitly `return false`, and callers observe that actual `false` outcome. There is no separate "action result slot" that can be left unmodified. This differs from the Zandronum behavior described above under "Success/failure and return value": there, the underlying C++ codepointer's early `return;` (triggered by the `COPY_AAPTR_NOT_NULL` macro when the resolved receiver is NULL) skips `ACTION_SET_RESULT` entirely, leaving whatever result a prior action function set in place. On UZDoom, a NULL target (or an unresolvable `giveto` pointer) always yields a deterministic `false`, never a stale prior value.

- **Zero-vs-negative `amount` clamping.** Zandronum only special-cases `amount == 0` (`if (amount==0) amount=1;`); a negative `amount` passes through unchanged, so `item->Amount = amount` (or, for `Health` items, `Amount *= amount`) ends up negative. UZDoom instead clamps any non-positive value: `if (amount <= 0) { amount = 1; }`, so a negative `amount` is treated the same as `0` and becomes `1`. A DECORATE/ZScript effect that relies on passing a negative `amount` to `A_GiveToTarget` (e.g. to subtract health via a `Health`-derived item) behaves differently between the two engines.

- **Owned-inventory receiver guard.** UZDoom's `DoGiveInventory` has an explicit early-out not present in Zandronum's version: `if (receiver is 'Inventory' && Inventory(receiver).Owner != null) return false;` — i.e. if the resolved receiver is itself an `Inventory` item that is already owned by something, the give is rejected outright. No equivalent check exists in the Zandronum implementation's `DoGiveInventory`. This document does not trace whether Zandronum's `CallTryPickup` path independently rejects this case for an owned-item receiver, only that the explicit helper-level guard itself is UZDoom-specific.

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
