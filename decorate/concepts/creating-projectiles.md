# Creating projectiles

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki "Creating new projectiles" (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Creating_new_projectiles&oldid=52213), cross-checked against the Zandronum source's `Projectile` property definition (`src/thingdef/thingdef_properties.cpp:1351-1357`), missile explosion logic (`src/p_mobj.cpp:1536-1562`), missile damage calculation (`src/p_mobj.cpp:3715-3733`), and action function implementations (`src/g_strife/a_spectral.cpp:101` for `A_Tracer2`; `src/g_doom/a_doomweaps.cpp:982` for `A_BFGSpray`). Zandronum corrections re-read at 3.3-alpha @bdd0f7beb: flag meanings (`src/actor.h:184,187`), damage multipliers per impact kind (`src/p_map.cpp:1246,1278`) and expression damage (`src/thingdef/thingdef_properties.cpp:550-561`), seeker `tracer` assignment (`src/thingdef/thingdef_codeptr.cpp:391,1270,1454,1719`), and `P_AproxDistance` (`src/p_maputl.cpp:59-64`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

This page covers the essential properties and state setup for creating a basic projectile (including homing variants), and the state selection logic when a projectile impacts its target. It does not cover action-function semantics in depth — see the `actions/` directory for those — or advanced behaviors like explosion trails or multi-damage-type handling.

## What the Projectile property does

The `Projectile` property is a shorthand that configures all the necessary actor flags for a projectile in one declaration. It ORs the following flags into the actor:

**`flags` (first word, via line 1354):**
- `MF_NOBLOCKMAP` — the projectile does not block other actors or appear in the blockmap.
- `MF_NOGRAVITY` — the projectile ignores gravity.
- `MF_DROPOFF` — the projectile can fall off ledges and platforms.
- `MF_MISSILE` — marks the actor as a projectile for engine lookups and special handling.

**`flags2` (second word, via line 1355):**
- `MF2_IMPACT` — the missile can activate line specials whose activation type is projectile impact (`SPAC_IMPACT`).
- `MF2_PCROSS` — the missile can activate line specials whose activation type is projectile cross (`SPAC_PCROSS`).
- `MF2_NOTELEPORT` — the projectile cannot be teleported.

**`flags5` (fifth word, conditional on Raven-game gametype, via line 1356):**
- `MF5_BLOODSPLATTER` — enabled for Raven-format games (Heretic, Hexen); has no effect on Doom/Doom II games.

In DECORATE, you may replace `Projectile` with individual flag declarations (`+NOBLOCKMAP`, `+NOGRAVITY`, etc.) if you need finer control, but the `Projectile` property is the standard starting point.

## Essential projectile properties

Beyond the `Projectile` flag bundle, a projectile typically requires:

- **`Damage`** — the impact damage value (integer). **Important:** the actual damage dealt is not constant; see "Damage randomization" below.
- **`Speed`** — the projectile's movement speed per tic.
- **`Height` and `Radius`** — the collision cylinder dimensions used for hit detection and blocking checks.
- **`Seesound` and `Deathsound`** — audio played at projectile spawn (launch) and explosion, respectively. Despite its name, "seesound" on a projectile means the launch sound, not a sound triggered when the projectile detects its target.

## State requirements

A projectile must define at least two states:

- **`Spawn:` state** — displayed while the projectile is in flight. This state must loop (via `loop` keyword) to continuously animate the projectile frame until it impacts something. If the Spawn state does not loop, the state machine falls through to the next state in the actor's state array when the Spawn state's duration expires — see `state-machine.md` for state-sequence rules.
- **`Death:` state** — displayed when the projectile impacts an object and explodes. This state typically ends with `stop` (removing the projectile) or `wait`/`loop` (leaving the remains in place).

A `Spawn:` state without a loop keyword is sometimes used deliberately to create a projectile with a fixed lifespan that automatically transitions to `Death:` after a set duration, rather than waiting for an impact — see "Complex projectiles" below.

## Impact state selection

When a projectile impacts an actor, wall, floor, or ceiling, the engine selects a death state based on what was hit, following this cascade:

Here a "damageable target" is an actor that is `SHOOTABLE`, a corpse (`CORPSE`), or already killed (`MF6_KILLED`). Zandronum also counts any player, as a workaround for a killed player losing `SHOOTABLE`.

1. **If the projectile hits a damageable target with the `NOBLOOD` flag:** the engine looks for a `Crash:` state. This state is for hitting non-bleeding targets.

2. **If no `Crash:` state exists, or the damageable target lacks `NOBLOOD`:** the engine looks for `XDeath:` (or equivalently, the dotted-label form `Death.Extreme`, per the fallback rules in `state-machine.md`).

3. **If no `XDeath:`/`Death.Extreme:` state exists, or the projectile hits a wall, floor, or an actor that is not a damageable target:** the engine uses the standard `Death:` state.

If none of these states are defined, the projectile is removed with no visible animation.

## Damage randomization

A projectile's `Damage` property is not the literal damage dealt on impact. Instead, the engine uses the `GetMissileDamage` function (`src/p_mobj.cpp:3715-3733`), which applies random variation to the damage:

```text
damage = ((random & mask) + add) * Damage
```

For normal projectiles (without the `MF4_STRIFEDAMAGE` flag), the function calculates:
```text
damage = ((random() & 7) + 1) * Damage
```

where `random()` is a pseudo-random value 0–255. This means a projectile with `damage 5` deals between 5 and 40 damage (1–8 multiplier times 5), not a constant 5. The randomization occurs for each impact; it is not a per-missile constant.

