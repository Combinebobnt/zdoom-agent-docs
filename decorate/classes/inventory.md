# `Inventory`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `Classes:Inventory` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3AInventory&oldid=53243) + verified against Zandronum source (`src/g_shared/a_pickups.h` lines 145–223, `src/g_shared/a_pickups.cpp`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** native C++ class in Zandronum (`class AInventory : public AActor` in `src/g_shared/a_pickups.h:145`); ZScript class in UZDoom (`wadsrc/static/zscript/actors/inventory/inventory.zs:27`; `class Inventory : Actor`, an ordinary scripted class — DECORATE-only fields like `ItemFlags` carry a `deprecated` marker but remain present for compatibility).

The base class for all inventory items — pickups that can be collected, dropped, and carried in a player or monster's inventory. This is the parent class for all item types: Ammo, Armor, Health, Keys, Weapons, PowerUps, and custom inventory items. Any actor inheriting from `Inventory` becomes a functional pickup item but produces no special effects by itself; effects are defined by subclasses.

## ZScript methods are not applicable

The wiki's "Methods" section documents ZScript virtuals. On Zandronum, DECORATE is the only actor-definition format that exists at all, and its authors cannot override any of these methods — they are internal C++ engine behavior only. On UZDoom, DECORATE lumps are still parsed and loaded (`src/scripting/decorate/thingdef_parse.cpp`), translated at load time into the same native `Inventory` ZScript class described below — but DECORATE syntax itself still has no mechanism to override a virtual method, so a DECORATE author on UZDoom is in exactly the same position as one on Zandronum: these are non-overridable engine behavior from DECORATE, only overridable by writing an actual ZScript subclass. The sections below describe those behaviors as they affect modding in DECORATE, not as an overridable API.

## Core pickup lifecycle

**`bool TryPickup(AActor *&toucher)`** — Called when an actor attempts to pick up this item. First checks if any existing inventory item (via `HandlePickup`) can absorb the new item. If no item handles it, creates a copy via `CreateCopy` and attaches it to the toucher via `AttachToOwner`. Items with `MaxAmount == 0` and `+AUTOACTIVATE` are placed temporarily in inventory, used via `Use()`, then removed (special case for zero-amount autoactivate items). Returns true if pickup succeeded.

**`bool HandlePickup(AInventory *item)`** — Called on every inventory item the toucher already owns when a new item is picked up. Allows items to merge with incoming items (e.g., ammo combining with ammo). Default implementation combines items of the same class, respecting `MaxAmount`. Returns true if this item handled the pickup (preventing normal pickup flow), false otherwise. Chained through the inventory list if the current item doesn't handle it.

**`AInventory *CreateCopy(AActor *other)`** — Determines whether the item should be placed directly in the toucher's inventory (respawning, returns a copy) or used immediately (non-respawning, returns itself). Decision is based on `GoAway()`. If creating a copy, the original item is hidden or destroyed.

**`bool GoAway()`** — Returns true if the item should respawn (a copy is given to the player), false if the original item is used directly. Checks `ShouldStay()` and `ShouldRespawn()` to decide. For respawning items, hides the item and returns true. For map-reset game modes (e.g., LMS), stores the item in `HideIndefinitely` state instead of the normal hide state.

