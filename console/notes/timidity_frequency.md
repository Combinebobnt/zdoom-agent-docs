# `timidity_frequency` (console cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `CVARs:Audio` (https://zdoom.org/w/index.php?title=CVARs:Audio&oldid=53412, saved 2026-08-02) for the default-value divergence; Zandronum source `src/sound/music_midi_timidity.cpp`, verified 2026-08-02.

Sampling rate at which the external TiMidity++ synthesizer renders MIDI output.

The cvar accepts values in the range 4000–65000 Hz; any value outside this range is automatically clamped to the nearest boundary.

**Units:** Hertz (Hz).

**Default:** 22050 Hz.

**Wiki divergence:** The ZDoom Wiki lists the default as 44100 Hz, but Zandronum's actual default is 22050 Hz.

This cvar only applies when using the external TiMidity++ synthesizer (`snd_mididevice` set to an external TiMidity device, not the built-in software synthesizer).
