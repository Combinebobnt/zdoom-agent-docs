# `snd_mididevice` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum source `src/sound/music_midi_base.cpp`, verified 2026-08-02; device-ID mapping and fallback from `src/sound/music_midistream.cpp:229-248` and `src/sound/i_music.cpp:490-500`.

Selects which MIDI device or synthesizer to use for MIDI and MUS music playback.

**Default:** -1 (use the default FMOD synthesizer).

**Behavior:** On Zandronum the negative IDs are the same on every platform: -1 FMOD, -2 TiMidity++ (external), -3 emulated OPL FM synth, -4 Gravis Ultrasound emulation (the internal Timidity-based synth), -5 FluidSynth. A song whose SNDINFO `$mididevice` names a device uses that device instead of this cvar. The valid range and validation depend on the platform:

**Windows:** Accepts values from -5 to N-1, where N is the number of `winmm` MIDI output devices counted at music init. Non-negative values select those devices by index. A value outside that range prints "ID out of range. Using default device." and resets the cvar to 0 (the first enumerated device). The check only runs once the device count is known, so a config-loaded value is validated at music init.

**Unix/Linux/Mac:** Accepts values from -5 to -1 only. A value outside that range is clamped, silently: below -5 becomes -5, above -1 (including any non-negative device index) becomes -1.

FluidSynth (-5) exists only in builds with FluidSynth compiled in. Without it, -5 falls through to the platform default (FMOD on Unix, the `winmm` device path on Windows) and is missing from the menu and `snd_listmididevices`. If the chosen synth fails to open a song while the cvar is negative, playback retries on FMOD; on Windows with a non-negative cvar, it retries on the `winmm` device.

Use the `snd_listmididevices` console command to see the full list of available MIDI devices and synthesizers on your system.

## Engine-family divergence

UZDoom's music playback runs through the shared ZMusic library rather than the FMOD-based pipeline described above, and `snd_mididevice`'s semantics differ substantially:

- **Default is -5 (FluidSynth), not -1.** There is no FMOD synthesizer in UZDoom at all; the closest equivalent, ID -1 ("Sound System"), is not FMOD but the engine's general audio-output path, which internally redirects to the same FluidSynth backend as -5.
- **The negative-ID range is unified across all platforms and extends further**, not split into a Windows range and a narrower Unix/Linux/Mac range: -1 Sound System (→ FluidSynth), -2 TiMidity++, -3 emulated OPL FM synth, -4 Gnu/Gravis Ultrasound emulation, -5 FluidSynth (always present), and, only when the corresponding library was compiled in, -6 WildMIDI, -7 libADLMIDI (OPL3 FM emulation), -8 libOPNMIDI (OPN2 FM emulation).
- **Non-negative IDs (real hardware/software MIDI output devices) are enumerated on Linux and macOS too, not just Windows** — via ALSA sequencer ports on Linux (when ALSA is available at build time) and CoreMIDI destinations on macOS, in addition to the Windows `winmm` device list. The doc's "Unix/Linux/Mac: -5 to -1 only" restriction does not hold for UZDoom.
- **Validation works by list membership, not a numeric range check or platform-specific clamp.** The cvar's change callback re-queries the live enumerated device list (the same one `snd_listmididevices` prints) and checks whether the new value's ID is present; if not, it resets the cvar to -5 (not 0, and not -1) and prints a message, except that the message is deliberately suppressed when the rejected value is 0 or -1, to avoid spamming on those two specific commonly-encountered values.

UZDoom's console/menu behavior (`snd_listmididevices` output, technology labels) is otherwise structurally the same idea as Zandronum's, just built from a different, longer device-ID table and driven by ZMusic rather than FMOD.
