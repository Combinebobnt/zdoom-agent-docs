# `autoaim`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/d_netinfo.cpp:76` and `zandronum/docs/commands.txt` (which describes the actual vertical-distance semantics; the wiki page is corrupted and describes a different system).

Controls the vertical aim-cone (pitch) tolerance the engine's automatic aiming system uses when searching above and below the crosshair for a target. The cvar's face value is nominally degrees, but neither engine reads it raw — both re-derive and clamp it through `userinfo_t::GetAimDist()` at the point of use, not as a literal distance.

## Actual behavior vs. wiki/docs description

**Wiki divergence warning:** The saved wiki page for "Console variables" contains corrupted text where a changelog fragment is spliced into the AutoAim row's description mid-sentence. Its description of a **horizontal** auto-aim precision system with specific degree presets (0°, 0.25°, 1°, 2°, 3°, 35°–56°) does not correspond to anything the `autoaim` cvar drives in either engine's source — see "Zandronum-specific: `compat_autoaim`" below for the one *horizontal* precision mechanism that genuinely exists, under a different name and gated by a different cvar entirely.

**`zandronum/docs/commands.txt`'s plain-English description is also inaccurate**, though it happens to give correct practical guidance despite that. It describes the cvar as a literal vertical-distance threshold ("how far above or below a target the player's sight must be"). The actually-verified source — Zandronum `src/d_player.h:366-382` + `src/p_map.cpp:4065`; UZDoom `src/playsim/d_player.h:188-205` + `src/playsim/p_map.cpp:4550` — shows it is really a **vertical angle (pitch) cone**, in degrees, used as the half-angle `P_AimLineAttack`/`P_BulletSlope` search above and below the crosshair when a shot doesn't hit a wall or an exact target first:

- `GetAimDist()` reads the raw cvar and, if the value falls outside its valid window, substitutes a flat fallback instead of passing the raw value through: Zandronum's window is `[0°, 35°]` with a `35°` fallback; UZDoom's is `[0°, bound]` (`bound` is 35° or 70° — see the engine-family divergence below) with a `bound` fallback.
- The call site clamps the result again — to `[0.5°, 35°]` on Zandronum, `[0.5°, bound]` on UZDoom — before using it as the aim-cone half-angle. **This second clamp has a hard floor of 0.5°, applied unconditionally** — the source comment explains this exists so `toppitch`/`bottompitch` can never be equal, which would break the aim trace entirely. So **setting the cvar to 0 does not fully disable the vertical pitch tolerance** in either engine; a residual 0.5° cone always survives along the exact firing yaw. Only the server-side `sv_noautoaim` flag genuinely gates autoaim as a whole (see "Related cvars" below for what it actually removes vs. leaves behind).
- Zandronum's cvar default, **5000**, is itself outside the `[0°, 35°]` window, so by default `GetAimDist()` always substitutes the flat 35° cap — the 5000 default is a leftover from whatever the value meant before this degree-based clamp existed, never updated to the unit `GetAimDist()` actually treats it as. UZDoom's default, **35**, sits exactly at the cap already. Despite the very different-looking raw defaults, both engines land on the same practical 35° default aim cone (the source comment in both calls this "approximately what Doom used").

**Default:** 5000.0 on Zandronum, 35.0 on UZDoom — see above for why these produce equivalent behavior in practice.

## Engine-family divergence: UZDoom doubles the max aim cone when freelook is allowed

Zandronum's call-site clamp always caps the cone at a fixed `ANGLE_1 * 35` (35°) whenever a player is autoaiming with freelook allowed (`src/p_map.cpp:4065`); the branch that reaches this clamp is gated by `t1->player != NULL && level.IsFreelookAllowed()` (`src/p_map.cpp:4047`).

