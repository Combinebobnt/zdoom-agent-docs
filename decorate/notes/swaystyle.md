# `Weapon.SwayStyle <name>`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/thingdef/thingdef_properties.cpp:2869-2881`, `src/p_pspr.h:58-61`, `src/p_pspr.cpp:721-736`, `:113-119`. UZDoom has no such property (zero hits in its `src/`/`wadsrc/`). Shared mechanics, client overrides and citations: [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md).
**Bucket:** `DEFINE_CLASS_PROPERTY(swaystyle, S, Weapon)` in Zandronum's `src/thingdef/thingdef_properties.cpp`.

Filters the vertical part of the weapon sway from [`ViewSwaySpeed`](viewswayspeed.md),
[`MotionSwaySpeed`](motionswayspeed.md) and [`JumpSwaySpeed`](jumpswayspeed.md). Default
`Normal`. Has no effect when all three speeds are `0`.

| Name | Integer | Vertical sway |
|---|---|---|
| `Normal` | 0 | applied as-is |
| `DownOnly` | 1 | only downward (positive `y`) movement kept |
| `UpOnly` | 2 | only upward (negative `y`) movement kept |
| `HorizontalOnly` | 3 | dropped entirely |

- **Horizontal sway is never filtered.** Every style applies the `x` part.
- **`HorizontalOnly` works by omission:** the style switch has no case for it, so the vertical
  offset is simply never added.
- **Names are case-insensitive;** an unknown name is a fatal `I_Error` ("Unknown swaystyle").
- **Integer order differs from [`ViewPitchStyle`](viewpitchstyle.md).** Here `DownOnly` is 1 and
  `UpOnly` is 2; in `ViewPitchStyle` `UpOnly` is 1 and `DownOnly` is 2. Matters when setting the
  `cl_swaystyle`/`cl_viewpitchstyle` cvars by number.
- **Client override.** With `cl_usecustomsway` on, `cl_swaystyle` (clamped to `0`-`3`) replaces
  this value.

```decorate
Weapon.ViewSwaySpeed 2.0
Weapon.SwayStyle "HorizontalOnly"
```

## Engine-family divergence

UZDoom has no `Weapon.SwayStyle`. The line is a fatal `is an unknown actor property` error there
(`sc.ScriptError`, `src/scripting/decorate/thingdef_parse.cpp:977` at @98b16b78fc), so keep it
out of DECORATE that must also load on UZDoom. The ZScript porting route is in the
[concept file](../concepts/zandronum-weapon-sway.md#engine-family-divergence).

## See also

- [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md)
