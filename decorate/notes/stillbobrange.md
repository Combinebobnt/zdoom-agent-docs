# `Weapon.StillBobRange <float>`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/thingdef/thingdef_properties.cpp:2860-2864`, `src/p_pspr.cpp:642-652`. UZDoom has no such property (zero hits in its `src/`/`wadsrc/`). Shared mechanics, client overrides and citations: [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md).
**Bucket:** `DEFINE_CLASS_PROPERTY(stillbobrange, F, Weapon)` in Zandronum's `src/thingdef/thingdef_properties.cpp`.

Amplitude, in HUD pixels, of an extra vertical bob that plays while the player stands still. Default
`0` (off). Needs [`Weapon.StillBobSpeed`](stillbobspeed.md) non-zero to actually move.

- **Absolute, not a multiplier.** Unlike `BobRangeX`/`BobRangeY`, which scale the movement bob,
  this value is used directly as the sine amplitude. The weapon only moves down from rest: the
  offset runs from `0` to `+range` (a half-sine), never above the rest position.
- **Fades out with movement.** The effective range is `StillBobRange` minus the player's current
  movement bob (`player->bob`), so still bob shrinks as the player speeds up and stops once the
  movement bob reaches the range. Moving players get the ordinary bob instead.
- **Obeys the bob gate.** It only applies while bobbing is allowed (`WF_WEAPONBOBBING`, i.e. during
  `A_WeaponReady` without `WRF_NOBOB`) or the client has `cl_alwaysbob` on. So it pauses while
  firing, like the regular bob. `+Weapon.DontBob` disables it.
- **Vertical only.** There is no horizontal still bob.
- **Client override.** With `cl_usecustombob` on, `cl_stillbobrange` replaces this value (default
  `0`, i.e. off).

```decorate
Weapon.StillBobRange 2.0
Weapon.StillBobSpeed 0.5
```

## Engine-family divergence

UZDoom has no `Weapon.StillBobRange`. The line is a fatal `is an unknown actor property` error there
(`sc.ScriptError`, `src/scripting/decorate/thingdef_parse.cpp:977` at @98b16b78fc), so keep it
out of DECORATE that must also load on UZDoom. The ZScript porting route is in the
[concept file](../concepts/zandronum-weapon-sway.md#engine-family-divergence).

## See also

- [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md)
