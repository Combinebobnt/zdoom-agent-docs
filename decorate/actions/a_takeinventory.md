# `bool A_TakeInventory(class<Inventory> itemtype, int amount = 0, int flags = 0, int giveto = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_TakeInventory` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_TakeInventory&oldid=53732) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2244-2333` and the native action declaration in `wadsrc/static/actors/actor.txt:218`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:2330-2333` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_TakeInventory)`, dispatched via a thin wrapper that passes `self` to the shared `DoTakeInventory` helper at lines 2253–2328).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Removes items of a specified type from the calling actor's inventory. The function operates on the item's existing amount and enforces a minimum of zero — attempting to remove more items than the actor possesses simply reduces the amount to zero without creating a deficit.

**Warning:** Using this function in weapon states to manually consume ammo should be avoided, as it bypasses engine-side ammo-consumption mechanics (infinite ammo cheats, item effects, etc.). Use the weapon's built-in `AmmoUse` property or the `DepleteAmmo` action instead.

## Parameters

- **`itemtype`** — the inventory item class to remove. This must be a valid class derived from `Inventory`. If the item doesn't exist in the actor's inventory, the function returns `false` without side effects.
- **`amount`** — the number of samples to remove. Default is `0`. If this value is `0` or is greater than or equal to the current amount of the item, the item is fully depleted: it is destroyed entirely *unless* the item has the `INVENTORY.KEEPDEPLETED` flag set, in which case its amount is set to zero instead. For values between zero and the current amount (exclusive), the amount is reduced by that value.
- **`flags`** — control flags for the removal. Default is `0`. Currently only one flag is defined: `TIF_NOTAKEINFINITE` (value `1`). See "Infinite ammo interaction" below.
- **`giveto`** — an actor pointer selector determining which actor the item is taken from. Default is `AAPTR_DEFAULT`, which corresponds to the calling actor itself. See [Actor pointer selectors](../../acs/concepts/actor-pointers.md) for the full selector set (includes `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER`, etc.).

## Return value and success/failure

The function returns `true` if the inventory item existed and had a non-zero amount **before** the removal attempt, or `false` otherwise. **Crucially, this return value does not indicate whether the item was actually taken** — a removal suppressed by `TIF_NOTAKEINFINITE` (see below) still returns `true` if the item existed and had non-zero amount. The function will also return `false` if the item is a `HexenArmor` class (engine-specific exclusion; the wiki omits this), since `HexenArmor` inventory is immune to removal via this action.

The result slot is always updated with this true/false value unless the `giveto` actor pointer resolves to NULL, in which case the function returns early before `ACTION_SET_RESULT` is called and the result slot retains its prior value.

## Zandronum-specific: HexenArmor immune to removal

