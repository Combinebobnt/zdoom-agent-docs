# The `SNDINFO` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `SNDINFO` (https://zdoom.org/w/index.php?title=SNDINFO&oldid=55137, retrieved 2026-09-28) + verified against the UZDoom source's `src/sound/s_advsound.cpp` (`SICommandStrings[]`, `S_ParseSndInfo`, `S_AddSNDINFO`, `S_ResolveIncludePath` at `:674`, `S_AddSound` at `:410-426`, `S_CheckIntegrity` at `:320`), `src/sound/s_doomsound.cpp` (`:276-292`), `src/common/audio/sound/s_sound.cpp`, `src/common/filesystem/source/filesystem.cpp`, `src/gamedata/gi.cpp`, `src/gamedata/g_mapinfo.cpp`, `src/d_main.cpp` (`:S_InitData` call site), and the Zandronum source's `src/s_advsound.cpp` (`S_ParseSndInfo` at `:905`, `S_AddSound` at `:569`), `src/s_sound.cpp` (`:450-468`), `src/w_wad.cpp`, `src/gi.h`, `src/g_mapinfo.cpp`, `src/d_main.cpp`, and `src/network.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

SNDINFO maps **logical sound names** (the names DECORATE, ZScript, ACS, MAPINFO and the engine's
own code ask for, such as `weapons/pistol`) to sound lumps, and carries `$`-commands that attach
playback properties, random/alias indirection, player-class sounds, ambient sounds and music
settings to those names. Nothing plays a lump directly by its lump name: a sound that no SNDINFO
line names does not exist for gameplay code.

## When it is read

- **Every lump named `SNDINFO` in the global namespace is parsed, in load order**
  (`S_ParseSndInfo`: UZDoom `s_advsound.cpp:602`, Zandronum `s_advsound.cpp:905`). The loop tests
  each lump's 8-character short name, so a pk3 can ship several root files such as
  `sndinfo.txt` and `sndinfo.weapons`, all read as SNDINFO; see
  [PK3 lump naming](../../shared/concepts/pk3-lump-naming.md) for how the short name is cut. A
  file in a pk3 subdirectory is not in the global namespace and is not picked up by name. The
  exception is UZDoom's `filter/<game>/` directories, whose files are moved to the root when the
  game matches (the stock SNDINFO ships that way).
- **Before MAPINFO** (`d_main.cpp`: `S_InitData` then `G_ParseMapInfo` on both engines). SNDINFO cannot depend on anything MAPINFO defines, but a
  MAPINFO map block can override what SNDINFO's `$map` set (see
  [music aliases](music-aliases.md)).
- The engine seeds sound 0 as the silent `{ no sound }` entry before the first lump. Strife voice
  lumps (the `voices/` namespace) are auto-registered on both engines as `svox/<lumpname>`
  during the same pass, so a voice needs no SNDINFO line.
- **Per-map SNDINFO.** A MAPINFO map block's `sndinfo`/`soundinfo` key names an extra lump for
  that map. On a map change where that name differs from the previous map's, the engine unloads
  cached sounds, re-parses every global SNDINFO from scratch, then parses the map's lump on top
  (UZDoom `s_doomsound.cpp:276-292`, Zandronum `s_sound.cpp:450-468`). The map lump is found by
  full path first, then by short name.

## Line grammar

The lump is read with the shared script scanner, one whitespace-separated token at a time, not
line by line. `//` line comments and `/* */` block comments work, and double quotes group a token
that contains spaces. Every name is case-insensitive.

A token that does not start with `$` begins a **logical mapping**: the next token is the lump it
maps to.

```text
// logicalname  lump
weapons/myshot  DSMYSHOT
weapons/myshot2 sounds/weapons/myshot2.ogg
```

- **Redefinition wins.** A later mapping for the same logical name, in the same or a later lump,
  repoints the existing entry to the new lump and clears any `$random`/`$alias` link it had
  (`S_AddSound`: UZDoom `:429`, Zandronum `:569`). Properties already set on it (`$volume`,
  `$limit`, `$rolloff` and so on) are kept. This is how a mod replaces a stock sound: redefine
  the stock logical name, do not rename the lump.
- **Lump lookup** (`CheckNumForFullName(name, true, ns_sounds)`, identical on both engines): the
  exact full path inside an archive, extension included, is tried first. If that fails and the
  name is at most 8 characters with no `.` or `/`, the short-name lookup runs in the sounds
  namespace, which also matches a plain WAD lump and a file under a pk3's `sounds/` directory
  by its base name. `sounds/myshot` without the extension therefore finds nothing, and neither
  does a base name longer than 8 characters.
