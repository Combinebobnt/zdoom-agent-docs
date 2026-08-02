# `timidity_mastervolume` (console cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/sound/music_midi_timidity.cpp`, verified 2026-08-02.

Volume scaling for the external TiMidity++ synthesizer.

The cvar accepts values in the range 0.0–4.0; any value outside this range is automatically clamped. Changing this cvar triggers a callback that notifies the currently-playing song (if any) that TiMidity's volume has changed.

**Units:** linear multiplier from 0 (silent) to 4.0 (400% volume).

**Default:** 1.0.

**Notes:** This cvar was added because TiMidity++ tends to produce louder output than other MIDI synthesizers. Allowing a value up to 4.0 permits quieting TiMidity if desired; values above 1.0 can be used to boost a particularly quiet MIDI file, but may introduce clipping at extreme settings.

This cvar only applies when using the external TiMidity++ synthesizer (`snd_mididevice` set to an external TiMidity device).
