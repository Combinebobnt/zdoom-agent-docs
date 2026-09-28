# `Weapon.ViewSwaySpeed <float>`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/thingdef/thingdef_properties.cpp:2886-2890`, `src/p_pspr.cpp:654-737` (jump/motion `else if`: `:692-703`), `src/p_user.cpp:3039`, `:4037`. UZDoom has no such property (zero hits in its `src/`/`wadsrc/`). Shared mechanics, client overrides and citations: [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md).
**Bucket:** `DEFINE_CLASS_PROPERTY(viewswayspeed, F, Weapon)` in Zandronum's `src/thingdef/thingdef_properties.cpp`.

Makes the weapon lag behind the player's view when turning or looking up and down. Default `0`
(off). Positive and negative values are both allowed; negative reverses the direction.

- **Formula.** Each tic the sway target gets `AngleDelta * speed / 256` added to `x` and
  `PitchDelta * speed / 256` added to `y`, where the deltas are how much the player's angle and
  pitch changed that tic in fixed-point angle units. That works out to about `0.71 * speed` pixels
  per degree turned per tic. The sprite then eases toward that target (see the concept file).
- **Direction at positive speed.** Turning left (angle increasing) pushes the weapon right; looking
  down (pitch increasing) pushes it down. Both relax back to centre once the view stops moving.
- **`SwayStyle` filters the vertical part only.** The horizontal sway is always applied; see
  [`Weapon.SwayStyle`](swaystyle.md).
- **Shares the vertical axis** with [`MotionSwaySpeed`](motionswayspeed.md) and
  [`JumpSwaySpeed`](jumpswayspeed.md). The pitch term is added to one shared vertical target,
  along with jump sway or motion sway, never both in the same tic (they are an `if`/`else if`).
- **Client override.** With `cl_usecustomsway` on, `cl_viewswayspeed` replaces this value (menu
  slider range `-5` to `5`).

```decorate
Weapon.ViewSwaySpeed 2.0
```

## Engine-family divergence

UZDoom has no `Weapon.ViewSwaySpeed`. The line is a fatal `is an unknown actor property` error there
(`sc.ScriptError`, `src/scripting/decorate/thingdef_parse.cpp:977` at @98b16b78fc), so keep it
out of DECORATE that must also load on UZDoom. The ZScript porting route is in the
[concept file](../concepts/zandronum-weapon-sway.md#engine-family-divergence).

## See also

- [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md)
