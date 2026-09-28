# `bool A_GiveToTarget(class<Inventory> itemtype, int amount = 0, int giveto = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_GiveToTarget` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_GiveToTarget&oldid=43419) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp` lines 2187–2190 and the shared `DoGiveInventory` helper at lines 2120–2180; result slot and NULL receiver: `src/thingdef/thingdef_codeptr.cpp:135-150` (`CallStateChain`), `src/thingdef/thingdef.h:435`, `src/actorptrselect.h:85`, `src/actorptrselect.cpp:35-92`; client check: `src/network.cpp:1598-1612`; `MaxAmount` handling: `src/g_shared/a_pickups.cpp:669-697`, `770-785`, `147-190`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:2187-2190` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_GiveToTarget)`, dispatched via a thin wrapper that passes `self->target` to the shared `DoGiveInventory` helper).

Adds inventory items of a specified type to the calling actor's **current target**'s inventory. How far the item's `MaxAmount` property limits the give differs by engine; see "Inventory-limit enforcement" below.

## Parameters

- **`itemtype`** — the inventory item class to give. This must be a valid class derived from `Inventory`.
- **`amount`** — the number of samples to give. Default is `0`, which is internally converted to `1` (see "Health items" below). For non-health items, the spawned item's `Amount` field is set to this value before the pickup attempt. See "Inventory-limit enforcement" below for what happens when it exceeds `MaxAmount`.
- **`giveto`** — an actor pointer selector determining which actor receives the item, with the calling actor's **target as the context** (not the calling actor itself). Default is `AAPTR_DEFAULT`, which corresponds to the calling actor's target. For example, `AAPTR_MASTER` here refers to the target's master, not the calling actor's master. See [Actor pointer selectors](../../acs/concepts/actor-pointers.md) for the full selector set.

## Health items: special amount handling

If the item class derives from `Health`, the `amount` parameter is multiplied by the item's own `Amount` property. For example, giving a `Medikit` (Health subclass with `Amount = 25`) to a target with `A_GiveToTarget("Medikit", 2)` results in the target receiving `50` health points, not `2`.

## Success/failure and return value

The outcome is `true` if the item was added to the receiver's inventory, or `false` if the pickup failed (e.g. `CallTryPickup` rejected it because the receiver already holds `MaxAmount`) or the item class was invalid. How that outcome is observed differs by engine:

- **UZDoom:** it is the function's `bool` return value.
- **Zandronum:** DECORATE action functions have no return value. The outcome is written only to the state-chain result of a `CustomInventory` `Pickup`/`Use`/`Drop` chain, and is discarded anywhere else. `CallStateChain` resets that result to `true` before every action, and the chain succeeds if any action leaves it `true`. **If the receiver is NULL**, the function returns early without writing the result, so the call counts as a success in the chain, not a failure.

## Engine-family divergence: `DoGiveInventory` helper differences

- **NULL-target result behavior.** In UZDoom, `A_GiveToTarget` and the shared `DoGiveInventory` helper are ZScript functions returning `bool`. Both NULL-receiver cases (the calling actor has no target at all, or the `giveto` selector resolves to NULL relative to the target) return `false`, and callers observe that `false`. On Zandronum, the `COPY_AAPTR_NOT_NULL` macro returns early without setting a result, which a `CustomInventory` chain reads as success (see "Success/failure and return value" above).

- **NULL target with a static `giveto` selector.** UZDoom returns `false` as soon as the target is NULL, before the selector is consulted. Zandronum's `COPY_AAPTR` resolves the static selectors (`AAPTR_PLAYER1` to `AAPTR_PLAYER8`, `AAPTR_NULL`) even when the origin actor is NULL. So on Zandronum, `A_GiveToTarget("Medikit", 1, AAPTR_PLAYER1)` from an actor with no target still gives to player 1.

- **Zero-vs-negative `amount` clamping.** Zandronum only replaces an `amount` of exactly `0` with `1`. A negative `amount` passes through unchanged, so the item's `Amount` (or, for `Health` items, the multiplied `Amount`) ends up negative. UZDoom replaces any non-positive `amount` with `1`, so a negative `amount` behaves like `0`. A DECORATE/ZScript effect that relies on passing a negative `amount` to `A_GiveToTarget` (e.g. to subtract health via a `Health`-derived item) behaves differently between the two engines.

- **Owned-inventory receiver guard.** UZDoom's `DoGiveInventory` has an explicit early-out not present in Zandronum's version. If the resolved receiver is itself an `Inventory` item that already has an owner, the give returns `false` outright. No equivalent check exists in the Zandronum implementation's `DoGiveInventory`. This document does not trace whether Zandronum's `CallTryPickup` path independently rejects this case for an owned-item receiver, only that the explicit helper-level guard itself is UZDoom-specific.

## Zandronum-specific: client/server behavior

**This is server-authoritative, except in weapon states.** The client check looks at the calling actor (`self`), not the receiver:

- **Called from the player's weapon or flash psprite state:** the client check is skipped, so a client runs the give locally, and the server never sends this give to clients.
- **Otherwise, on a client, if the calling actor is not client-handled** (it lacks the `CLIENTSIDEONLY` flag and has a nonzero network ID), the function **returns immediately without giving items or writing a result**, which a `CustomInventory` chain reads as success. A client-handled calling actor runs the give locally.
- **On the server**, a successful give from any other state is sent to clients with `SERVERCOMMANDS_GiveInventoryNotOverwritingAmount`. A failed give sends nothing.

## Inventory-limit enforcement

The pickup attempt is delegated to `CallTryPickup`, which applies any item-specific rules in the item's own `TryPickup` override. For generic items, `MaxAmount` works as follows:

- **Receiver already holds the item:** both engines add `amount` and clamp the total to `MaxAmount` (unless `sv_unlimited_pickup` is on). The give fails only when the receiver is already at `MaxAmount`.
- **Receiver does not hold it yet:** UZDoom clamps the new copy to `MaxAmount`. Zandronum's generic `Inventory` copy is not clamped, so a first give with `amount` above `MaxAmount` leaves the receiver holding more than `MaxAmount`. On Zandronum, `Ammo` clamps in its own copy step (after applying the skill's ammo factor unless `Inventory.IgnoreSkill` is set).

`Health` items and other classes with their own `TryPickup` follow their own rules instead.

## Use cases

A common use case is rewarding the player (stored as the `target` of a dying monster after the engine calls `Die` and sets `target = killer`) with items or points on the monster's death. A monster can also use the `giveto` parameter to give items to other actors relative to its target — for example, `A_GiveToTarget("BlurSphere", 1, AAPTR_MASTER)` on a monster's death gives a blur sphere to the target's master, not the target itself.

## Related functions

Three other action functions share the same underlying implementation (`DoGiveInventory`):

- `A_GiveInventory` — give to the calling actor itself
- `A_GiveToChildren` — give to all children (actors whose `master` is the calling actor)
- `A_GiveToSiblings` — give to all siblings (actors sharing the same `master`)