- **A missing lump is not an error.** The logical name is still created, with no data, and plays
  nothing. See the divergence section for the one warning UZDoom can print.
- A logical name cannot start with `$`; that token is read as a command.

## Game-conditional blocks

`$ifdoom`, `$ifheretic`, `$ifhexen` and `$ifstrife` compare the rest of their own name with the
running game (`CheckGame(..., true)`, so `$ifdoom` is also true for Chex Quest). When the test
fails, every following token is skipped until one equal to `$endif`
(UZDoom `s_advsound.cpp:774-781`, `:1261-1266`; Zandronum `:987-994`, `:1383-1388`).

- **No nesting and no else.** The skip state is one flag: the first `$endif` ends any skip,
  and a `$if` inside a skipped block is itself skipped.
- **`$endif` is not in the command table.** When the test passes, the later `$endif` is simply an
  unknown command and is ignored. An `$if` with no `$endif` skips to the end of that lump only;
  the flag does not carry into the next SNDINFO lump or into an included file.

## `$include` (UZDoom only)

`$include <path>` parses another lump inline, at the point of the command
(UZDoom `s_advsound.cpp:788-798`, path rules in `S_ResolveIncludePath` at `:674`).

- The path is relative to the directory of the including file: `sounds.txt` and `./sounds.txt`
  mean the same thing, and each leading `../` climbs one directory. It is then looked up by full
  name across all loaded archives, with the same 8-character short-name fallback as a mapping, so
  inside a WAD a bare lump name works.
- The included lump does not have to be named SNDINFO.
- A path that resolves to nothing is a fatal script error ("include file ... not found").
- There is no include guard: a lump that includes itself, directly or through a chain, recurses
  without limit.

Zandronum does not know `$include`; see the gotcha below for what happens to it there.

## Every `$`-command

Both engines match the command against a fixed keyword table, case-insensitively
(`SICommandStrings[]`: UZDoom `s_advsound.cpp:200-233`, 31 entries; Zandronum
`s_advsound.cpp:230-257`, 25 entries). `$endif` is handled separately (above) on both.

| Command | UZDoom | Zandronum | Covered on |
|---|---|---|---|
| `$include` | yes | no | this page |
| `$ifdoom`, `$ifheretic`, `$ifhexen`, `$ifstrife` | yes | yes | this page |
| `$endif` | yes (outside the table) | yes (outside the table) | this page |
| `$ambient` | yes | yes | [ambient sounds](ambient-sounds.md) |
| `$random` | yes | yes | [random and player sounds](random-and-player-sounds.md) |
| `$alias` | yes | yes | [random and player sounds](random-and-player-sounds.md) |
| `$singular` | yes | yes | [random and player sounds](random-and-player-sounds.md) |
| `$playersound` | yes | yes | [random and player sounds](random-and-player-sounds.md) |
| `$playersounddup` | yes | yes | [random and player sounds](random-and-player-sounds.md) |
| `$playercompat` | yes | yes | [random and player sounds](random-and-player-sounds.md) |
| `$playeralias` | yes | yes | [random and player sounds](random-and-player-sounds.md) |
| `$pitchshift` | yes | yes | [random and player sounds](random-and-player-sounds.md) |
| `$pitchshiftrange` | yes | yes | [random and player sounds](random-and-player-sounds.md) |
| `$pitchset` | yes | no | [random and player sounds](random-and-player-sounds.md) |
| `$limit` | yes | yes | [sound limits and rolloff](sound-limits-and-rolloff.md) |
| `$volume` | yes | yes | [sound limits and rolloff](sound-limits-and-rolloff.md) |
| `$attenuation` | yes | yes | [sound limits and rolloff](sound-limits-and-rolloff.md) |
| `$rolloff` | yes | yes | [sound limits and rolloff](sound-limits-and-rolloff.md) |
| `$rumbledef` | yes | no | [sound limits and rolloff](sound-limits-and-rolloff.md) |
| `$rumble` | yes | no | [sound limits and rolloff](sound-limits-and-rolloff.md) |
| `$musicalias` | yes | yes | [music aliases](music-aliases.md) |
| `$musicvolume` | yes | yes | [music aliases](music-aliases.md) |
| `$mididevice` | yes | yes | [music aliases](music-aliases.md) |
| `$modplayer` | yes | no | [music aliases](music-aliases.md) |
| `$replaygain` | accepted, no effect | no | [music aliases](music-aliases.md) |
| `$map` | yes | yes | [music aliases](music-aliases.md) |
| `$registered` | accepted, no effect | accepted, no effect | [music aliases](music-aliases.md) |
| `$archivepath` | accepted, no effect | accepted, no effect | [music aliases](music-aliases.md) |
| `$edfoverride` | accepted, no effect | accepted, no effect | [music aliases](music-aliases.md) |

