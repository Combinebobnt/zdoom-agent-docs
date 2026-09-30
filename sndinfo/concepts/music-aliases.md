# Music commands and the no-op commands

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/sound/s_advsound.cpp` (the `SI_MusicAlias`,
`SI_MusicVolume`, `SI_MidiDevice`, `SI_ModPlayer`, `SI_Map`, `SI_Registered`, `SI_ArchivePath`
and `SI_EDFOverride` cases, and the `SICommandStrings[]` entry for `$replaygain`),
`src/sound/s_doomsound.cpp` (`LookupMusic`, `FindMusic`), `src/common/audio/music/music.cpp`
and `src/gamedata/g_mapinfo.cpp`, and the Zandronum source's `src/s_advsound.cpp`,
`src/s_sound.cpp` (`S_ChangeMusic`), `src/s_sound.h`, `src/w_wad.cpp` and
`src/g_mapinfo.cpp`; SLADE `dist/res/config/languages/zdoom.txt` (`z_sndinfo`) checked for its
keyword list.

SNDINFO's music commands act on music names (what MAPINFO's `music` key, `SetMusic`, `changemus`
and the engine's own title/intermission code ask for), not on logical sound names. This page also
covers the commands that are accepted but do nothing, so every `$`-command has a home; the full
list is on [the SNDINFO lump](sndinfo-lump.md) page.

## `$musicalias`

```text
$musicalias <music name> <replacement>
```

```text
$musicalias D_RUNNIN MYSONG01
$musicalias D_E1M1   None
```

- Whenever anything asks to play `<music name>`, `<replacement>` plays instead. The match is on
  the whole name, case-insensitive, and only one level deep: an alias whose replacement is itself
  aliased is not followed further.
- **`None` as the replacement silences that song.** The play request succeeds and nothing plays;
  see [`SetMusic`](../../acs/functions/setmusic.md) for how that looks from a script.
- **The alias is only stored if `<replacement>` exists as music** at parse time (or is `None`);
  otherwise the line is dropped without a message.
- **A later file's own music wins.** If a music lump named `<music name>` is loaded from a file
  after the one holding this SNDINFO, the alias is skipped, so a mod loaded later that ships its
  own `D_RUNNIN` is not overridden by an earlier mod's alias.

## `$musicvolume`

```text
$musicvolume <music name> <volume>
```

Sets a per-song relative volume, applied on top of the music volume setting. The last entry for
a song wins. The accepted forms and the keying differ per engine (see divergence).

## `$mididevice`

```text
$mididevice <music name> <device>
```

Chooses the MIDI synthesizer for one song, overriding the `snd_mididevice` cvar for that song only
(see [`snd_mididevice`](../../console/notes/snd_mididevice.md) and
[`timidity_mastervolume`](../../console/notes/timidity_mastervolume.md)). Device words on both
engines: `default`, `standard` (the operating system's MIDI output), `opl`, `fmod`, `timidity`,
`fluidsynth`, `gus`. An unknown word is a fatal error. UZDoom adds more (see divergence).

## `$modplayer` (UZDoom only)

```text
$modplayer <music name> xmp|libxmp|dumb|libdumb
```

Chooses the tracker-module player for one song, overriding the `mod_preferred_player` setting
(UZDoom `s_advsound.cpp:1239-1259`). An unknown player name is a fatal error; an unknown song is
ignored.

## `$map`

```text
$map <level number> <music name>
```

Hexen-style default music by level number. It is applied when MAPINFO parses the header of the
map whose level number matches (for `MAPxx` names, xx), so it only affects maps that have a
MAPINFO entry, and a `music` key inside that map's own block, parsed afterwards, wins
(UZDoom `g_mapinfo.cpp:2285-2291`, Zandronum `g_mapinfo.cpp:1660-1666`). Level number 0 is
ignored.

## Accepted commands with no effect

| Command | Arguments consumed | Notes |
|---|---|---|
| `$registered` | none | Hexen leftover. |
| `$edfoverride` | none | Eternity Engine EDF compatibility marker. |
| `$archivepath` | one | The argument is read and discarded. |
| `$replaygain` (UZDoom) | none | In UZDoom's keyword table but has no handler. ReplayGain is controlled by the `mus_usereplaygain` cvar and the `setreplaygain` console command instead. SLADE's keyword list has it commented out. |

An argument given to a command that consumes none is read as the start of a logical mapping, as
for an unknown command (see the lump page's gotchas). `$replaygain <song> <gain>` therefore
defines a bogus sound named after the song instead of doing anything with music.

## Engine-family divergence

- **Name resolution.** UZDoom resolves each `$musicvolume`, `$mididevice` and `$modplayer` song
  to a lump when SNDINFO is parsed (full archive path first, then the short name in the music
  namespace), and stores the setting against that lump. A song that doesn't exist yet at that
  point is silently ignored, and any name that reaches the same lump at play time gets the
  setting. Zandronum stores `$musicvolume` and `$mididevice` against the name string itself and
  matches it against the requested name (after `$musicalias`) at play time, with no existence
  check.
- **`$musicalias` replacement lookup.** UZDoom accepts a full archive path or a short music
  name as `<replacement>`. Zandronum looks it up only as a short name in the music namespace, so
  a replacement longer than 8 characters or containing `/` or `.` never exists there and the
  alias is always dropped. UZDoom also still sets an alias when both the SNDINFO and the
  competing music lump come from the engine's own files or the IWAD, which Zandronum's
  "later file wins" check does not exempt.
- **`$musicalias` input name (UZDoom).** Before the alias lookup, UZDoom strips a leading `/`
  and resolves a `$`-prefixed name through the string table with a `D_` prefix (DEHACKED-style
  music), so an alias keyed on the resulting `D_` name applies to those requests too.
- **`$musicvolume` value.** UZDoom accepts a plain number or a decibel value written as one
  token with a `db` suffix, such as `-6db` (anything else is a fatal "Bad value for music
  volume"), and a song with an entry skips the ReplayGain lookup. Zandronum accepts only a plain
  number.
- **`$mididevice` extras (UZDoom).** UZDoom also accepts `sndsys` (same as `fmod`), `wildmidi`,
  `adl` and `opn`, and an optional `, <argument string>` after the device word, passed to the
  device (for example a sound font or bank selection). Zandronum has none of these.
- **`$modplayer`** is UZDoom-only; on Zandronum its two arguments become a bogus sound mapping.
