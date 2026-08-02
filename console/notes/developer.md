# `developer` (cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `CVARs:Debug` (retrieved 2026-08-02, oldid=49990) + verified against Zandronum source's `src/doomstat.cpp:43-44` and `zandronum/docs/commands.txt`.

Enables printing of debugging messages to the console. Unlike ZDoom/GZDoom, Zandronum does not implement severity levels — the cvar is a simple boolean flag with no numeric gradient (no levels 1–4). All debug messages print when enabled, or none print when disabled.

Zandronum uses this flag in script parsing (`sc_man.cpp`), map loading diagnostics (`p_setup.cpp`), and actor spawning checks (`p_spec.cpp`), among other subsystems. It does not persist to config (`Flags: 0`) and must be set from the command line or an `autoexec.cfg` file if a non-default behavior is desired at engine startup.

## Notes on wiki accuracy

The ZDoom wiki claims severity levels 1–4 controlling output granularity (errors, warnings, notifications, everything). This system does not exist in Zandronum; the cvar type is boolean, not integer.
