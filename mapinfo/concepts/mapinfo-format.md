# MAPINFO lump format

**Tier:** A
**Engine:** Zandronum 3.2.1 (primary); UZDoom 4.15pre for GZDoom-family blocks listed in divergence section below
**Provenance:** ZDoom Wiki `MAPINFO` (retrieved 2026-07-31, oldid=52570) + verified against the Zandronum source's `src/g_mapinfo.cpp` (`FMapInfoParser::ParseMapInfo`, `G_ParseMapInfo`) and the UZDoom source's `src/gamedata/g_mapinfo.cpp`.

## Overview

MAPINFO is a lump that defines map-level and engine-level configuration: map properties, episode structure, skill levels, intermission sequences, and automap colors. A WAD or PK3 can contain either a MAPINFO or ZMAPINFO lump; both use the same syntax, but ZMAPINFO forces the new format (see "Format variants" below).

## ZMAPINFO vs MAPINFO

Both lumps use identical parsing; the distinction is format enforcement:
- **MAPINFO**: format is auto-detected at parse time (old or new; see "Format variants" below).
- **ZMAPINFO**: format is forced to the new syntax; old-style (Hexen) MAPINFO syntax is not permitted.

**Per-WAD override rule:** If the same WAD contains both a MAPINFO and a ZMAPINFO lump, the MAPINFO is skipped entirely for that WAD (Zandronum source `src/g_mapinfo.cpp:2059-2067`). This allows a modder to write a MAPINFO for engines that don't support ZMAPINFO while providing ZMAPINFO-specific configuration to Zandronum/GZDoom-family ports that do.

## Format variants

The parser detects the format on first read (Zandronum source `src/g_mapinfo.cpp:462`):

- **New format:** Begins with a `{` character. Enables all block types listed below except the Hexen-era blocks. Sets C-mode parsing (no bare identifiers).
- **Old format (Hexen-style):** Does not begin with a `{`. A legacy format supporting only `map`, `episode`, `skill`, `clusterdef` (not `cluster`), and a limited property set per block. Parsed in non-C-mode to allow bare identifiers.

Once the format is determined, the entire MAPINFO/ZMAPINFO lump is locked into that format.

## Top-level block types

Block types available depend on format:

### New format (requires `{` syntax)
- `map <name>` — define or override a map's properties (e.g., `map E1M1 { ... }`). See the separate "MAPINFO_Map definition" page for property details.
- `defaultmap { ... }` — set default properties that apply to all subsequently-defined `map` blocks in this file.
- `adddefaultmap { ... }` — like `defaultmap`, but merges with existing defaults instead of replacing them.
- `cluster <number> { ... }` — define cluster properties (see separate "MAPINFO_Cluster definition" page). Zandronum enforces the format gate; old format uses `clusterdef` instead.
- `episode { ... }` — define or override an episode (see separate "MAPINFO_Episode definition" page).
- `skill <name> { ... }` — define or override a skill level (see separate "MAPINFO_Skill definition" page).
- `gameinfo { ... }` — configure engine-level properties like title screen, credit sequence, intermission defaults (see separate "MAPINFO_GameInfo definition" page). Unavailable in old format.
- `intermission <name> { ... }` — define a custom intermission sequence.
- `automap { ... }` — set automap color scheme; only applied if `am_customcolors` cvar is enabled. New format only.
- `automap_overlay { ... }` — like `automap`, but overlays settings on the default scheme instead of replacing it. New format only.

### Both formats
- `episode { ... }` (both formats support the same keyword; see "MAPINFO_Episode definition" page for property differences).
- `clearepisodes` — clear all previously-defined episodes. Requires that at least one episode be defined after this statement in the same file.
- `skill <name> { ... }` (both formats).
- `clearskills` — clear all previously-defined skills. Requires that at least one skill be defined after this statement in the same file.
- `clusterdef <number> { ... }` — old-format cluster syntax. See separate page. New format accepts `cluster` instead.

### Include statement
- `include <filename>` — load another MAPINFO file. Path is relative to the WAD/PK3 directory structure. Includes are resolved recursively and can themselves contain `include` statements.

### Zandronum-specific blocks
- `botepisode { ... }` — define a bot skill selection screen episode-like menu (for bot bot selection in multiplayer). Zandronum extension not found in GZDoom-family engines.
- `botskillname <name> "Title"` — define a custom bot skill menu title. Zandronum extension.
- `botskillpicname <name> "Picname"` — define a bot skill menu picture. Zandronum extension.
- Bot-related properties in `map` blocks: `nobotnodes` (flag), `islobby` (flag). Zandronum-specific.

## Engine-family divergence

### GZDoom-family only (not in Zandronum 3.2.1)

The following blocks exist in UZDoom/GZDoom but have no Zandronum implementation:

- `doomednums { ... }` — map editor thing numbers to actor classes. Replaces older external `DOOMEDNUMS` lump mechanism.
- `damagetype { ... }` — define custom damage types with associated properties.
- `spawnnums { ... }` — map spawn numbers to actor classes.
- `conversationids { ... }` — map conversation IDs to actor classes.

These are new-format-only and documented in the UZDoom/GZDoom MAPINFO reference, but **do not parse in Zandronum and should not be used in a Zandronum-compatible MAPINFO**. A modder targeting both engines should use separate MAPINFO/ZMAPINFO lumps, or conditionally use these only in ZMAPINFO where they won't be loaded by Zandronum.

## Syntax

Generic block structure:
```
<keyword> <name-or-number> {
	property = value1, value2, ...
	property_flag
	...
}
```

- Properties can take zero, one, or multiple values depending on the property (see per-block pages).
- If a property takes no parameters, the property name alone is sufficient (no `=`).
- String values must be quoted (e.g., `name = "E1M1: Entry Point"`).
- Numeric values are not quoted.
- Comments use `//` (to end of line) or `/* */` (block).

## See also

- "MAPINFO_Map definition" — individual map properties.
- "MAPINFO_GameInfo definition" — game configuration (title, music, credits, etc.).
- "MAPINFO_Cluster definition" — cluster properties (hub logic, intermission messages).
- "MAPINFO_Episode definition" — episode definitions and episode menu configuration.
