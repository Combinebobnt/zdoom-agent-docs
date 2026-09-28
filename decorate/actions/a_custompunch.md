# `A_CustomPunch(int damage, bool norandom = false, int flags = CPF_USEAMMO, class<Actor> pufftype = "BulletPuff", float range = 0, float lifesteal = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_CustomPunch` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_CustomPunch&oldid=54654) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1834-1918` and `wadsrc/static/actors/shared/inventory.txt:11`, plus `src/g_strife/a_strifeweapons.cpp:40-99` (`P_DaggerAlert`), `src/p_states.cpp:274-305` (non-exact `FindState`), `src/p_user.cpp:3760-3767` (`MF_JUSTATTACKED` reader), `src/g_shared/a_weapons.cpp:713-756` (`DepleteAmmo`), `src/g_shared/a_pickups.cpp:217-318` (`P_GiveBody`), `src/thingdef/thingdef_states.cpp:335-443` (action name lookup).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CustomPunch)` in `src/thingdef/thingdef_codeptr.cpp`; declared for DECORATE on `Inventory` (`wadsrc/static/actors/shared/inventory.txt:11`), so only `Inventory`-derived classes (weapons, CustomInventory) can call it.

A melee attack for weapons with customizable damage, ammo consumption, puff, range, and health-steal.

## Wiki/engine divergence

**The wiki page describes GZDoom/ZDoom, which has a significantly extended version.** Zandronum's version is simpler:

- **Missing parameters:** `lifestealmax`, `armorbonustype`, `MeleeSound`, `MissSound`. Zandronum has no per-call sound override and no armor-steal or lifesteal limits.
- **Missing flags:** `CPF_NOTURN` and `CPF_STEALARMOR` do not exist in Zandronum and will not compile. The wiki's `CPF_NOTURN` semantic does not apply — facing turn on a successful hit is **unconditional** (see "Behavior" below).
- **P_DaggerAlert behavior:** The wiki states that `CPF_DAGGER` causes struck enemies to be "unconditionally placed into their pain state." In Zandronum it is conditional: nothing happens if the struck actor is not a monster, is dead, has heard a noise already, or is already in combat (so only the first dagger hit counts), and it needs a `Pain.Dagger` or plain `Pain` state (see "Flags" below).

## Engine-family divergence: full wiki parameter and flag set present

UZDoom's `A_CustomPunch` (`wadsrc/static/zscript/actors/inventory/stateprovider.zs`) is **not** simplified the way Zandronum's is — it carries the complete signature the wiki describes: `int lifestealmax = 0`, `class<BasicArmorBonus> armorbonustype = "ArmorBonus"`, `sound MeleeSound = 0`, and `sound MissSound = ""` all exist as real parameters, and `CPF_NOTURN` (16) and `CPF_STEALARMOR` (32) both exist as real flags (`wadsrc/static/zscript/constants.zs`). Concretely, on UZDoom:

- **Facing turn is conditional.** The angle snap to the struck target only happens `if (!(flags & CPF_NOTURN))` — passing `CPF_NOTURN` suppresses it, unlike Zandronum's unconditional turn.
- **Sound is overridable.** If `MeleeSound` is non-zero it plays instead of the weapon's `AttackSound` on a hit; if `MissSound` is set, it plays on a miss (`!t.linetarget`). Zandronum has neither.
- **Lifesteal has a cap and an armor option.** `lifestealmax` is passed straight through to `GiveBody(amount, lifestealmax)`, capping how much a single hit can raise the attacker's health beyond their nominal max. If `CPF_STEALARMOR` is set, the healing is instead granted as an `armorbonustype` armor-bonus pickup (`ArmorBonus` by default) scaled by `actualdamage * lifesteal`, with `lifestealmax` becoming that item's `MaxSaveAmount` — Zandronum always heals health directly with no cap and has no armor-steal path at all.

The `P_DaggerAlert`/`DaggerAlert` conditional-pain-state behavior described above is the same on both engines — this divergence is only about the wiki's "unconditional" claim, not an engine-vs-engine difference.

## Engine-family divergence: no client/server authority split

UZDoom's source tree has no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style client-authority mechanism anywhere at all (unlike Zandronum's split-mode netcode). `A_CustomPunch` runs to completion as ordinary player-pawn logic with no client-mode early return and no server-broadcast calls — none of the "Server-authoritatively executed," `SERVERCOMMANDS_SetThingAngleExact()`/`SERVERCOMMANDS_SetPlayerHealth()`, or `SERVERCOMMANDS_TakeInventory` behavior described below applies to UZDoom. One related but separate difference: UZDoom's ammo-depletion check additionally requires `stateinfo != null && stateinfo.mStateType == STATE_Psprite` (the call must originate from a weapon pspr state) alongside `CPF_USEAMMO` and a successful hit — Zandronum has no such state-type guard, only the flag, a non-null ready weapon and a landed hit.

