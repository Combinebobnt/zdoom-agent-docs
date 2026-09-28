# `bool A_TakeInventory(class<Inventory> itemtype, int amount = 0, int flags = 0, int giveto = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_TakeInventory` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_TakeInventory&oldid=53732) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2244-2333` and the native action declaration in `wadsrc/static/actors/actor.txt:218`; result-slot, class-name, infinite-ammo and client-mode corrections from Zandronum's `src/thingdef/thingdef_codeptr.cpp:143-150`, `src/thingdef/thingdef_parse.cpp:88`, `src/g_shared/a_artifacts.cpp:2455-2482`, `src/d_main.cpp:465` and `src/network.cpp:1552-1555`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:2330-2333` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_TakeInventory)`, dispatched via a thin wrapper that passes `self` to the shared `DoTakeInventory` helper at lines 2253–2328).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Removes items of a specified type from the calling actor's inventory. The function operates on the item's existing amount and enforces a minimum of zero — attempting to remove more items than the actor possesses simply reduces the amount to zero without creating a deficit.

**Warning:** Using this function in weapon states to manually consume ammo should be avoided, as it bypasses engine-side ammo-consumption mechanics (infinite ammo cheats, item effects, etc.). Use the weapon's built-in `AmmoUse` property instead. On UZDoom, ZScript code can also call the weapon's `DepleteAmmo` method. Zandronum has no `DepleteAmmo` DECORATE action; its `DepleteAmmo` is internal C++ reached only through attack functions (e.g. their `useammo` argument).

## Parameters

- **`itemtype`** — the inventory item class to remove. This must be a valid class derived from `Inventory`. If the item doesn't exist in the actor's inventory, the function returns `false` without side effects. On Zandronum the name is only type-checked against `Actor` at load time (`src/thingdef/thingdef_parse.cpp:88`): a non-`Inventory` actor class loads fine and is simply never found, and an unknown class name prints a load-time warning, after which the call returns early (`src/thingdef/thingdef_codeptr.cpp:2279`) without taking anything or setting a result.
- **`amount`** — the number of samples to remove. Default is `0`. If this value is `0` or is greater than or equal to the current amount of the item, the item is fully depleted: it is destroyed entirely *unless* the item has the `INVENTORY.KEEPDEPLETED` flag set, in which case its amount is set to zero instead. For values between zero and the current amount (exclusive), the amount is reduced by that value.
- **`flags`** — control flags for the removal. Default is `0`. Currently only one flag is defined: `TIF_NOTAKEINFINITE` (value `1`). See "Infinite ammo interaction" below.
- **`giveto`** — an actor pointer selector determining which actor the item is taken from. Default is `AAPTR_DEFAULT`, which corresponds to the calling actor itself. See [Actor pointer selectors](../../acs/concepts/actor-pointers.md) for the full selector set (includes `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER`, etc.).

## Return value and success/failure

The function returns `true` if the inventory item existed and had a non-zero amount **before** the removal attempt, or `false` otherwise. **Crucially, this return value does not indicate whether the item was actually taken** — a removal suppressed by `TIF_NOTAKEINFINITE` (see below) still returns `true` if the item existed and had non-zero amount. The function will also return `false` if the item is a `HexenArmor` class (engine-specific exclusion; the wiki omits this), since `HexenArmor` inventory is immune to removal via this action.

On Zandronum the result is only consumed by `CustomInventory` state chains (e.g. `Pickup`/`Use`), where `CallStateChain` resets the slot to `true` before each state's action (`src/thingdef/thingdef_codeptr.cpp:143-150`). Zandronum DECORATE has no `if` to branch on it. The function writes its true/false result except on its early returns: an unknown item class (line 2279), a `giveto` pointer that resolves to NULL (line 2280), or the client-mode return described below. Those leave the slot at its `true` default, so in a `CustomInventory` chain they count as success.

## Zandronum-specific: HexenArmor immune to removal

