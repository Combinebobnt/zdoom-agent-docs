# `MaxHealth`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. Zandronum: `wadsrc/static/actors/Skulltag/skulltaghealth.txt:7-37`, `wadsrc/static/actors/shared/inventory.txt:137-142`, `wadsrc/static/actors/actor.txt:4`, `wadsrc/static/actors/doom/doomartifacts.txt:28-54`, `wadsrc/static/actors/doom/doomhealth.txt:3-10`, `src/g_shared/a_pickups.h:403-438`, `src/g_shared/a_pickups.cpp:217-310` (`P_GiveBody`), `:1089-1200` (`AInventory::Touch`), `:1860-1893` (`AHealth`), `:1971-2059` (`AMaxHealth::TryPickup`); these files are unchanged between the 3.2.1 version-bump commit and the `3.3-alpha` checkout read here (`bdd0f7beb`). `src/d_player.h:758`, `src/p_user.cpp` (`player_t` constructor :384, copy :543, `GetMaxHealth` :1502-1505, `GiveDefaultInventory` :1610-1629, degeneration :4210, `player_t::Serialize` :4461/:4527), `src/g_game.cpp` (`G_PlayerFinishLevel` :2108-2112, `G_PlayerReborn` :2121/:2216), `src/g_level.cpp:1422-1426`, `src/p_mobj.cpp` (`P_SpawnPlayer` :5519-5522, `SpawnHealth` :7830-7836), `src/p_lnspec.cpp:1155-1190` (`HealThing`), `src/g_shared/a_artifacts.cpp:2338-2369` (`APowerProsperity`), `src/sv_commands.cpp:516-531` and `:3986-4007`, `src/sv_main.cpp:2676,4226`, `src/cl_main.cpp:7565-7642`, `src/g_doom/doom_sbar.cpp:594-595`. UZDoom: `wadsrc/static/zscript/actors/inventory/health.zs:25-104`, `wadsrc/static/zscript/actors/inventory/inventory.zs:697-701`, `wadsrc/static/zscript/actors/player/player.zs:45-47,2154-2158`, `wadsrc/static/zscript/constants.zs:1225`, `src/playsim/p_mobj.cpp:1176-1297` (`P_GetRealMaxHealth`, `P_GiveBody`) and `:6344` (`P_SpawnPlayer`).
**Bucket:** native C++ class in Zandronum (`src/g_shared/a_pickups.h:433-438`, `AMaxHealth : public AHealth`; implementation `src/g_shared/a_pickups.cpp:1971-2059`; DECORATE declaration `wadsrc/static/actors/Skulltag/skulltaghealth.txt:7-11`, stock subclass `MaxHealthBonus` at `:19-37`, doomednum 5090); ZScript class in UZDoom (`wadsrc/static/zscript/actors/inventory/health.zs:80-104`, `class MaxHealth : Health`, no native backing).

A [`Health`](health.md) subclass that permanently raises a player's maximum health by `Inventory.Amount` (up to a cap of `Inventory.MaxAmount`) and, in the same pickup, heals the player. Like `Health`, it is consumed on pickup and never enters the inventory list (see [`Inventory`](inventory.md) for the general pickup flow). The two engines reach this outcome with different arithmetic, so a definition written for one does not behave the same on the other; see "Engine-family divergence" below before porting one.

