# SNDINFO doc index

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse SNDINFO.** UZDoom accepts 31 `$`-commands, Zandronum 25; the six extras
(`$include`, `$modplayer`, `$pitchset`, `$replaygain`, `$rumble`, `$rumbledef`) are UZDoom-only.
Commands are documented in grouped concept pages, not one file each: use the table below to find
a command.

## Concepts

- [The SNDINFO lump](concepts/sndinfo-lump.md) — tier A. Every SNDINFO lump in load order,
  parsed before MAPINFO; `logicalname lump` mappings, later wins; full-path-then-8-char lump
  lookup; `$ifdoom`-style blocks (no nesting, `$endif` outside the table); UZDoom's `$include`
  and `name = lump` form; per-map SNDINFO reload; the complete per-engine command table; unknown
  `$`-commands are dropped silently and their arguments become mappings.
- [Ambient sounds](concepts/ambient-sounds.md) — tier B. `$ambient` index, positioning
  (`world`/`point`/`surround`) and timing (`continuous`/`random`/`periodic`); the `AmbientSound`
  thing (14065, 14067, and 14001 to 14064 with preset slot), its five arguments, activation and
  self-destruction on an undefined slot.
- [Random, alias, player and pitch commands](concepts/random-and-player-sounds.md) — tier B.
  `$random`/`$alias` resolution and which name each playback property is read from; `$singular`
  failing through an alias; the `$playersound` family, sound classes, per-engine gender words and
  the male/default-class fallback; `$pitchshift`/`$pitchshiftrange`/`$pitchset` and `snd_pitched`.
- [Limits, volume, attenuation, rolloff, rumble](concepts/sound-limits-and-rolloff.md) — tier B.
  `$limit` default of 2 within 256 units; `$volume` capped product; `$attenuation` as a distance
  multiplier; the four `$rolloff` curves and `$rolloff *`; UZDoom's controller rumble commands
  and their stored strength order.
- [Music commands and no-op commands](concepts/music-aliases.md) — tier B. `$musicalias`
  (including `None`, and "a later file's own music wins"); `$musicvolume`, `$mididevice`,
  `$modplayer` keyed by lump on UZDoom and by name on Zandronum; Hexen `$map`; the accepted
  no-op commands, including UZDoom's handler-less `$replaygain`.

## Which page covers which `$`-command

| Command | UZDoom | Zandronum | Page |
|---|---|---|---|
| `$include` | yes | no | [lump](concepts/sndinfo-lump.md) |
| `$ifdoom`, `$ifheretic`, `$ifhexen`, `$ifstrife`, `$endif` | yes | yes | [lump](concepts/sndinfo-lump.md) |
| `$ambient` | yes | yes | [ambient](concepts/ambient-sounds.md) |
| `$random`, `$alias`, `$singular` | yes | yes | [random and player](concepts/random-and-player-sounds.md) |
| `$playersound`, `$playersounddup`, `$playercompat`, `$playeralias` | yes | yes | [random and player](concepts/random-and-player-sounds.md) |
| `$pitchshift`, `$pitchshiftrange` | yes | yes | [random and player](concepts/random-and-player-sounds.md) |
| `$pitchset` | yes | no | [random and player](concepts/random-and-player-sounds.md) |
| `$limit`, `$volume`, `$attenuation`, `$rolloff` | yes | yes | [limits and rolloff](concepts/sound-limits-and-rolloff.md) |
| `$rumbledef`, `$rumble` | yes | no | [limits and rolloff](concepts/sound-limits-and-rolloff.md) |
| `$musicalias`, `$musicvolume`, `$mididevice`, `$map` | yes | yes | [music](concepts/music-aliases.md) |
| `$modplayer` | yes | no | [music](concepts/music-aliases.md) |
| `$replaygain` | accepted, no effect | no | [music](concepts/music-aliases.md) |
| `$registered`, `$archivepath`, `$edfoverride` | accepted, no effect | accepted, no effect | [music](concepts/music-aliases.md) |
