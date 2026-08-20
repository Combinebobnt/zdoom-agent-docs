# `fov`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-16)
**Provenance:** Zandronum source `src/p_user.cpp` (CUSTOM_CVAR declaration) + verified against the implementation, which shows default 90.0 (not 100 as the wiki states).

Sets the player's field of vision in degrees. The value a client sets is genuine shared simulation
state, not purely local: changing it sends a `DEM_MYFOV` network command that both engines apply to
that player's `player_t::DesiredFOV`/`FOV` on every peer (Zandronum `src/d_net.cpp:2412-2413`;
UZDoom `src/d_net.cpp:2929-2930`), and both engines interpolate `DesiredFOV` into `FOV` every tic,
per-player, with the same 7°-smoothing threshold and weapon-`FOVScale` adjustment (Zandronum
`P_PlayerThink`, `src/p_user.cpp` around 3691-3705; UZDoom's equivalent moved to ZScript,
`PlayerPawn::CheckFOV`, `wadsrc/static/zscript/actors/player/player.zs:1025-1044`). Anyone whose
view camera is pointed at that player — chasecam, spectate, a scripted camera actor — renders using
that player's real `FOV` (Zandronum `src/d_main.cpp:891-892`; UZDoom `AActor::GetFOV`,
`src/playsim/p_mobj.cpp:4153-4166`, called from `src/d_main.cpp:1146`). See "Default and scope"
below for what Zandronum's `CVAR_UNSYNCED_USERINFO` flag actually does and doesn't gate.

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
(grepped absent tree-wide). On Zandronum, `CVAR_UNSYNCED_USERINFO` only gates the `playerinfo`
console command's userinfo dump: it makes the raw cvar value print as `<unknown>` when a *different*
player or the server queries it (`src/d_netinfo.cpp:1719-1722`). It does **not** stop the FOV value
itself from being simulated as shared per-player state — see the intro above. A prior revision of
this doc claimed the flag made FOV "purely local" and invisible to other players' view of the
world; that was inaccurate, and has been corrected here. Whether an equivalent per-player info-query
command exists on UZDoom, and whether it would surface `fov`, wasn't traced this pass.

## Zandronum-specific: server-configurable FOV limits

`sv_minfov`/`sv_maxfov` (`src/sv_main.cpp:436`, `:462`) are server-configurable `CUSTOM_CVAR`s that
clamp each connecting client's effective cvar-level FOV range, default 5°/179°. Each self-clamps
against the other: `sv_minfov` can't go below 5° or reach/exceed `sv_maxfov`; `sv_maxfov` can't
exceed 179° or reach/fall below `sv_minfov`. UZDoom has no equivalent cvars — its
`player_t::SetFOV` (function at `src/playsim/p_user.cpp:758`, clamp at `:779`) clamps directly to a
hardcoded `5.f`/`179.f`, which happens to match Zandronum's *defaults* but isn't adjustable by a
server operator.

## Engine-family divergence: network FOV precision

Zandronum's `DEM_MYFOV` command truncates the clamped FOV to a whole-degree `BYTE`
(`Net_WriteByte((BYTE)clamp<float>(fov, sv_minfov, sv_maxfov))`, `src/p_user.cpp:718`) before
sending it; UZDoom sends the full float (`Net_WriteFloat(clamp<float>(fov, 5.f, 179.f))`,
`src/playsim/p_user.cpp:779`). A fractional FOV (e.g. `92.5`) survives the network round-trip
un-truncated on UZDoom but gets rounded down to a whole degree on Zandronum.

## Effective range

The cvar itself is an unclamped `Float` with no local range restriction — the only limits are the
two layered clamps described in the intro. Putting the numbers together: a client or server can
set/allow up to 179° at the cvar level, but the renderer's own hard clamp caps the actually
displayed FOV at **170°** regardless, on both engines identically (Zandronum
`src/r_utility.cpp:362`; UZDoom `src/rendering/r_utility.cpp:201` — same `5.f`/`170.f` literals).
The effective floor is 5°, enforced at both layers on both engines.
