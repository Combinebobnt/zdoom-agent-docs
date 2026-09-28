# `void A_CustomComboAttack(class<Actor> missiletype, float spawnheight, int damage, sound meleesound = "", name damagetype = "none", bool bleed = true)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_CustomComboAttack` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CustomComboAttack&oldid=40208) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1416–1465`, `wadsrc/static/actors/actor.txt:264`, and `src/p_enemy.cpp:245–280`; also `wadsrc/static/actors/actor.txt:12`, `src/p_maputl.cpp:59–64`, `src/s_sound.cpp:1285–1294`, `src/p_mobj.cpp:7073–7130` and `1536–1580`, `src/thingdef/thingdef_expression.cpp:2538–2587`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function, defined on `AActor` (callable from any actor's state table).

A customizable combo attack for monsters that adapts based on range. The calling actor faces its target, then performs either a melee attack (if the target is within melee range) or fires a projectile (if out of range and a missile type is specified). Does nothing if there is no current target.

## Wiki/engine divergence: wiki type mismatch

The ZDoom Wiki page describing this function (oldid=40208) uses `string` types for `missiletype`, `meleesound`, and `damagetype`, but Zandronum's actual declaration uses `class<Actor>`, `sound`, and `name` respectively. The wiki signature predates any known divergence in this function across ZDoom-family engines; a current wiki revision was not checked and may differ further.

## Zandronum-specific: server-side behavior

**Facing happens before the network gate:** After the null-target check, the action calls `A_FaceTarget`, which runs on both server and client. The rest of the attack (range check, damage, missile spawn) is server-side only. A client returns right after facing (`NETWORK_InClientMode()`). This differs from the typical pattern of gating the entire action before any side effects.

The server tells clients about the attack explicitly. The melee sound goes out as `SERVERCOMMANDS_SoundActor` (the `true` last argument to `S_Sound`), and a missile whose spawn check succeeds goes out as `SERVERCOMMANDS_SpawnMissile`. This action sends nothing for the melee damage itself; any client update for it comes from inside `P_DamageMobj`. A missile whose spawn check fails is sent neither as a spawn nor as an explosion (see "Missile spawn and behavior").

## Parameters

