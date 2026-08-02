# `cl_maxdecals` (cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `CVARs:Display` (retrieved 2026-08-02, oldid=54715) + verified against Zandronum source's `src/g_shared/a_decals.cpp`.

Controls the maximum number of decals (blood splatters, projectile scorch marks, and similar wall graphics) that can exist simultaneously in the level.

## Default and special values

Default is 1024. Negative values are automatically clamped to 0.

- **0:** disables decals entirely; no decal graphics are rendered or created.
- **Positive values:** limit the total active decal count. When exceeded, the oldest decals are destroyed to stay within the limit.

The cvar carries the `CVAR_ARCHIVE` flag, allowing changes to persist to the config file. Changes trigger a `CUSTOM_CVAR` callback that enforces the negative-value clamp and removes excess decals if the new limit is lower than the current count.

## Performance considerations

High decal counts (hundreds visible on screen at once) can cause significant performance degradation even on fast machines. Lowering this value may improve frame rate on lower-end hardware.

## Related cvars

- `cl_bloodsplats` — enables/disables blood decals independently.
- `cl_missiledecals` — enables/disables missile scorch marks.
- `cl_spreaddecals` — controls decal spreading across nearby walls.
