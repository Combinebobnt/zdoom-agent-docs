# Episode block definition

**Tier:** B
**Engine:** Zandronum 3.2.1 (primary); UZDoom 4.15pre for `intro` property (source-verified for property existence only; sub-properties sourced from wiki)
**Provenance:** ZDoom Wiki `MAPINFO/Episode definition` (retrieved 2026-08-01, oldid=49575) + verified against the Zandronum source's `src/g_mapinfo.cpp` (`FMapInfoParser::ParseEpisodeInfo`, starting at line 1688) and the UZDoom source's `src/gamedata/g_mapinfo.cpp` (`FMapInfoParser::ParseEpisodeInfo`, starting at line 2311).

## Overview

An `episode` block in MAPINFO defines a selectable episode (campaign start point) in the episode menu. If only one episode is defined, the player skips the episode selection menu and starts at that episode's map automatically.

## Syntax

```
episode <maplump> [teaser <maplump>] {
    property = value
    property
    ...
}
```

- `<maplump>`: the map lump (e.g., `E1M1`) where the episode starts. Can be any valid map lump name, or `&wt@<number>` to reference a map by its warptrans number (see "Warptrans reference" section below).
- `teaser <maplump>` (optional): an alternate map lump used if the shareware flag is set in `gameinfo` (Hexen-style campaigns may use this to switch between demo and full-version start maps). Both engines check the `GI_SHAREWARE` flag; if set, `teaser` is used instead of the main `<maplump>`.

## Properties

### Common (both Zandronum and UZDoom)

**`name = "<episode_name>"`**
- The episode's display name in the episode selection menu. If `picname` is not specified, this name is converted to a graphic and used instead. If the name starts with `$`, it is interpreted as a lookup key in the LANGUAGE lump (e.g., `name = "$M_EPISODE1"` looks up the text from LANGUAGE).

**`picname = "<lump_name>"`**
- The name of a graphic lump to display as the episode's icon/title on the episode selection menu. If an invalid lump is specified, the "invalid graphic" image is used. If set to `""` (empty string), no graphic is shown. If omitted, the name from `name` is converted into a graphic and used instead. **Engine-specific:** UZDoom auto-synthesizes `name` as `$<lump_name>` if `name` is not specified (Zandronum does not).

**`key = "<key>"`**
- A single keyboard key as a shortcut for menu selection (e.g., `key = "k"` makes `K` select this episode). Only the first character is used.

**`remove`**
- A flag (no value). Removes the episode with the given `<maplump>` from the episode list. Useful to suppress a default episode from the IWAD in a PWAD.

**`noskillmenu`**
- A flag (no value). Disables the skill selection menu for this episode. Instead, the episode starts at the skill marked with the `DefaultSkill` flag in the skill definitions, or at the median skill if no default is available. Useful for WADs that implement skill selection via an intro map.