On Zandronum the class and its stock subclass `MaxHealthBonus` (Skulltag's max health bonus) live in the always-loaded `zandronum.pk3`, but the `BON3` sprite it uses is composited from art that ships separately; see [Skulltag legacy actor classes](../concepts/skulltag-legacy-classes.md).

## Zandronum pickup behavior

`AMaxHealth::TryPickup` (`a_pickups.cpp:1979-2059`) does not call `AHealth::TryPickup` or `P_GiveBody` for players. For a player toucher it runs these steps in order:

1. **Raise the bonus, unconditionally.** `player_t::MaxHealthBonus += Amount`, then clamp it to `MaxAmount` (`:1988-1993`). The `MaxHealth` base class sets `Inventory.MaxAmount 50`; `MaxHealthBonus` sets `Amount 1`, `MaxAmount 50`.
2. **Compute the heal ceiling `lMax`** (`:2000-2021`), from the item actor's own `Health` value, not from `MaxAmount`:
   - If the player has `CF_PROSPERITY` set (the `PowerProsperity` powerup, `a_artifacts.cpp:2346`), `lMax = deh.MaxSoulsphere + 50` (250 with default DEHACKED values). Neither the item's `Health` nor the bonus is used.
   - Else if the item's `Health` is 0, `lMax` = the player class's max health (`GetMaxHealth()`, i.e. `Player.MaxHealth` or the DEHACKED default, `p_user.cpp:1444-1447`) + stamina + `MaxHealthBonus`; while morphed, `MAXMORPHHEALTH` instead.
   - Else `lMax = Health + MaxHealthBonus`. Stamina is not added in this branch.
3. **Refuse or heal.** If the player's health is already `>= lMax`, the item is consumed without healing when it has `+INVENTORY.ALWAYSPICKUP`, otherwise the pickup fails and the item stays in the map (`:2025-2035`). Otherwise health goes up by `Amount`, clamped to `lMax`, and the pawn's health is synced to it.

`Inventory.Amount` therefore does double duty: it is both the bonus increment and the heal amount.

**The item's `Health` defaults to 1000, not 0.** `Actor` sets `Health 1000` (`actor.txt:4`), and neither `Inventory`, `Health` (`inventory.txt:137-142`) nor `MaxHealth` (`skulltaghealth.txt:7-11`) overrides it; an item's spawned health is its default (`SpawnHealth`, `p_mobj.cpp:7830-7836`, no skill scaling for non-monsters). So a custom subclass that doesn't set `Health` heals up to `1000 + bonus`, effectively uncapped. Set `Health 0` for "player's normal max plus bonus", or an explicit ceiling as `MaxHealthBonus` does with `Health 200` (so the bonus lets it overheal to 250).

**Side effect of a refused pickup (traced from code order).** Step 1 runs before step 3's refusal. A player at or above `lMax` who touches a `MaxHealth` item *without* `ALWAYSPICKUP` gets `Amount` added to the bonus on every touch, up to `MaxAmount`, while the item stays put with no message or sound. The stock `MaxHealthBonus` avoids this by carrying `+INVENTORY.ALWAYSPICKUP`.

`Health.LowMessage` works as on `Health`: `TryPickup` stores `PrevHealth` before healing and the inherited `AHealth::PickupMessage` (`:1860-1873`) compares against it.

A non-player toucher skips the bonus and falls through to `P_GiveBody(other, Amount)`, which heals a monster up to its spawn health (`:2045-2056`).

## Where the bonus lives and when it resets (Zandronum)

The bonus is `player_t::MaxHealthBonus` (`d_player.h:758`), a field on the player slot, not on the pawn and not an inventory item.

- **Death and respawn:** reset to 0. `G_PlayerReborn` destroys and reconstructs `player_t` (`g_game.cpp:2216`) without restoring the field, and `GiveDefaultInventory` also zeroes it (`p_user.cpp:1629`).
- **Map change:** at level load, every player in deathmatch, teamgame, or invasion (and any dead player) is set to `PST_ENTER` (`g_level.cpp:1422-1426`), which makes `P_SpawnPlayer` call `G_PlayerReborn` (`p_mobj.cpp:5519-5522`), so the bonus resets. In cooperative/single-player, a living player stays `PST_LIVE` and keeps the bonus, unless the map uses `ResetInventory`, whose `G_PlayerFinishLevel` path calls `GiveDefaultInventory` (`g_game.cpp:2108-2112`).
- **Savegames:** serialized with `player_t` (`p_user.cpp:4527`).

## How other health sources use the bonus (Zandronum)

The bonus only raises caps that are derived from the player's max health, never an explicit item cap:

- `P_GiveBody` (`a_pickups.cpp:236-246`) adds `MaxHealthBonus` only when called with `max <= 0`. Stock `Stimpack`/`Medikit` (`MaxAmount 0`) therefore heal up to max + stamina + bonus, while `HealthBonus`, `Soulsphere` (`MaxAmount 200`) and `MegasphereHealth` stay hard-capped at 200 (`doomhealth.txt:10`, `doomartifacts.txt:37,54`).
- The `HealThing` special adds the bonus when its `max` argument is 0 (spawn health + bonus) or 1 (`MaxSoulsphere` + bonus), not for any other explicit `max` (`p_lnspec.cpp:1155-1190`).
- With `DF2_YES_DEGENERATION`, health decays toward `StartHealth + MaxHealthBonus` rather than plain `StartHealth` (`p_user.cpp:4210`).
- The Skulltag-style Doom fullscreen HUD prints the max as `GetMaxHealth() + MaxHealthBonus`, or `MaxSoulsphere + 50` under prosperity (`doom_sbar.cpp:594-595`).

## Netcode (Zandronum)

Pickup is server-authoritative. On a successful pickup, `AInventory::Touch` sends `SERVERCOMMANDS_GiveInventory` with the item's class and `Amount` (`a_pickups.cpp:1165-1170`); the client handler spawns a copy of that class, clamps `Amount` to `MaxAmount` for `Health` descendants, and runs `CallTryPickup` on it locally (`cl_main.cpp:7565-7642`). So the client's `MaxHealthBonus` is a local replay of `AMaxHealth::TryPickup`, not a transmitted field. A refused pickup returns from `Touch` before any server command is sent, so the step-1 side effect above stays server-side until the next resync (inferred from code order).

For full resyncs (a client joining and seeing other players, `sv_main.cpp:2676`; `SERVER_ResetInventory`, `:4226`), `SERVERCOMMANDS_SetPlayerHealthAndMaxHealthBonus` (`sv_commands.cpp:516-531`) fabricates a temporary `MaxHealth` with `Amount` = the bonus and `MaxAmount` = bonus + `StartHealth`, sends it as a give-inventory-with-extra command, then sends the real health, which overwrites whatever the replayed pickup healed. Nothing in that path zeroes the client's existing bonus first, so the replay adds to whatever value the client already held (traced; whether it is ever nonzero at that point was not traced).

## Example

```decorate
// Permanent +5 max health per pickup, at most +25 total.
// Heals 5, up to the player's normal max plus the accumulated bonus.
ACTOR VitalityShard : MaxHealth 20500
{
  Inventory.Amount 5
  Inventory.MaxAmount 25
  Health 0                      // Zandronum: use player max + stamina + bonus as ceiling
  +INVENTORY.ALWAYSPICKUP       // consume even at full health; avoids the touch-ratchet
  Inventory.PickupMessage "Vitality increased."
  States
  {
  Spawn:
    BON1 A -1
    Stop
  }
}
```

On UZDoom this same definition raises the bonus the same way, but the heal ceiling becomes `MaxAmount + bonus` (25 to 50), so it will almost never heal a player at normal health; see below.

## Engine-family divergence

UZDoom's `MaxHealth` (`health.zs:80-104`) is a short ZScript override with materially different semantics. Paraphrased:

- **Storage.** The bonus is `PlayerPawn.BonusHealth`, a field on the pawn actor (`player.zs:45`), not on the player slot. There is no `player_t` field.
- **Bonus gating.** The bonus is raised only if it is currently below `MaxAmount`, then clamped to `MaxAmount`. Unlike Zandronum's unconditional increment, this counts as a successful pickup on its own.
- **Default cap is 0.** UZDoom's `MaxHealth` has no `Default` block, so it inherits `Health`'s `Inventory.MaxAmount 0` (`health.zs:37`). With `MaxAmount 0` the below-cap test never passes and the bonus is never raised. A UZDoom item must set `MaxAmount` above 0. Zandronum's base class defaults to 50.
- **Heal ceiling.** After the bonus step it defers to `Health`'s ordinary pickup, i.e. `GiveBody(Amount, MaxAmount)`. The item's `Health` property is not consulted at all, and there is no prosperity branch (`CF_PROSPERITY` exists only as a 0-valued compatibility constant, `constants.zs:1225`). `P_GetRealMaxHealth` (`p_mobj.cpp:1176-1219`) then uses `MaxAmount` both as the bonus cap and as the base of the heal ceiling: with `MaxAmount > 0` the ceiling is `MaxAmount + BonusHealth`. Worked through (traced, not run): Zandronum's `MaxHealthBonus` values (`Amount 1`, `MaxAmount 50`) on UZDoom give a heal ceiling of at most 100, so a 100-health player gets the bonus but no heal, while on Zandronum the same pickup heals toward 200 + bonus.
- **Success rule.** The item is consumed if either the bonus rose or the heal succeeded; `+INVENTORY.ALWAYSPICKUP` is handled generically by `Inventory`'s `CallTryPickup` (`inventory.zs:697-701`), as for any item.
- **Other health items.** `P_GetRealMaxHealth` adds `BonusHealth` on top of an explicit item limit too, so on UZDoom a Soulsphere (`MaxAmount 200`) caps at 200 + bonus, where Zandronum hard-caps it at 200. `PlayerPawn.MaxPickupHealth` (`player.zs:47`), when nonzero, overrides both. `GetMaxHealth(true)` includes stamina and `BonusHealth` (`player.zs:2154-2158`).
- **Skill scaling.** UZDoom's `P_GiveBody` scales the heal by the skill's `HealthFactor` (`p_mobj.cpp:1260`); Zandronum's hand-written player branch does not.
- **Persistence.** The bonus follows the pawn: a respawn spawns a fresh pawn (`P_SpawnPlayer`, `p_mobj.cpp:6344`), so it resets to 0 on death. Inferred, not traced end-to-end: it carries across level changes with the travelling pawn, and since nothing in UZDoom's source writes `BonusHealth` apart from `MaxHealth` itself, `ResetInventory` does not clear it (Zandronum's does).
- **No stock subclass.** UZDoom ships no `MaxHealthBonus` actor and no doomednum 5090 thing; only the base class exists.
- **Netcode.** UZDoom multiplayer is lockstep with no client/server split, so none of Zandronum's replay or resync machinery has a counterpart.
