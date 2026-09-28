# `A_JumpIfArmorType`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfArmorType&oldid=42385) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:983-996` and `wadsrc/static/actors/actor.txt:216`; armor type persistence from `src/g_shared/a_armor.cpp:153,275,299,391-397`; network behavior from `src/thingdef/thingdef_codeptr.cpp:695-758`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIfArmorType)` in `src/thingdef/thingdef_codeptr.cpp`).

Checks whether the actor's equipped armor matches a specified type. If the armor type matches and the armor amount is at least the minimum threshold, the jump is performed.

## Signature

```decorate
action native A_JumpIfArmorType(string Type, state label, int amount = 1)
```

## Parameters

- **`Type`** (string): The name of the armor class to check for (e.g., `"BlueArmor"`, `"GreenArmor"`). Compared as a name against the equipped `BasicArmor` item's `ArmorType` field. That comparison is an exact class-name match, with no inheritance check. See "Armor type persistence" below for which pickups set the field.
- **`label`** (state): The state to jump to if the condition is met.
- **`amount`** (int, optional, default 1): The minimum armor amount (points) required for the jump to occur. The equipped armor must have at least this amount. **Wiki divergence:** The wiki does not state the default value.

## Behavior

The function checks whether a `BasicArmor` item exists in the actor's inventory. If one exists:

1. Compares the armor's `ArmorType` field against the `Type` parameter.
2. Compares the armor's current `Amount` against the `amount` parameter.
3. If both conditions are true (type matches and `Amount >= amount`), the jump occurs.

In Zandronum the action function explicitly sets its result to false (`ACTION_SET_RESULT(false)`), which matters for inventory state chains like `CustomInventory.Pickup:`. The jump outcome by itself does not make the state chain succeed.

## Network synchronization

In Zandronum the jump passes no client-update flags (`ACTION_JUMP(JumpOffset, 0)`), so the server sends clients no state change when it jumps, and there is no client-mode guard. Each client evaluates the armor check against its own copy of the actor's inventory. The source's `[BB]` comment justifies this with "Clients know the player's inventory, so this is hopefully okay", a hedged assumption. Compare `A_JumpIfCloser`, whose jump does send a frame and position update. See [Jump functions and network synchronization](../concepts/network-jump-synchronization.md), especially its "Cause 2" section on inventory-based conditions lagging the server.

## Armor type persistence

Not every armor pickup sets `ArmorType`, and it does not always track the most recent pickup:

- A `BasicArmorPickup` (e.g. `GreenArmor`, `BlueArmor`) sets it to its own class name, but only if the pickup is accepted. One offering less than the armor you already have is refused, so `GreenArmor` touched while wearing undamaged `BlueArmor` changes nothing. `GreenArmor` picked up after `BlueArmor` has worn below 100 does overwrite the type.
- A `BasicArmorBonus` (e.g. `ArmorBonus`) sets it only when you currently have no armor points. An `ArmorBonus` picked up while wearing `BlueArmor` adds points but leaves the type as `BlueArmor`.
- When armor absorbs damage down to 0 points, the type is reset to none, so no `Type` matches until new armor is picked up.

Conditional pickup logic should account for these cases rather than assume the last armor item touched is the "equipped" type.

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

This item checks two conditions: "Do I have `GreenArmor` with at least 100 armor?"; if yes, pickup fails. If no, "Do I have `GreenArmor` at all?"; if yes, grant an `ArmorBonus`; if no, pickup fails. This refuses the shard once green armor is at 100 or more, while letting green-armor wearers below 100 pick it up.

## See also

- [Creating inventory items](../concepts/) (Inventory and CustomInventory base classes, pickup lifecycle)
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) (why jump functions' behavior differs in anonymous functions)
