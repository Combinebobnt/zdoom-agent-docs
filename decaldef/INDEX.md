# DECALDEF doc index

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse DECALDEF**; `translatable`/`opaqueblood`, `generator optional` and
`A_SprayDecal` are UZDoom-only.

## Concepts

- [The DECALDEF lump](concepts/decaldef-lump.md) — tier A. When it's read (startup, load order,
  references resolve at parse time except the DECORATE `Decal` property); outer grammar (`decal`,
  `decalgroup`, `generator`, the five animator blocks); IDs and the `Decal` thing; redefinition
  (decals/groups replaced with references carried over, animators added alongside); decal keyword
  table per engine; `lowerdecal` on a group (fixed at load on UZDoom, re-picked per stamp on
  Zandronum); errors (unknown `animator` is a non-fatal red line on UZDoom, silent on Zandronum;
  animators that create nothing); which Zandronum machine's copy decides what (impact decals
  client-only, `SpawnDecal` sent by name, map-placed `Decal` things server-only).
- [The `decal` block](concepts/decal-definition.md) — tier B. Every keyword per engine with
  defaults and units (`pic` lookup, scale clamp, which styles honour alpha, alpha survives a later
  style keyword, `shade` colour forms and `BloodDefault`, the blood-colour override, `colors`
  gradient quirks, random flips XOR, `lowerdecal` group timing and the self-reference hazard,
  UZDoom-only `translatable`/`opaqueblood`); ID rules; the `Decal` thing 9200 (args, 64-unit
  trace, permanent, UZDoom picks by name via `arg0str`); online Zandronum clients never see
  map-placed `Decal` things.
- [Decal groups and generators](concepts/decalgroups-and-generators.md) — tier B. `decalgroup`
  weights (16-bit, 0 drops a member, odds quantized to 1/256) and nesting; when each reference
  picks a member, per engine; which impacts read a class's generator (hitscan shooter/weapon then
  puff, rail, missile; blood never); generator vs `Decal` property vs DeHackEd `Decal`; generators
  aren't inherited but the property is; `generator optional` (UZDoom-only); redefinition hazards;
  rail `FORCEDECAL`/`ALWAYSPUFF` divergence; Zandronum client-side resolution and
  `cl_hitscandecalhack`.
- [Animators](concepts/animators.md) — tier B. `fader`, `stretcher`, `slider`, `colorchanger`,
  `combiner` keywords, defaults and runtime behaviour; times are seconds x35 truncated to tics
  (stock `StretchTime 35` is 35 s); `*Start` counts from decal spawn; only the fader removes its
  decal; `GoalX`/`GoalY` are absolute scales; `DistX` is ignored; colorchanger works only on
  `shade` decals; freezing the level doesn't extend the schedule.
