# `cl_maxdecals` (cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `CVARs:Display` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3ADisplay&oldid=54715) + verified against Zandronum source's `src/g_shared/a_decals.cpp` (cvar callback 574-591, `DImpactDecal::CheckMax`/`StaticCreate` 648-717, permanent `ShootDecal` path and `Decal` actor 780-862).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Controls the maximum number of impact decals (blood splatters, bullet and projectile scorch marks, and similar wall graphics created during play) that can exist simultaneously in the level. Permanent decals are not counted or limited: map-placed `Decal` actors and decals from ACS `SpawnDecal` with the `SDF_PERMANENT` flag.

## Default and special values

Default is 1024. Negative values are automatically clamped to 0.

- **0:** no new impact decals are created, and setting it removes every existing impact decal. Permanent decals still appear.
- **Positive values:** limit the active impact decal count. Each new impact decal (including the extra pieces a spread decal places on neighbouring walls) first destroys the oldest one once the count has reached the limit.

The cvar carries the `CVAR_ARCHIVE` flag, allowing changes to persist to the config file. Changes trigger a `CUSTOM_CVAR` callback that enforces the negative-value clamp and removes excess decals if the new limit is lower than the current count.

## Performance considerations

High decal counts (hundreds visible on screen at once) can cause significant performance degradation even on fast machines. Lowering this value may improve frame rate on lower-end hardware.

## Related cvars

- `cl_bloodsplats` — enables/disables blood decals independently.
- `cl_missiledecals` — enables/disables missile scorch marks.
- `cl_spreaddecals` — controls decal spreading across nearby walls.