On UZDoom, `HexenArmor` has no such exclusion. The ZScript methods backing `A_TakeInventory` (`AActor::TakeInventory` and `DoTakeInventory` in `wadsrc/static/zscript/actors/inventory_util.zs`) contain no class check at all — any `Inventory`-derived item found via `FindInventory` is depleted through the same path, `HexenArmor` included. Removal goes through the shared `Inventory::DepleteBy`/`DepleteOrDestroy` methods (`wadsrc/static/zscript/actors/inventory/inventory.zs`), and `HexenArmor` overrides `DepleteOrDestroy` (`wadsrc/static/zscript/actors/inventory/armor.zs`) to zero its four armor-type slots instead of destroying the item or setting `Amount = 0` — so on UZDoom the call succeeds and has a visible effect (the actor's Hexen-style armor protection is reset), rather than the Zandronum no-op described above.

## Engine-family divergence: giveto pointer resolving to NULL

UZDoom does not reproduce the Zandronum "early return leaves the `true` default" behavior described above for a `giveto` pointer that resolves to NULL. `DoTakeInventory` (`wadsrc/static/zscript/actors/inventory_util.zs`) explicitly returns `false` on every code path, including the one reached when the actor-pointer selector fails to resolve a receiver — there is no path that leaves the call without an explicit result. Calling `A_TakeInventory` with an unresolvable `giveto` on UZDoom therefore always yields `false`.

## Infinite ammo interaction

If the `TIF_NOTAKEINFINITE` flag is set (`flags = 1` or `flags |= TIF_NOTAKEINFINITE`), the function will **not** remove ammunition if the target actor benefits from infinite ammo — either via the `DF_INFINITE_AMMO` dmflags bit (the `sv_infiniteammo` cvar, `src/d_main.cpp:465`) or the player's `CF_INFINITEAMMO` cheats bit. On Zandronum that bit is set while a `PowerInfiniteAmmo` powerup is active (`src/g_shared/a_artifacts.cpp:2455-2482`), not by a console cheat. The skip applies only to items derived from `Ammo`. In this case, the item is left entirely untouched, the removal is skipped silently, and the function still returns `true` if the ammo existed with non-zero amount.

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

`||` evaluates its right operand only when the left one is false: if `DF_INFINITE_AMMO` is off, the code evaluates `receiver->player->cheats`. However, `receiver` can be any actor type (including monsters, projectiles, and non-player objects), and `AActor::player` is a pointer field that is only populated for player pawns. Dereferencing `receiver->player->cheats` on a non-player actor produces a NULL pointer dereference and crashes the engine.

**Trigger:** Call `A_TakeInventory` with the `TIF_NOTAKEINFINITE` flag set (`flags = 1`) on an actor that is **not** a player (e.g., a monster, projectile, or decoration), while the `DF_INFINITE_AMMO` dmflag is off. The receiver must currently hold the item: the check sits inside `if (inv && !inv->IsKindOf(RUNTIME_CLASS(AHexenArmor)))` (`src/thingdef/thingdef_codeptr.cpp:2286`), so a missing item or `HexenArmor` never reaches it. The item does not have to be ammo, since the `AAmmo` test comes after the dereference.

**Example crash scenario:**
```text
ACTOR SomeMonster : DoomImp
{
  States
  {
  Death:
    TNT1 A 0 A_TakeInventory("Clip", 1, TIF_NOTAKEINFINITE)  // Crashes if the imp holds a Clip and DF_INFINITE_AMMO is off
    Goto Super::Death
  }
}
```

**Workaround:** Do not use `TIF_NOTAKEINFINITE` with non-player actors. If you must check for infinite ammo conditions before removal, manually implement the check at state-code level using ACS or a conditional action.

## Zandronum-specific: client/server behavior

**This is server-authoritative** (`src/thingdef/thingdef_codeptr.cpp:2262-2276`). On a client (an online client or client-side demo playback, per `NETWORK_InClientMode`):

- **For weapon/flash states** (the calling actor is a player and the calling state is its current weapon or flash psprite state), the function runs to completion on the client. This is the only exception to the server-authoritative rule. There is no exception for client-side-only actors.
- **For every other call**, the function **returns immediately without removing items or setting a result**, so in a `CustomInventory` chain the slot keeps its `true` default.

On the server, a change is sent to clients with `SERVERCOMMANDS_TakeInventory` (the new amount, or 0 on depletion) only when the item's owner is a player and the call did not come from the caller's weapon/flash state, since clients run those themselves. Taking from a non-player actor sends nothing, and neither does the `TIF_NOTAKEINFINITE` skip.

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
