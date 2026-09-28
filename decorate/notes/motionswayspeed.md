# `Weapon.MotionSwaySpeed <float>`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/thingdef/thingdef_properties.cpp:2895-2899`, `src/p_pspr.cpp:692-703`, `src/templates.h:191-194`, `src/p_user.cpp:3625`. UZDoom has no such property (zero hits in its `src/`/`wadsrc/`). Shared mechanics, client overrides and citations: [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md).
**Bucket:** `DEFINE_CLASS_PROPERTY(motionswayspeed, F, Weapon)` in Zandronum's `src/thingdef/thingdef_properties.cpp`.

Vertical sway from the player's height changing (stairs, lifts, falling) and from crouching.
Default `0` (off).

- **Formula.** Each tic the vertical sway target gets `(zDiff + crouchviewdelta / 2) * speed`,
  where `zDiff` is `z - PrevZ` (height change since last tic) clamped to `±10 * speed` map units.
- **Crouching is a steady offset, not a transient.** `crouchviewdelta` is how far the view is
  currently lowered by crouching (negative while crouched), so at positive speed the weapon rises
  by half that drop times `speed` for as long as the player stays crouched.
- **Jump sway wins.** On any tic where [`JumpSwaySpeed`](jumpswayspeed.md) applies, this term is
  skipped entirely (`else if`). Falling that did not start with a jump, or falling faster than the
  jump speed, uses this term instead.
- **Negative values are broken.** The clamp bounds become `+10*|speed|` to `-10*|speed|` (min above
  max), and Zandronum's `clamp` then returns the lower bound for nearly every input. The result is
  a constant upward offset of about `10 * speed²` pixels even while standing still, rather than a
  reversed sway. Found by reading source, not yet confirmed in-engine; avoid negative values. The
  client's `cl_motionswayspeed` slider allows `-5` to `5` and hits the same path.
- **Client override.** With `cl_usecustomsway` on, `cl_motionswayspeed` replaces this value.

```decorate
Weapon.MotionSwaySpeed 1.0
```

## Engine-family divergence

UZDoom has no `Weapon.MotionSwaySpeed`. The line is a fatal `is an unknown actor property` error there
(`sc.ScriptError`, `src/scripting/decorate/thingdef_parse.cpp:977` at @98b16b78fc), so keep it
out of DECORATE that must also load on UZDoom. The ZScript porting route is in the
[concept file](../concepts/zandronum-weapon-sway.md#engine-family-divergence).

## See also

- [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md)
