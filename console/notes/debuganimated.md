# `debuganimated` (cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `CVARs:Debug` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3ADebug&oldid=49990) + verified against Zandronum source's `src/textures/animations.cpp:162` and behavior in `FTextureManager::InitAnimated()` (`animations.cpp:164-243`), startup order in `src/d_main.cpp:2831-2839, 2866, 2984`, startup cvar handling in `src/c_dispatch.cpp:678-714`, and the `restart` CCMD at `src/d_main.cpp:3341`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Prints debug information to the console while reading the ANIMATED lump during texture initialization. The cvar does not persist to config (`Flags: 0`). The ANIMATED lump is read once during startup, after command-line `+` commands, `autoexec.cfg` and `-exec` files have run. So set it there (e.g. `+debuganimated 1` or `+set debuganimated 1`) to see the output. Setting it from the console later works but prints nothing until texture initialization runs again. On Zandronum that happens on the `restart` command; on UZDoom the equivalent command is `debug_restart`.

When enabled, prints one line per ANIMATED definition that is actually processed, giving each end's texture name, texture index, source lump number and the index of the file containing that lump (a number, not a file name). Definitions skipped for a missing texture, an SMMU-style swirl speed (above 65535 on a texture not already warping) or mismatched texture use types print nothing. A single-frame definition prints its debug line and then the usual "has only one frame" message.
