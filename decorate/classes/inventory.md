# `Inventory`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `Classes:Inventory` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3AInventory&oldid=53243) + verified against Zandronum source (`src/g_shared/a_pickups.h` lines 145–223, `src/g_shared/a_pickups.cpp`, `wadsrc/static/actors/shared/inventory.txt`, `src/cl_main.cpp:3069-3110` for the client respawn handler).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** native C++ class in Zandronum (`class AInventory : public AActor` in `src/g_shared/a_pickups.h:145`); ZScript class in UZDoom (`wadsrc/static/zscript/actors/inventory/inventory.zs:27`; `class Inventory : Actor`, an ordinary scripted class — DECORATE-only fields like `ItemFlags` carry a `deprecated` marker but remain present for compatibility).

The base class for all inventory items — pickups that can be collected, dropped, and carried in a player or monster's inventory. This is the parent class for all item types: Ammo, Armor, Health, Keys, Weapons, PowerUps, and custom inventory items. Any actor inheriting from `Inventory` becomes a functional pickup item but produces no special effects by itself; effects are defined by subclasses.

## ZScript methods are not applicable

The wiki's "Methods" section documents ZScript virtuals. On Zandronum, DECORATE is the only actor-definition format that exists at all, and its authors cannot override any of these methods — they are internal C++ engine behavior only. On UZDoom, DECORATE lumps are still parsed and loaded (`src/scripting/decorate/thingdef_parse.cpp`), translated at load time into the same native `Inventory` ZScript class described below — but DECORATE syntax itself still has no mechanism to override a virtual method, so a DECORATE author on UZDoom is in exactly the same position as one on Zandronum: these are non-overridable engine behavior from DECORATE, only overridable by writing an actual ZScript subclass. The sections below describe those behaviors as they affect modding in DECORATE, not as an overridable API.

## Core pickup lifecycle

**`bool TryPickup(AActor *&toucher)`** — Called when an actor attempts to pick up this item. First offers the item to the toucher's existing inventory via `HandlePickup`. If an existing item claims it, the pickup succeeds (and `GoAwayAndDie()` runs) only if that handler set `IF_PICKUPGOOD`; otherwise the pickup fails. If nothing claims it, a non-`Ammo` item with `MaxAmount == 0` is only picked up if it has `+AUTOACTIVATE`: it is placed in the inventory just long enough to call `Use(true)`, then removed, and the pickup fails if `Use` returns false. Otherwise it gets a copy via `CreateCopy` and attaches it to the toucher via `AttachToOwner`. Returns true if pickup succeeded.

**`bool HandlePickup(AInventory *item)`** — Called on every inventory item the toucher already owns when a new item is picked up. Allows items to merge with incoming items (e.g., ammo combining with ammo). Default implementation combines items of the same class, clamping at `MaxAmount`. It returns true for a same-class item even when the stack is already full; in that case it doesn't set `IF_PICKUPGOOD`, so the pickup is refused. On Zandronum, the `sv_unlimited_pickup` server setting lifts the `MaxAmount` cap here. Returns true if this item handled the pickup (preventing normal pickup flow), false otherwise. Chained through the inventory list if the current item doesn't handle it.

**`AInventory *CreateCopy(AActor *other)`** — Returns the actor that goes into the toucher's inventory. If `GoAway()` returns true, it spawns a fresh copy of the item with the same `Amount` and `MaxAmount`, and the original on the map stays put or is hidden for respawn. If `GoAway()` returns false, the original item itself goes into the inventory.

**`bool GoAway()`** — Returns true if a copy must be given to the toucher, false if the original item can be handed over itself. Dropped items (`MF_DROPPED`) always return false. If `ShouldStay()` is true, returns true and the item stays visible. Otherwise it calls `Hide()`, then returns true if `ShouldRespawn()` is true. On Zandronum, a non-respawning item that is level-spawned (`STFL_LEVELSPAWNED`) in a game mode whose maps reset (`GMF_MAPRESETS`) is moved to `HideIndefinitely()` and also returns true. Anything else returns false.

**`void GoAwayAndDie()`** — Used when the touched actor itself won't enter the inventory (for example, it was merged into an existing stack by `HandlePickup`, or used on the spot). Calls `GoAway()`; if that returns false, it clears `MF_SPECIAL` and enters `HoldAndDestroy`. On Zandronum, a non-dropped item in a `GMF_MAPRESETS` game mode enters `HideIndefinitely` instead.

## Respawn lifecycle

**`bool ShouldStay()`** — Called during pickup to decide whether the item stays on the map, visible, after being picked up. Default returns false. Subclasses override it: on Zandronum, keys and puzzle items stay in any netgame, and weapons and weapon pieces follow the weapon-stay rules.

