# `snd_mididevice` (console cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/sound/music_midi_base.cpp`, verified 2026-08-02.

Selects which MIDI device or synthesizer to use for MIDI and MUS music playback.

**Default:** -1 (use the default FMOD synthesizer).

**Behavior:** The valid range and behavior depend on the platform:

**Windows:** Accepts values from -5 to N-1, where N is the total number of MIDI devices enumerated. The value -1 selects the FMOD synthesizer, -2 selects the default system MIDI device, and -3 through -5 select specific synthesizers (TiMidity++, external TiMidity, FluidSynth, etc.). Non-negative values select available MIDI devices by index. Invalid values cause the cvar to be reset to 0 (the first enumerated device) with a console message; no range clamping is performed, so the callback validates against the actual device list at runtime.

**Unix/Linux/Mac:** Accepts values from -5 to -1 only. Values -1 through -5 select different synthesizers (FMOD, TiMidity++, WildMIDI, FluidSynth, Timidity). Attempting to set a value outside the -5 to -1 range automatically resets the cvar to -1.

The value -1 (FMOD) is always available; other device indices depend on whether the corresponding synthesizer was compiled in and initialized.

Use the `snd_listmididevices` console command to see the full list of available MIDI devices and synthesizers on your system.
