# `developer` (cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** ZDoom Wiki `CVARs:Debug` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3ADebug&oldid=49990) + verified against Zandronum source's `src/doomstat.cpp:43-44` and `zandronum/docs/commands.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Enables printing of debugging messages to the console. Unlike ZDoom/GZDoom, Zandronum does not implement severity levels — the cvar is a simple boolean flag with no numeric gradient (no levels 1–4). All debug messages print when enabled, or none print when disabled.

Zandronum uses this flag in script parsing (`sc_man.cpp`), map loading diagnostics (`p_setup.cpp`), and actor spawning checks (`p_spec.cpp`), among other subsystems. It does not persist to config (`Flags: 0`) and must be set from the command line or an `autoexec.cfg` file if a non-default behavior is desired at engine startup.

## Notes on wiki accuracy

The ZDoom wiki claims severity levels 1–4 controlling output granularity (errors, warnings, notifications, everything). This system does not exist in Zandronum; the cvar type is boolean, not integer.

## Engine-family divergence

UZDoom's `developer` is not the boolean flag described above. It's declared `Int`, default `0`, with flags `CVAR_ARCHIVE | CVAR_GLOBALCONFIG` (`src/common/console/c_console.cpp`), so unlike Zandronum's non-persisting `Flags: 0` cvar, UZDoom's value does persist across sessions (saved to the global, not per-game, config). UZDoom implements exactly the numeric severity-level system the ZDoom wiki describes and this file's "Notes on wiki accuracy" section above says doesn't exist — that claim holds only for Zandronum, not for the engine family generally.

The gating enum (`src/common/engine/printf.h`) is `DMSG_OFF` (0), `DMSG_ERROR` (1), `DMSG_WARNING` (2), `DMSG_NOTIFY` (3), `DMSG_SPAMMY` (4, everything regardless of usefulness). A diagnostic call tagged at a given level prints only when `developer >= level`, and nothing prints at all when `developer` is `0`/off — so raising `developer` is cumulative: setting it to `DMSG_ERROR` (1) shows only the single most-severe tier, and each further step unlocks the next, less-severe tier on top of what's already shown, up through `DMSG_SPAMMY` (4) showing everything. This numeric scale is what `acs/families/inventory.md` depends on elsewhere in this tree when describing a UZDoom-only diagnostic gated behind `DMSG_ERROR`.