**`optional`**
- A flag (no value). The episode only appears in the menu if its starting map lump (`<maplump>`) actually exists in the loaded WAD/PK3 set. Used for bonus episodes (e.g., Doom's fourth episode in Ultimate Doom).

**`extended`**
- A flag (no value). The episode only appears if an `EXTENDED` lump is present in a loaded WAD. Used for Heretic's fourth and fifth episodes (Shadow of the Serpent Riders).

### Zandronum-specific

**`botepisode`**
- A flag (no value). Marks this episode definition as part of the bot skill selection screen. Zandronum extension; absent from GZDoom-family engines. When `botepisode` is set, the episode is added to the bot skill menu instead of the standard episode menu. Note: the actual behavior of bot episodes is not fully documented in engine source comments.

**`botskillname "<title>"`**
- Sets the title text for this bot episode in the bot skill menu. Syntax: `botskillname` followed by a string (no `=`). Only meaningful when `botepisode` is specified. Zandronum extension.

**`botskillpicname "<lump_name>"`**
- Sets a graphic lump to display as the bot episode's icon in the bot skill menu. Syntax: `botskillpicname` followed by a string (no `=`). Only meaningful when `botepisode` is specified. Note: `botskillname` and `botskillpicname` are mutually exclusive; the last one specified is used. Zandronum extension.

### UZDoom/GZDoom-family only (NOT in Zandronum 3.2.1)

**`intro { ... }`**
- Defines an introduction cutscene to play when the episode starts (UZDoom/GZDoom-family only; Zandronum has no equivalent). The `intro` block supports the following sub-properties (from ZDoom Wiki, source-verification incomplete):
  - `video = "<filepath>"` — the full path and filename of a video file to play (e.g., `video = "graphics/videos/intro.ivf"`). See the ZDoom Wiki's "Video format" page for supported formats.
  - `function = "<functionname>"` — the name of a static ZScript function with no return type and a single `ScreenJobRunner` parameter. The function is called to run the cutscene instead of a video.
  - `sound = "<soundname>"` — the logical sound name to play during the cutscene (from the SNDINFO lump). By default, GZDoom will search for an OGG, FLAC, MP3, OPUS, or WAV file with the same name in the same directory as the video (fallback behavior).
  - `soundid = <id>` — the numeric ID of a sound to play (alternative to `sound`). Semantics partially unverified; wiki indicates default is `-1` but context unclear.
  - `fps = <value>` — playback framerate for ANM videos. Only applies to ANM format.
  - `delete` — clears the video and function from the intro, leaving the intro defined but with no media to play.
  - `clear` — clears the entire intro definition.

**Engine-family divergence:** The `intro` block and all its sub-properties exist only in UZDoom/GZDoom-family engines. Zandronum does not parse or support intro cutscenes for episodes. A MAPINFO/ZMAPINFO targeting both engines should omit the `intro` block or conditionally include it only when `ZMAPINFO` syntax is required (which Zandronum will skip entirely).

### Wiki-referenced but unsupported in both engines

**`lookup = "<keyword>"`**
- A property mentioned in the ZDoom Wiki (as an alternative to `name` for specifying the episode's display name via LANGUAGE lump lookup). **Neither Zandronum nor UZDoom support this property.** Both engines parse the `episode` block and reject `lookup` as an unknown property. Modern UZDoom uses the `$`-prefixed form in the `name` property instead (e.g., `name = "$EPISODE1_NAME"`). Avoid using `lookup` in new MODs.

## Warptrans reference

A special map reference `&wt@<number>` allows starting an episode at a map identified by its warptrans number (a per-WAD map alias) rather than by lump name. Both Zandronum and UZDoom support this. Example:

```
episode "&wt@01" {
    name = "My cool episode"
    key = "m"
}
```

This starts the episode at the map with `warptrans 1` as defined in MAPINFO. At episode start time, the engine looks up the warptrans number in the loaded level list via `CheckWarpTransMap` (Zandronum source `src/g_mapinfo.cpp:157–176`). This is uncommon in PWADs. If the warptrans number doesn't exist and `substitute` mode is enabled, the engine falls back to `MAP<number>` (e.g., `MAP01` for `&wt@01`).

## Clear episodes

Use the `clearepisodes` keyword (outside any block) to remove all previously-defined episodes. Any use of `clearepisodes` must be followed by at least one episode definition in the same MAPINFO lump:

```
clearepisodes
episode e1m1 { ... }
```

## Examples

### Simple episode

```
episode e1m1 {
    picname = "M_EPI1"
    key = "1"
}
```

### Optional episode (appears only if map exists)

```
episode e4m1 {
    name = "Episode 4"
    picname = "M_EPI4"
    optional
}
```

### Episode with intro cutscene (UZDoom/GZDoom only)

```
episode e1m1 {
    name = "Episode 1: Entryway"
    picname = "M_EPI1"
    intro {
        video = "graphics/videos/e1intro.webm"
        sound = "e1_intro_music"
    }
}
```

## See also

- `clearepisodes` statement in `MAPINFO lump format` concept
- Related blocks: `clusterdef`/`cluster`, `skill`, `gameinfo`
