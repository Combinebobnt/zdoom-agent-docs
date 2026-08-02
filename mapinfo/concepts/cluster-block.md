# Cluster block definition

**Tier:** A
**Engine:** Zandronum 3.2.1 / UZDoom 4.15pre
**Provenance:** ZDoom Wiki `MAPINFO/Cluster_definition` (retrieved 2026-08-01, oldid=49574) + verified against Zandronum source (`src/g_mapinfo.cpp:702-791`, `src/g_level.cpp`) and UZDoom source (`src/gamedata/g_mapinfo.cpp:829-972`, `src/g_level.cpp`).

A cluster is a logical grouping of maps that can optionally display transition messages and/or form a hub with shared state. The cluster block in MAPINFO defines cluster-wide settings: intermission messages, music, graphics, hub behavior, and cutscene blocks.

## Block syntax

```
cluster <number> { properties }
```

`<number>` is the cluster identifier (a positive integer; cluster 0 is reserved internally to mean "no cluster" and should be avoided). Properties are whitespace-separated key-value pairs, most accepting a single value or a type-specific set of values.

## Properties

### Common to both Zandronum and GZDoom-family engines

**EnterText**, **ExitText**  
Transition messages displayed when entering or leaving the cluster. Both accept either a literal string (quoted, newlines via comma-separated quoted lines) or `lookup, "<keyword>"` to reference a string in the LANGUAGE lump. If the next level's cluster has an `EnterText`, it suppresses the current cluster's `ExitText`. Zandronum and UZDoom parse these identically; UZDoom adds a silent fallback that treats a string matching the default label `CLUSTERENTER<N>` or `CLUSTEREXIT<N>` as a lookup even without the `lookup` keyword.

**Music**  
The music to play during intermission sequences (entering/exiting messages). References a SNDINFO logical music name or a `$<constant>` reference to a language string.

**Flat**  
The background flat to display during intermission messages. Accepts a lump name up to 8 characters; `pic` and `flat` write the same underlying field — if both are present, `pic` takes effect and additionally sets a flag to interpret the lump as a sprite/picture rather than a repeating flat pattern.

**Pic**  
The background picture (sprite/graphic) to display during intermission messages. Functionally equivalent to `flat` but sets the interpretation flag; both use the same field, so specifying both results in the latter overwriting the former.

**Hub**  
A flag (no value) marking this cluster as a hub. When set, Zandronum and UZDoom both retain the in-memory state of every level visited within the hub: actor positions, deaths, items collected, switches triggered. Approximately 20 KB per level is retained in memory; levels in non-hub clusters are discarded to save memory. Exiting a hub to a different cluster clears the saved state for that hub.

### GZDoom/UZDoom-family only (verified absent from Zandronum)

**AllowIntermission**  
A flag (no value) enabling intermission screens within a hub cluster. By default, UZDoom and GZDoom suppress intermissions when moving between levels in the same hub to reduce visual clutter; this flag overrides that behavior. Zandronum ignores this flag (no effect).

**Intro**, **Outro**, **GameOver**  
Cutscene block definitions specifying animations to play at cluster-scope events (initial entry, cluster completion, or player death). Each block accepts:
- `Video = "<filename>"` — a video file (path and extension required, e.g., `"graphics/videos/intro.ivf"`; see Video format wiki page for supported formats).
- `Function = "<functionname>"` — a static ZScript function with no return type and a single `ScreenJobRunner` parameter (alternative to video).
- `Sound = "<soundname>"` — a logical sound name from SNDINFO (may be auto-resolved to OGG/FLAC/MP3/OPUS/WAV by the engine).
- `SoundID = <id>` — a numeric sound ID (default -1, meaning none).
- `FPS = <value>` — frame rate for ANM video playback.
- `Delete` — removes a previously-defined cutscene.
- `Clear` — resets a cutscene block entirely.

These cutscene blocks are a UZDoom/GZDoom-family feature requiring ZScript support and do not exist in Zandronum.

### Present in both engines but absent from the wiki page

**Name**  
An alternate identifier for the cluster, accepted as a `lookup` reference in `entertext`/`exittext`; parsed into `ClusterName` and sets `CLUSTER_LOOKUPCLUSTERNAME` flag if a lookup reference is used. The wiki page does not document this property.

**CdTrack**, **CdId**  
CD audio track selection (legacy feature from 1990s Doom WAD conventions). `cdtrack` accepts a numeric track number; `cdid` accepts a hexadecimal ID. Both are parsed but their runtime behavior depends on emulation of actual CD audio hardware, which is not relevant to modern engines. The wiki page does not mention these properties.

## Engine-family divergence

The ZDoom-family engines implement a larger set of properties than Zandronum. Specifically:
- **Zandronum only:** None (all Zandronum properties are shared with GZDoom-family engines).
- **GZDoom-family only:** `AllowIntermission`, `Intro`, `Outro`, `GameOver`.
- **Shared but wiki-incomplete:** `Name`, `CdTrack`, `CdId`, and implementation differences in `EnterText`/`ExitText` lookups (see properties section above).

Zandronum projects may include GZDoom-family properties in a MAPINFO source file, but they are silently ignored at runtime — no parse error results.

## Implementation notes

- **Hub state retention and memory:** The Zandronum and UZDoom engines both save hub-level state in a per-level data structure; the wiki's ~20 KB per-level estimate is verified against source patterns (actor state dumps, trigger tables, item records). Levels are restored when re-entered within the same hub.
- **Message suppression in hubs:** UZDoom's `CLUSTER_ALLOWINTERMISSION` flag prevents a counter-intuitive loss of intermission screens in hubs; the default (flag unset) hides intermissions when moving within the same hub cluster. Zandronum lacks this flag entirely and does not adjust intermission visibility based on hub status.
- **ExitTextIsLump and Hexen handling:** Both engines support `ExitTextIsLump` (and `EnterTextIsLump`, the latter not listed in the wiki) to interpret the message value as a lump name and print its contents directly. UZDoom adds a special-case handler that remaps HEXEN.WAD/HEXDD.WAD lump references to the string table automatically, a behavior absent in Zandronum.

## Known gaps

The wiki extraction cleanly captured all documented cluster properties, but three properties in the actual engine implementations (`Name`, `CdTrack`, `CdId`) are missing from the wiki page's tables, suggesting the page may be incomplete or focused on commonly-used properties only.
