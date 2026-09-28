# `Weapon.JumpSwaySpeed <float>`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/thingdef/thingdef_properties.cpp:2904-2908`, `src/p_pspr.cpp:692-695`, `src/p_user.cpp:3170-3210`, `:3907-3914`. UZDoom has no such property (zero hits in its `src/`/`wadsrc/`). Shared mechanics, client overrides and citations: [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md).
**Bucket:** `DEFINE_CLASS_PROPERTY(jumpswayspeed, F, Weapon)` in Zandronum's `src/thingdef/thingdef_properties.cpp`.

Vertical sway while the player is in the air after a jump. Default `0` (off).

- **Formula.** Each tic the vertical sway target gets `velz * speed` (vertical velocity in map
  units per tic). At positive speed the weapon rises while falling and dips while going up.
- **When it applies.** Only while the player is off the ground, `jumpTics` is non-zero, and
  `|velz|` is no more than the player's jump velocity (`CalcJumpVelz()`). By default a jump
  sets `jumpTics` to `-1` and it keeps counting down through the airtime, only returning to `0` a
  few tics after landing, so a plain walk-off fall normally does not qualify. Once a fall outpaces
  the jump speed the term stops applying.
- **Shorter under Skulltag jumping.** With the `ZACOMPATF_SKULLTAG_JUMPING` compat flag, a jump
  sets `jumpTics` to 18 instead and it stops at `0`, so jump sway only covers the first 18 tics
  of the jump and motion sway takes over for the rest of the airtime.
- **Spring pads skip it.** A jump from a `PLANEF_SPRINGPAD` floor sets `jumpTics` to `0`, so it
  gets motion sway instead of jump sway.
- **Takes precedence over [`MotionSwaySpeed`](motionswayspeed.md).** On tics where this applies,
  motion sway is skipped; on the others (landing, long falls, non-jump falls) motion sway takes
  over if set.
- **Added to the same vertical target** as [`ViewSwaySpeed`](viewswayspeed.md)'s pitch part, then
  filtered by [`SwayStyle`](swaystyle.md).
- **Client override.** With `cl_usecustomsway` on, `cl_jumpswayspeed` replaces this value.

```decorate
Weapon.JumpSwaySpeed 0.5
```

## Engine-family divergence

UZDoom has no `Weapon.JumpSwaySpeed`. The line is a fatal `is an unknown actor property` error there
(`sc.ScriptError`, `src/scripting/decorate/thingdef_parse.cpp:977` at @98b16b78fc), so keep it
out of DECORATE that must also load on UZDoom. The ZScript porting route is in the
[concept file](../concepts/zandronum-weapon-sway.md#engine-family-divergence).

## See also

- [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md)
