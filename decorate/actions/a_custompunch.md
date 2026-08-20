# `A_CustomPunch(int damage, bool norandom = false, int flags = CPF_USEAMMO, class<Actor> pufftype = "BulletPuff", float range = 0, float lifesteal = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_CustomPunch` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_CustomPunch&oldid=54654) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1834-1918` and `wadsrc/static/actors/shared/inventory.txt:11`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `AActor` (inheritable by any actor class; callable from any state table).

A melee attack for weapons with customizable damage, ammo consumption, puff, range, and health-steal.

## Wiki/engine divergence

**The wiki page describes GZDoom/ZDoom, which has a significantly extended version.** Zandronum's version is simpler:

- **Missing parameters:** `lifestealmax`, `armorbonustype`, `MeleeSound`, `MissSound`. Zandronum has no per-call sound override and no armor-steal or lifesteal limits.
- **Missing flags:** `CPF_NOTURN` and `CPF_STEALARMOR` do not exist in Zandronum and will not compile. The wiki's `CPF_NOTURN` semantic does not apply — facing turn on a successful hit is **unconditional** (see "Behavior" below).
- **P_DaggerAlert behavior:** The wiki states that `CPF_DAGGER` causes struck enemies to be "unconditionally placed into their pain state," but in Zandronum this only occurs if the target has a `Pain.Dagger` state defined (see "Flags" below).

## Engine-family divergence: full wiki parameter and flag set present

UZDoom's `A_CustomPunch` (`wadsrc/static/zscript/actors/inventory/stateprovider.zs`) is **not** simplified the way Zandronum's is — it carries the complete signature the wiki describes: `int lifestealmax = 0`, `class<BasicArmorBonus> armorbonustype = "ArmorBonus"`, `sound MeleeSound = 0`, and `sound MissSound = ""` all exist as real parameters, and `CPF_NOTURN` (16) and `CPF_STEALARMOR` (32) both exist as real flags (`wadsrc/static/zscript/constants.zs`). Concretely, on UZDoom:

- **Facing turn is conditional.** The angle snap to the struck target only happens `if (!(flags & CPF_NOTURN))` — passing `CPF_NOTURN` suppresses it, unlike Zandronum's unconditional turn.
- **Sound is overridable.** If `MeleeSound` is non-zero it plays instead of the weapon's `AttackSound` on a hit; if `MissSound` is set, it plays on a miss (`!t.linetarget`). Zandronum has neither.
- **Lifesteal has a cap and an armor option.** `lifestealmax` is passed straight through to `GiveBody(amount, lifestealmax)`, capping how much a single hit can raise the attacker's health beyond their nominal max. If `CPF_STEALARMOR` is set, the healing is instead granted as an `armorbonustype` armor-bonus pickup (`ArmorBonus` by default) scaled by `actualdamage * lifesteal`, with `lifestealmax` becoming that item's `MaxSaveAmount` — Zandronum always heals health directly with no cap and has no armor-steal path at all.

The `P_DaggerAlert`/`DaggerAlert` conditional-pain-state behavior described above is the same on both engines — this divergence is only about the wiki's "unconditional" claim, not an engine-vs-engine difference.

## Engine-family divergence: no client/server authority split

UZDoom's source tree has no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style client-authority mechanism anywhere at all (unlike Zandronum's split-mode netcode). `A_CustomPunch` runs to completion as ordinary player-pawn logic with no client-mode early return and no server-broadcast calls — none of the "Server-authoritatively executed," `SERVERCOMMANDS_SetThingAngleExact()`/`SERVERCOMMANDS_SetPlayerHealth()`, or `SERVERCOMMANDS_TakeInventory` behavior described below applies to UZDoom. One related but separate difference: UZDoom's ammo-depletion check additionally requires `stateinfo != null && stateinfo.mStateType == STATE_Psprite` (the call must originate from a weapon pspr state) alongside `CPF_USEAMMO` and a successful hit — Zandronum has no such state-type guard, only the flag and a landed hit.

## Parameters

- **`int damage`** — The raw damage inflicted. If `norandom` is false (the default), this value is multiplied by `random(1, 8)` before application, so the final damage ranges from `damage` to `damage * 8`. Set `norandom` to true to disable this randomization.
- **`bool norandom`** — Default false. If true, skip the `random(1, 8)` multiplication and use `damage` as-is.
- **`int flags`** — Default `CPF_USEAMMO`. Bitfield of optional flags (see "Flags" below); combine with `|`.
- **`class<Actor> pufftype`** — Default `"BulletPuff"`. The puff actor to spawn at the impact point when hitting a wall or a non-bleeding actor. If the attack hits an actor with `MF5_DONTDRAIN` set, the puff still spawns but lifesteal is suppressed (see "Lifesteal" below).
- **`float range`** — Default `0`. Attack range in map units. A value of `0` defaults to `MELEERANGE` (64 map units). This is measured from the actor's center; ranges smaller than the actor's radius may fail to connect with anything.
- **`float lifesteal`** — Default `0`. If positive, a multiplier on the inflicted damage to apply back as healing to the attacker. A value of `1.0` heals the attacker by the exact damage dealt; higher values heal more. Zandronum applies this healing only if the target does not have the `MF5_DONTDRAIN` flag set, and only on a successful hit.

