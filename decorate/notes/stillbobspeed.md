# `Weapon.StillBobSpeed <float>`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/thingdef/thingdef_properties.cpp:2851-2855`, `src/p_pspr.cpp:642-652`. UZDoom has no such property (zero hits in its `src/`/`wadsrc/`). Shared mechanics, client overrides and citations: [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md).
**Bucket:** `DEFINE_CLASS_PROPERTY(stillbobspeed, F, Weapon)` in Zandronum's `src/thingdef/thingdef_properties.cpp`.

Speed of the standing-still bob set by [`Weapon.StillBobRange`](stillbobrange.md). Default `0`.
Does nothing unless the range is greater than `0`.

- **Units.** Each tic of `level.time` advances the bob angle by `speed * 128` fine angles,
  truncated to a whole number, and the offset is read from the half-sine table (4096 entries). At
  `1.0` one full down-and-back bounce takes **32 tics** (just under a second); `0.5` takes 64 tics.
  The period is about `32 / speed` tics (exact only when `speed * 128` is a whole number that
  divides 4096). A positive speed below `1/128` truncates to `0` and gives no bob.
- **Speed `0` with a range set** freezes the angle at `0`, which gives an offset of `0`: no bob.
- **Tied to `level.time`**, not to when the player stopped moving, so the bob does not restart
  from rest each time the player stops.
- **Negative values** run the angle backwards; since the half-sine table is symmetric in that use,
  the result looks the same as the positive speed.
- **Client override.** With `cl_usecustombob` on, `cl_stillbobspeed` replaces this value.

```decorate
Weapon.StillBobRange 1.5
Weapon.StillBobSpeed 1.0
```

## Engine-family divergence

UZDoom has no `Weapon.StillBobSpeed`. The line is a fatal `is an unknown actor property` error there
(`sc.ScriptError`, `src/scripting/decorate/thingdef_parse.cpp:977` at @98b16b78fc), so keep it
out of DECORATE that must also load on UZDoom. The ZScript porting route is in the
[concept file](../concepts/zandronum-weapon-sway.md#engine-family-divergence).

## See also

- [Zandronum weapon still-bob, sway and pitch offset](../concepts/zandronum-weapon-sway.md)
