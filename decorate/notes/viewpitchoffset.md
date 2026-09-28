# `Weapon.ViewPitchOffset <float>`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/thingdef/thingdef_properties.cpp:2930-2934`, `src/p_pspr.cpp:739-772`. UZDoom has no such property (zero hits in its `src/`/`wadsrc/`). Shared mechanics, client overrides and citations: [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md).
**Bucket:** `DEFINE_CLASS_PROPERTY(viewpitchoffset, F, Weapon)` in Zandronum's `src/thingdef/thingdef_properties.cpp`.

Moves the weapon vertically according to the player's pitch, in HUD pixels. Default `0`, which
skips the whole pitch step. How pitch maps to movement is set by
[`Weapon.ViewPitchStyle`](viewpitchstyle.md).

- **Formula.** `y -= v * offset + min(0, offset)`, where `v` is the style's pitch factor (`0` to `1`,
  or `-1` to `1` for `Centered`). With a positive offset the weapon moves up by `v * offset` pixels.
- **A negative offset also shifts the rest position.** The `min(0, offset)` term lowers the weapon
  by `|offset|` pixels on top of the reversed `v * offset`. For example, `-8` with `Full` sits
  12 pixels lower looking level (`8 * 0.5 + 8`) and 16 lower looking straight up.
- **Not smoothed.** Unlike sway, the pitch offset follows the current pitch directly each frame.
- **Applied last,** after the regular bob, still bob and sway, and is not gated by
  `A_WeaponReady`'s bob flags. `+Weapon.DontBob` still disables it along with everything else.
- **Client override.** With `cl_usecustompitch` on, `cl_viewpitchoffset` replaces this value (menu
  slider range `-16` to `16`).

```decorate
Weapon.ViewPitchOffset 6
Weapon.ViewPitchStyle "UpOnly"
```

## Engine-family divergence

UZDoom has no `Weapon.ViewPitchOffset`. The line is a fatal `is an unknown actor property` error there
(`sc.ScriptError`, `src/scripting/decorate/thingdef_parse.cpp:977` at @98b16b78fc), so keep it
out of DECORATE that must also load on UZDoom. The ZScript porting route is in the
[concept file](../concepts/zandronum-weapon-sway.md#engine-family-divergence).

## See also

- [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md)
