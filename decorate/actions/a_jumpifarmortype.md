# `A_JumpIfArmorType`

**Tier:** A
**Engine:** Zandronum 3.2.1, UZDoom 4.15pre
**Provenance:** ZDoom Wiki (retrieved 2026-08-01, oldid=42385) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:983-996` and `wadsrc/static/actors/actor.txt:216`.
**Bucket:** Action function (`DEFINE_ACTION_FUNCTION(AActor, A_JumpIfArmorType)` in `src/thingdef/thingdef_codeptr.cpp`).

Checks whether the actor's equipped armor matches a specified type. If the armor type matches and the armor amount is at least the minimum threshold, the jump is performed.

## Signature

```decorate
action native A_JumpIfArmorType(string Type, state label, int amount = 1)
```

## Parameters

- **`Type`** (string): The name of the armor class to check for (e.g., `"BlueArmor"`, `"GreenArmor"`). Compared against the equipped `BasicArmor` item's `ArmorType` field, which is set to the class name of the armor pickup that was picked up.
- **`label`** (state): The state to jump to if the condition is met.
- **`amount`** (int, optional, default 1): The minimum armor amount (points) required for the jump to occur. The equipped armor must have at least this amount. **Wiki divergence:** The wiki does not state the default value.

## Behavior

The function checks whether a `BasicArmor` item exists in the actor's inventory. If one exists:

1. Compares the armor's `ArmorType` field against the `Type` parameter.
2. Compares the armor's current `Amount` against the `amount` parameter.
3. If both conditions are true (type matches and `Amount >= amount`), the jump occurs.

The action function does **not** set a result value (`ACTION_SET_RESULT(false)` in the source), which is significant for inventory state chains like `CustomInventory.Pickup:` — jump outcomes do not cause the state chain to succeed or fail, allowing subsequent states to be evaluated.

## Network synchronization

The source includes a `[BB]` comment suggesting clients' knowledge of player inventory should allow safe clientside evaluation ("Clients know the player's inventory, so this is hopefully okay"), but this is a Zandronum-specific netcode annotation and the phrasing is hedged. Jump functions perform differently inside anonymous functions due to their network synchronization requirements; see the DECORATE concepts `[network-jump-synchronization](../concepts/network-jump-synchronization.md)` for details.

## Important note on armor type persistence

The `ArmorType` field is set to the class name of whichever armor pickup was picked up most recently. Picking up a different armor type (e.g., `GreenArmor` after `BlueArmor`, or `ArmorBonus` after either) overwrites this field. This means a modder designing conditional pickup logic must account for the fact that repeated pickups of different item types change what armor type is "equipped."

## Examples

**Example 1: Pickup-gated on armor type**

```decorate
ACTOR CustomArmorBonus1 : CustomInventory
{
  Inventory.PickupMessage "$GOTARMBONUS"
  States
  {
  Spawn:
    BON2 ABCDCB 6
    Loop
  Pickup:
    TNT1 A 0 A_JumpIfArmorType("BlueArmor", "GiveArmorBonus")
    Fail
  GiveArmorBonus:
    TNT1 A 0 A_GiveInventory("ArmorBonus", 1)
    Stop
  }
}
```

This item grants an armor bonus only if the player has `BlueArmor` equipped. If they lack `BlueArmor`, the pickup fails.

**Example 2: Type and amount check**

```decorate
ACTOR ArmorShard : CustomInventory
{
  Inventory.PickupMessage "Picked up an armor shard."
  States
  {
  Spawn:
    BON2 A 6
    BON2 D 6 Bright
    Loop
  Pickup:
    TNT1 A 0 A_JumpIfArmorType("GreenArmor", "NoPickup", 100)
    TNT1 A 0 A_JumpIfArmorType("GreenArmor", "GiveArmorBonus")
    Fail
  NoPickup:
    TNT1 A 0
    Fail
  GiveArmorBonus:
    TNT1 A 0 A_GiveInventory("ArmorBonus", 1)
    Stop
  }
}
```

This item checks two conditions: "Do I have `GreenArmor` with at least 100 armor?"; if yes, pickup fails. If no, "Do I have `GreenArmor` at all?"; if yes, grant an armor shard; if no, pickup fails. This prevents overcapping a fully-healthy green-armor character while allowing undamaged green-armor wearers to pick up shards.

## See also

- [Creating inventory items](../concepts/) (Inventory and CustomInventory base classes, pickup lifecycle)
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) (why jump functions' behavior differs in anonymous functions)
