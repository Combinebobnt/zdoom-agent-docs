# Custom damage types

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `Custom damage types` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=Custom_damage_types&oldid=52258) + verified against the Zandronum source's damage-type implementation in `src/p_interaction.cpp`, `src/p_mobj.cpp`, `src/g_shared/a_armor.cpp`, `src/info.cpp`, and `src/thingdef/thingdef_parse.cpp`; the built-in name list, `PainChance`/`DamageFactor` `"Normal"` mapping and shipped `Drowning` declaration corrected against `src/namedef.h`, `src/p_terrain.cpp`, `src/thingdef/thingdef_properties.cpp` and `wadsrc/static/actors/shared/damagetypes.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

DECORATE allows you to define custom damage types for projectiles, attacks, and actors — and to create specialized behavior (different pain/death/impact states, armor-bypassing, resistance/vulnerability) tailored to each type.

## Overview

Damage types are names (like `Fire`, `Ice`, `Poison`) that you assign to a projectile or attack and then use to trigger corresponding state sequences in receiving actors. The engine itself inflicts or special-cases a handful of built-in names (`Fire`, `Ice`, `Poison`, `Electric`, `Extreme`, `Drowning`, `Slime`, `Crush`, `Telefrag`, `Falling`, `Massacre`, among others). There is no built-in `Spike` type, and a TERRAIN `damagetype lava` is read as `Fire`. Any other name works too, and you can declare custom ones with their own default damage-reduction factors and armor-bypass rules.

## Assigning damage types to attacks

### On projectiles

Use the `DamageType` property to specify what type of damage a projectile inflicts:

```text
Actor Fireball : Actor
{
    Projectile
    DamageType Fire
    // ...
}
```

The damage type is passed along to the actor that takes damage from the projectile, where it triggers custom pain/death states and applies damage factors.

### On hitscan or melee attacks

Hitscan weapons and melee attacks don't carry damage type directly on the weapon or monster — they inflict damage through **puff actors** (the small impact actors spawned at the bullet or fist hit point). The puff carries the damage type via its own `DamageType` property, so you must create a custom puff to assign a damage type to hitscan/melee:

```text
Actor CustomPuff : BulletPuff
{
    DamageType CustomType
}
```

## Triggering custom states based on damage type

Actors can respond to specific damage types by defining state labels using the `State.DamageType` syntax. When damage of a given type is inflicted, the engine looks for the corresponding damage-typed state before falling back to the default:

### Pain states

Define custom pain reactions to specific damage types using `Pain.<DamageType>` labels:

```text
Actor MyZombie : ZombieMan
{
    States
    {
        Pain.Fire:
            ZMBF AB 3
            ZMBF C 5 A_PlaySound("myzombie/burn")
            ZMBF D 3
            goto See
        // ... other states
    }
}
```

When the zombie takes damage of type `Fire`, it enters the `Pain.Fire` state instead of the default pain sequence. If no `Pain.Fire` state exists, it falls back to the default `Pain` state.

### Death states

Define custom death sequences for each damage type using `Death.<DamageType>` labels:

```text
Actor MyZombie : ZombieMan
{
    States
    {
        Death.Fire:
            ZMBF EFG 3
            ZMBF H 2 A_PlaySound("myzombie/death_burn")
            ZMBF IJKL 3
            stop
        // ... other states
    }
}
```

The engine searches for damage-typed death states in this order:
1. If the damage type exists and death is extreme (health below `GibHealth`, or an inflictor with `EXTREMEDEATH`, and no `NOEXTREMEDEATH` on the inflictor): `Death.Extreme.<DamageType>` (e.g., `Death.Extreme.Fire`)
2. If no such state exists or death is not extreme: `Death.<DamageType>`
3. For `Ice`-type damage on monsters/players with no custom ice death state: automatic generic freeze death (unless disabled via `deh.NoAutofreeze` or the `MF4_NOICEDEATH` flag)
4. If still no state found and death is extreme: `Death.Extreme` (the generic extreme/gib death)
5. If still no state found: `Death` (the default death sequence)

**Engine-gate note (Zandronum vs. GZDoom):** The ZDoom wiki notes "custom XDeath states are not currently supported" with a GZDoom-version qualifier (pre-1.8.10). Zandronum **does** support damage-typed XDeath states via the `Death.Extreme.<DamageType>` path — Zandronum diverges from the wiki's GZDoom-era statement.

### Wound states

`Wound.<DamageType>` states are entered when a hit of that type leaves the actor alive at or below its `WoundHealth` (default 6), whatever kind of attack delivered it:

```text
Actor MyZombie : ZombieMan
{
    States
    {
        Wound.Ice:
            ZMBF A 10 A_PlaySound("myzombie/icy_wound")
            goto See
    }
}
```

### Crash states

Damage-typed `Crash` states belong to the victim, not the projectile. When a killed actor's corpse comes to rest on the floor (or on top of another actor), the engine looks for `Crash.Extreme.<DamageType>` if its health is below `GibHealth`, then `Crash.<DamageType>`, then the plain `Crash.Extreme`/`Crash` labels. The damage type is the one that killed it, and it only survives death if the actor had a matching `Death.<DamageType>` or `Death.Extreme.<DamageType>` state. Otherwise it is cleared (except `Massacre`), so only the plain labels can match. Ice-frozen corpses never enter a crash state.

```text
Actor MyZombie : ZombieMan
{
    States
    {
        Death.Fire:
            ZMBF EFG 3
            ZMBF H -1
            stop
        Crash.Fire:
            ZMBF M 5
            ZMBF N -1
            stop
    }
}
```

