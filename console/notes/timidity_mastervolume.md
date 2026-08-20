# `timidity_mastervolume` (console cvar)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum source `src/sound/music_midi_timidity.cpp`, verified 2026-08-02.

Volume scaling for the external TiMidity++ synthesizer.

The cvar accepts values in the range 0.0–4.0; any value outside this range is automatically clamped. Changing this cvar triggers a callback that notifies the currently-playing song (if any) that TiMidity's volume has changed.

**Units:** linear multiplier from 0 (silent) to 4.0 (400% volume).

**Default:** 1.0.

**Notes:** This cvar was added because TiMidity++ tends to produce louder output than other MIDI synthesizers. Allowing a value up to 4.0 permits quieting TiMidity if desired; values above 1.0 can be used to boost a particularly quiet MIDI file, but may introduce clipping at extreme settings.

This cvar only applies when using the external TiMidity++ synthesizer (`snd_mididevice` set to an external TiMidity device).

## Engine-family divergence

`timidity_mastervolume` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. UZDoom does not ship the Timidity++ backend this cvar configures; its music playback goes through zmusic, a differently-named settings surface entirely.

Attempting to set it under UZDoom — via the console, a config file, or ACS's `ConsoleCommand()` — prints `Unknown command "timidity_mastervolume"` to console/log and the write silently fails to apply: visible if someone's watching the console at the time, easy to miss if not (e.g. an `autoexec.cfg` line or unattended server startup script). Since this cvar exists specifically to tame TiMidity's tendency to render louder than other MIDI synthesizers, a config carrying a non-default value here (to quiet TiMidity, or to boost a quiet file) has no equivalent lever on UZDoom, and no equivalent volume-mismatch problem either, since the backend it would have compensated for isn't present.
