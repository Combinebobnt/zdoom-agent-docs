# `debuganimated` (cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** ZDoom Wiki `CVARs:Debug` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3ADebug&oldid=49990) + verified against Zandronum source's `src/textures/animations.cpp:162` and behavior in `FTextureManager::InitAnimated()`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Prints debug information to the console while reading the ANIMATED lump during texture initialization. The cvar does not persist to config (`Flags: 0`), and the ANIMATED lump loading occurs very early in engine startup, before the console command interface is available. As a result, this cvar can only be set from the command line (e.g. `+set debuganimated 1`) or from an `autoexec.cfg` file — it cannot be changed interactively after the engine has started, even if the administrator has console access.

When enabled, prints one line of debug output per animation definition in the ANIMATED lump, showing the from-texture name/index and to-texture name/index, as well as their source lumps and wad files.
