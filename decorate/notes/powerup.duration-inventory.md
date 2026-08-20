# `powerup.duration <int>`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Source-derived (no wiki page consulted) — verified against the Zandronum source's
`src/thingdef/thingdef_properties.cpp:2131-2149` (`DEFINE_CLASS_PROPERTY_PREFIX(powerup, duration,
I, Inventory)`).
**Bucket:** the same `DEFINE_CLASS_PROPERTY_PREFIX(powerup, duration, I, Inventory)` macro on both
engines, requiring the actor descend from `Powerup` or `PowerupGiver` — Zandronum:
`src/thingdef/thingdef_properties.cpp`; UZDoom: `src/scripting/thingdef_properties.cpp` (a
different directory, but still native C++ — this one DECORATE-compat property parser was never
moved into UZDoom's ZScript tree even though `Powerup`/`PowerupGiver` themselves were, see
[Powerup](../classes/powerup.md)).

Sets a `Powerup`/`PowerupGiver` subclass's effect duration (`EffectTics`). The sign of the value
changes its unit, not just its magnitude:

- **Non-negative** (`>= 0`): the raw value is used directly as tics.
- **Negative**: the value is treated as a count of seconds and converted with `-i * TICRATE`
  (i.e. `Powerup.Duration -15` means "15 seconds", stored internally as `15 * TICRATE` tics).

This mirrors the same `i >= 0 ? i : -i*TICRATE` idiom used by several other DECORATE integer-tic
properties (e.g. `MorphProjectile`'s `duration` property, `thingdef_properties.cpp:2764-2768`) —
if a property's doc/prose doesn't explicitly say which convention it uses, check its definition
for this pattern before assuming a plain tic count.

**Clean agreement on UZDoom.** UZDoom's native property-parsing layer carries the identical
sign-check idiom for this property, at `src/scripting/thingdef_properties.cpp:1413-1422` — same
macro (with the same four arguments), same conversion, and the same fatal load-time error
(identically worded) for an actor that isn't a descendant of `Powerup`/`PowerupGiver`. This holds
even though `Powerup`/`PowerupGiver` themselves are ordinary ZScript classes on UZDoom
(`wadsrc/static/zscript/actors/inventory/powerups.zs`): neither class declares a ZScript-level
`property Duration:` of its own, so `Powerup.Duration <int>` is still parsed exclusively by this
one native C++ handler on UZDoom, exactly as on Zandronum — a DECORATE-style property that never
migrated into the ZScript property-declaration system despite its owning classes doing so.
`MorphProjectile`'s parallel `duration` property shows the same idiom carried forward on UZDoom
too, at `thingdef_properties.cpp:1837-1841`.

## Behavior notes

- A positive value is very easy to write by accident when the intent was "N seconds" — e.g.
  `Powerup.Duration 16` sets a 16-**tic** (~0.46s at 35 tics/sec) effect, not 16 seconds. There is
  no compiler warning for this on either engine; the mistake only shows up as an effect that
  expires almost immediately.
- `I_Error`s at load time if applied to a class that isn't a descendant of `Powerup` or
  `PowerupGiver` — this is a hard class-hierarchy requirement, not just convention, on both
  engines.

## See also

- [Powerup](../classes/powerup.md) — the base class this property applies to.
