# `snd_musicvolume` (console cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/sound/i_music.cpp:118–142`, verified 2026-08-02.

Volume multiplier for music playback.

The cvar accepts values in the range 0.0–1.0; any value outside this range is automatically clamped. Changing this cvar triggers a callback that updates the music volume immediately if music is currently playing, and restarts music if the volume was previously 0 (muted).

**Units:** linear multiplier from 0 (silent) to 1 (100% volume), corresponding to `relative_volume * self`.

**Default:** 0.5.
