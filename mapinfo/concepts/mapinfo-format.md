# MAPINFO lump format

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `MAPINFO` (retrieved 2026-09-28, https://zdoom.org/w/index.php?title=MAPINFO&oldid=52570) + verified against the Zandronum source's `src/g_mapinfo.cpp` (`FMapInfoParser::ParseMapInfo`, `G_ParseMapInfo`, `FMapInfoParser::ParseOpenBrace`, `FMapInfoParser::ParseEpisodeInfo`, lines 2053-2072 for ZMAPINFO override behavior) and `src/sc_man_scanner.re` (comment handling per scanner mode), and the UZDoom source's `src/gamedata/g_mapinfo.cpp` (G_ParseMapInfo lines 2764-2798 for MAPINFO/ZMAPINFO/UMAPINFO precedence).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Overview

MAPINFO is a lump that defines map-level and engine-level configuration: map properties, episode structure, skill levels, intermission sequences, and automap colors. A WAD or PK3 can contain MAPINFO and/or ZMAPINFO lumps; both use the same syntax, but ZMAPINFO forces the new format (see "Format variants" below). UZDoom additionally supports UMAPINFO, a community-created format; see "Engine-family divergence" below for precedence rules across all three lump types.

## ZMAPINFO vs MAPINFO

Both lumps use identical parsing; the distinction is format enforcement:
- **MAPINFO**: format is auto-detected at parse time (old or new; see "Format variants" below).
- **ZMAPINFO**: format is forced to the new syntax; old-style (Hexen) MAPINFO syntax is not permitted.

**Per-WAD override rule:** When multiple MAPINFO-style lumps exist in the same WAD, a MAPINFO or ZMAPINFO suppresses any UMAPINFO in the same WAD regardless of order (UZDoom only, `src/gamedata/g_mapinfo.cpp:2764-2798`), and ZMAPINFO suppresses any MAPINFO in the same WAD. In Zandronum (which lacks UMAPINFO), if a WAD contains both MAPINFO and ZMAPINFO, the MAPINFO is skipped entirely (source `src/g_mapinfo.cpp:2059-2067`).

## Format variants

The parser detects format at the first brace-bearing construct (Zandronum source `src/g_mapinfo.cpp:462`):

- **New format:** Begins with a `{` character. Enables every block type listed below; the old-format `clusterdef` keyword is still accepted too. Switches the scanner to C-mode, which also splits punctuation such as `,`, `(` and `;` into separate tokens (the Hexen scanner only splits `{`, `}`, `|` and `=`) and stops treating `;` as a comment. Can be inferred from the first block itself if it starts with `{`.
- **Old format (Hexen-style):** Does not begin with a `{`. A legacy format without the new-format-only blocks (see "Top-level block types" below) and with a limited property set per block. Stays on the classic Hexen scanner, which accepts `//`, `/* */` and `;` comments (`src/sc_man_scanner.re:237-241`). Only `specialaction` switches to C-mode temporarily while it reads its arguments.

Once the format is determined by the first `{`, it governs the entire lump. Additionally, certain new-format-only block types (`gameinfo`, `intermission`, `automap`, `automap_overlay`) can promote an indeterminate format to new format when encountered.

## Top-level block types

Block types available depend on format:

### New format only
These are rejected with a script error once the lump has been detected as old format. Encountering `gameinfo`, `intermission`, `automap` or `automap_overlay` while the format is still undetermined promotes the lump to new format; `cluster` does not promote it.
- `cluster <number> { ... }` — define cluster properties (see separate "MAPINFO_Cluster definition" page). Old format uses `clusterdef` instead.
- `gameinfo { ... }` — configure engine-level properties like title screen, credit sequence, intermission defaults (see separate "MAPINFO_GameInfo definition" page).
- `intermission <name> { ... }` — define a custom intermission sequence. See [intermission-block.md](intermission-block.md).
- `automap { ... }` — set automap color scheme; only applied if `am_customcolors` cvar is enabled. See [automap-block.md](automap-block.md).
- `automap_overlay { ... }` — same keys as `automap`, but sets the separate colorset used when the automap is shown as an overlay on the game view.

### Both formats
In the new format the blocks here that take properties are brace-delimited; in the old format a block ends at the first word that isn't one of its properties, normally the next top-level keyword.
- `map <name>` — define or override a map's properties (e.g., `map E1M1 { ... }`). See the separate "MAPINFO_Map definition" page for property details.
- `defaultmap { ... }` — set default properties that apply to all subsequently-defined `map` blocks in this file.
- `adddefaultmap { ... }` — like `defaultmap`, but merges with existing defaults instead of replacing them.
- `episode <map> { ... }` — define or override an episode (see "MAPINFO_Episode definition" page for property differences).
- `clearepisodes` — clear all previously-defined episodes. If used, at least one episode must be defined somewhere across all loaded MAPINFO lumps afterward.
- `skill <name> { ... }` — define or override a skill level (see separate "MAPINFO_Skill definition" page).
- `clearskills` — clear all previously-defined skills. If used, at least one skill must be defined somewhere across all loaded MAPINFO lumps afterward.
- `clusterdef <number> { ... }` — old-format cluster syntax, still accepted in the new format alongside `cluster`. See separate page.

### Include statement
- `include <filename>` — load another MAPINFO file. Path is relative to the WAD/PK3 directory structure. Includes are resolved recursively and can themselves contain `include` statements.

### Zandronum-specific episode and map properties
These are not top-level blocks. The three bot properties go inside an `episode` block (`FMapInfoParser::ParseEpisodeInfo`, `src/g_mapinfo.cpp:1759-1774`) and are not found in GZDoom-family engines.
- `botepisode`: bare flag marking the episode as one that shows the bot skill selection menu.
- `botskillname "Title"`: text title for that bot skill menu. Takes one string with no `=`.
- `botskillpicname "Picname"`: graphic title for that menu instead of text. Takes one string with no `=`; whichever of the two comes last wins.
- Either title property in an episode without `botepisode` is ignored with a script message (`src/g_mapinfo.cpp:1834-1835`).
- Bot-related properties in `map` blocks: `islobby` (flag, alias `lobby`) is Zandronum-specific. `nobotnodes` exists in both engines but is only functional in Zandronum; UZDoom accepts and ignores it.

## Engine-family divergence

### UZDoom-specific lump types

UZDoom supports a third lump type, **UMAPINFO**, alongside MAPINFO and ZMAPINFO. UMAPINFO is a community-authored format with its own syntax; its key difference is that MAPINFO and ZMAPINFO in the same WAD take precedence over it. UMAPINFO lumps are collected and only committed when the next regular MAPINFO/ZMAPINFO lump is reached (or at the end), so they are applied on top of the base settings as they stood at that point.

### GZDoom-family only (not in Zandronum)

The following blocks exist in UZDoom/GZDoom but have no Zandronum implementation:

- `doomednums { ... }` — map editor thing numbers to actor classes. See [doomednums-block.md](doomednums-block.md).
- `damagetype { ... }` — define custom damage types with associated properties. See [damagetype-block.md](damagetype-block.md).
- `spawnnums { ... }` — map spawn numbers to actor classes. See [spawnnums-block.md](spawnnums-block.md).
- `conversationids { ... }` — map conversation IDs to actor classes. See [conversationids-block.md](conversationids-block.md).

These are new-format-only and documented in the UZDoom/GZDoom MAPINFO reference, but **do not parse in Zandronum and should not be used in a Zandronum-compatible MAPINFO**. Zandronum reads ZMAPINFO too (and prefers it over a MAPINFO in the same WAD, `src/g_mapinfo.cpp:2053-2069`), so moving these blocks into ZMAPINFO does not hide them from Zandronum. A modder targeting both engines should keep them out of every MAPINFO/ZMAPINFO lump that Zandronum loads (for example in a separate PWAD that is only loaded on UZDoom), or use the actor-level equivalents where one exists (DECORATE `damagetype`, and the `SpawnID`/`ConversationID` properties and editor number in the actor header).

### Per-lump defaults behavior

Each MAPINFO lump in a load order begins with a fresh copy of the current engine defaults when parsed. The `defaultmap` and `adddefaultmap` directives within a lump set that lump's own default properties for subsequently-defined `map` blocks within that same lump, but do not carry forward to the next lump. This allows separate WADs to define independent sets of maps without interfering with each other's map defaults.

## Syntax

Generic block structure:
```text
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
- Comments use `//` (to end of line) or `/* */` (block). Old-format lumps also accept `;` to end of line (see "Format variants").

## See also

- "MAPINFO_Map definition" — individual map properties.
- "MAPINFO_GameInfo definition" — game configuration (title, music, credits, etc.).
- "MAPINFO_Cluster definition" — cluster properties (hub logic, intermission messages).
- "MAPINFO_Episode definition" — episode definitions and episode menu configuration.
