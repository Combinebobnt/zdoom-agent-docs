# `bool A_GiveInventory(class<Inventory> itemtype, int amount = 0, int giveto = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_GiveInventory` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_GiveInventory&oldid=52121) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp` (`DoGiveInventory`) and `wadsrc/static/actors/actor.txt:217` (action native declaration). MaxAmount and client-mode corrections: Zandronum `src/g_shared/a_pickups.cpp:669-697` (`AInventory::HandlePickup`), `:770-785` (`AInventory::CreateCopy`), `:185-188` (`AAmmo::CreateCopy` clamp), `src/network.cpp:1598-1612` (`NETWORK_IsActorClientHandled`), `src/actorptrselect.h:85` (`COPY_AAPTR_NOT_NULL`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:2120-2180` (`static void DoGiveInventory`; dispatched via `A_GiveInventory` macro at `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_GiveInventory)` line 2182 and related thin wrappers).

Adds inventory items of a specified type to an actor's inventory. The function will not add more items than the inventory item's `MaxAmount` property permits.

On Zandronum there is one exception: the first give of a class that uses the base `AInventory::CreateCopy` (a plain `Inventory` item, not `Ammo`) does not clamp, so the receiver ends up holding the full `amount` even above `MaxAmount`. Later gives to a receiver that already holds the item clamp to `MaxAmount` in `HandlePickup`. `Ammo` clamps on the first give too.

## Parameters

- **`itemtype`** — the inventory item class to give. This must be a valid class derived from `Inventory`.
- **`amount`** — the number of samples to give. Default is `0`, which is internally converted to `1` (see "Health items" below). For non-health items, the spawned item's `Amount` field is directly set to this value. An `amount` above `MaxAmount` is not rejected. When the receiver already holds the item, the total is clamped to `MaxAmount` (see the Zandronum first-give exception above). A receiver already holding `MaxAmount` makes the give fail.
- **`giveto`** — an actor pointer selector determining which actor receives the item. Default is `AAPTR_DEFAULT`, which corresponds to the calling actor (the calling action function's `self`). See [Actor pointer selectors](../../acs/concepts/actor-pointers.md) for the full selector set.

## Health items: special amount handling

If the item class derives from `Health`, the `amount` parameter is multiplied by the item's own `Amount` property. For example, giving a `Medikit` (Health subclass with `Amount = 25`) with `A_GiveInventory("Medikit", 2)` results in the actor receiving `50` health points, not `2`.

## Success/failure and return value

The function returns `true` if the item was successfully added to the actor's inventory, or `false` if the pickup failed (e.g., the receiver already held the item's `MaxAmount`, so `CallTryPickup` rejected it, or the item class was invalid).

On Zandronum, if the receiver resolves to no actor (e.g. a `giveto` selector with nothing behind it), the function returns early without setting the result slot, so any prior value persists.

## Zandronum-specific: client/server behavior

**This is server-authoritative.** On clients:

- **For client-handled actors** (the calling actor has the `NETFL_CLIENTSIDEONLY` network flag or a `NetID` of 0, per `NETWORK_IsActorClientHandled`), the function runs to completion and returns the actual result (true/false). The test is on the calling actor, not the receiver.
- **When called from a player's weapon or flash psprite state**, the client also runs the give locally and sets the actual result. The server does not send a give command for these calls.
- **For all other actors**, the function **returns immediately without giving items or setting an explicit result**. The state-code result slot is not modified in this case (any prior value persists), so a DECORATE `if` branch off the return value will use that prior value, not the actual outcome. On the server, a successful give from such a call is sent to clients via `SERVERCOMMANDS_GiveInventoryNotOverwritingAmount`. A failed give sends nothing.

## Inventory-limit enforcement

The actual pickup attempt is delegated to `CallTryPickup`, which enforces the item's `MaxAmount` inventory limit and any item-specific pickup rules defined in the item's own `TryPickup` override.

## Related functions

Three related action functions share the same underlying implementation (`DoGiveInventory`):

- `A_GiveToTarget` — give to the actor's target instead of the actor itself
- `A_GiveToChildren` — give to all children (actors whose `master` is the calling actor)
- `A_GiveToSiblings` — give to all siblings (actors sharing the same `master`)
