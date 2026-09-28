# `timidity_frequency` (console cvar)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `CVARs:Audio` (https://zdoom.org/w/index.php?title=CVARs:Audio&oldid=53412, saved 2026-08-02) for the default-value divergence; Zandronum source `src/sound/music_midi_timidity.cpp`, verified 2026-08-02.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Sampling rate at which the external TiMidity++ synthesizer renders MIDI output.

The cvar accepts values in the range 4000–65000 Hz; any value outside this range is automatically clamped to the nearest boundary.

**Units:** Hertz (Hz).

**Default:** 22050 Hz.

**Wiki divergence:** The ZDoom Wiki lists the default as 44100 Hz, but Zandronum's actual default is 22050 Hz.

This cvar only applies when using the external TiMidity++ synthesizer (`snd_mididevice -2`, or a song whose MUSINFO `$mididevice` selects TiMidity), not the built-in GUS-patch software synthesizer (`snd_mididevice -4`). It is passed to the TiMidity++ command line as `-s<rate>` and used as the playback stream's rate when the device opens (`src/sound/music_midi_timidity.cpp:187-218`).

## Engine-family divergence

`timidity_frequency` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. UZDoom has no external-executable TiMidity++ backend. Its `snd_mididevice -2` device is zmusic's in-process TiMidity++ port, configured through a different `timidity_*` cvar set (`timidity_config`, `timidity_reverb`, `timidity_chorus` and others) that has no sample-rate cvar.

Typing `timidity_frequency <value>` in the UZDoom console or putting it in a config file prints `Unknown command "timidity_frequency"` to console/log and the write silently fails to apply: visible if someone's watching the console at the time, easy to miss if not (e.g. an `autoexec.cfg` line or unattended server startup script). ACS's `ConsoleCommand()` never reaches the console dispatcher on UZDoom at all. It only prints "<game> doesn't support execution of console commands from scripts" (`src/playsim/p_acs.cpp` ~10371-10378). Since this cvar's whole job is setting the external synthesizer's output sample rate, a config that relies on it to avoid a mismatched-rate artifact on Zandronum has no equivalent lever to pull on UZDoom.
