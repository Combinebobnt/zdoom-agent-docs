# `opl_numchips` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum source `src/sound/music_mus_opl.cpp`, verified 2026-08-02.

Number of virtual OPL chips to emulate when rendering MUS (Doom-format) MIDI music via OPL synthesis.

The cvar accepts values in the range 1–8; any value outside this range is automatically clamped. Changing this cvar triggers a callback that resets the emulated OPL chips if OPL music is currently playing, allowing real-time updates without stopping playback.

**Units:** count of virtual chips.

**Default:** 2.

**Notes:** The OPL hardware emulated here refers to Yamaha OPL2 and OPL3 synthesizer chips found on vintage sound cards. Using only one chip (which was a cost-cutting measure in 1980s budget cards) is slightly faster but insufficient to render most of Doom's music adequately. Two or more chips is the typical requirement for acceptable polyphony. The maximum of 8 chips may be useful for testing or for systems with excess CPU capacity, but the hardware limit for raw OPL was 2 chips per card at most, so values above 2 are not authentic emulation.
