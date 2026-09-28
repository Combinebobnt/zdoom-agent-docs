# `Weapon.ViewPitchStyle <name>`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/thingdef/thingdef_properties.cpp:2913-2925`, `src/p_pspr.h:67-71`, `src/p_pspr.cpp:739-771`, `wadsrc/static/menudef.za:652-659`. UZDoom has no such property (zero hits in its `src/`/`wadsrc/`). Shared mechanics, client overrides and citations: [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md).
**Bucket:** `DEFINE_CLASS_PROPERTY(viewpitchstyle, S, Weapon)` in Zandronum's `src/thingdef/thingdef_properties.cpp`.

Chooses which part of the player's pitch drives [`Weapon.ViewPitchOffset`](viewpitchoffset.md).
Default `Full`. Has no effect while the offset is `0`.

Each style turns pitch into a factor `v`; the offset step then moves the weapon up by
`v * ViewPitchOffset` (see that note for the exact formula and negative offsets). With a positive
offset:

| Name | Integer | `v` | Effect (positive offset) |
|---|---|---|---|
| `Full` | 0 | `0` looking straight down, `0.5` level, `1` straight up | always raised, more when looking up |
| `UpOnly` | 1 | `0` level or down, up to `1` straight up | raised only when looking up |
| `DownOnly` | 2 | `0` level or up, up to `1` straight down | raised only when looking down |
| `DownAndUp` | 3 | `0` level, up to `1` straight up or down | raised when looking either way |
| `Centered` | 4 | `1` straight down, `0` level, `-1` straight up | raised looking down, lowered looking up |

- **`v` is linear in pitch** and reaches its extremes only at `±90°`, so with the usual pitch
  limits they are never quite reached.
- **`Centered`** is commented in source as Dark Forces style: no offset looking straight ahead.
  It is the only style where `v` goes negative.
- **A negative offset reverses every row** (and adds a constant drop; see
  [`ViewPitchOffset`](viewpitchoffset.md)).
- **Integer order differs from [`SwayStyle`](swaystyle.md)** (`UpOnly`/`DownOnly` are swapped).
- **Names are case-insensitive;** an unknown name is a fatal `I_Error` ("Unknown viewpitchstyle").
- **Client override.** With `cl_usecustompitch` on, `cl_viewpitchstyle` (clamped to `0`-`4`)
  replaces this value.

```decorate
Weapon.ViewPitchOffset 8
Weapon.ViewPitchStyle "Centered"
```

## Engine-family divergence

UZDoom has no `Weapon.ViewPitchStyle`. The line is a fatal `is an unknown actor property` error there
(`sc.ScriptError`, `src/scripting/decorate/thingdef_parse.cpp:977` at @98b16b78fc), so keep it
out of DECORATE that must also load on UZDoom. The ZScript porting route is in the
[concept file](../concepts/zandronum-weapon-sway.md#engine-family-divergence).

## See also

- [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md)
