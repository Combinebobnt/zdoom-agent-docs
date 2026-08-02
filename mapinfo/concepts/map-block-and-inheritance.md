# Map block definitions and inheritance

**Tier:** B
**Engine:** Zandronum 3.2.1 (block forms and file-scoping verified in `src/g_mapinfo.cpp`); GZDoom-family keys noted where divergent
**Provenance:** ZDoom Wiki `MAPINFO/Map_definition` (retrieved 2026-07-31, oldid=55486) + verified against Zandronum engine source and spot-checked against UZDoom for engine-family divergence.

The `map` definition block and its related default-setting variants (`defaultmap`, `adddefaultmap`, `gamedefaults`) form a hierarchical inheritance system. A map definition specifies per-level behavior (sky texture, music, next map, flags, etc.); the default blocks establish shared baseline properties to avoid repetition across many maps.

## Block forms and scoping

**`map <lump> <nicename> { properties }`** — or **`map <lump> lookup <keyword> { properties }`**

Defines a single level. The `<lump>` is the map marker name (conventionally `MAP##` or `E#M#`, but any valid lump name works). The `<nicename>` is displayed on the automap; the `lookup` variant retrieves it from the `LANGUAGE` lump instead. Properties inherit from the current `defaultmap` baseline, then apply overrides specific to this map.

**`defaultmap { properties }`**

Resets the default baseline to the current `gamedefaults` state (see below), then applies properties to it. The new baseline applies to all subsequent `map` definitions *within the same file only* — `defaultmap` does not persist across `include` boundaries or into other MAPINFO lumps. `defaultmap` fully replaces any previous default state in the file; to add to an existing baseline without resetting it, use `adddefaultmap` instead.

**`adddefaultmap { properties }`**

Similar to `defaultmap`, but preserves any existing defaults already set by a prior `defaultmap` or `adddefaultmap` in the file and applies additional properties on top. A common pattern is to establish a game-wide baseline with `gamedefaults`, then refine it per-PWAD with `defaultmap`, and finally adjust per-subset-of-maps with `adddefaultmap`.

**`gamedefaults { properties }`**

Resets the global default baseline (used when loading PWADs that define their own `defaultmap`). Properties in `gamedefaults` apply to the entire game, including PWADs loaded afterwards — any PWAD's own `defaultmap` will inherit from this global baseline, not replace it entirely. `gamedefaults` is primarily used by base-game definitions and is less common in PWADs.

## Property surface and engine-family availability

A map definition accepts approximately 150 properties total, covering:
- **Rendering:** sky textures (`Sky1`, `Sky2`), fog color and density, lighting models (lighting shading, fake contrast)
- **Audio:** level music, custom sound sequences, intermission music
- **Flow:** next map on normal/secret exit, cluster assignment, par time, exit/enter screen animation
- **Gameplay:** gravity, air control, damage settings, monster behavior flags, player abilities (jump, crouch, freelook)
- **Compatibility:** flags controlling Hexen/Doom/Strife mode behaviors, monster telefrag, switch-range checking, infighting rules

### Significant engine-family divergence

**Zandronum 3.2.1 supports** a subset of the ZDoom-family property surface, including most core properties (sky, music, next, gameplay flags, compatibility flags). **Zandronum does not support** several renderer-specific and modern properties that exist in GZDoom/UZDoom:

- **Renderer features:** `EnableShadowmap`, `DisableShadowmap`, `AttenuateLights`, `EnableSkyboxAO`, `DisableSkyboxAO`, `NoFogOfWar`, `SkyMist`, `UseSkyMist`, `SkyMistYScale`, `ThickFogDistance`, `ThickFogMultiplier`, `ForceFakeContrast`, `ForceWorldPanning` — these are absent in Zandronum and will generate an "Unknown property" script warning.
- **ZScript integration:** `EventHandlers` (assigns ZScript event handlers to a map) — not applicable in Zandronum, which does not support ZScript.
- **Cutscenes:** `Intro` and `Outro` blocks (video/function/intermission cutscenes) — UZDoom supports these; Zandronum does not.
- **Metadata:** `Author`, `Label` — GZDoom-family properties for automap display; Zandronum lacks these.
- **Precaching:** `PrecacheClasses` (precaches actor sprites) — GZDoom-family only; Zandronum has `PrecacheSounds` and `PrecacheTextures` but not actor precaching.
- **Monster behavior:** `ProperMonsterFallingDamage` (corrects monster falling-damage formula) — UZDoom supports this; Zandronum does not.

**Zandronum-specific properties:**
- Multiplayer and campaign-mode properties (`IsLobby`, `NoSkirmish`, `NoBotNodes`, `BotEpisode`-related cluster flags) — these are Zandronum/Skulltag extensions not present in UZDoom/GZDoom.

The `pausemusicinmenus` property does exist in both Zandronum and UZDoom.

## Note on archival

This page's underlying property list (~150 entries, each with semantics, parameter formats, and interaction notes) represents archetype-2 material (Table-of-entries) and should eventually populate `mapinfo/inventory/map.md`. As of this writing, no `tools/gen_inventory.py` generator exists for MAPINFO keys, and no hand-maintained inventory file exists. The detailed property descriptions from the ZDoom wiki remain unindexed in this documentation tree; see the source wiki page for the complete reference until an inventory table is written.
