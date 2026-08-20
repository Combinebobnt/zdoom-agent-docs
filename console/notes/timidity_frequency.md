# `timidity_frequency` (console cvar)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** ZDoom Wiki `CVARs:Audio` (https://zdoom.org/w/index.php?title=CVARs:Audio&oldid=53412, saved 2026-08-02) for the default-value divergence; Zandronum source `src/sound/music_midi_timidity.cpp`, verified 2026-08-02.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Sampling rate at which the external TiMidity++ synthesizer renders MIDI output.

The cvar accepts values in the range 4000–65000 Hz; any value outside this range is automatically clamped to the nearest boundary.

**Units:** Hertz (Hz).

**Default:** 22050 Hz.

**Wiki divergence:** The ZDoom Wiki lists the default as 44100 Hz, but Zandronum's actual default is 22050 Hz.

This cvar only applies when using the external TiMidity++ synthesizer (`snd_mididevice` set to an external TiMidity device, not the built-in software synthesizer).

## Engine-family divergence

`timidity_frequency` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. UZDoom does not ship the Timidity++ backend this cvar configures; its music playback goes through zmusic, a differently-named settings surface entirely.

Attempting to set it under UZDoom — via the console, a config file, or ACS's `ConsoleCommand()` — prints `Unknown command "timidity_frequency"` to console/log and the write silently fails to apply: visible if someone's watching the console at the time, easy to miss if not (e.g. an `autoexec.cfg` line or unattended server startup script). Since this cvar's whole job is setting the synthesizer's output sample rate, a config that relies on it to avoid a mismatched-rate artifact on Zandronum has no equivalent lever to pull on UZDoom, and no equivalent problem either, since the backend it would have tuned isn't present.