UZDoom's six extra table entries are `$include`, `$modplayer`, `$pitchset`, `$replaygain`,
`$rumble` and `$rumbledef`. `$replaygain` is in the table but has no handler, so it behaves like
the no-op commands.

## Errors and gotchas

- **An unknown `$`-command is dropped silently, and its arguments become mappings.** A command
  missing from the table matches nothing, nothing is printed, and the parser moves to the next
  token. That token does not start with `$`, so it and the one after it are read as
  `logicalname lump`. On Zandronum `$include extra.txt` therefore defines a sound called
  `extra.txt`; a two-argument unknown command creates one bogus sound; an odd argument count
  shifts every later mapping in the lump by one token. The same applies on UZDoom to
  `$replaygain`, and on both to `$registered`/`$edfoverride` if given an argument (they take
  none; `$archivepath` consumes exactly one). UDB's highlighting config also lists a
  `$playerreserve` keyword that neither engine accepts.
- **Fatal script errors** stop startup with the lump name and line: redefining a name reserved by
  `$playersound` ("Sounds that are reserved for players cannot be reassigned"), using an ordinary
  sound's name in a `$playersound`-family command, a `$playersounddup` target that is not a player
  sound, an unknown `$rolloff` type or MIDI device, a missing `{` after `$random`, or a non-number
  where a number is required.
- **Non-fatal messages** go to the console and parsing continues: an unknown `$ambient` timing
  type, and a `$random` list naming itself (Zandronum; UZDoom's version of that check is covered
  on the [random sounds page](random-and-player-sounds.md)).

## Wiki/engine divergence

The ZDoom Wiki says of `$include` that "the only thing not supported is includes from a different
archive" (the source comment above `S_ResolveIncludePath` says the same). What that means in
practice: there is no syntax to name another archive, but the resolved path is then looked up with
`CheckNumForFullName` across every loaded file (`s_advsound.cpp:790`). A file at the same path in
another archive is found, and if several archives have one, the last-loaded wins, even over the
including archive's own copy.

## Engine-family divergence

The keyword table differs by the six UZDoom-only entries above. The grammar, lookup and
redefinition rules otherwise match, with these differences:

- **`logicalname = lump` form (UZDoom only).** UZDoom accepts an optional `=` between a logical
  name and its lump. Whether a lump uses it is decided by its first mapping: after that, every
  mapping in the same lump must match, and a missing `=` is a fatal "expected '='" error
  (UZDoom `s_advsound.cpp:1327-1341`). Zandronum has no such rule and reads `=` as the lump name,
  which defines a silent sound and shifts the rest of the lump by one token. Write `=` only in a
  UZDoom-only SNDINFO, and put spaces around it.
- **Missing-lump warning.** UZDoom prints `<lump>, <name> - Lump doesn't exist: <lump name>` for
  an unresolved mapping or `$playersound`, but only when the `developer` cvar is 2 or higher,
  and never for SNDINFO inside the engine's own pk3 (`S_AddSound` at `:410`). Zandronum is always
  silent.
- **Post-parse integrity check (UZDoom only).** After all lumps, `S_CheckIntegrity` (`:320`)
  walks every `$alias` and `$random` chain, prints the cycle for any that loops back to itself and
  disables that sound. Zandronum has no equivalent.
- **Per-map SNDINFO and DEHACKED sounds (UZDoom only).** When DEHACKED adds new sound slots,
  UZDoom locks out per-map SNDINFO and prints "Local SNDINFO cannot be combined with DSDHacked
  sounds!" instead of loading it (`d_main.cpp:3714`, `S_AddLocalSndInfo` at `:649`).
- **Blood sound effects (Zandronum only).** Zandronum's parse pass also registers Blood `.SFX`
  lumps as sounds (`S_AddBloodSFX`, `s_advsound.cpp:1409`). UZDoom keeps the function but no
  longer calls it.
- **Network authentication (Zandronum).** SNDINFO is not in the set of lumps a Zandronum server
  checksums when a client connects (`network.cpp`, `lumpsToAuthenticate`), so a client with a
  different SNDINFO can join. A mod can add it through
  [AUTHINFO](../../zandronum-lumps/concepts/authinfo.md).
