# `bool A_TakeFromTarget(class<Inventory> itemtype, int amount = 0, int flags = 0, int forward_ptr = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_TakeFromTarget` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_TakeFromTarget&oldid=43420) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp` lines 2335–2338 and the shared `DoTakeInventory` helper at lines 2253–2328.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:2335-2338` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_TakeFromTarget)`, dispatched via a thin wrapper that passes `self->target` to the shared `DoTakeInventory` helper).

Removes inventory items of a specified type from the calling actor's **current target**'s inventory (or from another actor relative to the target, via the `forward_ptr` parameter). The amount removed is clamped to the inventory item's current amount (zero is the minimum), and items with the `INVENTORY.KEEPDEPLETED` flag are reduced to zero rather than destroyed.

## Parameters

- **`itemtype`** — the inventory item class to remove. This must be a valid class derived from `Inventory`. If the item class is invalid, the function returns `false` without modifying the inventory.
- **`amount`** — the number of samples to remove. Default is `0`. If zero or greater than or equal to the current amount, the entire stack is removed (unless the item has the `INVENTORY.KEEPDEPLETED` flag, in which case only the `Amount` field is reduced to zero).
- **`flags`** — control flags. Currently only one flag is defined:
  - `TIF_NOTAKEINFINITE` — If set, the function skips removal if the target is a player with infinite ammo enabled (either via the `DF_INFINITE_AMMO` dmflag or the `CF_INFINITEAMMO` cheat) and the item is ammo. In this case, the function still returns the original `res` value (whether the item existed and had amount > 0 before the check). **Crash risk against a non-player target:** Zandronum's guard is `if (flags & TIF_NOTAKEINFINITE && ((dmflags & DF_INFINITE_AMMO) || (receiver->player->cheats & CF_INFINITEAMMO)) && inv->IsKindOf(RUNTIME_CLASS(AAmmo)))` — `receiver->player` is dereferenced with no NULL guard. Short-circuiting only protects it when `DF_INFINITE_AMMO` is already set; `A_TakeFromTarget("SomeAmmo", 0, TIF_NOTAKEINFINITE)` aimed (via `forward_ptr`) at a non-player target that owns that ammo, with `DF_INFINITE_AMMO` off, is a null-pointer dereference. Worth checking against [the crash-and-bug checklist](../../acs/concepts/crash-and-bug-checklist.md) before shipping a `TIF_NOTAKEINFINITE` call where the resolved actor might not be a player.
- **`forward_ptr`** — an actor pointer selector determining which actor loses the item, with the calling actor's **target as the context** (not the calling actor itself). Default is `AAPTR_DEFAULT`, which corresponds to the calling actor's target. For example, `AAPTR_MASTER` here refers to the target's master, not the calling actor's master. See [Actor pointer selectors](../../acs/concepts/actor-pointers.md) for the full selector set.

## Success/failure and return value

The function returns `true` if the item was found and had an amount greater than zero **before the removal attempt**, or `false` if the item was not found or already had zero amount. **If the target is NULL**, the function returns early without modifying the result slot; any prior value persists, so a subsequent DECORATE `if` branch will use that prior value, not a guaranteed outcome.

Note that a return value of `true` indicates the item existed and had quantity; it does not guarantee the removal succeeded (e.g., if `TIF_NOTAKEINFINITE` blocked the removal, the return value is still `true`, but nothing was taken).

## Item cleanup behavior

- **Items without `INVENTORY.KEEPDEPLETED`**: When the amount reaches zero, the item object is destroyed (`Destroy()` called), and subsequent `FindInventory` lookups return NULL.
- **Items with `INVENTORY.KEEPDEPLETED`**: When the amount reaches zero, the item remains in the inventory with `Amount = 0`, and subsequent `FindInventory` lookups still return the item object.

## Engine-family divergence: `DoTakeInventory` helper differences

