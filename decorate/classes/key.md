# `Key`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki Classes:Key (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3AKey&oldid=53839) + verified against Zandronum source `src/g_shared/a_keys.h:6–16` (native C++ class `AKey : public AInventory`) and `src/g_shared/a_keys.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** native C++ class in Zandronum (`src/g_shared/a_keys.h:6–16`, `AKey : public AInventory`, implementation in `src/g_shared/a_keys.cpp`; default DECORATE properties/flags in `wadsrc/static/actors/shared/inventory.txt:150-155`); ZScript class in UZDoom (`wadsrc/static/zscript/actors/inventory/inv_misc.zs:50-91`, `class Key : Inventory`, an ordinary scripted class with no native backing beyond what `Inventory` itself provides; lock/key engine internals in `src/gamedata/a_keys.h` and `src/gamedata/a_keys.cpp`).
**Source excerpt:** This file quotes Zandronum engine source verbatim (the `Key` DECORATE definition, `wadsrc/static/actors/shared/inventory.txt:150-155`); reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

A built-in actor class representing a key item used to unlock locked doors. `Key` is an abstract base class — it is never instantiated directly in DECORATE. Modders create concrete key items by inheriting from `Key` or from engine-defined subclasses like `DoomKey`, `HereticKey`, `HexenKey`, or `StrifeKey`. All keys are single-instance inventory items: a player can hold only one of each key type, even though multiple copies can be picked up in single-player (pickup re-triggers do not consolidate into a count).

## Key matching and locks

Lock-and-key matching in Zandronum is **class-identity based**, not inheritance-based, and does **not** use the `Species` property as the wiki describes for ZDoom/GZDoom. A custom key subclass — even one that inherits from a predefined key like `RedCard` — will not automatically open locks designated for its parent; it requires its own lock definition in a LOCKDEFS lump.

Zandronum's lock-checking occurs via its own engine function `P_CheckKeys(owner, keynum, remote)` (`src/g_shared/a_keys.cpp:398`), which:

