# `snd_musicvolume` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum source `src/sound/i_music.cpp:118–142`, verified 2026-08-02.

Volume multiplier for music playback.

The cvar accepts values in the range 0.0–1.0; any value outside this range is automatically clamped. Changing this cvar triggers a callback that updates the music volume immediately if music is currently playing, and restarts music if the volume was previously 0 (muted).

**Units:** linear multiplier from 0 (silent) to 1 (100% volume), corresponding to `relative_volume * self`.

**Default:** 0.5.

## Engine-family divergence: UZDoom's default differs and it also multiplies by a separate `snd_mastervolume` cvar Zandronum doesn't have

The clamping, range, and immediate-update/restart-on-unmute behavior described above hold identically on UZDoom (`src/common/audio/music/i_music.cpp`) — same clamp-to-[0,1] logic, same restart of music when raising the volume off of 0. Two things differ.

First, the cvar's own stored default is `1.0` on UZDoom, not `0.5`.

Second, what actually reaches the sound renderer differs: UZDoom's callback passes `self * relative_volume * snd_mastervolume`, where Zandronum's passes `self * relative_volume` alone. `snd_mastervolume` is a UZDoom-only cvar (also documented in `snd_sfxvolume.md`'s own divergence section, where it plays the same role for sound effects) that has no Zandronum equivalent; it defaults to `0.5` and is itself clamped to [0,1].

**Practical impact:** the two engines' effective default output volume works out the same in practice — UZDoom's `1.0` (music) × `1.0` (relative) × `0.5` (master) ≈ Zandronum's `0.5` (music) × `1.0` (relative) — but that's a coincidence of the two defaults, not an equivalence of mechanism. Setting `snd_musicvolume 1` on a UZDoom install with a non-default `snd_mastervolume` produces a different actual music gain than the same `snd_musicvolume` setting on Zandronum, which has no master-volume lever to compensate.
