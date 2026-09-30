# Terrain functions (`SetSectorTerrain`/`GetActorFloorTerrain`): UZDoom only

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-29)
**Provenance:** written from the UZDoom source's `src/playsim/p_acs.cpp:4819`, `:4839` (enum
entries), `:6560-6573` (`ACSF_SetSectorTerrain`) and `:6754-6767` (`ACSF_GetActorFloorTerrain`),
`src/gamedata/p_terrain.cpp:697-710` (`P_FindTerrain`); the Zandronum 3.3-alpha @bdd0f7beb source's `src/p_acs.cpp`
(`EACSFunctions` enum, which has neither name, and `CallFunction`'s `default:` case at `:9059`);
and the zt-bcc source's `lib/zcommon.bcs:1725`, `:1836`. The terrain model these functions read
and write is from [`terrain/concepts/floor-assignment.md`](../../terrain/concepts/floor-assignment.md);
no wiki page was used.
**Bucket:** extension function (`SetSectorTerrain` index -95, `GetActorFloorTerrain` index -205;
dispatched as `ACSF_SetSectorTerrain`/`ACSF_GetActorFloorTerrain`).

One file for both because they share one root cause on Zandronum (neither index is in its
extension enum) and are the ACS side of the same UZDoom per-sector terrain override. How a floor
gets its terrain, when an actor's cached terrain refreshes, and what a terrain does are on
[`floor-assignment.md`](../../terrain/concepts/floor-assignment.md) and
[`terrain-block.md`](../../terrain/concepts/terrain-block.md).

## `void SetSectorTerrain(int tag, int plane, str terrain)`

Overrides the TERRAIN terrain of the floor or ceiling of every sector with `tag`, regardless of
the flat.

- `tag`: sectors to change. **`0` means every untagged sector**, not the activator's sector.
- `plane`: `0` floor, `1` ceiling. Any other value does nothing.
- `terrain`: a terrain name from TERRAIN, resolved at the call. An unknown name, `""` or `"None"`
  clears the override, so the plane goes back to its flat's terrain. There is no error message
  for a typo: it silently clears instead.
- No return value, no message in any case.

The override is stored per sector and saved in savegames by name. Actors standing on the sector pick it
up at their next cached-terrain refresh (usually their next move), while splashes, friction and
footclip read it at once. See
[floor-assignment.md's per-sector terrain section](../../terrain/concepts/floor-assignment.md#per-sector-terrain-uzdoom-only)
for the full table.

## `str GetActorFloorTerrain(int tid)`

Returns the name of the terrain the actor is standing on.

- `tid`: `0` reads the activator; otherwise the first actor with that TID.
- **Return value:** the terrain's name (`"Solid"` for the built-in default terrain), or `""` when
  no actor matches.
- It reads the actor's **cached** terrain, not the sector's current one. The cache reflects 3D
  floors and 3D middle textures under the actor, but lags a `SetSectorTerrain` or flat change
  until the actor's next refresh. An actor that hasn't moved since the change still reports the
  old terrain.

## Engine-family divergence: neither function exists on Zandronum

zt-bcc declares both (`zcommon.bcs:1725`, `:1836`), so scripts compile for either engine.
Zandronum's `EACSFunctions` enum has no entry at index 95 or 205, so the call reaches
`CallFunction`'s `default:` case and returns `0` with no effect and no message (`p_acs.cpp:9059`).
`SetSectorTerrain` silently does nothing. `GetActorFloorTerrain` returns `0`, which as a string
is string-table index 0 of the calling module, not `""`: don't compare its result against `""`
on Zandronum. Same shape of gap as
[`zdoom-math-stubs.md`](zdoom-math-stubs.md). Zandronum has no ACS way to read or change a
sector's terrain; UDMF `floorterrain`/`ceilingterrain` are UZDoom-only too.