- **NULL-target/NULL-itemtype/unresolved-`forward_ptr` result behavior.** In UZDoom, `A_TakeFromTarget` and the shared `DoTakeInventory` helper are real ZScript functions with a `bool` return type. Every early-out path — an invalid/NULL `itemtype`, the calling actor having no target at all, or the `forward_ptr` selector resolving to NULL relative to the target — explicitly `return false`, and callers observe that actual `false` outcome. There is no separate "action result slot" that can be left unmodified. This differs from the Zandronum behavior described above under "Success/failure and return value": there, the underlying C++ codepointer's `if (!item) return;` and the `COPY_AAPTR_NOT_NULL` macro's early `return;` (triggered when the resolved receiver is NULL) both skip `ACTION_SET_RESULT` entirely, leaving whatever result a prior action function set in place. On UZDoom, a NULL target, NULL item class, or an unresolvable `forward_ptr` always yields a deterministic `false`, never a stale prior value.

- **`TIF_NOTAKEINFINITE`-blocked removal's return value.** Zandronum's `DoTakeInventory` computes `res` before checking the flag (`true` if the item existed with `Amount > 0`) and, when `TIF_NOTAKEINFINITE` blocks the removal, takes the branch that does nothing further — `res` keeps that pre-check `true` value, matching this file's documented "return value is still `true`, but nothing was taken." UZDoom's `Actor.TakeInventory` instead forces its result to `false` in the equivalent blocked branch, overriding the pre-check value. So on UZDoom, a `TIF_NOTAKEINFINITE`-blocked `A_TakeFromTarget` call returns `false`, not `true` — the opposite of Zandronum's documented behavior for this case.

- **Negative `amount` is taken as its absolute value, not passed through.** UZDoom's `Actor.TakeInventory` opens with `amount = abs(amount)` before depleting, so a negative `amount` behaves identically to the same positive magnitude. Zandronum's `DoTakeInventory` has no equivalent normalization: a negative `amount` fails both the `!amount` and `amount>=inv->Amount` checks (for a positive current `Amount`), falls into the subtraction branch, and computes `inv->Amount -= amount` — which, for a negative `amount`, *increases* the item's amount instead of removing any. A DECORATE/ZScript effect that (accidentally or deliberately) passes a negative `amount` to `A_TakeFromTarget` adds to the stack on Zandronum but removes `abs(amount)` from it on UZDoom — this mirrors the sibling `A_GiveToTarget` divergence already documented for negative-amount handling, just on the take side.

- **`HexenArmor`-derived items are excluded on Zandronum, not on UZDoom.** Zandronum's `DoTakeInventory` guards its entire removal block with `!inv->IsKindOf(RUNTIME_CLASS(AHexenArmor))`: when the found item is (or derives from) `HexenArmor`, the block is skipped altogether, `res` stays `false`, and the item is left completely untouched — `A_TakeFromTarget` targeting Hexen armor is a guaranteed no-op returning `false` on Zandronum. UZDoom's `Actor.TakeInventory` carries no such class exclusion; it depletes a `HexenArmor` item through the same generic path as any other item, and a full deplete (default `amount = 0`, or an `amount` at or above the current amount) reaches `HexenArmor`'s overridden `DepleteOrDestroy()`, which explicitly zeroes all four of its armor `Slots[]` entries rather than just adjusting a single `Amount` field. So on UZDoom, `A_TakeFromTarget` against Hexen armor is a real, functioning removal (returning `true` if the item existed) that Zandronum refuses to perform at all.

## Zandronum-specific: client/server behavior

**This is server-authoritative.** On clients:

- **`DoTakeInventory` has no client-handled-actor exemption at all** — unlike `A_RadiusGive`, which genuinely does check `NETWORK_InClientModeAndActorNotClientHandled`, this function's only client-side exemption is a bare `NETWORK_InClientMode()` check, and even that is skipped only when the calling actor is a player **and** the calling state is that player's own `ps_weapon`/`ps_flash` psprite state.
- **When that exemption applies** (player, weapon/flash state), the function runs to completion on the client and returns the actual result (true/false) — this is the normal case for a player's own weapon calling `A_TakeFromTarget` on itself/its target.
- **In every other case**, the function **returns immediately without removing items or setting an explicit result** when running on a client. The state-code result slot is not modified in this case (any prior value persists), so a DECORATE `if` branch off the return value will use that prior value, not the actual outcome. The server separately syncs inventory changes to clients via `SERVERCOMMANDS_TakeInventory`. This matches the general server-authoritative pattern for action functions in Zandronum's netcode. **A target's own client-handled/`+CLIENTSIDEONLY` status plays no role in this check** — only whether the calling actor is the local player's own weapon/flash state does.

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
