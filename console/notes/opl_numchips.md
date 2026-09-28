# `opl_numchips` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum source `src/sound/music_mus_opl.cpp`, verified 2026-08-02. Correction backed by `src/oplsynth/opl_mus_player.cpp:26,42`, `src/oplsynth/music_opl_mididevice.cpp:97`, `src/sound/i_music.cpp:501-509`, `src/sound/music_midistream.cpp:237`, `src/oplsynth/mlopl_io.cpp:322-346`.

Number of virtual OPL chips to emulate when music is synthesized by the built-in OPL emulator.

The cvar accepts values in the range 1–8; any value outside this range is automatically clamped.

On Zandronum the value is used by two separate paths:

- **OPL MIDI device** (`snd_mididevice -3`). MUS, MIDI, HMI and XMI music played through it uses the full clamped value (1 to 8). A change made while such a song is playing is not applied live; it takes effect when the next song opens.
- **Raw OPL register dumps** (RDosPlay RAW, DOSBox DRO, and the modified IMF format). These play through a separate player that caps the count at 2, so any value above 2 behaves like 2. Changing the cvar while one of these is playing re-initializes its chips immediately, still capped at 2.

With an OPL3 emulator core selected (`opl_core`), Zandronum halves the requested count, rounding up, since each OPL3 chip provides twice the channels of an OPL2.

**Units:** count of virtual chips.

**Default:** 2.

**Notes:** The OPL hardware emulated here refers to Yamaha OPL2 and OPL3 synthesizer chips found on vintage sound cards. Each emulated OPL2 chip provides 9 voices, so the chip count sets the synthesizer's polyphony. Using only one chip (which was a cost-cutting measure in 1980s budget cards) is slightly faster but insufficient to render most of Doom's music adequately. Two or more chips is the typical requirement for acceptable polyphony. On Zandronum, values above 2 only matter for the OPL MIDI device; the raw OPL formats ignore them.