**`bool ShouldRespawn()`** — Determines whether the item will respawn at all. On Zandronum it checks, in order: the survival-mode flag `IF_FORCERESPAWNINSURVIVAL` (forces true in survival), `IF_BIGPOWERUP` without `DF_RESPAWN_SUPER` (false), `IF_NEVERRESPAWN` (false), then `DF_ITEMS_RESPAWN` or `IF_ALWAYSRESPAWN`. A picked-up item that doesn't stay is hidden via `Hide()` whether or not it will respawn.

**`bool DoRespawn()`** — Called when a hidden item is about to reappear. If `SpawnPointClass` is set and a random spot of that class is found, moves the item there; otherwise it doesn't move the item. Moving the item back to its original spawn point is done separately by `A_RestoreSpecialPosition` in the hide state sequence. Zandronum-specific: calls `GAMEMODE_AdjustActorSpawnFlags()` to potentially modify flags for the current game mode. Always returns true on the base class.

**`void Hide()`** — Hides the item and prepares it for respawn. Sets `MF_NOGRAVITY`, clears `MF_SPECIAL`, sets `RF_INVISIBLE`. Selects a hide state (`HideSpecial` for Raven games, `HideDoomish` for others, falling back to the other if the preferred one is missing) and sets its tics: 1050 for `HideDoomish`, or 1400 for `HideSpecial` plus 30 if `PickupFlash` is set. A nonzero `RespawnTics` replaces either value. On Zandronum it also removes the item as a bot goal.

**`void HideIndefinitely()`** — Zandronum-specific. Hides the item without a respawn timer (the `HideIndefinitely` state loops forever). Used when a level-spawned item that won't respawn is picked up in a game mode whose maps reset, so the item returns on the next map reset without respawning mid-level.

## Key fields and state machine

| Field | Type | Notes |
|---|---|---|
| `Owner` | AActor* | The actor owning this item (NULL if still a pickup on the map). |
| `Amount` | int | Number of this item held (e.g., ammo count). |
| `MaxAmount` | int | Maximum amount of this item the owner can carry. Default 1, so a plain item (keys included) doesn't stack. Zero means a non-`Ammo` item can't be held at all: it is only picked up with `+AUTOACTIVATE`, and is used on the spot. |
| `InterHubAmount` | int | Amount kept when traveling between hubs or single levels (default 1). An item with 0 is removed on leaving a hub or on a non-hub level change; on a non-hub change, `INVBAR` items are cut down to this amount. Replaces the deprecated `INTERHUBSTRIP` flag (setting it means 0). |
| `Icon` | FTextureID | The item's status bar/HUD icon. |
| `RespawnTics` | int | Custom respawn time in tics (1/35 second). If zero, uses default hide-state duration. |
| `PickupFlash` | PClass* | Actor class to spawn when picked up (e.g., `PickupFlash` for the blue effect). |
| `PickupSound` | FSoundIDNoInit | Sound played when picked up. |

**Reserved states:**
- `Spawn` — Initial state when placed in the map.
- `HideDoomish` — Hide state (used in non-Raven games). Tics = 1050, then `A_RestoreSpecialPosition` and `A_RestoreSpecialDoomThing` bring the item back.
- `HideSpecial` — Hide state (used in Raven games). Tics = 1400 (+ 30 if PickupFlash), then `A_RestoreSpecialPosition`, `A_RestoreSpecialThing1`, a short reappear animation and `A_RestoreSpecialThing2`.
- `HideIndefinitely` — Zandronum-only. Indefinite hide for map resets (a looping invisible state).
- `Held` — Infinite-duration (-1 tics) invisible state that `BecomeItem()` puts the item in once it enters an inventory.
- `HoldAndDestroy` — One-tic state used to destroy the item next frame.

## Flags

See [decorate/inventory/actor-flags.md](../inventory/actor-flags.md) for the complete `InventoryFlags` table (rows where Class = `AInventory`).

- `ADDITIVETIME` (both engines) — When a second powerup is picked up before the first expires, its duration is added instead of reset.
- `FORCERESPAWNINSURVIVAL` (Zandronum-specific) — Item always respawns in survival mode, even without `DF_ITEMS_RESPAWN`. UZDoom accepts the flag name but it does nothing there.

Missing in Zandronum (GZDoom/UZDoom additions): `UNCLEARABLE`, `NOSCREENBLINK`, `ISHEALTH`, `ISARMOR`, `NOTELEPORTFREEZE`, `TRANSFER`, `NEVERLOCAL`, `ISKEYITEM`.

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
- `Inventory.GiveQuest` — Optionally give a quest item (1–30 on Zandronum; other values give nothing).
- `Inventory.RestrictedTo` — Player classes allowed to pick up (empty list = all allowed).
- `Inventory.ForbiddenTo` — Player classes not allowed to pick up (empty list = no restrictions).
- `Inventory.DefMaxAmount` — Set max to game default (16 for Heretic, 25 for others).

