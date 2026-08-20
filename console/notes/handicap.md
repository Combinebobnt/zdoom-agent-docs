# `handicap`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/d_netinfo.cpp:93` + verified against the implementation in `src/d_netinfo.cpp:HandicapChanged()` which shows clamping to `(0, deh.MaxSoulsphere)`.

## Zandronum-specific: conditional spawn-health reduction

Reduces the player's spawn health, but only when a deathmatch-family ruleset is active. In
`APlayerPawn::GiveDefaultInventory()` (`src/p_user.cpp:1610-1639`), spawn health starts as the
player class's own default (`GetDefault()->health` — 100 for the stock `DoomPlayer`), **not**
`MaxSoulsphere`; a prior revision of this doc conflated the two. The handicap subtraction itself
only runs `if (( deathmatch || teamgame || alwaysapplydmflags ) && player->userinfo.GetHandicap())`
(`alwaysapplydmflags` is the `CVAR_SERVERINFO` cvar at `src/doomstat.cpp:52`, default false) — in
plain single-player or untouched co-op, a nonzero `handicap` has no effect on spawn health at all.
When it does apply: `player->health -= handicap`, then floored to a minimum of **1**, not 0 — a
handicap large enough to zero out health still leaves the player alive with 1 HP on spawn, it does
not produce a spawn health of 0.

## Valid range

Two independent clamps apply to the raw cvar value, at different layers:

- **Client-side hard clamp — 0 to 200.** `D_UserInfoChanged()`'s `cvar == &handicap` branch
  (`src/d_netinfo.cpp:917-929`) clamps the local cvar itself to a fixed `[0, 200]` the moment it's
  set (console, config file, or menu), independent of `MaxSoulsphere`. This callback is skipped
  server-side (`if (NETWORK_GetState() == NETSTATE_SERVER) return;` at the top of the function), so
  it only governs a connecting client's own local value.
- **Userinfo-population clamp — 0 to `MaxSoulsphere`.** `userinfo_t::HandicapChanged()`
  (`src/d_netinfo.cpp:787-797`) re-clamps to `(0, deh.MaxSoulsphere)` whenever the userinfo struct
  actually used for gameplay is (re)built from the cvar — at `D_SetupUserInfo()` and whenever the
  server or client processes an incoming userinfo change (`src/sv_main.cpp:2332`,
  `src/cl_main.cpp:4356`). This is the clamp that governs the value `GetHandicap()` returns for the
  spawn-health calculation above.

By default in standard (non-DEHACKED) Doom, `MaxSoulsphere` is **200**, not 100 — confirmed at
`src/d_dehacked.cpp:216`'s default `DehInfo` struct (`StartHealth` is the one that defaults to 100,
a distinct field). A prior revision of this doc stated 100 for `MaxSoulsphere`; that was a
transposition with `StartHealth` and has been corrected here. The 0–`MaxSoulsphere` range still
changes if the IWAD or a loaded DEHACKED lump redefines `MaxSoulsphere`, but in practice the tighter
client-side `[0, 200]` clamp is usually the one actually limiting what a player can type in, since
200 is also `MaxSoulsphere`'s own default.

The scoreboard's handicap display column (`COLUMNTYPE_HANDICAP`, `src/scoreboard.cpp:1736-1748`)
computes an *approximation* of resulting health for display purposes using `deh.StartHealth` (or,
in Last Man Standing, a mix of `MaxSoulsphere`/`MaxArmor`) rather than re-deriving the player
class's actual default health — it can disagree with the real spawn health `GiveDefaultInventory()`
produces and is not itself the authoritative calculation.

## Network and storage

This cvar is marked `CVAR_USERINFO | CVAR_ARCHIVE`, so it's part of the player's network userinfo and persists to the player's config file.

## Engine-family divergence

`handicap` does not exist on UZDoom at all — confirmed absent from the entire checkout (no
`CVAR`/`CUSTOM_CVAR` declaration and no bare mention of the name anywhere in the tree, aside from an
unrelated audio-related string in a translation file). Attempting to set it under UZDoom (console,
config file, or ACS's `ConsoleCommand()`) hits the console dispatcher's unknown-command path
(`src/common/console/c_dispatch.cpp:324`) and prints `Unknown command "handicap"` — a visible
failure at the console, easy to miss from an unattended context like a saved client config. UZDoom
has no self-handicapping spawn-health mechanism of any kind to substitute for it.
