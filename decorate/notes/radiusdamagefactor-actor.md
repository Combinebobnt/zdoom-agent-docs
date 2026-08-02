# `radiusdamagefactor <float>`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Source-derived (no wiki page consulted) — verified against the Zandronum source's
`src/thingdef/thingdef_properties.cpp:1274-1277` (property parsing, stores into `AMETA_RDFactor`)
and `src/p_map.cpp:5838` (`P_RadiusAttack` application) and `src/p_map.cpp:5955` (a second,
railgun-splash-specific application site).
**Bucket:** `DEFINE_PROPERTY(radiusdamagefactor, F, Actor)` in `src/thingdef/thingdef_properties.cpp`.

Per-actor multiplier applied to the damage a radius explosion (`A_Explode`, `A_RadiusThrust`, or
any other caller of the engine's internal `P_RadiusAttack`) inflicts on **this actor when it is
the victim** — i.e. it scales how much splash damage the actor *receives*, not how much its own
explosions deal. Default `1.0` (no change).

## Behavior notes

- Applied directly to the falloff-adjusted `points` value inside `P_RadiusAttack`
  (`src/p_map.cpp:5838`), **before** the actor's own `DamageFactor` is applied (`DamageFactor` is
  applied later, inside `P_DamageMobj`). Because Zandronum's thrust calculation also derives from
  this same pre-`DamageFactor` `points` value (see [A_Explode](../actions/a_explode.md#behavior-notes)),
  `radiusdamagefactor` scales **both** the HP damage and the knockback thrust an actor receives
  from a radius attack, proportionally. This is the one knob in DECORATE that moves thrust and
  damage together — `DamageFactor` only ever affects the HP-damage half.
- Setting `radiusdamagefactor` to `0.0` zeroes `points` outright for that actor, which zeroes both
  the damage and the thrust it receives from any radius attack — unlike `DamageFactor 0.0`, which
  only zeroes the HP damage and leaves thrust untouched.
- A second, distinct application site exists at `src/p_map.cpp:5955`, in the splash-damage path
  used by railgun-type attacks — not part of `P_RadiusAttack`'s main body, but the same
  `AMETA_RDFactor` value is consulted there too.

## See also

- [Custom damage types](../concepts/custom-damage-types.md) — `DamageFactor` precedence chain;
  contrast with this property, which acts before that chain and also touches thrust.
- [A_Explode](../actions/a_explode.md) — the thrust-vs-`DamageFactor` interaction this property
  changes.
