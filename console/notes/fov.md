# `fov`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum source `src/p_user.cpp` (CUSTOM_CVAR declaration) + verified against the implementation, which shows default 90.0 (not 100 as the wiki states). Zandronum online-locality correction (2026-09-25): `src/cl_commands.cpp:163`, `:247`; `src/g_game.cpp:1653-1669`; `src/p_user.cpp:712-713`; `src/cl_main.cpp:3861`; `src/p_mobj.cpp:5556`; commits `8401defe5`, `69a79af2f`, `7de15ffb4` checked for ancestry against `28f736fb3`.

Sets the player's field of vision in degrees. On UZDoom the value a client sets is genuine shared
simulation state, not purely local: changing it sends a `DEM_MYFOV` network command that is applied
to that player's `player_t::DesiredFOV`/`FOV` on every peer (UZDoom `src/d_net.cpp:2929-2930`).
Zandronum has the same `DEM_MYFOV` handler (`src/d_net.cpp:2413-2414`), but it only runs offline:
`RunNetSpecs` is skipped in client mode and on the server (`src/g_game.cpp:1653-1669`), so online a
client's FOV stays local. See "Default and scope" below. Both engines interpolate `DesiredFOV` into
`FOV` every tic, per-player, with the same 7°-smoothing threshold and weapon-`FOVScale` adjustment
(Zandronum `P_PlayerThink`, `src/p_user.cpp` around 3691-3705; UZDoom's equivalent moved to ZScript,
`PlayerPawn::CheckFOV`, `wadsrc/static/zscript/actors/player/player.zs:1025-1044`). Rendering uses
the `FOV` of whichever player the view camera points at, so chasecam, spectate or a scripted camera
actor picks up that player's `FOV` (Zandronum `src/d_main.cpp:890-891`; UZDoom `AActor::GetFOV`,
`src/playsim/p_mobj.cpp:4153-4166`, called from `src/d_main.cpp:1146`). On UZDoom that is the
watched player's real setting. On a Zandronum client it is only the local copy, which is seeded
from the viewer's own `fov` cvar when the player spawns (see below).

**Zandronum 3.2.1:** `fov` is not a cvar there. It was a `CCMD (fov)` (`src/c_cmds.cpp` at
`28f736fb3`) taking a whole-degree integer clamped to 5-179, with no config persistence. The cvar
arrived after 3.2.1 in commit `8401defe5`, `sv_minfov`/`sv_maxfov` in `69a79af2f`, and the
`CVAR_UNSYNCED_USERINFO` flag on it in `7de15ffb4`; none is an ancestor of the 3.2.1 bump.

Two independent clamps then apply on top of that shared value: a `SetFOV`-level clamp (Zandronum:
`sv_minfov`/`sv_maxfov`, server-configurable, default 5°/179°; UZDoom: hardcoded `5.f`/`179.f`, not
configurable — see "Zandronum-specific" below) and, underneath that, a renderer-level hard clamp of
**5° to 170°** (`R_SetFOV`, identical on both engines — see "Effective range" below) that is the
true effective limit regardless of what the cvar-level clamp lets through.

## Default and scope

**Default:** 90° (standard Doom field of view — not 100 as the wiki inventory row states; this is
a wiki documentation error). Confirmed identical on UZDoom (`src/playsim/p_user.cpp:110`).

On Zandronum this cvar is marked `CVAR_ARCHIVE | CVAR_USERINFO | CVAR_UNSYNCED_USERINFO |
CVAR_NOINITCALL`; on UZDoom it's `CVAR_ARCHIVE | CVAR_USERINFO | CVAR_NOINITCALL`
(`src/playsim/p_user.cpp:110`) — `CVAR_UNSYNCED_USERINFO` doesn't exist as a flag on UZDoom at all
(grepped absent tree-wide). On Zandronum, `CVAR_UNSYNCED_USERINFO` keeps the value off the wire:
the client skips it when writing `CLC_USERINFO` to the server (`src/cl_commands.cpp:163`, `:247`),
and the `playerinfo` console command prints it as `<unknown>` for a *different* player or on the
server (`src/d_netinfo.cpp:1720-1724`). No server command carries a player's FOV either. Online, a
Zandronum client's FOV is therefore local: `SetFOV` sets the console player's `DesiredFOV` directly
in client mode (`src/p_user.cpp:712-713`), and every player a client spawns gets `DesiredFOV`/`FOV`
from that client's own `fov` cvar (`src/cl_main.cpp:3861`; server and offline spawns do the same
from the local cvar, `src/p_mobj.cpp:5556`). So spectating another player on Zandronum renders at
the spectator's own FOV, not the watched player's setting. Whether an equivalent per-player
info-query command exists on UZDoom, and whether it would surface `fov`, wasn't traced this pass.

## Zandronum-specific: server-configurable FOV limits

`sv_minfov`/`sv_maxfov` (`src/sv_main.cpp:436`, `:462`) are server-configurable `CUSTOM_CVAR`s that
clamp each connecting client's effective cvar-level FOV range, default 5°/179°. Each self-clamps
against the other: `sv_minfov` can't go below 5° or reach/exceed `sv_maxfov`; `sv_maxfov` can't
exceed 179° or reach/fall below `sv_minfov`. UZDoom has no equivalent cvars — its
`player_t::SetFOV` (function at `src/playsim/p_user.cpp:758`, clamp at `:779`) clamps directly to a
hardcoded `5.f`/`179.f`, which happens to match Zandronum's *defaults* but isn't adjustable by a
server operator. Both cvars were added after 3.2.1 (commit `69a79af2f`); a 3.2.1 build hardcodes
5/179 like UZDoom.

## Engine-family divergence: network FOV precision

Zandronum's `DEM_MYFOV` command truncates the clamped FOV to a whole-degree `BYTE`
(`Net_WriteByte((BYTE)clamp<float>(fov, sv_minfov, sv_maxfov))`, `src/p_user.cpp:718`) before
sending it; UZDoom sends the full float (`Net_WriteFloat(clamp<float>(fov, 5.f, 179.f))`,
`src/playsim/p_user.cpp:779`). A fractional FOV (e.g. `92.5`) survives the network round-trip
un-truncated on UZDoom but gets rounded down to a whole degree on Zandronum wherever `DEM_MYFOV`
actually runs, i.e. offline. Online the byte is never applied, and the client-mode direct
assignment (`src/p_user.cpp:713`) keeps the fraction locally.

## Effective range

The cvar itself is an unclamped `Float` with no local range restriction — the only limits are the
two layered clamps described in the intro. Putting the numbers together: a client or server can
set/allow up to 179° at the cvar level, but the renderer's own hard clamp caps the actually
displayed FOV at **170°** regardless, on both engines identically (Zandronum
`src/r_utility.cpp:362`; UZDoom `src/rendering/r_utility.cpp:201` — same `5.f`/`170.f` literals).
The effective floor is 5°, enforced at both layers on both engines.