UZDoom's equivalent branch is gated the same way (`t1->player != NULL && t1->Level->IsFreelookAllowed()`, `src/playsim/p_map.cpp:4531`), but its clamp ceiling is `bound = (dmflags & DF_NO_FREELOOK) ? 35 : 70` (`src/playsim/p_map.cpp:4549`, used at `:4550`) — nominally conditional on the raw `DF_NO_FREELOOK` bit. In practice this ternary's `35` branch is unreachable at that point: UZDoom's `IsFreelookAllowed()` (`src/g_levellocals.h:855-862`) checks `DF_NO_FREELOOK` *first* and returns `false` immediately if it's set, so the outer branch's `IsFreelookAllowed()` guard has already excluded that case before code reaches the `bound` ternary. So whenever UZDoom's freelook-allowed branch actually executes, `bound` is always **70°** — double Zandronum's fixed 35° ceiling for the equivalent case. (Zandronum's own `IsFreelookAllowed()`, `src/g_level.cpp:2156-2163`, checks map-level `LEVEL_FREELOOK_YES`/`_NO` flags before `DF_NO_FREELOOK`, an ordering difference from UZDoom's — but it doesn't affect this divergence, since Zandronum's clamp ceiling isn't conditional on the dmflag at all.)

A player can still dial the effective cone down below whichever ceiling applies via the `autoaim` cvar itself on either engine; only the *ceiling* a high cvar value saturates to differs.

## Network and storage

This cvar is marked `CVAR_USERINFO | CVAR_ARCHIVE` on both engines, so it's part of the player's network userinfo and persists to the config file.

## Related cvars

- **`sv_noautoaim`** — a server-side flag (`DF2_NOAUTOAIM` in `dmflags2`) present and identical on both engines. It makes `GetAimDist()` return 0 outright. Its practical effect differs by axis: `P_BulletSlope`'s candidate-angle loop breaks immediately after its first (dead-center) try once `GetAimDist() <= 0.5°` (Zandronum `src/p_pspr.cpp:1314-1319`; UZDoom `src/playsim/p_pspr.cpp:1273-1278`), so the *horizontal* near-miss search across the wider angle table is skipped entirely — but that one dead-center trace still goes through the vertical clamp's unconditional 0.5° floor (see above), so a residual 0.5° *vertical* pitch tolerance survives along the exact firing yaw even with this flag set.
- **`cl_doautoaim`** — present and identical on both engines, but its actual effect is narrower than "applies autoaiming at all": `src/p_map.cpp:3865` (Zandronum) / `src/playsim/p_map.cpp:4353-4354` (UZDoom) show it only overrides the exclusion of actors flagged `MF6_NOTAUTOAIMED` from autoaim consideration. With it false (the default), such actors are skipped by autoaim regardless of the `autoaim` cvar's value; with it true, they're eligible like any other actor. It doesn't gate autoaim as a whole.
- **`compat_autoaim`** — Zandronum-only; see the dedicated section below. No equivalent cvar, flag, or constant exists in UZDoom.

## Zandronum-specific: `compat_autoaim` widens the bullet-slope search

`compat_autoaim` (declared `CVAR (Flag, compat_autoaim, zacompatflags, ZACOMPATF_AUTOAIM)` in `src/d_main.cpp` — no line number cited here since this checkout's `d_main.cpp` carries local uncommitted changes, per the version-control check above; the declaration itself is untouched by that diff, backed by the `ZACOMPATF_AUTOAIM` bit of `zacompatflags`, default off) is a distinct, Zandronum-only mechanism that also affects autoaim but does not read the `autoaim` cvar at all. It gates how many candidate angles `P_BulletSlope` (`src/p_pspr.cpp:1290-1320`) tries when searching for a near-miss target for hitscan weapons: with the flag off (default), the search walks a wider 15-entry table of angle offsets, including several small `AUTOAIM_MINANGLE` increments (`src/p_pspr.cpp:53`) added by a later patch; with the flag on, the search stops short of those finer increments, reproducing the older, narrower search. This is the one place a horizontal precision-style autoaim adjustment genuinely exists in Zandronum — closer in spirit to what the corrupted wiki page describes than the `autoaim` cvar itself is — but it's a separate compatibility toggle with its own cvar, not a mode of `autoaim`. UZDoom has no `compat_autoaim`, `ZACOMPATF_AUTOAIM`, or `AUTOAIM_MINANGLE` equivalent; its own `P_BulletSlope` (`src/playsim/p_pspr.cpp:1256-1280`) always uses one fixed table.
