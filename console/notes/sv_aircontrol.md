# `sv_aircontrol`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/p_user.cpp` (CUSTOM_CVAR declaration) and `src/g_level.cpp` (fixed-point conversion logic).

Controls the player's ability to steer/adjust direction while airborne (e.g., during jumps or falling). Higher values increase air-steer responsiveness; 0 disables mid-air steering entirely. The cvar itself, its default, and the falling-friction formula it feeds are shared between both engines — see the divergence sections below for where the two engines actually differ: how the value is represented internally, one cvar flag, and — the largest practical difference — whether the cvar's value is even consulted for movement input by default.

## Value encoding and units

The default value **`0.00390625`** equals `1/256` as a floating-point multiplier. On Zandronum, the engine converts this to a fixed-point representation by multiplying by 65536 (`src/g_level.cpp:2034`, `2075`), representing fractions with 16 bits of decimal precision; `level.aircontrol` is stored as a `fixed_t` (`src/g_level.h:455`). See "Engine-family divergence" below for how UZDoom differs.

This small default value provides very limited air control — it's roughly equivalent to classic Doom behavior, where players have minimal directional influence while airborne. The default of `1/256` is a legacy choice for gameplay balance; increasing it (e.g., to `0.01` or higher) makes players much more maneuverable in the air. On both engines, the falling-friction formula that scales existing horizontal velocity while airborne (as opposed to the movement-input scaling covered below) uses the same threshold and coefficients: friction is left at 1 (no extra decay) when `aircontrol <= 1/256`, and otherwise computed as `aircontrol * -0.0941 + 1.0004` (Zandronum: `G_AirControlChanged`, `src/g_level.cpp:2191-2203`; UZDoom: `FLevelLocals::AirControlChanged`, `src/g_level.cpp:2056-2066`).

## Engine-family divergence: value representation and cvar flags

Zandronum stores `level.aircontrol` as a 16.16 `fixed_t` and converts the float cvar into it by multiplying by 65536 (see above). UZDoom stores the equivalent field, `FLevelLocals::aircontrol`, as a plain `double` (`src/g_levellocals.h:731`) and never performs a fixed-point conversion at all — `FLevelLocals::Init` and the cvar's callback both just assign the float value straight across (`src/g_level.cpp:1934`; `src/playsim/p_user.cpp:1381-1384`). The two representations produce the same practical numeric results (both are precise enough for this cvar's range), so this is an implementation detail, not a behavioral difference — but a reader tracing the code on UZDoom will not find any `* 65536` conversion, since it doesn't exist there.

The cvar's flags also differ in one respect each direction. Zandronum's declaration is `CUSTOM_CVAR (Float, sv_aircontrol, 0.00390625f, CVAR_SERVERINFO|CVAR_NOSAVE|CVAR_GAMEPLAYSETTING)` (`src/p_user.cpp:2978`); UZDoom's is `CUSTOM_CVAR (Float, sv_aircontrol, 0.00390625f, CVAR_SERVERINFO|CVAR_NOSAVE|CVAR_NOINITCALL)` (`src/playsim/p_user.cpp:1381`). `CVAR_SERVERINFO` and `CVAR_NOSAVE` are shared and behave the same on both (see "Network and storage" below). `CVAR_GAMEPLAYSETTING` exists only on Zandronum's declaration; it lets a game mode lock the cvar against being changed (`GAMEMODE_IsGameplaySettingLocked`, checked in `C_CVar::SetGenericRepDefault`-adjacent code at `src/c_cvars.cpp:283`) — UZDoom has no equivalent lock mechanism for this cvar. `CVAR_NOINITCALL` appears only on UZDoom's declaration; it suppresses the callback firing once at cvar registration (harmless either way here, since `FLevelLocals::Init` already assigns `aircontrol` from the cvar explicitly on level start).

## Zandronum-specific: `compat_limited_airmovement`

This entire mechanism is Zandronum-only, inherited from Skulltag's `zacompatflags` compatibility-flag system. It has no equivalent cvar, flag, or code path on UZDoom.

**Correction to a prior claim on this page:** the relationship between this flag and `sv_aircontrol` is the reverse of what an earlier revision of this doc said. By default (`compat_limited_airmovement` unset), Zandronum does **not** consult `sv_aircontrol` for movement-input scaling at all: while airborne, `movefactor`/`bobfactor` are instead divided by a fixed `4` — a Skulltag-era change described in-source as needed "for jump pads, etc." Only when a map or server explicitly sets `compat_limited_airmovement` does the engine switch to multiplying `movefactor`/`bobfactor` by `level.aircontrol` instead (`src/p_user.cpp:3078-3086`, inside `P_MovePlayer`; the flag itself is `ZACOMPATF_LIMITED_AIRMOVEMENT`, `src/doomdef.h:499`, declared as a compat cvar in `src/d_main.cpp` — no line number cited since this checkout's `src/d_main.cpp` carries local uncommitted changes per `git status`, though the surrounding diff hunks don't touch this declaration's immediate vicinity). So the flag does not "restrict" the cvar's effect on movement input — it is what turns that effect **on** in the first place. Without it, `sv_aircontrol`'s value only ever affects the falling-friction decay described above, never air-steering input, regardless of how high it's set.

UZDoom has no such gate. Its `PlayerPawn.MovePlayer` (ZScript, `wadsrc/static/zscript/actors/player/player.zs:1359`) unconditionally calls a virtual `ApplyAirControl(movefactor, bobfactor)` method whenever the player is airborne; the base implementation (same file, `:1309-1313`) multiplies both by `level.aircontrol` directly, with no compat flag and no `/4` fallback branch. `sv_aircontrol`'s value therefore always governs air-steering input on UZDoom, and a `PlayerPawn` subclass can even override `ApplyAirControl` to customize the behavior per mod. Net effect: with the shared default `0.00390625`, Zandronum's out-of-the-box air-steering ignores the cvar and uses the fixed `/4` factor, while UZDoom's out-of-the-box air-steering already applies the tiny `1/256` multiplier directly — the two engines' default air-movement feel is not the same despite sharing the same cvar default.

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_NOSAVE` on both engines (plus one engine-specific flag each — see the divergence section above). `CVAR_SERVERINFO` means the value is replicated to clients; `CVAR_NOSAVE` means it doesn't persist to the config file (it must be set per-game or per-server, not globally). This part of the cvar's storage/network behavior is identical between UZDoom and Zandronum.

## Related cvars and flags

- **`compat_limited_airmovement`** — Zandronum-only compatibility flag; see the dedicated section above for what it actually gates (the reverse of what this page previously said) and why UZDoom has nothing equivalent.
- **`sv_gravity`** — another physics cvar affecting vertical movement; works independently of air control on both engines.
