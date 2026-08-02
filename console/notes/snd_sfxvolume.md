# `snd_sfxvolume` (console cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/sound/i_sound.cpp`, verified 2026-08-02.

Volume multiplier for sound effects.

The cvar accepts values in the range 0.0–1.0; any value outside this range is automatically clamped. Changing this cvar triggers a callback that updates the SFX volume in the sound renderer if one is available.

**Units:** linear multiplier from 0 (silent) to 1 (100% volume).

**Default:** 1.0.

**Flags:** `CVAR_ARCHIVE | CVAR_GLOBALCONFIG | CVAR_NOINITCALL` — the `CVAR_NOINITCALL` flag prevents the callback from executing during engine startup (before the sound system is initialized), avoiding operations on a null sound renderer.
