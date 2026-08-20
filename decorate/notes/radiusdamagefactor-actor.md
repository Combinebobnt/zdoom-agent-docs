# `radiusdamagefactor <float>`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Source-derived (no wiki page consulted) — verified against the Zandronum source's
`src/thingdef/thingdef_properties.cpp:1274-1277` (property parsing, stores into `AMETA_RDFactor`)
and `src/p_map.cpp:5838` (`P_RadiusAttack` application) and `src/p_map.cpp:5955` (a second,
railgun-splash-specific application site).
**Bucket:** `DEFINE_PROPERTY(radiusdamagefactor, F, Actor)` in `src/thingdef/thingdef_properties.cpp`.

Per-actor multiplier applied to the damage a radius explosion (`A_Explode`, `A_RadiusThrust`, or
any other caller of the engine's internal `P_RadiusAttack`) inflicts on **this actor when it is
the victim** — i.e. it scales how much splash damage the actor *receives*, not how much its own
explosions deal. Default `1.0` (no change). Confirmed identical in effect on UZDoom, which exposes
the same DECORATE property name resolving to a native `RadiusDamageFactor` field
(`src/playsim/actor.h:1217`) consulted from the same two call sites inside `P_RadiusAttack`
(`src/playsim/p_map.cpp:6125` and `:6168`) — see "Engine-family divergence" below for the one real
implementation difference between the two engines.

## Behavior notes

- Applied directly to the falloff-adjusted `points` value inside `P_RadiusAttack`
  (`src/p_map.cpp:5838`), **before** the actor's own `DamageFactor` is applied (`DamageFactor` is
  applied later, inside `P_DamageMobj`). Because Zandronum's thrust calculation also derives from
  this same pre-`DamageFactor` `points` value (see [A_Explode](../actions/a_explode.md#behavior-notes)),
  `radiusdamagefactor` scales **both** the HP damage and the knockback thrust an actor receives
  from a radius attack, proportionally. This is the one knob in DECORATE that moves thrust and
  damage together — `DamageFactor` only ever affects the HP-damage half. Confirmed identical on
  UZDoom: `P_RadiusAttack` (`src/playsim/p_map.cpp:6295-6316`) likewise derives its per-target
  damage magnitude from the same `RadiusDamageFactor`-scaled `points` value computed inside
  `GetRadiusDamage`, and feeds that same magnitude into both the thrust calculation and the call
  into `P_DamageMobj` — `AActor::ApplyDamageFactor()` (`src/playsim/p_interaction.cpp:1234`) runs
  later, inside `P_DamageMobj`, same ordering as Zandronum.
- Setting `radiusdamagefactor` to `0.0` zeroes `points` outright for that actor, which zeroes both
  the damage and the thrust it receives from any radius attack — unlike `DamageFactor 0.0`, which
  only zeroes the HP damage and leaves thrust untouched. Same on UZDoom, same underlying mechanism.
- **Correction to this file's own `Provenance:` citation:** the `src/p_map.cpp:5955` site the
  citation above calls "railgun-splash-specific" is not railgun-related at all — reading the
  surrounding code shows it's the legacy/"old" radius-damage code path (the `else` branch guarded
  by `MF5_OLDRADIUSDMG` on the bomb spot or target, or the `ZACOMPATF_OLDRADIUSDMG` compat flag),
  used specifically for barrels and BossBrain-type actors that need the old square-distance falloff
  math instead of the newer 3D calculation — see the "Barrels always use the original code..."
  comment immediately above the branch. `AMETA_RDFactor` is consulted there too, at `:5955`, in the
  same `Scale()`-based percentage-damage calculation the old code path uses — so the underlying
  claim — that this second site also honors `radiusdamagefactor` — is correct, only the "railgun"
  label attached to it was wrong. Grepping the full Zandronum tree
  confirms `AMETA_RDFactor` has no other consultation site anywhere, including the railgun
  action-function/hitscan path, which never touches it. UZDoom has the exact same two-site
  structure for the same reason (`src/playsim/p_map.cpp:6292-6295` new-code branch vs.
  `:6380-6383` old-code/barrel branch calling `GetOldRadiusDamage`, which applies
  `RadiusDamageFactor` at `:6168`) — this is a plain factual correction to the original claim, not
  a cross-engine difference.

## Engine-family divergence: per-instance field vs. class-wide metadata

The property's *effect* is identical on both engines (see above), but the two engines store the
value through fundamentally different mechanisms, with a real behavioral consequence:

- **Zandronum stores it as `PClass`-level metadata**, set once when the DECORATE property line is
  parsed (`AMETA_RDFactor`, `src/thingdef/thingdef_properties.cpp:1274-1278`) and read back via
  `thing->GetClass()->Meta.GetMetaFixed(...)` at both `P_RadiusAttack` call sites. Every instance
  of a given actor class shares the one value baked in at parse time — there is no ACS `APROP_*`
  constant or any other mechanism for changing it per-instance at runtime (grepping Zandronum's
  `src/p_acs.cpp` and `src/actor.h` for an `APROP` tied to `AMETA_RDFactor`/radius-damage-factor
  turns up nothing); the only way to give two actors of the same class different radius-damage
  factors is to make them different classes.
- **UZDoom stores it as a genuine per-actor-instance field** — a native `double RadiusDamageFactor`
  member directly on `AActor` (`src/playsim/actor.h:1217`), defaulted from the class's declared
  value at spawn but independently readable and writable per instance from ZScript at runtime (the
  field is exposed to script via `DEFINE_FIELD(AActor, RadiusDamageFactor)`,
  `src/scripting/vmthunks_actors.cpp:2116`). A UZDoom mod can give one specific actor instance a
  different radius-damage factor than the rest of its class without subclassing — not possible on
  Zandronum.
- **Doesn't extend to UZDoom's destructible-geometry radius damage.** `P_RadiusAttack` on UZDoom
  unconditionally calls `P_GeometryRadiusAttack` (see
  [A_RadiusThrust](../actions/a_radiusthrust.md#engine-family-divergence)'s note on the same
  function) to damage UDMF health-sector/health-group geometry, and that function never reads
  `RadiusDamageFactor` — the field is only consulted in the two per-actor call sites inside
  `GetRadiusDamage`/`GetOldRadiusDamage`. Zandronum has no destructible-geometry system at all, so
  this gap doesn't arise there. Either way, `radiusdamagefactor` only ever protects the actor
  itself, never geometry near it.

## See also

- [Custom damage types](../concepts/custom-damage-types.md) — `DamageFactor` precedence chain;
  contrast with this property, which acts before that chain and also touches thrust.
- [A_Explode](../actions/a_explode.md) — the thrust-vs-`DamageFactor` interaction this property
  changes.
- [A_RadiusThrust](../actions/a_radiusthrust.md) — documents `P_GeometryRadiusAttack`, the
  UZDoom-only destructible-geometry damage path this property never reaches.
- [A_RadiusGive](../actions/a_radiusgive.md) — an unrelated `P_RadiusAttack`-adjacent function with
  its own coarse-vs-precise center-point inconsistency on UZDoom; not the same mechanism as this
  property (checked, no overlap).
