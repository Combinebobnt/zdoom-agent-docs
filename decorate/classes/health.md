# `Health`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `Classes:Health` (retrieved 2026-08-01, oldid=54036) + verified against the Zandronum source's `src/g_shared/a_pickups.h` and `a_pickups.cpp`.
**Bucket:** native C++ base class (`src/g_shared/a_pickups.h:404-414`; `AHealth : public AInventory`).

A built-in DECORATE base class for items that restore an actor's health when picked up. This is a base class only — never instantiate `Health` directly in a WAD or map. Define a derived actor class (like `Stimpack` or a custom health item) and set `Inventory.Amount` and `Inventory.MaxAmount` to control how much health the item grants and what the maximum allowable health is after pickup.

## Pickup behavior

Health items call `TryPickup` when collected, which invokes the engine's `P_GiveBody` function. Health items:
- Are **not** automatically effective when picked up if the actor is already at or above their maximum health (despite wiki descriptions suggesting this). Items like `HealthBonus` use the `+INVENTORY.ALWAYSPICKUP` flag to force pickup even when at max health.
- Call `GoAwayAndDie()` and disappear only if `P_GiveBody` returns true (the health was successfully added).
- Return false and remain in the map if the receiving actor is dead, if the actor is a voodoo-doll dummy player (multiplayer), or (in networked multiplayer) if the client is not allowed to know the target's health.

## `Health.LowMessage`

Health items support one custom property: `Health.LowMessage <threshold>, "<message>"`. When the item is picked up and the recipient's *previous* health (stored during `TryPickup`) was below the specified threshold, the pickup message is replaced with the provided message string. If no low-health message is set, the default `Inventory.PickupMessage` is used.

Example (DECORATE):
```
ACTOR Medikit : Health 2012
{
  Inventory.Amount 25
  Inventory.PickupMessage "$GOTMEDIKIT"
  Health.LowMessage 25, "$GOTMEDINEED"
  States { Spawn: MEDI A -1; Stop; }
}
```

In this example, if a player with health below 25 picks up the medikit, the pickup message becomes "$GOTMEDINEED"; otherwise it's "$GOTMEDIKIT".

## Zandronum-specific note

The wiki page shown (a ZDoom wiki page) describes the GZDoom/UZDoom variant using ZScript syntax and UZDoom-specific features like `+INVENTORY.ISHEALTH` flag and `property` declarations. These do not exist in Zandronum's DECORATE system. Zandronum uses DECORATE actor inheritance only — define a class as `ACTOR YourHealthItem : Health { ... }`.

## Related

- `HealthPickup` — a separate native class for health items that are stored in inventory and used later (via the `Use` action) rather than consumed immediately on pickup.
- `AMaxHealth` — a Zandronum-specific native class that increases both the player's current health and their maximum-health bonus simultaneously.