- **missiletype** — The class name of the projectile to spawn if the target is out of melee range. Takes `class<Actor>` type. It has no default, so it cannot be omitted. Passing `"None"` or `""` gives no class, and then an out-of-range target makes the attack do nothing. On Zandronum an unknown class name prints a load-time warning and also resolves to no class.
- **spawnheight** — Height offset for the spawned projectile, in map units. Takes `float` type. The actual spawn height is adjusted to `self->z + spawnheight + self->GetBobOffset()` to account for bobbing (relevant for monsters with `FLOATBOB` or similar movement).
- **damage** — Damage passed to `P_DamageMobj` for the melee hit. Takes `int` type. The action applies no randomization of its own (unlike `A_CustomPunch`'s random multiplier); an expression such as `random(1, 8) * 10` is re-evaluated on each call. `P_DamageMobj` still applies its usual modifiers (damage factors, armor, protection powerups).
- **meleesound** — Sound played whenever the melee branch is taken, before the damage is applied. Takes `sound` type. Default is empty string (no sound). Played on the `CHAN_WEAPON` channel and replicated to clients in multiplayer (via the `true` parameter to `S_Sound`).
- **damagetype** — Type of damage dealt in melee. Takes `name` type. Default is `"none"`, which is silently converted to `NAME_Melee` at entry — **you cannot deal `"none"`-typed melee damage with this action**. Any other type (e.g. `"Fire"`, `"Plasma"`) is passed through to `P_DamageMobj`.
- **bleed** — Whether the target bleeds on a successful melee hit. Takes `bool` type. Default `true`. If `true`, calls `P_TraceBleed`, which may spray blood decals on walls behind the target. Uses the actual damage inflicted (`newdam`); if `newdam` is not positive (damage fully absorbed or refused), it uses the original `damage` value instead, so a hit that deals no actual damage can still leave blood. `P_TraceBleed` itself skips targets with `NOBLOOD`, `NOBLOODDECALS`, invulnerability or god mode, and randomly skips low damage (below 15).

## Melee range check

The melee branch activates if `self->CheckMeleeRange()` returns `true`. This function performs several checks:

- **Distance:** The 2D distance (ignoring vertical gap) from the actor to its target must be less than `self->meleerange + target->radius`. `meleerange` is the actor's `MeleeRange` property (default 44 map units, inherited from `Actor`); adding the target's radius accounts for hitbox size. On Zandronum the distance is `P_AproxDistance`, which never under-estimates and over-estimates by up to about 11.8%, so the effective reach is somewhat shorter off the axes.
- **Goal shortcut:** If the target is also the actor's `goal`, the check passes right after the distance test and skips the remaining checks.
- **Vertical clearance:** Unless the actor has the `MF5_NOVERTICALMELEERANGE` flag, the target must be within the actor's height. Target's z must be less than `self->z + self->height` (not above) and target's z + target height must be greater than `self->z` (not below).
- **Friendship:** The function returns `false` if the actor is friendly to its target (`IsFriend` check).
- **Sight:** The actor must have line-of-sight to the target (`P_CheckSight`); targets behind walls/obstacles fail this check.

If all checks pass, melee is used; otherwise the missile branch is attempted.

## Engine-family divergence: SECF_NOATTACK sector flag in melee range check

On UZDoom, the underlying melee-range check (`P_CheckMeleeRange`, exposed to ZScript as `AActor.CheckMeleeRange`) adds one condition not present in Zandronum: the check fails (falls through to the missile branch) if the calling actor's current sector has the `SECF_NOATTACK` flag set — a UDMF sector flag that suppresses monster attack initiation in that sector, and that does not exist in Zandronum at all. This check runs after the distance test and before the vertical-clearance test. On a map using this flag, a monster that would melee-attack on Zandronum instead falls through to the missile branch (or no-ops, if `missiletype` is null) on UZDoom.

## Missile spawn and behavior

If out of melee range and `missiletype` is not null:

- **Spawn location:** The projectile is spawned at `self->x`, `self->y`, and `self->z + spawnheight + self->GetBobOffset()`. The implementation temporarily adjusts `self->z` during the spawn call to help the aiming calculation see the correct height, then restores it. On Zandronum, `P_SpawnMissileXYZ` also subtracts the actor's `floorclip` from that height.
- **Targeting:** The projectile is spawned as if targeting `self->target` via `P_SpawnMissileXYZ`. The missile is aimed at the target.
- **Seeker missiles:** If the spawned projectile has the `MF2_SEEKERMISSILE` flag, the `tracer` field is automatically populated with the target actor, allowing homing actions like `A_Tracer2` to work.
- **Spawn collision:** The projectile passes through `P_CheckMissileSpawn`, which nudges it forward and tests whether it fits. On success, the Zandronum server sends the spawn to clients.
- **Blocked spawn:** If that test fails, the projectile explodes in place (enters its `Death` state, so any death-state actions such as `A_Explode` still run), or is removed outright if it hit a `Line_Horizon` line. There is no fallback to melee. On Zandronum the call passes `bClientHasMissile = false`, so a blocked missile is sent to clients neither as a spawn nor as an explosion.

If the target is out of range and `missiletype` is null: the attack silently does nothing (no alternative fallback).

## Return value

None (returns immediately on client after `A_FaceTarget`).

## Interaction with actor properties and flags

- **`meleerange` property:** Controls the distance threshold. Default 44 units. Monsters can override this via the `MeleeRange` property.
- **`MF5_NOVERTICALMELEERANGE` flag:** Disables vertical-clearance check in melee range evaluation.
- **Target pointer:** Requires `self->target` to be non-null; does nothing otherwise.
- **`MF2_SEEKERMISSILE` flag on projectile:** Automatically sets `tracer` to the target.

## Examples

From the wiki example, reproducing the Baron of Hell's combo attack:

```decorate
ACTOR ComboBaron : BaronOfHell
{
  States
  {
  Melee:
  Missile:
    BOSS EF 8 A_FaceTarget
    BOSS G 8 A_CustomComboAttack("BaronBall", 32, 10 * random(1, 8), "baron/melee")
    Goto See
  }
}
```

Both the `Melee` and `Missile` labels point at the same frames, so whichever the AI picks, the action decides by range: a melee hit (10 to 80 damage) or a `BaronBall` projectile. The `32` spawn height places the missile origin 32 units above the actor's `z` (its feet), plus any bob offset. The `"baron/melee"` sound plays whenever the melee branch is taken.

A demon that gains a ranged fallback:

```decorate
ACTOR ComboDemon : Demon
{
  States
  {
  Melee:
  Missile:
    SARG E 8 A_FaceTarget
    SARG F 8 A_CustomComboAttack("DoomImpBall", 24, 20, "demon/melee", "Melee")
    SARG G 8
    Goto See
  }
}
```

This deals 20 melee damage of type `"Melee"` in range, fires a `DoomImpBall` out of range, and plays `"demon/melee"` when the melee branch is taken. The projectile spawns 24 units above the actor's `z`. The labels must be `Melee`/`Missile`: monster AI never enters a custom label such as `Attack` on its own.

## See also

- [`A_CustomMeleeAttack`](a_custommeleeattack.md) — melee-only variant (simpler, no projectile fallback).
- [`A_CustomMissile`](a_custommissile.md) — projectile-only variant with more configuration options (aim modes, flags).
- [Creating monsters](../concepts/creating-monsters.md) — Monster attack state design and action calling conventions.
- [Creating projectiles](../concepts/creating-projectiles.md) — Projectile flag bundles and state requirements.