## Parameters

- **`int damage`** — The raw damage inflicted. If `norandom` is false (the default), this value is multiplied by `random(1, 8)` before application, so the final damage ranges from `damage` to `damage * 8`. Set `norandom` to true to disable this randomization.
- **`bool norandom`** — Default false. If true, skip the `random(1, 8)` multiplication and use `damage` as-is.
- **`int flags`** — Default `CPF_USEAMMO`. Bitfield of optional flags (see "Flags" below); combine with `|`.
- **`class<Actor> pufftype`** — Default `"BulletPuff"`. The puff actor to spawn at the impact point when hitting a wall or a non-bleeding actor. If the attack hits an actor with `MF5_DONTDRAIN` set, the puff still spawns but lifesteal is suppressed (see "Lifesteal" below).
- **`float range`** — Default `0`. Attack range in map units. A value of `0` defaults to `MELEERANGE` (64 map units). This is measured from the actor's center; ranges smaller than the actor's radius may fail to connect with anything.
- **`float lifesteal`** — Default `0`. If positive, a multiplier on the inflicted damage to apply back as healing to the attacker. A value of `1.0` heals the attacker by the exact damage dealt; higher values heal more. Zandronum applies this healing only if the target does not have the `MF5_DONTDRAIN` flag set, and only on a successful hit.

## Flags

Defined in `wadsrc/static/actors/constants.txt:162-165`:

| Flag | Value | Effect |
|---|---|---|
| `CPF_USEAMMO` | 1 | Consume ammo on hit. Only depletes ammo if the player has a ready weapon and the aim trace found a target (`linetarget` from `P_AimLineAttack` is non-null). Calls `weapon->DepleteAmmo(bAltFire, true)`: primary fire takes `Weapon.AmmoUse1` from ammo slot 1, alt fire takes `Weapon.AmmoUse2` from slot 2 (both slots only with `WIF_PRIMARY_USES_BOTH`/`WIF_ALT_USES_BOTH`). If there is not enough ammo (and infinite ammo is off), the action returns before the attack: no damage, no puff, no sound. On a server, the remaining amount of each ammo slot is then sent to all clients via `SERVERCOMMANDS_TakeInventory`. |
| `CPF_DAGGER` | 2 | Dagger alert. On a successful hit, calls `P_DaggerAlert(attacker, struck actor)`. It does nothing if the struck actor already has a `LastHeard` noise target, is dead, lacks `MF3_ISMONSTER`, or already has `MF4_INCOMBAT`. Otherwise it sets `MF4_INCOMBAT`, targets the attacker, and enters `Pain.Dagger`. The lookup is non-exact, so a monster with no `Pain.Dagger` enters its plain `Pain` state instead (no pain entry only if it has neither). It then alerts every live actor with `MF4_SEESDAGGERS` in the struck actor's own sector that is not yet in combat and can see the attacker or the struck actor: it targets the attacker, plays its `SeeSound`, enters its `See` state and gets `MF4_INCOMBAT`. The wiki's claim that pain entry is "unconditional" is incorrect in Zandronum. |
| `CPF_PULLIN` | 4 | Pull-in. On a successful hit, sets `MF_JUSTATTACKED` on the attacker, the same flag `A_Saw` sets. On Zandronum the only code that reads this flag on a player is the chainsaw/gauntlets auto-forward block in `P_PlayerThink` (`src/p_user.cpp:3760-3767`): for one tic it zeroes turning and sidemove, forces a forward move and clears the flag. That block only runs when `NETWORK_InClientMode()` is true, and `A_CustomPunch` sends no flag update to clients. |
| `CPF_NORANDOMPUFFZ` | 8 | Disable puff z-offset randomization. By default, the spawned puff actor receives a random vertical offset. This flag suppresses that offset, spawning the puff at the exact hit point's z-coordinate. |

## Behavior

**Server-authoritatively executed.** In client mode, the action returns right after the `if (!self->player) return;` check unless `self` has `NETFL_CLIENTSIDEONLY`. On a successful hit the server sends the attacker's new angle via `SERVERCOMMANDS_SetThingAngleExact()`, and `SERVERCOMMANDS_SetPlayerHealth()` only if lifesteal actually changed the attacker's health. The hit sound is started with the flag that tells clients to play it.

