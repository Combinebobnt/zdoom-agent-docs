# stat

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, saved 2026-08-02); verified against `src/stats.h` (ADD_STAT macros) and engine source.

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
