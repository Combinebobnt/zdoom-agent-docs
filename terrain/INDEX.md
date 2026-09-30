# TERRAIN doc index

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse TERRAIN**; footsteps, `damageonland` and per-sector terrain overrides are
UZDoom-only, and the footstep timing keywords are named differently on each engine.

## Concepts

- [The TERRAIN lump](concepts/terrain-lump.md) — tier A. When it's read (startup, load order,
  names resolve at parse time); outer grammar (`splash`/`terrain`/`floor`/`defaultterrain`,
  `modify`, redefinition resets, the built-in `Solid`); `ifdoom`..`endif` (Chex counts as Doom, no
  nesting); keyword table per engine (`walksteptics` vs `walkingsteptime`, each fatal on the other
  engine); errors; `damagetimemask` is an interval on UZDoom (default 31) but a bitmask on
  Zandronum (default 0, every tic); who takes damage; friction precedence inverted; `floor
  optional`/`None` UZDoom-only; which Zandronum machine's copy decides damage, splashes, friction.
- [TERRAIN `splash` blocks](concepts/splash-block.md) — tier B. All 11 splash keywords with
  defaults and units (velocity shifts, `-1` = leave X/Y alone); redefinition without `modify`
  resets, `modify` can't clear `noalert`; errors; the order of checks in `P_HitWater` (slow-fall
  cutoff for monsters and players, `Mass` below 10 is small, small splashes never alert, stock
  `BulletPuff` splashes small); `DONTSPLASH`/`NOSPLASHALERT` details; 3D-floor, explosion-distance
  and `target` differences; server-decided splashes on Zandronum.
- [TERRAIN `terrain` blocks](concepts/terrain-block.md) — tier B. Every terrain keyword per engine
  (value, default, units, fatal vs silent bad input); damage runtime (level-time clock,
  `allowprotection` = `PowerIronFeet` only, `damagetype lava` is `Fire`, ice-corpse melt), UZDoom
  `damageonland` quirks; footclip (shallowest wins, 3D floors); the friction scale and the
  Zandronum `friction 1.0` trap (about 1/8 movement speed); what reads `liquid`; UZDoom footsteps
  (`stepvolume` defaults to 0); which Zandronum machine's copy decides each keyword.
- [How a floor gets its terrain](concepts/floor-assignment.md) — tier B. `floor` uses the same
  texture lookup as a sector's floor (TEXTURES `texture` beats `flat`, wall textures as a
  fallback); terrain doesn't follow an animation, so each frame needs its own line;
  `defaultterrain` is read at lookup time, so the last one wins; an unknown terrain leaves the
  texture unassigned on UZDoom but sets `Solid` on Zandronum; which plane decides the terrain for
  3D floors, `Transfer_Heights` and 3D midtex (on Zandronum a 3D floor's friction and splash come
  from different planes); what reads ceiling terrain; UZDoom per-sector overrides (UDMF,
  ExtraData, `SetSectorTerrain`, `GetActorFloorTerrain` reads a cached value).
