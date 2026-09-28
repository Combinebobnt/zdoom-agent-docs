# `timidity_mastervolume` (console cvar)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum source `src/sound/music_midi_timidity.cpp`, verified 2026-08-02. Device scope: `src/sound/music_midi_timidity.cpp:562-567`, `src/sound/music_midistream.cpp:233-246,1473-1475`, `src/s_advsound.cpp:1372`. UZDoom paths (at `5a9b0ec511`): `src/common/console/c_dispatch.cpp:324`, `src/playsim/p_acs.cpp:10371-10378`, `src/gameconfigfile.cpp:894-911`, `src/common/audio/music/music_config.cpp`.

Volume scaling for the external TiMidity++ synthesizer.

The cvar accepts values in the range 0.0–4.0; any value outside this range is automatically clamped. Changing this cvar triggers a callback that notifies the currently-playing song (if any) that TiMidity's volume has changed.

**Units:** linear multiplier from 0 (silent) to 4.0 (400% volume).

**Default:** 1.0.

**Flags:** `CVAR_ARCHIVE|CVAR_GLOBALCONFIG` (saved to the global section of the config, not per game).

**Notes:** This cvar was added because TiMidity++ tends to produce louder output than other MIDI synthesizers. Values below 1.0 quiet it. The ceiling of 4.0 leaves room to boost a particularly quiet MIDI file, but may introduce clipping at extreme settings.

This cvar only applies to the external TiMidity++ process device (`TimidityPPMIDIDevice`), the only MIDI device that reacts to the change callback. A song uses that device when `snd_mididevice` is -2 and the song has no device of its own, or when SNDINFO's `$mididevice <song> timidity` selects it (that per-song choice wins over `snd_mididevice`). Every other device ignores the cvar, including `snd_mididevice` -4 (the Gravis Ultrasound emulation, whose class is confusingly named `TimidityMIDIDevice`). It also has no effect if the engine failed to open the audio stream for TiMidity++'s output ("Could not create music stream.").

## Engine-family divergence

`timidity_mastervolume` does not exist in UZDoom at all. It is confirmed absent from source, not merely undocumented. UZDoom has no external-executable TiMidity++ backend (no `timidity_exe`). Its TiMidity++ is an internal ZMusic port, configured by other `timidity_*` cvars (`timidity_reverb`, `timidity_chorus` and so on), none of which is a master volume.

How setting it fails under UZDoom depends on the path:

- Typed in the console or run from an exec'd `.cfg` (e.g. an `autoexec.cfg` line): the dispatcher prints `Unknown command "timidity_mastervolume"`. That is visible if someone's watching the console at the time, easy to miss if not (e.g. an unattended server startup script).
- ACS `ConsoleCommand()`: never reaches the dispatcher. UZDoom prints that it doesn't support execution of console commands from scripts, whatever the command is.
- A `timidity_mastervolume=` key in the `.ini` config: silently kept as an auto-created string cvar, with no message and no effect.

A config carrying a non-default value here (to quiet TiMidity, or to boost a quiet file) has no equivalent lever on UZDoom.
