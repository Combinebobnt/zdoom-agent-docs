# `void A_CustomBulletAttack(double spread_xy, double spread_z, int numbullets, int damageperbullet, class<Actor> pufftype = "BulletPuff", double range = 0, int flags = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_CustomBulletAttack` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CustomBulletAttack&oldid=55199) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1312-1373`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CustomBulletAttack)` at line 1321).

A customizable hitscan attack that fires a specified number of bullets with configurable spread, damage, and puff behavior.

## Parameters

- `double spread_xy` — The horizontal spread, in degrees. When `CBAF_EXPLICITANGLE` is not set, the actual firing angle varies randomly within ±*spread_xy* degrees from the target direction. When `CBAF_EXPLICITANGLE` is set, the firing angle is offset by exactly *spread_xy* degrees.
- `double spread_z` — The vertical spread, in degrees. Behaves the same way as *spread_xy* but for pitch (vertical aim).
- `int numbullets` — The number of bullets to fire in this attack.
- `int damageperbullet` — The base damage per bullet. Unless `CBAF_NORANDOM` is set, each bullet's actual damage is multiplied by a random integer from 1 to 3 (inclusive).
- `class<Actor> pufftype` — The puff actor to spawn at the point of impact. Defaults to `BulletPuff` if not specified or if the class cannot be found.
- `double range` — The maximum range of the bullets in map units. A value of 0 is interpreted as `MISSILERANGE` (2048 map units).
- `int flags` — Flags modifying the behavior (see below). Flags can be combined with bitwise OR (`|`).

## Flags

The following flags are defined:

- `CBAF_AIMFACING` — By default, the actor turns to face its target before firing. If this flag is set, the actor fires in the direction it is currently facing instead.
- `CBAF_NORANDOM` — By default, each bullet's damage is multiplied by a random value (see *damageperbullet* above). If this flag is set, each bullet deals exactly *damageperbullet* damage with no randomization.
- `CBAF_EXPLICITANGLE` — By default, *spread_xy* and *spread_z* define the maximum random spread range. If this flag is set, they define the exact angle offset applied to every bullet.
- `CBAF_NOPITCH` — By default, the vertical aim is automatically adjusted using hitscan autoaim to point at the target. If this flag is set, vertical aim is not adjusted; only the horizontal angle is used.
- `CBAF_NORANDOMPUFFZ` — By default, puffs spawned at the impact point receive a small random vertical offset. If this flag is set, puffs are spawned at the exact impact height with no vertical randomization.

## Behavior

When called, the function checks whether the calling actor has a target. If no target exists and `CBAF_AIMFACING` is not set, the function returns without firing.

If a target exists or `CBAF_AIMFACING` is set:

1. Unless `CBAF_AIMFACING` is set, the actor turns to face the target.
2. The current actor angle and, unless `CBAF_NOPITCH` is set, the pitch needed to aim at the target are determined.
3. For each bullet, if `CBAF_EXPLICITANGLE` is not set, random spread is applied to both the horizontal angle and pitch. If `CBAF_EXPLICITANGLE` is set, the exact spread values are applied as angle offsets.
4. Each bullet's damage is determined (randomized unless `CBAF_NORANDOM` is set).
5. A hitscan attack is performed using `P_LineAttack`, which spawns the specified puff at the impact point and applies damage to any actor in the way.

The attack sound is played using the actor's configured `AttackSound`. **Note:** Unlike `A_CustomMeleeAttack` and `A_CustomComboAttack`, `A_CustomBulletAttack` itself has no `NETWORK_InClientMode()` guard — it runs its full loop, including the `pr_cwbullet.Random2()`/`pr_cabullet()` spread and damage rolls, on both server and client. What actually keeps this safe is that the internal `P_LineAttack` (`src/p_map.cpp`) has its **own** client-mode guard and returns `NULL` immediately on a client (barring the `cl_hitscandecalhack`/puff-prediction exceptions), so no damage or hit-detection ever happens client-side. The client does still burn `pr_cwbullet`/`pr_cabullet` RNG rolls per bullet that the server doesn't need to make identically — a wasted-roll footgun for any non-`+CLIENTSIDEONLY` actor, same shape as the `A_JumpIf` RNG-ordering issue in [the crash-and-bug checklist](../concepts/crash-and-bug-checklist.md), though using named streams here rather than the shared `pr_exrandom`.

## Engine-family divergence: client/server authority split

The Zandronum-specific behavior described above under "Behavior" — `A_CustomBulletAttack` itself running unguarded on both server and client while the internal `P_LineAttack` silently no-ops on clients — does not apply to UZDoom. UZDoom's source tree has no client/server authority split at all (no `NETWORK_InClientMode`/`SERVERCOMMANDS_*` equivalents anywhere), so `LineAttack` runs its full effect unconditionally every time `A_CustomBulletAttack` is called. There is no wasted-RNG-roll footgun on UZDoom of the kind described for Zandronum, since there's only one execution context to begin with.

## Engine-family divergence: extended parameters not in Zandronum

The ZDoom upstream source has extended this function with additional parameters (`ptr`, `missile`, `Spawnheight`, `Spawnofs_xy`) that allow spawning a missile-projectile along with or instead of the bullet attack. These parameters and their associated flags (`CBAF_PUFFTARGET`, `CBAF_PUFFMASTER`, `CBAF_PUFFTRACER`) **do not exist in Zandronum 3.2.1**. Code using only the seven documented parameters above will compile and work in Zandronum; code using the extended parameters will fail to compile.

## Examples

```decorate
class CustomSniper : ShotgunGuy
{
  States
  {
  Missile:
    SPOS E 2 A_FaceTarget;
    SPOS E 0 A_StartSound("weapons/sshotf", CHAN_WEAPON);
    SPOS F 3 Bright A_CustomBulletAttack(2, 2, 1, 20);
    SPOS E 5;
    Goto See;
  }
}
```

This example defines a modified ShotgunGuy that fires a single bullet with 2-degree spread in both horizontal and vertical directions, dealing 20 base damage (before randomization), whenever it executes the Missile state. The attack will use the default `BulletPuff` for impact effects.