1. Looks up the lock number (a value from `0` to `255`, typically drawn from a linedef's argument or a map special) in a global locks table
2. For each key group in that lock's key list, iterates through the required keys
3. Checks if the owner has an inventory item whose exact class type (`GetClass() == type`, not subclass-inclusive) matches any key in the group
4. Returns `true` if all key groups are satisfied; `false` otherwise

An undefined lock (one with no LOCKDEFS entry) triggers a failure message and sound. Lock numbers outside the `0–255` range pass (return `true`) without checking, and lock numbers ≤ 0 are skipped (always pass). UZDoom's own `P_CheckKeys` follows the same four-step shape but differs on both the matching criteria and the range check — see "Engine-family divergence: lock-matching criteria" and "Engine-family divergence: lock-number range and key-number storage" below.

## The `KeyNumber` field

Each Zandronum `AKey` subclass has a `BYTE KeyNumber` field, but this is **not** the lock number and is **not** used for lock matching. `KeyNumber` is assigned sequentially (starting from 1) by the LOCKDEFS parser when a map loads, and it is used only for display and cheat purposes: sorting keys in the HUD, the `give keys` cheat, and SBARINFO key-icon drawing. Lock checking uses the linedef/map-special argument directly, bypassing `KeyNumber` entirely. UZDoom's `Key` has no equivalent native field at all — see "Engine-family divergence: lock-number range and key-number storage" below for what it uses instead.

## Multiplayer and pickup behavior

In Zandronum, the `HandlePickup()` and `ShouldStay()` methods are gated on the network state (single-player vs. multiplayer):

- **Single-player (`NETSTATE_SINGLE`):** `HandlePickup()` returns `true` when the incoming item's class matches the actor's class, allowing infinite pickup. `ShouldStay()` returns `false`, so the pickup is removed after collection.
- **Multiplayer (any other net state):** Both methods call their parent `Inventory` implementation, which follows standard item re-pickup rules. `ShouldStay()` returns `true` (item stays in the world for respawn), and `HandlePickup()` respects the item's `IF_PICKUPGOOD` flag.

UZDoom's `Key.HandlePickup()`/`ShouldStay()` (`wadsrc/static/zscript/actors/inventory/inv_misc.zs:71-90`) follow the identical shape, gated on the plain `multiplayer` bool instead of a `NETSTATE_*` enum (Zandronum's client/server netcode exposes a more granular network-state enum than UZDoom's peer-style `multiplayer` flag) — same single-player-vs-everything-else split, same infinite-pickup-in-single-player behavior, so this is a naming difference rather than a behavioral one and doesn't get its own divergence section.

## DECORATE vs. ZScript — Zandronum differences

**This page documents Zandronum's DECORATE implementation, which differs significantly from the ZScript definition shown on the ZDoom wiki:**

- **No static helper methods in Zandronum:** The wiki's ZScript lists static methods (`IsLockDefined()`, `GetKeyTypeCount()`, `GetKeyType()`, `GetMapColorForLock()`, `GetMapColorForKey()`) that provide lock/key metadata. None of these exist in Zandronum's DECORATE. Equivalent C++ functions exist internally (`P_GetMapColorForLock`, `P_GetMapColorForKey`) but are not exposed to DECORATE or ACS. Confirmed against UZDoom's actual source (not just the wiki): UZDoom's `Key` class declares exactly these five as `static native clearscope` methods (`wadsrc/static/zscript/actors/inventory/inv_misc.zs:60-64`), backed by `P_IsLockDefined`/`P_GetKeyTypeCount`/`P_GetKeyType`/`P_GetMapColorForLock`/`P_GetMapColorForKey` in `src/gamedata/a_keys.h` — the wiki's ZScript description holds as written for UZDoom.
- **Species property does not affect lock matching:** The wiki states that setting `Species` to an existing key makes a new key function as a duplicate. In Zandronum, this is not true — key matching is based on exact class type from LOCKDEFS definitions, and `Species` has no effect on lock checking (it remains a general actor property with no special meaning for keys).
- **No custom DECORATE properties:** The Key class adds no custom properties beyond those inherited from `Inventory`. `Inventory.PickupMessage`, `Inventory.Icon`, `Inventory.InterHubAmount`, and other standard inventory properties are available, but no Key-specific DECORATE properties exist (no `Key.LockNumber`, no `Key.Species`-lock-binding, etc.).
- **LOCKDEFS is the only lock-definition mechanism:** Zandronum has no way to define locks or key requirements from DECORATE — all lock setup happens in a LOCKDEFS lump, which is parsed at map load. This is a hard fork divergence from the wiki's framing: a modder cannot define entirely custom lock behaviors in DECORATE, only define new key items and reference locks defined in LOCKDEFS.

The remaining two bullets (no custom properties, LOCKDEFS-only) hold on UZDoom too — its `Key` class declares no `property` block either, and its `ParseLock`/`ParseKeygroup` (`src/gamedata/a_keys.cpp`) are the same LOCKDEFS-lump parser role as Zandronum's, just with the matching-criteria and range differences covered in the divergence sections below.

## Engine-family divergence: lock-matching criteria

UZDoom's `OneKey::check()` (`src/gamedata/a_keys.cpp:47-77`) accepts a key by **either** of two independent checks, unioned together:

- Exact class-type match — `owner->IsA(key)` for the direct-actor case, `item->IsA(key)` while walking the inventory chain. `IsA` is defined as `type == GetClass()` (`src/common/objects/dobject.h:395-398`), i.e. exact type identity, not subclass-inclusive — the same semantics as Zandronum's `GetClass() == type` check via `FindInventory(key, /*subclass=*/false)`. This half agrees between engines.
- **`owner->GetSpecies() == key->TypeName` (or `item->GetSpecies() == key->TypeName` for an inventory item)** — this is new. A custom key subclass can be made to satisfy a lock by setting its `Species` property to match a predefined key's class name, exactly as the ZDoom wiki describes for the GZDoom/UZDoom lineage. Zandronum's `OneKey::check()` (`src/g_shared/a_keys.cpp:18-30`) has no equivalent branch anywhere in its key-matching path — `Species` has no effect on lock checking there, confirming the "Species property does not affect lock matching" bullet above is Zandronum-only, not an engine-wide fact.
- UZDoom also special-cases a `DehackedPickup` replacee (`owner->GetClass()->ActorInfo()->Replacee == key`, or matching `Species`) so a Dehacked-replaced key item still satisfies the original lock. No equivalent exists in Zandronum's code (Zandronum has no `DehackedPickup` inventory replacee concept in this path).

Worth keeping for porting work: a WAD relying on Species-based key substitution (a documented GZDoom/UZDoom modding pattern) will silently fail to unlock the matching door on Zandronum, since Zandronum requires the exact class or a LOCKDEFS entry naming it directly.

## Engine-family divergence: lock-number range and key-number storage

- **Lock-number range.** Zandronum's `P_CheckKeys` (`src/g_shared/a_keys.cpp:398-405`) indexes a fixed-size `locks[]` array and explicitly passes (`return true`) for `keynum > 255` as well as `keynum <= 0`. UZDoom's `P_CheckKeys` (`src/gamedata/a_keys.cpp:466-473`) backs its lock table with `TMap<int, Lock> Locks` (`src/gamedata/a_keys.cpp:141`) and only short-circuits on `keynum <= 0` — there is no upper bound, so a lock number above 255 is looked up and enforced normally instead of always passing.
- **Key-number storage.** Zandronum's `AKey` declares a dedicated native `BYTE KeyNumber` field (`src/g_shared/a_keys.h:11`), assigned by the LOCKDEFS parser's `AddOneKey()`. UZDoom's `Key` is a plain ZScript class with no native backing of its own (see `Bucket:` above), so it has no Key-specific field to add — its LOCKDEFS parser instead reuses the generic, already-existing `special1` int field inherited from `AActor` for the same sequential-numbering purpose (`src/gamedata/a_keys.cpp:180`, `:363`, `:384`, `:400`). Both are display/cheat-only, per the "The `KeyNumber` field" section above; only the storage location changed.

## Engine-family divergence: coop key-sharing opt-out

UZDoom's `Key` overrides `ShouldShareItem(Actor giver)` to return the `sv_coopsharekeys` cvar (`wadsrc/static/zscript/actors/inventory/inv_misc.zs:66-69`; cvar defined `src/d_main.cpp:779` as a `dmflags3` flag, `DF3_COOP_SHARE_KEYS`) — a GZDoom-lineage coop mechanic controlling whether one player picking up a key shares it with teammates. Zandronum's `AKey` has no `ShouldShareItem` override and no `sv_coopsharekeys`-equivalent cvar (grepping the Zandronum source turns up nothing); this mechanism doesn't exist there at all, not merely defaulted differently. Relatedly, UZDoom's `Key` also sets `+INVENTORY.ISKEYITEM` (a ZScript `flagdef` on `Inventory.ItemFlags`, bit 26 — `wadsrc/static/zscript/actors/inventory/inventory.zs:92`), which has no Zandronum counterpart; in this checkout it's a declarative marker only (no other engine code branches on it), so it isn't itself a behavior divergence worth porting attention, unlike the `sv_coopsharekeys` mechanic above.

## DECORATE definition

```text
ACTOR Key : Inventory native
{
  +DONTGIB
  +INVENTORY.INTERHUBSTRIP
  Inventory.PickupSound "misc/k_pkup"
}
```

The `+DONTGIB` flag prevents keys from being destroyed by crushers. `+INVENTORY.INTERHUBSTRIP` (the DECORATE spelling) is equivalent to `Inventory.InterHubAmount 0` in ZScript and clears keys between hub levels in hub-based campaigns.

## See also

- Predefined key subclasses: `DoomKey`, `HereticKey`, `HexenKey`, `StrifeKey`, and game-specific variants (`RedCard`, `KeyGreen`, etc.) exist by the same names on both engines (UZDoom adds `Chex`-game key variants too).
- Related lock-checking functions: `P_CheckKeys()` (line special evaluation; separate implementations per engine — `src/g_shared/a_keys.cpp` on Zandronum, `src/gamedata/a_keys.cpp` on UZDoom, see "Engine-family divergence" sections above), `P_GetMapColorForLock()` (automap display)