Strife-format weapons set the `MF4_STRIFEDAMAGE` flag, which changes the multiplier range to `(random() & 3) + 1` instead, yielding 1–4x damage.

Two exceptions. A parenthesized damage expression (`Damage (5)`) is evaluated and used as-is, with no random multiplier, and `Damage 0` deals 0. A ripper (`RIPPER`) passing through an actor uses `(random() & 3) + 2`, a 2-5x multiplier.

## Homing projectiles (seekermissiles)

To create a projectile that tracks a target:

1. Set the `SEEKERMISSILE` flag. This is what makes the standard fire functions fill in the projectile's `tracer` field (see below).
2. Call `A_Tracer2` or `A_SeekerMissile` in the projectile's `Spawn:` state. The function adjusts the projectile's angle and velocity each tic to home in on its `tracer` field.

Seeking functions steer toward `tracer` and do nothing while it is empty. The generic DECORATE fire functions assign it only when the spawned missile has `SEEKERMISSILE`. `A_CustomMissile`, `A_CustomComboAttack`, `A_MissileAttack`, `A_ComboAttack` and `A_BasicAttack` set it to the shooter's `target`. `A_FireCustomMissile` sets it to the actor its autoaim found, if any. Without the flag these functions leave `tracer` empty, so the missile flies straight. `A_SeekerMissile` with `SMF_LOOK` can also acquire a `tracer` itself when none is set.

## Complex projectiles

More advanced projectiles can:

- **Spawn trails or effects** by calling `A_SpawnItemEx` or similar in the `Spawn:` state to leave visual effects behind.
- **Use non-looping spawn states** to create projectiles with a fixed lifespan. In the example below, the `Spawn:` state lasts 100 tics and contains no `loop` keyword, so the state machine transitions to the physically next state (`Death:`) when the duration expires, triggering the explosion animation without requiring an explicit impact. The `Death:` state then calls `A_BFGSpray` to perform the actual explosion effect.
- **Randomize state duration** via the `RANDOMIZE` flag (`MF4_RANDOMIZE`), which subtracts 0–3 tics from the spawn state's duration at the moment the projectile spawns (`src/p_mobj.cpp:7076-7081`). This creates visual variation across multiple fired projectiles.

## Simple projectile example (generic)

```text
actor GenericShot
{
  Projectile
  Damage 5
  Speed 10
  Height 8
  Radius 6
  Seesound "misc/shot"
  Deathsound "misc/shotx"
  +RANDOMIZE
  States
  {
  Spawn:
    SHOT A 4 Bright
    Loop
  Death:
    SHOT BC 6 Bright
    Stop
  }
}
```

## Homing projectile example (generic)

```text
actor GenericTracker
{
  Projectile
  Damage 8
  Speed 10
  Height 8
  Radius 6
  Seesound "misc/lock"
  Deathsound "misc/hitx"
  +SEEKERMISSILE
  States
  {
  Spawn:
    TRAK A 4 Bright A_Tracer2
    Loop
  Death:
    TRAK BC 6 Bright
    Stop
  }
}
```

This example uses `A_Tracer2`, Strife's fixed-turn seeking function, which both engines provide. `A_SeekerMissile` is the more configurable alternative (see "Engine-family divergence" below).

## Limited-lifespan projectile example (generic)

```text
actor GenericBurst
{
  Projectile
  Damage 50
  Speed 25
  Height 8
  Radius 13
  Seesound "weapons/launch"
  Deathsound "weapons/burstx"
  States
  {
  Spawn:
    BUST A 100 Bright
  Death:
    BUST AB 8 Bright
    BUST C 8 Bright A_BFGSpray
    BUST DEF 8 Bright
    Stop
  }
}
```

In this example, the `Spawn:` state lasts 100 tics with no loop statement. When the duration expires, the projectile automatically transitions to the `Death:` state without requiring a physical impact, and the `Death:` sequence executes the explosion animation.

## Engine-family divergence: seeking behavior

**Seeking action functions.**

Both engines provide `A_Tracer2`, the Strife seeking action function, so the homing example above runs on either. Zandronum's version takes no parameters and turns by a fixed angle per call. UZDoom's takes an optional turn-angle parameter. `A_SeekerMissile` exists on both and offers flags (precise seeking, target lookup, speed options) that `A_Tracer2` lacks. Both engines support the `SEEKERMISSILE` flag and the `tracer` field that seeking functions require.

**Seeking missile trajectory math differs in non-precise mode.**

When calculating vertical velocity for a seeking missile (to adjust pitch toward a target above or below), Zandronum's non-precise seeking mode uses the octagonal-distance approximation function `P_AproxDistance`, which returns max(|dx|, |dy|) + min(|dx|, |dy|)/2 (overestimating diagonal distances) and can produce less-accurate aim in diagonal directions. UZDoom uses true Euclidean distance (`Distance2D`, based on sqrt(dx² + dy²)) for the same calculation. Both engines offer precise-mode seeking (enabled by the `SMF_PRECISE` flag in `A_SeekerMissile`) which uses proper Euclidean distance on both. For gameplay purposes, this divergence is minor — the difference is most visible in extreme diagonal ranges — but mods targeting both engines should be aware that non-precise seeking slightly favors axis-aligned directions in Zandronum.

## See also

- `state-machine.md` — detailed state-machine rules, reserved-state-name fallbacks, and label scoping.
- `actions/a_tracer2.md` (if documented) — specific semantics of the seeking action function.
- `actions/a_bfgspray.md` (if documented) — specific semantics of the explosion-spray action function.

## Open questions (unverified in this checkout — don't guess past these)

None at this time. All major claims have been traced against both UZDoom and Zandronum source.
