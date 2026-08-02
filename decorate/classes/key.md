# `Key`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki Classes:Key (retrieved 2026-08-01, oldid=53839) + verified against Zandronum source `src/g_shared/a_keys.h:6–16` (native C++ class `AKey : public AInventory`) and `src/g_shared/a_keys.cpp`.
**Bucket:** `src/g_shared/a_keys.h:6–16` (native C++ class `AKey : public AInventory`, implementation in `src/g_shared/a_keys.cpp`); default DECORATE properties/flags set in `wadsrc/static/actors/shared/inventory.txt:150-155`.
**Source excerpt:** This file quotes Zandronum engine source verbatim (the `Key` DECORATE definition, `wadsrc/static/actors/shared/inventory.txt:150-155`); reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

A built-in actor class representing a key item used to unlock locked doors. `Key` is an abstract base class — it is never instantiated directly in DECORATE. Modders create concrete key items by inheriting from `Key` or from engine-defined subclasses like `DoomKey`, `HereticKey`, `HexenKey`, or `StrifeKey`. All keys are single-instance inventory items: a player can hold only one of each key type, even though multiple copies can be picked up in single-player (pickup re-triggers do not consolidate into a count).

## Key matching and locks

Lock-and-key matching in Zandronum is **class-identity based**, not inheritance-based, and does **not** use the `Species` property as the wiki describes for ZDoom/GZDoom. A custom key subclass — even one that inherits from a predefined key like `RedCard` — will not automatically open locks designated for its parent; it requires its own lock definition in a LOCKDEFS lump.

The actual lock-checking occurs via the engine function `P_CheckKeys(owner, keynum, remote)`, which:

1. Looks up the lock number (a value from `0` to `255`, typically drawn from a linedef's argument or a map special) in a global locks table
2. For each key group in that lock's key list, iterates through the required keys
3. Checks if the owner has an inventory item whose exact class type (`GetClass() == type`, not subclass-inclusive) matches any key in the group
4. Returns `true` if all key groups are satisfied; `false` otherwise

An undefined lock (one with no LOCKDEFS entry) triggers a failure message and sound. Lock numbers outside the `0–255` range pass (return `true`) without checking, and lock numbers ≤ 0 are skipped (always pass).

## The `KeyNumber` field

Each `AKey` subclass has a `BYTE KeyNumber` field, but this is **not** the lock number and is **not** used for lock matching. `KeyNumber` is assigned sequentially (starting from 1) by the LOCKDEFS parser when a map loads, and it is used only for display and cheat purposes: sorting keys in the HUD, the `give keys` cheat, and SBARINFO key-icon drawing. Lock checking uses the linedef/map-special argument directly, bypassing `KeyNumber` entirely.

## Multiplayer and pickup behavior

The `HandlePickup()` and `ShouldStay()` methods are gated on the network state (single-player vs. multiplayer):

- **Single-player (`NETSTATE_SINGLE`):** `HandlePickup()` returns `true` when the incoming item's class matches the actor's class, allowing infinite pickup. `ShouldStay()` returns `false`, so the pickup is removed after collection.
- **Multiplayer (any other net state):** Both methods call their parent `Inventory` implementation, which follows standard item re-pickup rules. `ShouldStay()` returns `true` (item stays in the world for respawn), and `HandlePickup()` respects the item's `IF_PICKUPGOOD` flag.

## DECORATE vs. ZScript — Zandronum differences

**This page documents Zandronum's DECORATE implementation, which differs significantly from the ZScript definition shown on the ZDoom wiki:**

- **No static helper methods in Zandronum:** The wiki's ZScript lists static methods (`IsLockDefined()`, `GetKeyTypeCount()`, `GetKeyType()`, `GetMapColorForLock()`, `GetMapColorForKey()`) that provide lock/key metadata. None of these exist in Zandronum's DECORATE. Equivalent C++ functions exist internally (`P_GetMapColorForLock`, `P_GetMapColorForKey`) but are not exposed to DECORATE or ACS.
- **Species property does not affect lock matching:** The wiki states that setting `Species` to an existing key makes a new key function as a duplicate. In Zandronum, this is not true — key matching is based on exact class type from LOCKDEFS definitions, and `Species` has no effect on lock checking (it remains a general actor property with no special meaning for keys).
- **No custom DECORATE properties:** The Key class adds no custom properties beyond those inherited from `Inventory`. `Inventory.PickupMessage`, `Inventory.Icon`, `Inventory.InterHubAmount`, and other standard inventory properties are available, but no Key-specific DECORATE properties exist (no `Key.LockNumber`, no `Key.Species`-lock-binding, etc.).
- **LOCKDEFS is the only lock-definition mechanism:** Zandronum has no way to define locks or key requirements from DECORATE — all lock setup happens in a LOCKDEFS lump, which is parsed at map load. This is a hard fork divergence from the wiki's framing: a modder cannot define entirely custom lock behaviors in DECORATE, only define new key items and reference locks defined in LOCKDEFS.

## DECORATE definition

```
ACTOR Key : Inventory native
{
  +DONTGIB
  +INVENTORY.INTERHUBSTRIP
  Inventory.PickupSound "misc/k_pkup"
}
```

The `+DONTGIB` flag prevents keys from being destroyed by crushers. `+INVENTORY.INTERHUBSTRIP` (the DECORATE spelling) is equivalent to `Inventory.InterHubAmount 0` in ZScript and clears keys between hub levels in hub-based campaigns.

## See also

- Predefined key subclasses: `DoomKey`, `HereticKey`, `HexenKey`, `StrifeKey`, and game-specific variants (`RedCard`, `KeyGreen`, etc.)
- Related lock-checking functions: `P_CheckKeys()` (line special evaluation), `P_GetMapColorForLock()` (automap display)