**Weapon and CustomInventory states only.** Although the C++ function is defined on `AActor`, the DECORATE declaration lives in the `Inventory` class (`wadsrc/static/actors/shared/inventory.txt:11`). State parsing looks action names up in the actor's own class and its ancestors (`src/thingdef/thingdef_states.cpp:335-443`), so a monster or other non-`Inventory` actor using it fails to load with `Invalid state parameter A_CustomPunch`. When it does run, it returns immediately if `self` (the owner, for weapon and CustomInventory states) is not a player, with no error and no effect.

**Facing turn.** On a successful hit, the attacker's angle is **always** set to face the struck actor (`R_PointToAngle2()`), unconditional and with no flag to disable it in Zandronum (unlike the wiki's `CPF_NOTURN`).

**Damage type.** The attack is always a melee attack (hardcoded `NAME_Melee` damage type). No way to override this.

**Sound.** On a successful hit, plays the weapon's `AttackSound` property (if the weapon is valid). There is no parameter to override the hit sound and no miss sound in Zandronum, contrary to the wiki.

**Lifesteal limits.** No `lifestealmax` parameter exists in Zandronum. Lifesteal heals `(actualdamage * lifesteal)` truncated to an integer via `P_GiveBody()` with its default maximum. So there is no per-hit cap, but a player never goes above their normal maximum (max health plus stamina plus any max-health bonus, or the Prosperity value). The wiki's `CPF_STEALARMOR` flag and `armorbonustype` parameter do not exist.

**Puff flags.** The puff spawn is always treated as a melee attack (`LAF_ISMELEEATTACK`), and the `CPF_NORANDOMPUFFZ` flag gates `LAF_NORANDOMPUFFZ` per the flag table above.

**Aim spread.** Horizontal spread is hardcoded: the angle is adjusted by `pr_cwpunch.Random2() << 18`. `Random2()` is the difference of two random bytes (-255 to 255, weighted toward 0), so the offset is at most about ±5.6 degrees, simulating an inaccurate punch. This cannot be disabled or controlled via parameters.

## Example

This example reproduces a simple melee attack similar to Doom's fist, using the default damage randomization:

```decorate
ACTOR CustomFist : Fist
{
  States
  {
  Fire:
    PUNG B 4
    PUNG C 4 A_CustomPunch(2, FALSE, 0, "BulletPuff", 64, 0)
    PUNG D 5
    PUNG C 4
    PUNG B 5 A_ReFire
    Goto Ready
  }
}
```

Here, `2` is the base damage (randomized to `2–16`), `FALSE` enables randomization, `0` flags means no special behavior, `"BulletPuff"` is the impact puff, `64` is the range, and `0` means no lifesteal. To use the default range of 64 and default puff, you can omit those parameters: `A_CustomPunch(2, FALSE, 0)`. Omitting `flags` too would switch it to the default `CPF_USEAMMO`.

A weapon using ammo consumption and lifesteal:

```decorate
ACTOR CustomSword : Weapon
{
  Weapon.AmmoType1 "Clip"
  Weapon.AmmoUse1 1

  States
  {
  Ready:
    SWRD A 1 A_WeaponReady
    Loop
  Deselect:
    SWRD A 1 A_Lower
    Loop
  Select:
    SWRD A 1 A_Raise
    Loop
  Fire:
    SWRD B 4
    SWRD C 4 A_CustomPunch(10, TRUE, CPF_USEAMMO, "SwordPuff", 96, 0.5) // SwordPuff must be defined elsewhere
    SWRD D 5
    SWRD C 4
    SWRD B 5 A_ReFire
    Goto Ready
  }
}
```

This deals fixed 10 damage, uses ammo (`CPF_USEAMMO`), spawns `SwordPuff` on impact, has a 96-unit range, and heals the player for half the damage dealt.

**Berserk handling.** The internal comment in the Zandronum source suggests using `A_CheckIfInventory`, but that function does not exist in Zandronum — use `A_JumpIfInventory` instead. To conditionally apply berserk damage multiplier:

```decorate
ACTOR BerserkFist : Fist
{
  States
  {
  Fire:
    PUNG B 4
    TNT1 A 0 A_JumpIfInventory("PowerStrength", 1, "Berserked")
    PUNG C 4 A_CustomPunch(2, TRUE, 0)
    Goto FireEnd
  Berserked:
    PUNG C 4 A_CustomPunch(20, TRUE, 0)
  FireEnd:
    PUNG D 5
    PUNG C 4
    PUNG B 5 A_ReFire
    Goto Ready
  }
}
```