On UZDoom, `HexenArmor` has no such exclusion. The ZScript methods backing `A_TakeInventory` (`AActor::TakeInventory` and `DoTakeInventory` in `wadsrc/static/zscript/actors/inventory_util.zs`) contain no class check at all — any `Inventory`-derived item found via `FindInventory` is depleted through the same path, `HexenArmor` included. Removal goes through the shared `Inventory::DepleteBy`/`DepleteOrDestroy` methods (`wadsrc/static/zscript/actors/inventory/inventory.zs`), and `HexenArmor` overrides `DepleteOrDestroy` (`wadsrc/static/zscript/actors/inventory/armor.zs`) to zero its four armor-type slots instead of destroying the item or setting `Amount = 0` — so on UZDoom the call succeeds and has a visible effect (the actor's Hexen-style armor protection is reset), rather than the Zandronum no-op described above.

## Engine-family divergence: giveto pointer resolving to NULL

UZDoom does not reproduce the "result slot retains its prior value" behavior described above for a `giveto` pointer that resolves to NULL. `DoTakeInventory` (`wadsrc/static/zscript/actors/inventory_util.zs`) explicitly returns `false` on every code path, including the one reached when the actor-pointer selector fails to resolve a receiver — there is no path that leaves the call without an explicit result. Calling `A_TakeInventory` with an unresolvable `giveto` on UZDoom therefore always yields `false`, not whatever a previous action in the same state left behind.

## Infinite ammo interaction

If the `TIF_NOTAKEINFINITE` flag is set (`flags = 1` or `flags |= TIF_NOTAKEINFINITE`), the function will **not** remove ammunition if the target actor benefits from infinite ammo — either via the `DF_INFINITE_AMMO` map flag or a player's `CF_INFINITEAMMO` cheat. In this case, the item is left entirely untouched, the removal is skipped silently, and the function still returns `true` if the ammo existed with non-zero amount.

## Engine-family divergence: infinite ammo mechanism

UZDoom's infinite-ammo check (inside `AActor::TakeInventory`, `wadsrc/static/zscript/actors/inventory_util.zs`) does not reference `DF_INFINITE_AMMO`/`CF_INFINITEAMMO` the way the paragraph above describes for Zandronum. `CF_INFINITEAMMO` is a dead cheats-flags bit on UZDoom — defined as `= 0` and kept only for source compatibility with mods that still reference the name (`wadsrc/static/zscript/constants.zs`), the same finding `a_checkreload.md` recorded for this flag. The actual condition is `sv_infiniteammo || (player && FindInventory('PowerInfiniteAmmo', true))`: `sv_infiniteammo` is a `Flag` cvar bound directly to the `DF_INFINITE_AMMO` dmflags bit (`src/d_main.cpp:667`, `src/doomdef.h:108`), functionally equivalent to Zandronum's map-flag half of the check, but the cheat half is replaced entirely by testing for a `PowerInfiniteAmmo` inventory item (`wadsrc/static/zscript/actors/inventory/powerups.zs`) rather than a player cheats bitfield.

This also means the NULL-pointer crash described in the next section does not reproduce on UZDoom: the `PowerInfiniteAmmo` check is already guarded by `player &&` before it runs, so a non-player `receiver` (a monster, projectile, or other non-player actor) short-circuits past it instead of dereferencing a null `player` field.

## Zandronum-specific: NULL pointer crash in infinite ammo check

**This is a critical crash condition that does not occur in the wiki's upstream engine.**

The infinite ammo check contains an unguarded NULL pointer dereference:

```c
if (flags & TIF_NOTAKEINFINITE &&
    ((dmflags & DF_INFINITE_AMMO) || (receiver->player->cheats & CF_INFINITEAMMO)) &&
    inv->IsKindOf(RUNTIME_CLASS(AAmmo)))
```

The `&&` operator short-circuits left-to-right: if `DF_INFINITE_AMMO` is off (the first `||` operand is false), the code evaluates `receiver->player->cheats`. However, `receiver` can be any actor type (including monsters, projectiles, and non-player objects), and `AActor::player` is a pointer field that is only populated for player pawns. Dereferencing `receiver->player->cheats` on a non-player actor produces a NULL pointer dereference and crashes the engine.

**Trigger:** Call `A_TakeInventory` with the `TIF_NOTAKEINFINITE` flag set (`flags = 1`) on an actor that is **not** a player (e.g., a monster, projectile, or decoration), while the map's `DF_INFINITE_AMMO` flag is off.

**Example crash scenario:**
```text
ACTOR SomeMonster : DoomImp
{
  States
  {
  Death:
    TNT1 A 0 A_TakeInventory("Clip", 1, TIF_NOTAKEINFINITE)  // Crashes if map doesn't have DF_INFINITE_AMMO
    ...
  }
}
```

**Workaround:** Do not use `TIF_NOTAKEINFINITE` with non-player actors. If you must check for infinite ammo conditions before removal, manually implement the check at state-code level using ACS or a conditional action.

## Zandronum-specific: client/server behavior

**This is server-authoritative.** On clients:

- **For client-handled actors** (where the calling actor has `MF6_CLIENTSIDE` or similar engine-recognized flag), the function runs to completion and returns the actual result (true/false).
- **For weapon/flash states** (player weapon firing), the function runs to completion on the client and returns the actual result. This is an exception to the general server-authoritative rule.
- **For all other actors**, the function **returns immediately without removing items or setting an explicit result**. The state-code result slot is not modified in this case (any prior value persists), so a DECORATE `if` branch off the return value will use that prior value, not the actual outcome. The server separately syncs inventory changes to clients via `SERVERCOMMANDS_TakeInventory`. This matches the general server-authoritative pattern for action functions in Zandronum's netcode.

## Item behavior on depletion

When an item's amount reaches zero (either from the `amount` parameter equaling or exceeding the current amount, or from setting `amount = 0` explicitly), the fate of the item depends on its `INVENTORY.KEEPDEPLETED` flag:

- **Without `KEEPDEPLETED`:** The item object is destroyed entirely, and subsequent queries for that item in the actor's inventory will find nothing.
- **With `KEEPDEPLETED`:** The item object persists in the inventory with `Amount = 0`. This is useful for placeholder items that need to remain tracked in the inventory even when depleted (e.g., progress counters, state machines).

## Use cases

A common use case is resetting a timer-based inventory item on certain events. For example, a monster might use `A_GiveInventory` to track elapsed time, then call `A_TakeInventory("TimerItem", 0)` to reset the timer when the event fires. Another use case is weapon ammo handling, though the built-in `AmmoUse` property is preferred (see the warning above).

## Related functions

Three other action functions share the same underlying implementation (`DoTakeInventory`):

- `A_TakeFromTarget` — remove from the calling actor's current target
- `A_TakeFromChildren` — remove from all children (actors whose `master` is the calling actor)
- `A_TakeFromSiblings` — remove from all siblings (actors sharing the same `master`)
