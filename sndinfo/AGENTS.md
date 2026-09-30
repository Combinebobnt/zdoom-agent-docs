# sndinfo/: the SNDINFO lump

SNDINFO maps logical sound names to sound lumps and carries `$`-commands for random and alias
sounds, player-class sounds, ambient sounds, per-sound playback properties and per-song music
settings. **Read `../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

**Both engines parse SNDINFO**, with the same parser lineage: UZDoom accepts 31 `$`-commands and
Zandronum 25, the six extras being UZDoom-only. Every file here stamps
`Applies to: UZDoom=yes, Zandronum=yes` plus a `Verified against:` pair, and carries an
`## Engine-family divergence` heading.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router, including a table saying which page covers each
  `$`-command.
- `concepts/<topic>.md`: Archetype 3. The lump itself (grammar, load order, conditionals,
  errors and the full command table), then four pages that each group several `$`-commands.

**No `inventory/`/`notes/` and no one-file-per-command.** The command set is small and fixed (a
31-entry keyword table), and most commands only make sense next to their neighbors: `$alias`
and `$random` share the resolution rules that decide where `$volume` or `$limit` is read from,
and the `$playersound` family shares one lookup and fallback. A new command, or a finding about
an existing one, goes on the concept page that already covers it; update the lump page's command
table and the INDEX table if it is a new command.

## Where SNDINFO is implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| Parser (`S_ParseSndInfo`, `S_AddSNDINFO`, keyword table `SICommandStrings[]`) | `src/sound/s_advsound.cpp` | `src/s_advsound.cpp` |
| Player-sound tables and lookup (`S_LookupPlayerSound`, `S_FindSkinnedSound`) | `src/sound/s_advsound.cpp` | `src/s_advsound.cpp` |
| `AmbientSound` thing | `src/sound/s_advsound.cpp` natives, class in `wadsrc/static/zscript/actors/shared/soundsequence.zs` | `src/s_advsound.cpp` (`AAmbientSound`), `wadsrc/static/actors/shared/soundsequence.txt` |
| Sound table, playback, limits, pitch, rolloff (`StartSound`, `CheckSoundLimit`, `GetRolloff`) | `src/common/audio/sound/s_sound.cpp`, `s_soundinternal.h` | `src/s_sound.cpp` |
| Game-side glue: per-map SNDINFO reload, music-name lookup and aliases | `src/sound/s_doomsound.cpp` | `src/s_sound.cpp` |
| Music playback (`$musicvolume`, `$mididevice`, `$modplayer` consumers) | `src/common/audio/music/music.cpp` | `src/s_sound.cpp`, `src/s_advsound.cpp` (`S_GetMusicVolume`) |
| Controller rumble (`$rumbledef`/`$rumble`) | `src/common/engine/m_haptics.cpp` | none |
| Startup call site (`S_InitData`, before `G_ParseMapInfo`) | `src/d_main.cpp` | `src/d_main.cpp` |
| Stock SNDINFO | `wadsrc/static/sndinfo.txt`, `wadsrc/static/filter/game-*/sndinfo.txt` | `wadsrc/static/sndinfo.txt` |

Tier-B backing prose: UDB `Build/Scripting/ZDoom_SNDINFO.cfg` (keyword list only; it lists a
`$playerreserve` that neither engine accepts and has no UZDoom-only commands) and SLADE
`dist/res/config/languages/zdoom.txt`'s `z_sndinfo` block (keyword list with `$pitchset` and
`$modplayer`, and `replaygain` commented out).
