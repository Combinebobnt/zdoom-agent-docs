# `Health`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `Classes:Health` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3AHealth&oldid=54036) + verified against the Zandronum source's `src/g_shared/a_pickups.h` and `a_pickups.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** native C++ base class in Zandronum (`src/g_shared/a_pickups.h:404-414`; `AHealth : public AInventory`); ZScript class in UZDoom (`wadsrc/static/zscript/actors/inventory/health.zs:25-78`; `class Health : Inventory`, an ordinary scripted class with no native backing beyond what `Inventory` itself provides).

A built-in DECORATE base class for items that restore an actor's health when picked up. This is a base class only — never instantiate `Health` directly in a WAD or map. Define a derived actor class (like `Stimpack` or a custom health item) and set `Inventory.Amount` and `Inventory.MaxAmount` to control how much health the item grants and what the maximum allowable health is after pickup.

## Pickup behavior

Health items call `TryPickup` when collected, which invokes the engine's `P_GiveBody` function (Zandronum) or the equivalent `Actor.GiveBody` method, backed by the same-named `P_GiveBody` in `src/playsim/p_mobj.cpp` (UZDoom). Health items:
- Are **not** automatically effective when picked up if the actor is already at or above their maximum health (despite wiki descriptions suggesting this). Items like `HealthBonus` use the `+INVENTORY.ALWAYSPICKUP` flag to force pickup even when at max health.
- Call `GoAwayAndDie()` and disappear only if `P_GiveBody`/`GiveBody` returns true (the health was successfully added).
- Return false and remain in the map if the receiving actor is dead (`health <= 0`, or a player in `PST_DEAD`) — true on both engines. Two further rejection cases are Zandronum-only; see "Zandronum-specific: multiplayer pickup-eligibility checks" below.

## `Health.LowMessage`

Health items support one custom property: `Health.LowMessage <threshold>, "<message>"`. When the item is picked up and the recipient's *previous* health (stored during `TryPickup`) was below the specified threshold, the pickup message is replaced with the provided message string. If no low-health message is set, the default `Inventory.PickupMessage` is used.

Example (DECORATE):
```text
ACTOR Medikit : Health 2012
{
  Inventory.Amount 25
  Inventory.PickupMessage "$GOTMEDIKIT"
  Health.LowMessage 25, "$GOTMEDINEED"
  States { Spawn: MEDI A -1; Stop; }
}
```

In this example, if a player with health below 25 picks up the medikit, the pickup message becomes "$GOTMEDINEED"; otherwise it's "$GOTMEDIKIT".

## Zandronum-specific: multiplayer pickup-eligibility checks

Zandronum's `P_GiveBody` (`src/g_shared/a_pickups.cpp:217-227`) rejects a pickup for two reasons beyond the shared dead-actor check, both tied to Zandronum's server-authoritative coop/network model:

- The receiving actor is a voodoo-doll dummy player (`actor->player == COOP_GetVoodooDollDummyPlayer()`) — a Zandronum coop-mode concept with no UZDoom equivalent.
- The command is running in client mode and the local client isn't allowed to know the target player's actual health (`NETWORK_InClientMode()` + `SERVER_IsPlayerAllowedToKnowHealth()`), part of Zandronum's client/server health-visibility model.

UZDoom's `P_GiveBody` (`src/playsim/p_mobj.cpp:1232-1297`) has neither check — it only tests `actor->health <= 0` / `playerstate == PST_DEAD`. Grepping UZDoom's source tree turns up no `VoodooDoll` or `AllowedToKnowHealth` concept at all, so this isn't "differs," it's a mechanism that doesn't exist on UZDoom — a health item can't be rejected on UZDoom for either of these reasons.

## Engine-family divergence: `nohealth` dmflag spawn gating

Both engines can suppress health-item spawning in deathmatch via a dmflag, but the mechanism is structurally different, not just a naming change:

