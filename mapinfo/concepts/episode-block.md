# Episode block definition

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `MAPINFO/Episode definition` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=MAPINFO%2FEpisode_definition&oldid=49575) + verified against the Zandronum source's `src/g_mapinfo.cpp` (`FMapInfoParser::ParseEpisodeInfo`, starting at line 1688; `clearepisodes` check at 2074-2077), `src/menu/menudef.cpp:1075-1150` (episode menu), `src/menu/menu.cpp:397-424` (bot episodes), `src/menu/listmenu.cpp:551-554` and `src/v_draw.cpp:343-347` (missing `picname` graphic draws nothing), `src/w_wad.cpp:111-119` (`uppercopy`) and the UZDoom source's `src/gamedata/g_mapinfo.cpp` (`FMapInfoParser::ParseEpisodeInfo`, starting at line 2311).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Overview

An `episode` block in MAPINFO defines a selectable episode (campaign start point) in the episode menu. If only one episode is defined, the player skips the episode selection menu and starts at that episode's map automatically.

## Syntax

```text
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
- The episode's display name in the episode selection menu. If `picname` is not specified, this name is rendered as text using the menu font. If the name starts with `$`, it is interpreted as a lookup key in the LANGUAGE lump (e.g., `name = "$M_EPISODE1"` looks up the text from LANGUAGE).

**`picname = "<lump_name>"`**
- The name of a graphic lump to display as the episode's icon/title on the episode selection menu. On UZDoom, per the wiki, an invalid lump shows the "invalid graphic" image. On Zandronum, a `picname` that names no existing graphic draws nothing: the entry is blank but still selectable, and `name` is not used as a fallback. If set to `""` (empty string), no graphic is shown; on Zandronum this is the same as omitting it. If omitted, the episode name from `name` is rendered as text using the menu font instead. On Zandronum, if the episode list is too tall to fit the list menu, an option menu is built instead and every entry shows its `name` text, ignoring `picname`. **Engine-specific:** UZDoom auto-synthesizes `name` as `$<lump_name>` if `name` is not specified (Zandronum does not).

**`key = "<key>"`**
- A single keyboard key as a shortcut for menu selection (e.g., `key = "k"` makes `K` or `k` select this episode). Only the first character is used; the shortcut is case-insensitive.

**`remove`**
- A flag (no value). Removes the episode with the given `<maplump>` from the episode list. Useful to suppress a default episode from the IWAD in a PWAD.

**`noskillmenu`**
- A flag (no value). Disables the skill selection menu for this episode. Instead, the episode starts at the skill marked with the `DefaultSkill` flag in the skill definitions, or at the median skill if no default is available. Useful for WADs that implement skill selection via an intro map.

**`optional`**
- A flag (no value). The episode is only added to the episode list if its starting map lump (`<maplump>`) actually exists in the loaded WAD/PK3 set. If the map lump is missing, the episode definition is skipped entirely and never appears in the menu. Used for bonus episodes (e.g., Doom's fourth episode in Ultimate Doom).

**`extended`**
- A flag (no value). The episode only appears if the IWAD is marked with the extended-version compatibility flag (set during IWAD detection via `Compatibility = Extended`). Used for Heretic's fourth and fifth episodes (Shadow of the Serpent Riders). Both engines check only the IWAD's compatibility flag. An `EXTENDED` lump in a PWAD does nothing; the stock IWADINFO entry for the extended Heretic IWAD lists `EXTENDED` among the lumps used to recognize that IWAD.

### Zandronum-specific

**`botepisode`**
- A flag (no value). Zandronum extension; absent from GZDoom-family engines. The episode is still listed in the normal episode menu like any other. Selecting it opens the bot skill menu (`BotSkillMenu` in MENUDEF) instead of the regular skill menu (`src/menu/menu.cpp:397-424`).

**`botskillname "<title>"`**
- Sets a text title (drawn in red with the big font) at the top of the bot skill menu opened from this episode. Syntax: `botskillname` followed by a string (no `=`). Only meaningful when `botepisode` is specified; without it the parser prints "'botskillname' used without 'botepisode' in the episode definition. It will be ignored." Zandronum extension.

**`botskillpicname "<lump_name>"`**
- Sets a graphic lump drawn as the title at the top of the bot skill menu opened from this episode. Syntax: `botskillpicname` followed by a string (no `=`). Only meaningful when `botepisode` is specified; without it the parser prints the same "used without 'botepisode'" warning. Note: `botskillname` and `botskillpicname` are mutually exclusive; the last one specified is used. Zandronum extension.

### UZDoom/GZDoom-family only (NOT in Zandronum 3.2.1)

**`intro { ... }`**
- Defines an introduction cutscene to play when the episode starts (UZDoom/GZDoom-family only; Zandronum has no equivalent). The `intro` block supports the following sub-properties:
  - `video = "<filepath>"` — the full path and filename of a video file to play (e.g., `video = "graphics/videos/intro.ivf"`). See the ZDoom Wiki's "Video format" page for supported formats.
  - `function = "<functionname>"` — the name of a static ZScript function with no return type and a single `ScreenJobRunner` parameter. The function is called to run the cutscene instead of a video.
  - `sound = "<soundname>"` — the logical sound name to play during the cutscene (from the SNDINFO lump). By default, GZDoom will search for an OGG, FLAC, MP3, OPUS, or WAV file with the same name in the same directory as the video (fallback behavior).
  - `soundid = <id>` — a resource ID (not an SNDINFO sound name) to play during the cutscene. Defaults to `-1` (no sound). Alternative to `sound`.
  - `fps = <value>` — playback framerate for ANM videos. Only applies to ANM format; has no effect on other video types.
  - `delete` — clears the video and function from the intro, leaving the intro defined but with no media to play.
  - `clear` — clears the entire intro definition.

**Engine-family divergence:** The `intro` block and all its sub-properties exist only in UZDoom/GZDoom-family engines. Zandronum does not parse or support intro cutscenes for episodes. A MAPINFO/ZMAPINFO targeting both engines should omit the `intro` block or conditionally include it only when `ZMAPINFO` syntax is required (which Zandronum will skip entirely).

## Engine-family divergence: name and map-lump parsing

**Episode name escape sequences (UZDoom only):** UZDoom applies escape-sequence processing to the `name` property, allowing sequences like `\c` to embed text-color control codes. Zandronum stores the `name` literally, preserving any backslashes as written. A `name` value like `"Episode \cq1"` will render with color codes in UZDoom but as literal text `"Episode \cq1"` in Zandronum.

**Episode lump-name handling:** Zandronum truncates the `<maplump>` positional argument of an `episode` block to 8 characters at parse time and converts it to uppercase (e.g., `episode MyLevelMap {...}` becomes `MYLEVELM`). UZDoom preserves the full lump name as specified and matches it case-insensitively at runtime. For map lumps longer than 8 characters, only Zandronum's truncation applies; both engines perform case-insensitive matching on the truncated/full name.

## Engine-family divergence: skill selection and localization

**Default skill selection precedence:** UZDoom checks skill selection in this order: (1) `LastSkill` — the skill the player selected in a previous game; (2) `DefaultSkill` — a skill marked with the `DefaultSkill` flag in its definition; (3) the median skill if neither is set. Zandronum skips the `LastSkill` step entirely, checking only `DefaultSkill` with median fallback. In both engines, `noskillmenu` triggers the default/median skill to be used automatically without showing the skill menu.

**Episode name localization in UZDoom:** When an episode's `name` is a localizable string (starts with `$`), UZDoom prefers rendering it as text over displaying the `picname` graphic if the graphic is not valid for the current language. Zandronum does not have this preference — it displays the `picname` graphic if one is specified, regardless of whether the name is localizable.

### Wiki-referenced but unsupported in both engines

**`lookup = "<keyword>"`**
- A property mentioned in the ZDoom Wiki (as an alternative to `name` for specifying the episode's display name via LANGUAGE lump lookup). **Neither Zandronum nor UZDoom support this property.** Both engines print "Unknown property 'lookup' found in episode definition" and skip it; this is not fatal. Modern UZDoom uses the `$`-prefixed form in the `name` property instead (e.g., `name = "$EPISODE1_NAME"`). Avoid using `lookup` in new MODs.

## Warptrans reference

A special map reference `&wt@<number>` allows starting an episode at a map identified by its warptrans number (a per-WAD map alias) rather than by lump name. Both Zandronum and UZDoom support this. Example:

```text
episode "&wt@01" {
    name = "My cool episode"
    key = "m"
}
```

This starts the episode at the map with `warptrans 1` as defined in MAPINFO. At episode start time, the engine looks up the warptrans number in the loaded level list via `CheckWarpTransMap` (Zandronum source `src/g_mapinfo.cpp:157–176`). This is uncommon in PWADs. Both engines always run this lookup in substitute mode at episode start (Zandronum `src/g_level.cpp:179`), so if the warptrans number doesn't exist the engine falls back to `MAP` followed by the two characters after `@` (e.g., `MAP01` for `&wt@01`).

## Clear episodes

Use the `clearepisodes` keyword (outside any block) to remove all previously-defined episodes. At least one episode must exist once every MAPINFO/ZMAPINFO lump has been parsed, so a later lump may supply it. If none does (including when every episode was dropped with `remove`), startup aborts with the fatal error "You cannot use clearepisodes in a MAPINFO if you do not define any new episodes after it." (Zandronum `src/g_mapinfo.cpp:2074-2077`):

```text
clearepisodes
episode e1m1 { ... }
```

## Examples

### Simple episode

```text
episode e1m1 {
    picname = "M_EPI1"
    key = "1"
}
```

### Optional episode (appears only if map exists)

```text
episode e4m1 {
    name = "Episode 4"
    picname = "M_EPI4"
    optional
}
```

### Episode with intro cutscene (UZDoom/GZDoom only)

```text
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
