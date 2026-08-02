# Custom damage types

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `Custom damage types` (retrieved 2026-08-02, oldid=52258) + verified against the Zandronum source's damage-type implementation in `src/p_interaction.cpp`, `src/p_mobj.cpp`, `src/g_shared/a_armor.cpp`, `src/info.cpp`, and `src/thingdef/thingdef_parse.cpp`.

DECORATE allows you to define custom damage types for projectiles, attacks, and actors — and to create specialized behavior (different pain/death/impact states, armor-bypassing, resistance/vulnerability) tailored to each type.

## Overview

Damage types are names (like `Fire`, `Ice`, `Poison`) that you assign to a projectile or attack and then use to trigger corresponding state sequences in receiving actors. Zandronum predefines a few built-in types (`Fire`, `Ice`, `Poison`, `Extreme`, `Drowning`, `Slime`, `Lava`, `Crush`, `Telefrag`, `Falling`, `Spike`, `Massacre`) but you can declare custom ones with their own default damage-reduction factors and armor-bypass rules.

## Assigning damage types to attacks

### On projectiles

Use the `DamageType` property to specify what type of damage a projectile inflicts:

```
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

```
Actor CustomPuff : BulletPuff
{
    DamageType CustomType
}
```

## Triggering custom states based on damage type

Actors can respond to specific damage types by defining state labels using the `State.DamageType` syntax. When damage of a given type is inflicted, the engine looks for the corresponding damage-typed state before falling back to the default:

### Pain states

Define custom pain reactions to specific damage types using `Pain.<DamageType>` labels:

```
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

```
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
1. If the damage type exists and health is below `GibHealth` (extreme death): `Death.Extreme.<DamageType>` (e.g., `Death.Extreme.Fire`)
2. If no such state exists or death is not extreme: `Death.<DamageType>`
3. For `Ice`-type damage on monsters/players with no custom ice death state: automatic generic freeze death (unless disabled via `deh.NoAutofreeze` or the `MF4_NOICEDEATH` flag)
4. If still no state found and death is extreme: `Death.Extreme` (the generic extreme/gib death)
5. If still no state found: `Death` (the default death sequence)

**Engine-gate note (Zandronum vs. GZDoom):** The ZDoom wiki notes "custom XDeath states are not currently supported" with a GZDoom-version qualifier (pre-1.8.10). Zandronum **does** support damage-typed XDeath states via the `Death.Extreme.<DamageType>` path — this fork diverges from the wiki's GZDoom-era statement.

### Wound states

For projectile impacts and grazes, define `Wound.<DamageType>` states:

```
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

For unblocked projectiles hitting non-actors (floor/ceiling/wall impacts), define `Crash.<DamageType>` states. Crash states apply both in 2-name form (`Crash.<DamageType>`) and in 3-name form with extreme gib (`Crash.Extreme.<DamageType>`):

```
Actor IceShard : Actor
{
    Projectile
    DamageType Ice
    States
    {
        Crash.Ice:
            ICSN A 10
            stop
    }
}
```

## Pain chance per damage type

Use `PainChance` with a damage-type parameter to set the probability an actor enters pain state for that damage type specifically:

```
Actor MyZombie : ZombieMan
{
    PainChance "Fire", 255     // Always enter pain state for Fire damage (100%)
    PainChance "Freeze", 0     // Never enter pain state for Freeze damage (0%)
    PainChance "Normal", 100   // Default chance (50% = 100 out of 200)
}
```

The numeric argument is out of 256 (where 256 = 100%). Set it to `0` to suppress pain states for a type entirely, and to `255` for guaranteed pain reaction.

## Damage resistance and vulnerability

Use the `DamageFactor` property to make an actor take more or less damage from a specific type:

```
Actor RaiDoom : DoomImp
{
    DamageFactor "Electric", 0.2   // Takes 20% damage from Electric (80% reduction)
    DamageFactor "Water", 1.8      // Takes 180% damage from Water (80% vulnerability)
}
```

Multiple `DamageFactor` entries work with one another. If an actor has no `DamageFactor` entry for a type, or has no `DamageFactor` entries at all, the global default factor for that type (see "Declaring damage types" below) is applied instead.

**Precedence chain for damage reduction:** When an actor takes damage:
1. If the actor has a `DamageFactor` for the exact damage type, use that (highest priority).
2. Otherwise, apply the global default factor for that damage type (if one exists).
3. Otherwise, if the actor has `DamageFactor "Normal"` (the untyped fallback), apply that.
4. Otherwise, use a factor of 1.0 (no reduction).

The global `ReplaceFactor` flag (see below) can suppress step 3 by making the global default **replace** the untyped fallback rather than multiply it.

## Declaring damage types with default properties

Define a damage type globally in DECORATE using the `DamageType` block:

```
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

```
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

```
DamageType Drowning
{
    NoArmor
}
```

**Important:** Declaring a damage type resets its definition to defaults. If you declare the same type twice, the second declaration replaces the first, not merges with it.

## Engine-specific caveats

**MAPINFO damagetype blocks:** The ZDoom wiki mentions declaring damage types via MAPINFO as an alternative to (and recommended replacement for) the DECORATE `DamageType` block. This is a GZDoom-family feature only — **Zandronum has no MAPINFO damagetype support**. In Zandronum, the DECORATE `DamageType` block is the only way to declare global damage-type properties.
