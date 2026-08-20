# stat

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/stats.h` (ADD_STAT macros) and engine source.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Displays real-time profiling and diagnostic information. Syntax: `stat [property]`

Running `stat` with no argument lists all available properties and their current state (on or off). Running `stat <property>` toggles that property on or off; when enabled, a live counter or timer displays on the HUD during gameplay.

## Available stat properties

- **fps** — Frames per second (render time, not same as `vid_fps 1`)
- **bots** — Time spent on bot AI and pathfinding
- **think** — Time spent running all game thinkers (physics, state machines, etc.)
- **sight** — Time spent doing visibility/linecast checks (hit-scan targeting, line-of-sight AI)
- **spawns** — Actor spawn/despawn activity
- **pathing** — AI pathfinding grid updates and navigation
- **gc** — Garbage collector cycles
- **blit** — Software/buffer copy time (SDL video)
- **interpolations** — Interpolation state tracking
- **music** — Music subsystem and streaming
- **sound** — Sound playback and mixing
- **nettraffic** — Network packet send/receive traffic (clients and servers)
- **renderstats** — OpenGL/rendering pipeline statistics (draw calls, batches, etc.)
- **rendertimes** — Per-stage render timing breakdown
- **lightstats** — Light calculation and shadow timing (OpenGL renderer)
- **wallcycles** — Rasterizer wall-drawing cycles
- **scancycles** — Rasterizer scan-span cycles
- **missingtextures** — Texture lookup failures and fallback activity
- **sectorhacks** — Sector geometry and hack/workaround application
- **voice** — Voice chat subsystem activity

Some properties may be unavailable depending on renderer (OpenGL vs software), build (debug vs release), or platform.

## Engine-family divergence

The general `stat`/`stat <property>` toggle mechanism is unchanged: called bare it lists every
registered property with its on/off state, called with an argument it toggles that property.
UZDoom's dispatch lives in `src/common/engine/stats.cpp`'s `CCMD(stat)`, backed by the same
`FStat`/`ADD_STAT` registration pattern Zandronum uses (now declared in
`src/common/engine/stats.h` rather than Zandronum's top-level `src/stats.h`). Only `ADD_STAT`
exists as a registration macro on UZDoom too — there is no separate `ADD_GPU_STAT`-style macro;
GPU-side timing rides the same mechanism (see `gpu`, below).

Of the 20 documented properties, several no longer exist on UZDoom at all:
- **spawns** — no stat registration exists near the actor-spawn code
  (`src/playsim/p_mobj.cpp`); spawn/despawn activity isn't tracked as a toggleable stat.
- **pathing** — UZDoom's tree has no A*/pathfinding-grid file equivalent to Zandronum's
  `astar.cpp` at all, so there's nothing for a `pathing` stat to report. (`bots` itself still
  exists — see below — it just no longer has a separate pathing-specific counterpart.)
- **blit** — no software-framebuffer/video-backend blit-copy stat exists anywhere in the platform
  layer (checked the SDL, Win32, and macOS/Cocoa backend files).
- **scancycles** — removed outright. Zandronum registers it alongside `wallcycles` in the same
  renderer file; UZDoom's software-renderer equivalent keeps only `wallcycles`.
- **missingtextures** / **sectorhacks** — the underlying sector-patching/render-hack logic still
  exists (`src/rendering/hwrenderer/scene/hw_renderhacks.cpp` handles the equivalent
  missing-texture workaround logic), but no longer registers separate toggleable stats for it.
- **voice** — UZDoom has no voice-chat subsystem at all (no file resembling Zandronum's
  `voicechat.cpp`), so there's no voice-activity stat.

One documented property is renamed rather than removed: **nettraffic** is registered as
**network** on UZDoom (`src/d_net.cpp`), reporting the same kind of tic-dup/network-timing summary
under a different name.

**renderstats**, **rendertimes**, and **lightstats** exist, but their scope is stated too narrowly
in the prose above: they're registered in `src/common/rendering/hwrenderer/data/hw_clock.cpp`,
UZDoom's backend-agnostic hardware-renderer data layer, not an OpenGL-specific one — UZDoom ships
GL, GLES, and Vulkan backends, so these three properties apply across whichever hardware backend
is active, not "OpenGL" specifically. **wallcycles** still exists, and only in the
software-renderer scene code (`src/rendering/swrenderer/scene/r_scene.cpp`) exactly as it does on
Zandronum — that property hasn't diverged; it's its Zandronum-only companion `scancycles` that was
dropped.

The remaining documented properties — **fps**, **bots**, **think**, **sight**, **gc**,
**interpolations**, **music**, **sound** — still exist with equivalent meaning, though some moved
files (e.g. `interpolations` is now registered in `src/g_dumpinfo.cpp` rather than alongside the
interpolator code, and `bots`'s AI-timing counter now lives in `src/playsim/bots/b_game.cpp`).

UZDoom also registers several stat names that don't exist on Zandronum at all: **shadowmap**
(hardware shadow-map timing), **gpu** (GPU/postprocessing pipeline timing), **VM** (general script
VM execution stats) and **ACS** (a separate ACS-VM-specific stat), **psprites**
(player-sprite/weapon-state stats), **velocity** (current player-velocity readout), **sounddebug**,
**analogue**/**digital** (input-command diagnostics), and **swfps**/**swfps_accumulated**
(software-renderer frame-timing counters, distinctly named from Zandronum's own
`fps`/`fps_accumulated` pair).