Projectiles and puffs only use the plain `Crash` label, with no damage-type suffix. A projectile enters `Crash` when it hits a `NOBLOOD` actor, and a puff enters it when it hits no actor at all. A projectile hitting a wall, floor or ceiling uses its `Death` state.

## Pain chance per damage type

Use `PainChance` with a damage-type parameter to set the probability an actor enters pain state for that damage type specifically:

```text
Actor MyZombie : ZombieMan
{
    PainChance "Fire", 256     // Always enter pain state for Fire damage (100%)
    PainChance "Freeze", 0     // Never enter pain state for Freeze damage (0%)
    PainChance "Normal", 100   // Untyped damage only: 100 out of 256 (about 39%)
}
```

The numeric argument is out of 256: the engine rolls 0 to 255 and enters pain when the roll is below the chance (and the damage reaches `PainThreshold`). Set it to `0` to suppress pain states for a type entirely, and to `256` for a guaranteed pain reaction; `255` still misses 1 time in 256. `"Normal"` names untyped damage, not a default: a typed hit with no entry of its own falls back to the actor's plain `PainChance` property.

## Damage resistance and vulnerability

Use the `DamageFactor` property to make an actor take more or less damage from a specific type:

```text
Actor RaiDoom : DoomImp
{
    DamageFactor "Electric", 0.2   // Takes 20% damage from Electric (80% reduction)
    DamageFactor "Water", 1.8      // Takes 180% damage from Water (80% vulnerability)
}
```

Multiple `DamageFactor` entries work with one another. If an actor has no `DamageFactor` entry for a type, or has no `DamageFactor` entries at all, the global default factor for that type (see "Declaring damage types" below) is applied instead.

**Precedence chain for damage reduction:** When an actor takes damage:
1. If the actor has a `DamageFactor` for the exact damage type, use that alone (highest priority).
2. Otherwise, for typed damage, multiply the actor's `DamageFactor "Normal"` (the untyped fallback, 1.0 if absent) by the damage type's global `Factor` (1.0 if the type was never declared).
3. Untyped damage uses only the actor's `"Normal"` factor, or 1.0.

The global `ReplaceFactor` flag (see below) changes step 2 so the global `Factor` **replaces** the actor's `"Normal"` factor instead of multiplying it.

## Declaring damage types with default properties

Define a damage type globally in DECORATE using the `DamageType` block:

```text
DamageType Fire
{
    Factor 1.0          // Default damage factor for actors with no specific DamageFactor
    // ReplaceFactor   // (optional) Suppress the actor's untyped DamageFactor fallback
    // NoArmor         // (optional) Bypass armor entirely for this damage type
}
```

### DamageType properties

- **`Factor` (default 1.0):** The global damage factor applied to actors that have no `DamageFactor` entry for this type. A `Factor` of `0` is a valid way to create a damage type that does nothing unless an actor explicitly allows it with `DamageFactor "<type>", 1.0`.

  When `Factor` is `0`, the `ReplaceFactor` flag is implicitly set to prevent the computation `damage * 0 * normal_factor`, which would be pointlessly wasteful.

- **`ReplaceFactor` (default: not set):** If set, the global `Factor` **replaces** an actor's untyped `DamageFactor "Normal"` instead of multiplying it. This is useful when a damage type should ignore the actor's general vulnerability/resistance and use only the global or type-specific factor.

- **`NoArmor` (default: not set):** If set, damage of this type always bypasses armor, even if the actor is wearing BasicArmor or similar. This is checked in the armor's own `AbsorbDamage` method — armor will not reduce damage of a `NoArmor` type.

### Declaration examples

A custom damage type that does nothing by default unless an actor explicitly allows it:

```text
DamageType SpecialDamage
{
    Factor 0
}

Actor VulnerableToSpecial
{
    DamageFactor "SpecialDamage", 1  // Explicitly vulnerable; global 0 factor does not apply
}
```

Redefining a built-in type (in this case `Drowning`) to ignore armor:

```text
DamageType Drowning
{
    NoArmor
}
```

Both engines already ship exactly this declaration (Zandronum in its DECORATE `actors/shared/damagetypes.txt`, UZDoom in its base MAPINFO), so it only matters as a reset. Redeclaring `Drowning` with, say, just a `Factor` drops the built-in `NoArmor`.

**Important:** Declaring a damage type resets its definition to defaults. If you declare the same type twice, the second declaration replaces the first, not merges with it.

## Engine-specific caveats

**MAPINFO damagetype blocks:** The ZDoom wiki mentions declaring damage types via MAPINFO as an alternative to (and recommended replacement for) the DECORATE `DamageType` block. This is a GZDoom-family feature only — **Zandronum has no MAPINFO damagetype support**. In Zandronum, the DECORATE `DamageType` block is the only way to declare global damage-type properties.

## Engine-family divergence

Confirmed directly in the UZDoom source (not just the wiki's mention above): UZDoom's MAPINFO parser
recognizes a `damagetype` block (`src/gamedata/g_mapinfo.cpp`) alongside the DECORATE-level
`DamageType { }` block (`src/scripting/decorate/thingdef_parse.cpp`, the same `Factor`/
`ReplaceFactor`/`NoArmor` mechanics documented above) — both mechanisms coexist on UZDoom. Zandronum
only ever had the DECORATE-level block. This is the only confirmed divergence in this file; the
DECORATE-side mechanics documented everywhere else above (the `DamageType` property, puff-carried
damage types, `Pain.`/`Death.`/`Wound.`/`Crash.<DamageType>` state labels, `PainChance`, and
`DamageFactor`/global `DamageType` block resolution) were spot-checked against UZDoom's
`thingdef_properties.cpp` and `thingdef_parse.cpp` and match the behavior described above.