- **Zandronum**: `sv_nohealth` sets the `DF_NO_HEALTH` dmflag bit, which is checked post-spawn in `src/p_setup.cpp:3612-3626` — things already placed in the map get removed (`P_RemoveThingLocal`) if their class `IsDescendantOf(AHealth)` or `IsDescendantOf(AMaxHealth)`, or if the class is by-name `Berserk`, `Soulsphere`, or `Megasphere`. (A near-identical block exists in `src/p_mobj.cpp` around line 6154 but is dead code — wrapped in a `/* ... */` comment — so it isn't the active check; don't cite it as live behavior.)
- **UZDoom**: `sv_nohealth` gates `Inventory::ShouldSpawn()` (`wadsrc/static/zscript/actors/inventory/inventory.zs:222-231`), an overridable virtual called before an item spawns, via a per-item `+INVENTORY.ISHEALTH` flag (`bIsHealth`) rather than a class check. `Health`'s own `Default` block sets `+INVENTORY.ISHEALTH`, so every `Health` subclass (including `Soulsphere : Health`) is covered automatically; `Megasphere` and `Berserk`, which aren't `Health` subclasses (`CustomInventory` instead), opt in explicitly by also setting `+INVENTORY.ISHEALTH` in their own `Default` blocks (`wadsrc/static/zscript/actors/doom/doomartifacts.zs:96,215`) — the same three special-cased classes Zandronum hardcodes by name, reached by a flag instead.

Practical consequence for a modder: on UZDoom, a *non*-`Health`-derived custom item can opt into `sv_nohealth` gating by adding `+INVENTORY.ISHEALTH` to its own `Default` block; on Zandronum, only an `AHealth`/`AMaxHealth` descendant (or the three hardcoded class names) is ever affected — there is no equivalent per-item opt-in flag.

## Zandronum-specific note

The wiki page shown (a ZDoom wiki page) describes the GZDoom/UZDoom variant using ZScript syntax and UZDoom-specific features like `+INVENTORY.ISHEALTH` flag and `property` declarations. These do not exist in Zandronum's DECORATE system. Zandronum uses DECORATE actor inheritance only — define a class as `ACTOR YourHealthItem : Health { ... }`.

## Related

- `HealthPickup` — a separate class for health items that are stored in inventory and used later (via the `Use` action) rather than consumed immediately on pickup. Native C++ in Zandronum (`AHealthPickup`); ZScript in UZDoom (`wadsrc/static/zscript/actors/inventory/health.zs`).
- `MaxHealth` — a subclass of `Health` on **both** engines (native C++ `AMaxHealth` in Zandronum, `src/g_shared/a_pickups.cpp:1979-2059`; ZScript `MaxHealth` in UZDoom, `health.zs:80-104`) that raises the player's max-health bonus and, if there's room under the new cap, tops up their current health in the same pickup. The two implementations reach that outcome differently: Zandronum's `AMaxHealth::TryPickup` bumps `player_t::MaxHealthBonus` directly, computes its own `lMax` ceiling from the item's `health` property (or the player's base max health + stamina + bonus if `health` is 0) with a special case for the `CF_PROSPERITY` cheat, and writes `player->health`/`mo->health` by hand — bypassing `P_GiveBody` entirely for the player case (it's only used for the non-player/monster branch). UZDoom's `MaxHealth::TryPickup` raises `player.BonusHealth` by `Amount` (capped to `MaxAmount`), then calls `Super.TryPickup()`, so the actual health top-up goes through the ordinary `Health.TryPickup` → `GiveBody(Amount, MaxAmount)` → `P_GetRealMaxHealth` path (which itself adds `BonusHealth` on top of `GetMaxHealth(true)` + stamina) rather than a bespoke ceiling calculation. Net effect is similar for the common case; edge cases (the `health` property vs. `Amount`/`MaxAmount` split, the prosperity-cheat special case) aren't equivalent and would need their own entry to fully reconcile if it matters to a caller.