## Flags

Defined in `wadsrc/static/actors/constants.txt:161-164`:

| Flag | Value | Effect |
|---|---|---|
| `CPF_USEAMMO` | 1 | Consume ammo on hit. Only depletes ammo if the attack connects with a target (`linetarget` is non-null). The ammo used follows the weapon's `Weapon.AmmoUse` property for both primary and secondary ammo slots, applied via `weapon->DepleteAmmo()`. In multiplayer, server-authoritative; the server broadcasts the depletion to all clients via `SERVERCOMMANDS_TakeInventory`. |
| `CPF_DAGGER` | 2 | Dagger alert. On a successful hit, calls `P_DaggerAlert()`, which attempts to place the struck actor into its `Pain.Dagger` state (if defined) and sets the `MF4_INCOMBAT` flag. Also alerts nearby monsters with the `MF4_SEESDAGGERS` flag who witness either the attacker or the target, placing them into their `See` state. The wiki's claim that pain entry is "unconditional" is incorrect in Zandronum — it only occurs if the `Pain.Dagger` state exists. |
| `CPF_PULLIN` | 4 | Pull-in effect. On a successful hit, sets the `MF_JUSTATTACKED` flag on the attacker (the player pawn), pulling them forward. This modifies velocity differently than the classic Chainsaw (which applies a direct velocity push); the exact effect depends on how the engine interprets the flag during the next tick's physics. |
| `CPF_NORANDOMPUFFZ` | 8 | Disable puff z-offset randomization. By default, the spawned puff actor receives a random vertical offset. This flag suppresses that offset, spawning the puff at the exact hit point's z-coordinate. |

## Behavior

**Server-authoritatively executed.** In multiplayer client-mode, an early return immediately after the `if (!self->player) return;` check prevents any further action (not clientside-safe). Server broadcasts weapon angle and player health changes via `SERVERCOMMANDS_SetThingAngleExact()` and `SERVERCOMMANDS_SetPlayerHealth()` on a successful hit.

**No-op off player pawns.** The function early-returns if `!self->player`, so it cannot be used from monster state tables or non-player actors despite the `AActor` class declaration. Attempting to call it from a non-player context silently succeeds (no error, no effect).

**Facing turn.** On a successful hit, the attacker's angle is **always** set to face the struck actor (`R_PointToAngle2()`), unconditional and with no flag to disable it in Zandronum (unlike the wiki's `CPF_NOTURN`).

**Damage type.** The attack is always a melee attack (hardcoded `NAME_Melee` damage type). No way to override this.

**Sound.** On a successful hit, plays the weapon's `AttackSound` property (if the weapon is valid). There is no parameter to override the hit sound and no miss sound in Zandronum, contrary to the wiki.

**Lifesteal limits.** No `lifestealmax` parameter exists in Zandronum. All healing from lifesteal goes directly to `self->health` via `P_GiveBody()` with no upper cap — the player heals up to their max health (set by the `Health` property) and stops. The wiki's `CPF_STEALARMOR` flag and `armorbonustype` parameter do not exist.

**Puff flags.** The puff spawn is always treated as a melee attack (`LAF_ISMELEEATTACK`), and the `CPF_NORANDOMPUFFZ` flag gates `LAF_NORANDOMPUFFZ` per the flag table above.

**Sight spread.** Horizontal spread is hardcoded: the angle is adjusted by `pr_cwpunch.Random2() << 18` (a ±65536 rotation unit offset), simulating an inaccurate punch. This cannot be disabled or controlled via parameters.

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

Here, `2` is the base damage (randomized to `2–16`), `FALSE` enables randomization, `0` flags means no special behavior, `"BulletPuff"` is the impact puff, `64` is the range, and `0` means no lifesteal. To use the default range of 64 and default puff, you can omit those parameters: `A_CustomPunch(2)`.

A weapon using ammo consumption and lifesteal:

```decorate
ACTOR CustomSword : Weapon
{
  Weapon.AmmoType1 "Clip"
  Weapon.AmmoUse1 1

  States
  {
  Fire:
    SWRD B 4
    SWRD C 4 A_CustomPunch(10, TRUE, CPF_USEAMMO, "SwordPuff", 96, 0.5)
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
Fire:
  PUNG B 4
  TNT1 A 0 A_JumpIfInventory("PowerStrength", 1, "Berserked")
  PUNG C 4 A_CustomPunch(2, TRUE)
  Goto FireEnd
Berserked:
  PUNG C 4 A_CustomPunch(20, TRUE)
FireEnd:
  PUNG D 5
  PUNG C 4
  PUNG B 5 A_ReFire
  Goto Ready
```