**Missing in Zandronum:** `Inventory.AltHUDIcon` (GZDoom addition).

## Pickup flow and class restrictions

The pickup process follows this order:

1. `CallTryPickup(toucher)` is called (main entry point). A toucher with `MF_UNMORPHED` (the stored unmorphed body of a morphed player) can't pick up anything.
2. `CanPickup(toucher)` checks the class lists. If `RestrictedTo` is non-empty, only those classes may pick the item up and `ForbiddenTo` is not consulted; otherwise the `ForbiddenTo` classes are refused.
3. If `CanPickup` returns true, `TryPickup()` is called. If false and `IF_RESTRICTABSOLUTELY` is *not* set, `TryPickupRestricted()` is called (default returns false).
4. `TryPickup()` checks existing inventory for a handler via `HandlePickup()`. If handled with `IF_PICKUPGOOD` set, calls `GoAwayAndDie()`; if handled without it, the pickup fails.
5. Otherwise (after the `MaxAmount == 0` special case described under `TryPickup`), creates a copy via `CreateCopy()` and attaches it via `AttachToOwner()`.
6. If the item has `+AUTOACTIVATE`, `Use(true)` is called; each successful use takes one from `Amount`, and at 0 the item enters `HoldAndDestroy`.
7. If the pickup failed but the item has `+ALWAYSPICKUP` and doesn't stay, it is counted as picked up anyway and `GoAwayAndDie()` runs.
8. Finally, if the pickup succeeded, `GiveQuest()` gives the quest item named by `Inventory.GiveQuest`, if any.

## Network and map-reset specifics

**Client-side hiding:** On a Zandronum client, the hide states still count down, but when they reach `A_RestoreSpecialDoomThing` or `A_RestoreSpecialThing1`, those actions just call `Hide()` again instead of respawning, so the item stays hidden. The respawn itself comes from the server. There, those actions run `DoRespawn()` and send `RespawnDoomThing` (with fog) or `RespawnRavenThing`. A client receiving `RespawnDoomThing` runs `A_RestoreSpecialPosition`, makes the item visible and touchable, runs its own `DoRespawn()`, and returns the item to its `Spawn` state with the spawn sound and `ItemFog`. A client receiving `RespawnRavenThing` makes the item visible, plays the spawn sound and jumps into the `HideSpecial` reappear animation.

**Map resets (Survival, Invasion, Duel, LMS, Team LMS):** In these `GMF_MAPRESETS` game modes, a level-spawned item that is picked up and won't respawn (`ShouldRespawn()` is false) is moved to `HideIndefinitely` instead of being handed over or destroyed. The map reset can then bring it back, while it never respawns mid-game.

## Zandronum-specific: map-reset item persistence (`HideIndefinitely`, `GMF_MAPRESETS`)

Confirmed against UZDoom's `Inventory` ZScript class: this entire mechanism has no UZDoom
equivalent, not even as a stub. UZDoom's `GoAway()`/`GoAwayAndDie()` have no branch analogous to
Zandronum's map-reset check. Zandronum's `GoAway()` calls `HideIndefinitely()` for a
level-spawned (`STFL_LEVELSPAWNED`) item in a `GMF_MAPRESETS` mode, and Zandronum's
`GoAwayAndDie()` sets a `HideIndefinitely` state directly for a non-dropped item in such a mode.
UZDoom's versions of both methods only ever choose between "stay" and the
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

**`AInventory *CreateTossable()`** — Creates a copy for dropping. Returns NULL if the item can't be dropped (no `Spawn` state of its own, `IF_UNDROPPABLE`/`IF_UNTOSSABLE`, no owner, or `Amount <= 0`). Returns `this` if only one remains (unless `+KEEPDEPLETED`), otherwise spawns a copy with `Amount = 1`. **Zandronum-specific behavior:** In client mode, the client only lowers the local amount (or removes the last one from the inventory) and returns NULL; the server sends the spawned actor separately.

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
  `Actor.Grind`). On Zandronum, the dropped-item case goes through `HideOrDestroyIfSafe()`
  instead of a plain destroy, clients never destroy the item themselves, and a server tells
  clients to destroy it.
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
copy with `Amount = 1` and decrementing the original) or, if only one unit remains and the item
lacks `+KEEPDEPLETED`, the item itself. UZDoom's `Inventory::CreateTossable(int amt = -1)` additionally accepts an explicit amount
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