**`void GoAwayAndDie()`** — Used by non-inventory items (e.g., map pickups). Calls `GoAway()`; if it returns false (item won't respawn), destroys the item or places it in `HoldAndDestroy` state.

## Respawn lifecycle

**`bool ShouldStay()`** — Called during pickup to determine if the item should stay in the map after being picked up. Default returns true (item stays and respawns). Override in subclasses to control respawn behavior.

**`bool ShouldRespawn()`** — Determines whether the item will respawn at all. Checks dmflags (`DF_ITEMS_RESPAWN`), the `ALWAYSRESPAWN` flag, the `NEVERRESPAWN` flag, and (Zandronum-specific) the survival-mode flag `IF_FORCERESPAWNINSURVIVAL`. An item set to respawn is hidden via `Hide()` after being picked up.

**`bool DoRespawn()`** — Called to reset the item's position before it becomes visible again. If `SpawnPointClass` is set, repositions the item to a random spawn spot of that class; otherwise uses the original spawn location. Zandronum-specific: calls `GAMEMODE_AdjustActorSpawnFlags()` to potentially modify flags for the current game mode.

**`void Hide()`** — Hides the item and prepares it for respawn. Sets `MF_NOGRAVITY`, clears `MF_SPECIAL`, sets `RF_INVISIBLE`. Selects a hide state (`HideSpecial` for Raven games, `HideDoomish` for others) and sets tics to a default or custom `RespawnTics` value (1050–1400 tics normally, plus 30 if `PickupFlash` is set).

**`void HideIndefinitely()`** — Zandronum-specific. Hides the item indefinitely without a respawn timer, used during map resets or when the item is level-spawned but not supposed to respawn regularly. Allows the item to return when the map resets without respawning mid-level.

## Key fields and state machine

| Field | Type | Notes |
|---|---|---|
| `Owner` | AActor* | The actor owning this item (NULL if still a pickup on the map). |
| `Amount` | int | Number of this item held (e.g., ammo count, powerup duration in some subclasses). |
| `MaxAmount` | int | Maximum amount of this item the owner can carry. Zero means a non-stackable item (e.g., keys). |
| `InterHubAmount` | int | Amount kept when traveling between hubs or single levels (default 1). Replaces deprecated `INTERHUBSTRIP` flag. |
| `Icon` | FTextureID | The item's status bar/HUD icon. |
| `RespawnTics` | int | Custom respawn time in tics (1/35 second). If zero, uses default hide-state duration. |
| `PickupFlash` | PClass* | Actor class to spawn when picked up (e.g., `PickupFlash` for the blue effect). |
| `PickupSound` | FSoundIDNoInit | Sound played when picked up. |

**Reserved states:**
- `Spawn` — Initial state when placed in the map.
- `HideDoomish` — Hide state (used in non-Raven games). Tics = 1050.
- `HideSpecial` — Hide state (used in Raven games). Tics = 1400 (+ 30 if PickupFlash).
- `HideIndefinitely` — Zandronum-only. Indefinite hide for map resets.
- `Held` — Loop state (item is held in inventory, never called automatically).
- `HoldAndDestroy` — One-tic state used to destroy the item next frame.

## Flags

See [decorate/inventory/actor-flags.md](../inventory/actor-flags.md) for the complete `InventoryFlags` table (rows where Class = `AInventory`). Zandronum-specific flags:

- `ADDITIVETIME` — When a second powerup is picked up before the first expires, duration is added instead of reset.
- `FORCERESPAWNINSURVIVAL` — Item always respawns in survival mode, even without `DF_ITEMS_RESPAWN`.

Missing in Zandronum (GZDoom/UZDoom additions): `UNCLEARABLE`, `NOSCREENBLINK`, `ISHEALTH`, `ISARMOR`, `NOTELEPORTFREEZE`, `TRANSFER`.

## Properties

See [decorate/inventory/actor-properties.md](../inventory/actor-properties.md) for the complete table. Common Inventory properties:

- `Inventory.Amount` — Initial amount of the item.
- `Inventory.MaxAmount` — Maximum the owner can carry.
- `Inventory.InterHubAmount` — Amount kept between hubs.
- `Inventory.Icon` — Sprite for the status bar icon.
- `Inventory.PickupMessage` — String printed when picked up (supports LANGUAGE lump `$` prefix).
- `Inventory.PickupSound` — Sound played on pickup.
- `Inventory.UseSound` — Sound played when the item is used.
- `Inventory.PickupFlash` — Actor to spawn on pickup (e.g., `PickupFlash`).
- `Inventory.RespawnTics` — Custom respawn time.
- `Inventory.GiveQuest` — Optionally give a quest item (1–31).
- `Inventory.RestrictedTo` — Player classes allowed to pick up (empty list = all allowed).
- `Inventory.ForbiddenTo` — Player classes not allowed to pick up (empty list = no restrictions).
- `Inventory.DefMaxAmount` — Set max to game default (16 for Heretic, 25 for others).

**Missing in Zandronum:** `Inventory.AltHUDIcon` (GZDoom addition).

## Pickup flow and class restrictions

The pickup process follows this order:

1. `CallTryPickup(toucher)` is called (main entry point).
2. `CanPickup(toucher)` checks `RestrictedTo` and `ForbiddenTo` class lists. Returns false if the toucher is not allowed.
3. If `CanPickup` returns true, `TryPickup()` is called. If false and `IF_RESTRICTABSOLUTELY` is *not* set, `TryPickupRestricted()` is called (default returns false).
4. `TryPickup()` checks existing inventory for a handler via `HandlePickup()`. If handled, calls `GoAwayAndDie()`.
5. Otherwise, creates a copy via `CreateCopy()` and attaches it via `AttachToOwner()`.
6. If the item has `+AUTOACTIVATE`, `Use(true)` is called; if the amount reaches 0, the item is destroyed.
7. Finally, `GiveQuest()` is called if the item has a GiveQuest value.

## Network and map-reset specifics

**Client-side hiding:** In multiplayer, clients never execute `DoRespawn()` directly. When a server-side pickup respawn action occurs, `A_RestoreSpecialThing1` or `A_RestoreSpecialDoomThing` sends a network command; clients respond by re-calling `Hide()` to wait for the server's respawn notification.

**Map resets (Survival/LMS):** When a map resets and an item is level-spawned but not configured to respawn regularly (no `DF_ITEMS_RESPAWN`), the item is moved to `HideIndefinitely` instead of the normal hide state. This preserves the item for map-reset respawning without respawning mid-game.

## Zandronum-specific: map-reset item persistence (`HideIndefinitely`, `GMF_MAPRESETS`)

Confirmed against UZDoom's `Inventory` ZScript class: this entire mechanism has no UZDoom
equivalent, not even as a stub. UZDoom's `GoAway()`/`GoAwayAndDie()` have no branch analogous to
Zandronum's `STFL_LEVELSPAWNED`/`GMF_MAPRESETS` check — Zandronum's `GoAway()` calls
`HideIndefinitely()` and Zandronum's `GoAwayAndDie()` sets a `HideIndefinitely` state directly when
that condition holds; UZDoom's versions of both methods only ever choose between "stay" and the
normal `Hide()`/destroy path. UZDoom also has no `HideIndefinitely` state defined on `Inventory` at
all (only `HideDoomish`/`HideSpecial`/`Held`/`HoldAndDestroy`), and `ShouldRespawn()` on UZDoom has
no equivalent of Zandronum's survival-mode `IF_FORCERESPAWNINSURVIVAL` early-return. Worth keeping
for porting work: a DECORATE actor that depends on surviving an LMS/Survival map reset via this
path has no direct UZDoom translation and would need reimplementing against whatever level-reset
hooks UZDoom's own game modes expose (not investigated here — out of scope for this file).

## Methods used by subclasses

**`bool Use(bool pickup)`** — Called when the item is used (from inventory or during autoactivate pickup). Default returns false (item has no use). Subclasses override to define behavior (e.g., weapons change to ready state, health pickups heal).

**`void AttachToOwner(AActor *other)`** — Called when an item is added to an actor's inventory for the first time. Calls `BecomeItem()` and `AddInventory()`.

**`void BecomeItem()`** — Marks the actor as an inventory item: unlinks from the world blockmap/sector list and prepares it for inventory storage.

**`void BecomePickup()`** — Reverse of `BecomeItem()`: marks the actor as a map pickup, removes its owner, resets visibility, and prepares it for dropping.

**`void DetachFromOwner()`** — Called when the item is removed from the owner's inventory.

**`AInventory *CreateTossable()`** — Creates a copy for dropping. Returns NULL if the item can't be dropped (has `IF_UNDROPPABLE`/`IF_UNTOSSABLE` or `Amount <= 0`). Returns `this` if only one remains, otherwise spawns a copy with `Amount = 1`. **Zandronum-specific behavior:** In client mode, the client updates the local amount but does not spawn; the server sends the spawned actor separately.

**`void Travelled()`** — Called when the item's owner moves to another map (hub or non-hub). Used for special cleanup or reinitalization. Default body is empty on both engines.

**`void OwnerDied()`** — Called when the owner dies, allowing the item to react (e.g., some powerups end, some persist).

## API differences from ZScript/GZDoom

Zandronum's virtual method signatures differ from the wiki's ZScript originals:

- `ModifyDamage(int damage, FName damageType, int &newdamage, bool passive)` — 4 parameters (no inflictor/source/flags).
- `AbsorbDamage(int damage, FName damageType, int &newdamage)` — 3 parameters.
- `AlterWeaponSprite(visstyle_t *vis)` — Takes `visstyle_t*`, returns `int`.
- `GetSpeedFactor()` — Returns `fixed_t`, not `double`.
- `CreateTossable()` — Takes no arguments (not `int amt`).

Methods this file previously labeled "Zandronum-only (not on the wiki)" — re-checked directly
against UZDoom's `Inventory` ZScript class (`wadsrc/static/zscript/actors/inventory/inventory.zs`)
rather than against wiki coverage. Three of the five actually exist on UZDoom too; only the last
two are genuinely engine-specific to Zandronum:

- `bool DrawPowerup(int x, int y)` — exists on UZDoom, but as `virtual ui version("2.4")
  bool DrawPowerup(int x, int y)`: `ui`-scoped (callable only from UI-context code, e.g. HUD
  drawing) and gated behind ZScript version 2.4.
- `bool Grind(bool items)` — exists on UZDoom with an identical signature and near-identical body
  (dropped items with `bDontGib` unset are destroyed; non-dropped items fall through to
  `Actor.Grind`).
- `void MarkPrecacheSounds()` — exists on UZDoom with an identical signature.
- `AInventory *PrevItem()` — confirmed absent from UZDoom's `Inventory` class and not found
  anywhere else in the UZDoom source tree. Genuinely Zandronum-only; UZDoom only exposes
  `NextInv()`/`PrevInv()` (which walk the `IF_INVBAR`-flagged subset, not the full raw list).
- `const char *PickupAnnouncerEntry()` — the *method* is confirmed absent from UZDoom. The
  `Inventory.PickupAnnouncerEntry` DECORATE *property* does still parse on UZDoom
  (`DEFINE_CLASS_PROPERTY(pickupannouncerentry, S, Inventory)` in
  `src/scripting/thingdef_properties.cpp`) but is an explicitly-commented no-op ("Dummy for
  Skulltag compatibility...") — it accepts the string and discards it. A DECORATE actor ported
  from Zandronum that relies on this property for announcer callouts will compile silently on
  UZDoom and produce no announcer sound at all.

## Engine-family divergence: CreateTossable amount parameter

Zandronum's `CreateTossable()` takes no arguments and always drops either one unit (spawning a
copy with `Amount = 1` and decrementing the original) or, if only one unit remains, the item
itself. UZDoom's `Inventory::CreateTossable(int amt = -1)` additionally accepts an explicit amount
to drop: `amt` is clamped to `[1, Amount]`, and if it equals the full remaining `Amount` (and
`bKeepDepleted` isn't set) the item becomes the pickup itself rather than spawning a copy —
otherwise a copy with `Amount = amt` is spawned and the original is reduced by `amt`. Code that
calls `CreateTossable()` with no arguments behaves the same on both engines (drops one unit); the
partial-stack drop behavior is a UZDoom-only addition with no Zandronum equivalent.

## Engine-family divergence: `Travelled()` hook location

Zandronum declares `Travelled()` directly on `AInventory` (`src/g_shared/a_pickups.h:204`, empty
default body). UZDoom's `Inventory` class does not redeclare `Travelled()` at all — it inherits an
identical empty-body `virtual void Travelled() {}` from the common `Thinker` base class
(`wadsrc/static/zscript/doombase.zs:287`), alongside a `PreTravelled()` counterpart
(`doombase.zs:278`) that has no `AInventory` equivalent on Zandronum. Both engines run the hook at
the same point (a carried-over item on hub/level travel) and both default to a no-op, so overriding
`Travelled()` in a subclass behaves identically either way — the divergence is only that UZDoom
generalized level-travel hooks to every `Thinker`, not just inventory items, per that engine's
level-traveling rework, and offers the additional pre-travel hook `Inventory` subclasses can use on
UZDoom but not on Zandronum.

For complete details on properties, flags, and subclasses, see the concepts docs on
[creating monsters](../concepts/creating-monsters.md) (`DropItem`, monster-carried inventory) and
[creating weapons](../concepts/creating-weapons.md) (the `Weapon`/`Ammo` subclass hierarchy), and
the [`Health`](health.md), [`Key`](key.md), and [`Powerup`](powerup.md) class files for specific
subclass families.
