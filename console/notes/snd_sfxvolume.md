# `snd_sfxvolume` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum source `src/sound/i_sound.cpp`, verified 2026-08-02.

Volume multiplier for sound effects.

The cvar accepts values in the range 0.0–1.0; any value outside this range is automatically clamped. Changing this cvar triggers a callback that updates the SFX volume in the sound renderer if one is available.

**Units:** linear multiplier from 0 (silent) to 1 (100% volume).

**Default:** 1.0.

**Flags:** `CVAR_ARCHIVE | CVAR_GLOBALCONFIG | CVAR_NOINITCALL` — the `CVAR_NOINITCALL` flag prevents the callback from executing during engine startup (before the sound system is initialized), avoiding operations on a null sound renderer.

## Engine-family divergence: UZDoom multiplies by a separate `snd_mastervolume` cvar Zandronum doesn't have

The clamping, default, range, and flags described above hold identically on UZDoom (`src/common/audio/sound/i_sound.cpp`) — same `CUSTOM_CVAR(Float, snd_sfxvolume, 1.f, CVAR_ARCHIVE|CVAR_GLOBALCONFIG|CVAR_NOINITCALL)` declaration, same clamp-to-[0,1] logic. Where UZDoom diverges is what actually reaches the sound renderer: its callback passes the sound renderer `self * snd_mastervolume` rather than `self` alone. Zandronum has no `snd_mastervolume` cvar at all — its callback passes the sound renderer `self` directly, so `snd_sfxvolume` alone is the effective SFX gain.

`snd_mastervolume` is a UZDoom-only `CUSTOM_CVAR(Float, ..., 0.5f, CVAR_ARCHIVE|CVAR_GLOBALCONFIG|CVAR_NOINITCALL)`, itself clamped to [0,1], that also feeds into the music-volume path and is re-applied by re-invoking `snd_sfxvolume`'s (and `snd_musicvolume`'s) callback whenever it changes.

**Practical impact:** on UZDoom, the effective sound-effects gain at the renderer is `snd_sfxvolume * snd_mastervolume`, not `snd_sfxvolume` alone. Since `snd_mastervolume` defaults to 0.5, a stock UZDoom install with `snd_sfxvolume 1` plays sound effects at roughly half the raw gain a Zandronum install with the same `snd_sfxvolume` setting would (assuming Zandronum's own master-mixing, if any, is not itself in play).
