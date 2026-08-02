# `autoaim`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/d_netinfo.cpp:76` and `zandronum/docs/commands.txt` (which describes the actual vertical-distance semantics; the wiki page is corrupted and describes a different system).

Controls the vertical distance threshold at which the engine's automatic aiming system targets actors. The value is stored in **Doom angle units** (1 degree = `ANGLE_1` in the source).

## Actual behavior vs. wiki description

**Wiki divergence warning:** The saved wiki page for "Console variables" contains corrupted text where a changelog fragment is spliced into the AutoAim row's description mid-sentence. More importantly, the wiki's description describes a **horizontal** auto-aim precision system with specific degree presets (0°, 0.25°, 1°, 2°, 3°, 35°–56°), but that system does not exist in Zandronum.

The **actual Zandronum behavior** per `zandronum/docs/commands.txt`:
- This is a **vertical distance** cvar, not a horizontal angle precision system.
- Setting to 0 disables autoaiming entirely.
- Setting to large values (e.g., 5000) reproduces classic DOOM auto-aim behavior.
- The value represents how far above or below a target the player's sight can be before that target is auto-aimed.

**Default:** 5000.0 (classic DOOM auto-aim, which is generous and will auto-aim at most visible enemies).

## Network and storage

This cvar is marked `CVAR_USERINFO | CVAR_ARCHIVE`, so it's part of the player's network userinfo and persists to the config file.

## Related cvars

- **`sv_noautoaim`** — a server-side flag (DMFlag) that can disable autoaiming server-wide.
- **`cl_doautoaim`** — a separate boolean cvar that controls whether the client *applies* autoaiming at all (independent of this cvar's value).
- **`compat_autoaim`** — a compatibility flag for behavior control.
