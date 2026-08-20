# `snd_mididevice` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum source `src/sound/music_midi_base.cpp`, verified 2026-08-02.

Selects which MIDI device or synthesizer to use for MIDI and MUS music playback.

**Default:** -1 (use the default FMOD synthesizer).

**Behavior:** The valid range and behavior depend on the platform:

**Windows:** Accepts values from -5 to N-1, where N is the total number of MIDI devices enumerated. The value -1 selects the FMOD synthesizer, -2 selects the default system MIDI device, and -3 through -5 select specific synthesizers (TiMidity++, external TiMidity, FluidSynth, etc.). Non-negative values select available MIDI devices by index. Invalid values cause the cvar to be reset to 0 (the first enumerated device) with a console message; no range clamping is performed, so the callback validates against the actual device list at runtime.

**Unix/Linux/Mac:** Accepts values from -5 to -1 only. Values -1 through -5 select different synthesizers (FMOD, TiMidity++, WildMIDI, FluidSynth, Timidity). Attempting to set a value outside the -5 to -1 range automatically resets the cvar to -1.

The value -1 (FMOD) is always available; other device indices depend on whether the corresponding synthesizer was compiled in and initialized.

Use the `snd_listmididevices` console command to see the full list of available MIDI devices and synthesizers on your system.

## Engine-family divergence

UZDoom's music playback runs through the shared ZMusic library rather than the FMOD-based pipeline described above, and `snd_mididevice`'s semantics differ substantially:

- **Default is -5 (FluidSynth), not -1.** There is no FMOD synthesizer in UZDoom at all; the closest equivalent, ID -1 ("Sound System"), is not FMOD but the engine's general audio-output path, which internally redirects to the same FluidSynth backend as -5.
- **The negative-ID range is unified across all platforms and extends further**, not split into a Windows range and a narrower Unix/Linux/Mac range: -1 Sound System (→ FluidSynth), -2 TiMidity++, -3 emulated OPL FM synth, -4 Gnu/Gravis Ultrasound emulation, -5 FluidSynth (always present), and, only when the corresponding library was compiled in, -6 WildMIDI, -7 libADLMIDI (OPL3 FM emulation), -8 libOPNMIDI (OPN2 FM emulation).
- **Non-negative IDs (real hardware/software MIDI output devices) are enumerated on Linux and macOS too, not just Windows** — via ALSA sequencer ports on Linux (when ALSA is available at build time) and CoreMIDI destinations on macOS, in addition to the Windows `winmm` device list. The doc's "Unix/Linux/Mac: -5 to -1 only" restriction does not hold for UZDoom.
- **Validation works by list membership, not a numeric range check or platform-specific clamp.** The cvar's change callback re-queries the live enumerated device list (the same one `snd_listmididevices` prints) and checks whether the new value's ID is present; if not, it resets the cvar to -5 (not 0, and not -1) and prints a message, except that the message is deliberately suppressed when the rejected value is 0 or -1, to avoid spamming on those two specific commonly-encountered values.

UZDoom's console/menu behavior (`snd_listmididevices` output, technology labels) is otherwise structurally the same idea as Zandronum's, just built from a different, longer device-ID table and driven by ZMusic rather than FMOD.
