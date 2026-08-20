# Map block definitions and inheritance

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `MAPINFO/Map_definition` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=MAPINFO%2FMap_definition&oldid=55486) + verified against Zandronum engine source and spot-checked against UZDoom for engine-family divergence.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

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
- **Precaching:** `PrecacheClasses` (precaches actor sprites) — GZDoom-family only; Zandronum has `PrecacheSounds` but not `PrecacheTextures` or actor precaching.
- **Monster behavior:** `ProperMonsterFallingDamage` (corrects monster falling-damage formula) — UZDoom supports this; Zandronum does not. Zandronum's monster falling damage is gated by a separate, older mechanism (the `monsterfallingdamage`/`nomonsterfallingdamage` keys below), not by this property.

**Zandronum-specific properties:**
- Multiplayer and campaign-mode properties (`IsLobby`, `NoSkirmish`, `NoBotNodes` at map level, and `BotEpisode` at episode level) — these are Zandronum/Skulltag extensions not present in UZDoom/GZDoom.

The `pausemusicinmenus` property does exist in both Zandronum and UZDoom.

## Monster falling damage and the HexenHack retraction gap

This section is engine-source-derived (verified against the Zandronum source's `src/g_mapinfo.cpp` and the UZDoom source's `src/gamedata/g_mapinfo.cpp` — specifically `FMapInfoParser::ParseMapHeader`/`ParseMapInfo` and related declarations in `src/g_level.h` / `src/gamedata/g_mapinfo.h`), not drawn from the wiki page this file otherwise cites in its `Provenance:` field above.

The `monsterfallingdamage` / `nomonsterfallingdamage` map-definition keys set/clear the
`LEVEL2_MONSTERFALLINGDAMAGE` level flag (see [Monster and player falling
damage](../../decorate/concepts/falling-damage.md) for what that flag gates). Like any other
key, setting it through `defaultmap`/`gamedefaults` and inheriting it into a `map` block normally
works the way "Block forms and scoping" above describes — with one gap specific to this flag.

`ParseMapHeader` copies the current `defaultmap`/`gamedefaults` baseline onto the new
`level_info_t` first (`*levelinfo = defaultinfo`), which is where an inherited
`nomonsterfallingdamage` would normally take effect. But when the map header itself is declared
with a **bare numeric map name** (`map 1 "..."` rather than `map map01 "..."` or a named lookup —
the classic Hexen-style header form, detected by `sc.CheckNumber()`), `ParseMapHeader`
subsequently re-applies a fixed set of flags unconditionally, **after** that copy, including
`LEVEL2_MONSTERFALLINGDAMAGE` (alongside `LEVEL_NOINTERMISSION`, `LEVEL_SNDSEQTOTALCTRL`,
`LEVEL_FALLDMG_HX`, `LEVEL_ACTOWNSPECIAL`, `LEVEL2_HEXENHACK`, `LEVEL2_INFINITE_FLIGHT`, and
`LEVEL2_MISSILESACTIVATEIMPACT`). This re-application ("HexenHack") runs regardless of what the
inherited baseline said, so a `nomonsterfallingdamage` set via `defaultmap`/`gamedefaults` has no
effect on any map declared this way — including hexen.wad's own IWAD map declarations, which use
exactly this numeric header form. A PWAD cannot retract the flag from an already-parsed IWAD
level's `level_info_t` either — parsing only ever creates or fully overwrites a `wadlevelinfos`
entry keyed by map name, there is no partial-flag-clear operation exposed to a later MAPINFO lump.

**On Zandronum,** the trigger is purely the header's **numeric-vs-named form**: a numeric map name triggers HexenHack regardless of context. However, see the divergence section below for UZDoom's format-based gating and a critical caveat about HexenHack flag stickiness within a lump that affects both engines. Given the sticky-flag limitation, the practical mitigation shape is "accept HexenHack as unavoidable in affected lumps" rather than "clear it everywhere."

A `gamedefaults` block is also not a safe way to set this key in isolation: `gamedefaults` fully
resets (`Reset()`s) the entire global baseline before applying the block's properties
(`ParseMapInfo`'s handling of the `gamedefaults` keyword), so a `gamedefaults { nomonsterfallingdamage }`
block silently discards every other global default property that isn't restated in the same block
— it doesn't merge one flag on top of the existing baseline.

## Engine-family divergence: HexenHack format-type gating

Zandronum and UZDoom differ in how strictly they trigger the HexenHack retraction, with an important caveat about the HexenHack flag's persistence within a lump. When a numeric map name is encountered, Zandronum sets the HexenHack flag unconditionally; UZDoom gates it based on MAPINFO format — the flag is only set when the lump uses old-style (non-braced) syntax. UZDoom detects format by testing for an opening brace when beginning to parse each definition. In new-format (braced) MAPINFO, numeric map names in UZDoom are accepted literally and do not trigger HexenHack.

**Critical limitation:** The HexenHack flag is set to false only when a new MAPINFO lump begins parsing (`ParseMapInfo` entry), not between individual map headers within the same lump. Once a numeric map name sets the flag to true in either engine, it remains true for all subsequent map definitions in that lump — including maps declared with named lumps rather than bare numbers. This means the practical mitigation from the HexenHack retraction section (declaring new maps with named lumps) works on Zandronum only if no preceding map in that lump used a numeric name. UZDoom's format gating provides better isolation: maps in new-format (braced) MAPINFO are never affected by HexenHack, regardless of what came before in the same lump.

Zandronum's less-strict triggering means the gap described above can affect any map following a numeric-named map, even if declared with a named lump. UZDoom's limitation to old-format lumps means the gap is specific to legacy (non-braced) MAPINFO files, not a general property mechanism.

## Note on archival

This page's underlying property list (~150 entries, each with semantics, parameter formats, and interaction notes) represents archetype-2 material (Table-of-entries) and should eventually populate `mapinfo/inventory/map.md`. As of this writing, no `tools/gen_inventory.py` generator exists for MAPINFO keys, and no hand-maintained inventory file exists. The detailed property descriptions from the ZDoom wiki remain unindexed in this documentation tree; see the source wiki page for the complete reference until an inventory table is written.
