# `handicap`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/d_netinfo.cpp:93` + verified against the implementation in `src/d_netinfo.cpp:HandicapChanged()` which shows clamping to `(0, deh.MaxSoulsphere)`.

Reduces the player's spawn health. The spawn health is calculated as `MaxSoulsphere - handicap`, where `MaxSoulsphere` is the maximum soul sphere health value from the active IWAD or custom DEHACKED lump.

## Valid range

The cvar is clamped to **0 to `MaxSoulsphere`** (inclusive). By default in standard Doom, `MaxSoulsphere` is 100, making the default clamp range 0–100. However, this range changes if the IWAD or a loaded DEHACKED lump redefines `MaxSoulsphere`.

Setting `handicap` to 0 produces the normal spawn health. Setting it to `MaxSoulsphere` produces a spawn health of 0 (effectively zero health on spawn, depending on other spawn logic).

## Network and storage

This cvar is marked `CVAR_USERINFO | CVAR_ARCHIVE`, so it's part of the player's network userinfo and persists to the player's config file.
