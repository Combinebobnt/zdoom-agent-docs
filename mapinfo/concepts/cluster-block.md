# Cluster block definition

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `MAPINFO/Cluster_definition` (retrieved 2026-09-28, same revision as the 2026-08-01 intake, https://zdoom.org/w/index.php?title=MAPINFO%2FCluster_definition&oldid=49574) + re-verified against Zandronum source (`src/g_mapinfo.cpp:702-791`, unknown-key handling `src/g_mapinfo.cpp:482-495,583-593,779-784,1999`; `src/g_level.cpp:741,977-1046,1672-1743`; `src/g_hub.cpp:130-143`) and UZDoom source (`src/gamedata/g_mapinfo.cpp:819-938`, `src/g_level.cpp:699-717`, `src/g_hub.cpp:120-132`, `src/common/engine/stringtable.cpp:1019-1031`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

A cluster is a logical grouping of maps that can optionally display transition messages and/or form a hub with shared state. The cluster block in MAPINFO defines cluster-wide settings: intermission messages, music, graphics, hub behavior, and cutscene blocks.

## Block syntax

```text
cluster <number> { properties }
```

`<number>` is the cluster identifier (a positive integer). Cluster 0 is the default unset value in level definitions, so using a cluster number ≥ 1 is recommended to avoid confusion with maps that lack an explicit cluster assignment. Properties are whitespace-separated key-value pairs, most accepting a single value or a type-specific set of values.

## Properties

### Common to both Zandronum and GZDoom-family engines

**EnterText**, **ExitText**  
Transition messages displayed when entering or leaving the cluster. Both accept three input forms: a literal string (quoted, newlines via comma-separated quoted lines), `lookup, "<keyword>"` to reference a string in the [LANGUAGE](../../language/concepts/language-lump.md) lump, or `$<keyword>` (shorthand for lookup). If the next level's cluster has an `EnterText`, it suppresses the current cluster's `ExitText`. Zandronum and UZDoom parse these identically; UZDoom adds an additional silent fallback: if the literal text matches the English default-language value of `CLUSTERENTER<N>` or `CLUSTEREXIT<N>` (where N is the cluster number), the literal is promoted to a lookup so translations apply.

**Music**  
The music to play during the text screen (entering/exiting messages). Accepts a SNDINFO logical music name, optionally followed by a track order (e.g., `D_VICTOR:2` or `D_VICTOR 2` for track 2 of a multi-track lump).

**Flat**  
The background flat to display during the text screen. Accepts a lump name (no length limit in modern engines); `pic` and `flat` write to the same underlying field and additionally set/modify the `CLUSTER_FINALEPIC` flag — if both are specified, both changes take effect in order (last name wins), but the flag set by `pic` persists.

**Pic**  
The background picture (sprite/graphic) to display during the text screen. Functionally equivalent to `flat` but sets the `CLUSTER_FINALEPIC` flag to interpret the lump as a full-sized picture instead of a repeating flat pattern; both write to the same name field. If `flat` is specified after `pic`, the name is replaced but the `CLUSTER_FINALEPIC` flag persists, causing the flat's name to be drawn as a picture.

**Hub**  
A flag (no value) marking this cluster as a hub. When set, Zandronum and UZDoom both retain the in-memory state of every level visited within the hub: actor positions, deaths, items collected, switches triggered. The wiki estimates approximately 20 KB per level is retained in memory; levels in non-hub clusters are discarded to save memory. Exiting a hub to a different cluster clears the saved state for that hub.

### GZDoom/UZDoom-family only (verified absent from Zandronum)

**AllowIntermission**  
A flag (no value) enabling intermission screens within a hub cluster. By default, UZDoom and GZDoom suppress intermissions when moving between levels in the same hub (unless `sv_alwaystally` is set to 2, which forces all intermissions on, or deathmatch mode); this flag overrides that suppression. Zandronum ignores this flag (no effect, intermissions are always suppressed in non-deathmatch mode when staying within the same hub).

**Intro**, **Outro**, **GameOver**  
Cutscene block definitions specifying animations to play at cluster-scope events (initial entry, cluster completion, or player death). Each block accepts:
- `Video = "<filename>"` — a video file (path and extension required, e.g., `"graphics/videos/intro.ivf"`; see Video format wiki page for supported formats).
- `Function = "<functionname>"` — a static ZScript function with no return type and a single `ScreenJobRunner` parameter (alternative to video; requires ZScript support).
- `Sound = "<soundname>"` — a logical sound name from SNDINFO (may be auto-resolved to OGG/FLAC/MP3/OPUS/WAV by the engine).
- `SoundID = <id>` — a numeric sound ID (default -1, meaning none).
- `FPS = <value>` — frame rate for ANM video playback.
- `Delete` — clears the video and function but leaves the cutscene block defined (will play nothing).
- `Clear` — completely resets the cutscene block to an empty state.

These cutscene blocks are a UZDoom/GZDoom-family feature with no equivalent in Zandronum's MAPINFO parser (the parser does not recognize these keywords).

### Present in both engines but absent from the wiki page

**Name**  
The cluster's display name, stored in `ClusterName` field (accepts a literal string, `lookup, "<keyword>"`, or `$<keyword>`). It is not referenced by `entertext`/`exittext`. In Zandronum, its only effect is on leaving a hub cluster: `G_LeavingHub()` substitutes it for the level name shown on the hub-total intermission. UZDoom does the same and also exposes it through `Level.GetClusterName()`. Bug in both engines: the parser sets the `CLUSTER_LOOKUPCLUSTERNAME` flag when a lookup is used, but the consumer code (`G_LeavingHub` in both engines, `Level.GetClusterName()` in UZDoom) checks the different `CLUSTER_LOOKUPNAME` flag (which nothing ever sets), so a lookup name is never translated — it is displayed as the raw keyword string instead of the translated text. The wiki page does not document this property.

**CdTrack**, **CdId**  
CD audio track selection (legacy feature from 1990s Doom WAD conventions). `cdtrack` accepts a numeric track number; `cdid` accepts a hexadecimal ID. Both are parsed but not functionally used in modern engines. The wiki page does not mention these properties.

## Engine-family divergence

The ZDoom-family engines implement a larger set of properties than Zandronum. Specifically:
- **Zandronum only:** None (all Zandronum properties are shared with GZDoom-family engines).
- **GZDoom-family only:** `AllowIntermission`, `Intro`, `Outro`, `GameOver`.
- **Shared but wiki-incomplete:** `Name`, `CdTrack`, `CdId`, and implementation differences in `EnterText`/`ExitText` lookups (see properties section above).

Zandronum does not silently accept GZDoom-family properties. A bare flag such as `AllowIntermission` is skipped with a non-fatal "Unknown property" console message (`src/g_mapinfo.cpp:782`). A cutscene block (`Intro`/`Outro`/`GameOver { ... }`) breaks the parse fatally: Zandronum's `SkipToNext()` helper only consumes `= value, ...` patterns and does nothing for `{` blocks, so the block's opening `{` and contents remain in the token stream. The closing `}` from the cutscene block ends the cluster definition prematurely, and the remaining unparsed tokens (the block contents plus any remaining cluster properties) reach the top level, where the parser aborts startup with a fatal "Unknown top level keyword" script error (`src/g_mapinfo.cpp:1999`). Keep cutscene blocks out of any MAPINFO file a Zandronum build loads.

## Implementation notes

- **Hub state retention and memory:** The Zandronum and UZDoom engines both save hub-level state in a per-level data structure (visible in source as snapshot serialization, actor records, and switch state storage). The wiki's ~20 KB per-level estimate reflects typical snapshot sizes for average-complexity maps. Levels are restored when re-entered within the same hub.
- **Text screen display gates:** Both engines conditionally suppress cluster text screens (`EnterText`/`ExitText`) when moving between maps. Zandronum shows the screen only in single-player mode (`NETWORK_GetState() == NETSTATE_SINGLE`, `src/g_level.cpp:741`); UZDoom gates on a per-level flag (`LEVEL2_NOCLUSTERTEXT`, `src/g_level.cpp:789`). End-of-game text is not gated in this way.
- **Intermission screen suppression in hubs:** Both engines suppress the stats screen (intermission) by default when moving between levels in the same hub cluster to reduce visual clutter. UZDoom adds the `CLUSTER_ALLOWINTERMISSION` flag to override this (subject to `sv_alwaystally == 2` or deathmatch mode forcing all intermissions on); Zandronum lacks this flag and always suppresses intermissions within the same hub in non-deathmatch mode.
- **ExitTextIsLump and Hexen handling:** Both engines support `ExitTextIsLump` (and `EnterTextIsLump`, the latter not listed in the wiki) to interpret the message value as a lump name and print its contents directly. UZDoom adds a special-case handler (`src/gamedata/g_mapinfo.cpp:940-957`) that remaps HEXEN.WAD/HEXDD.WAD lump references in `ExitText` to the string table automatically, a behavior absent in Zandronum.

## Known gaps

The wiki extraction cleanly captured all documented cluster properties, but three properties in the actual engine implementations (`Name`, `CdTrack`, `CdId`) are missing from the wiki page's tables, suggesting the page may be incomplete or focused on commonly-used properties only.
