# `instagib`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes — a Zandronum/Skulltag-lineage server game-mode modifier; UZDoom/GZDoom has no `instagib` cvar or built-in Instagib mode (see "Zandronum-specific" below).
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum source `src/gamemode.cpp` (CVAR declaration showing `CVAR_SERVERINFO | CVAR_LATCH | CVAR_CAMPAIGNLOCK | CVAR_GAMEPLAYSETTING`). Rail-only damage override: `src/p_map.cpp:4835,4956-4958` (`P_RailAttack`). Unlatch point: `src/g_level.cpp:188-235,336-348,441,447` (`map` ccmd, `G_DoNewGame`, `G_InitNew`), `src/c_cvars.cpp:303-313`. Client sync: `src/sv_commands.cpp:2498-2505`, `src/sv_main.cpp:1535,7051`.

Enables or disables the Instagib game mode modifier. It has two separate effects with different gating:

- **Loadout (deathmatch or team games only).** A `DoomPlayer` spawns with the `Railgun` (or its DECORATE replacement) as its ready weapon, with that weapon's ammo filled to `MaxAmount`, and the class's normal starting items are skipped (`src/p_user.cpp:1679-1694`). `Railgun` is defined in the `skulltag_actors` content package, not the base engine; without it the engine stops with `I_Error` "Tried to play instagib without a railgun!". Map items flagged `MF_SPECIAL` (pickups) are also removed at level setup, except CTF/Skulltag team items (`src/p_setup.cpp:3564-3574`).
- **Rail damage (any game mode, server side).** While `instagib` is true, every rail attack deals a fixed `999` damage to each actor it hits (`src/p_map.cpp:4956-4958`, inside `P_RailAttack`). This covers `A_FireRailgun`, `A_RailAttack`, `A_CustomRailgun` and monster rail attacks alike. `A_FireRailgun` itself picks `1000` under instagib (vs. `75` in ordinary deathmatch and `200` otherwise; `src/g_doom/a_doomweaps.cpp:882-889`), but `P_RailAttack` overrides that to `999` per victim. Bullet hitscan (`P_LineAttack`) is not affected. `999` is ordinary damage, not telefrag magnitude, so damage factors and protection still apply.

**Default:** false (disabled).

## Critical netcode semantic: CVAR_LATCH

This cvar is marked `CVAR_LATCH`. Setting it while a level is running does not change the value. The new value is queued (`src/c_cvars.cpp:303-313`) and the console prints "instagib will be changed for next game." (`src/c_cvars.cpp:1861-1867`).

The queue is applied only by the two `UnlatchCVars()` calls in `G_InitNew()` (`src/g_level.cpp:441,447`, skipped on clients). `G_InitNew()` runs when a new game starts: the `map` command (`src/g_level.cpp:188-235`, via `G_DoNewGame`), startup, map-rotation start, loading a save, or a single-player death reload. It does **not** run on `changemap` or an ordinary level exit, which go through `G_ChangeLevel` and `G_DoLoadLevel`. So a queued `instagib` change waits for the next `map` command, not the next map in rotation.

The latch is bypassed in some cases. It does not apply while `gamestate` is `GS_FULLCONSOLE` or `GS_STARTUP`. Engine code that sets the modifier directly (`GAMEMODE_SetModifier`, a campaign map's `instagib` setting at `src/g_level.cpp:1286-1289`, and the client's handler for the server's game-mode command) uses `ForceSet`, which applies immediately.

Nothing is sent to clients when the value is queued. Clients learn the server's value only from the `SVC_SETGAMEMODE` command (`src/sv_commands.cpp:2498-2505`), which the server sends to each client individually when it connects (`src/sv_main.cpp:1535`) and when it authenticates each new level (`src/sv_main.cpp:7051`).

(The `CVAR_LATCH` flag's own source comment, identical in both Zandronum's and UZDoom's `c_cvars.h`, is "save changes until server restart". Taken literally that is misleading. The unlatch point is `G_InitNew()` in both engines (Zandronum `src/g_level.cpp:441,447`; UZDoom `src/g_level.cpp:572,591`), which runs on every new game, not only on a process restart and not on every level change. This applied behavior is identical between the two engines even though `instagib` itself only exists on Zandronum.)

## Server and campaign scope

As `CVAR_SERVERINFO | CVAR_CAMPAIGNLOCK | CVAR_GAMEPLAYSETTING`:
- **`CVAR_SERVERINFO`**: a server-side setting. For `instagib` the generic serverinfo path sends nothing (it only sends `CVAR_MOD` cvars); the value reaches clients through `SVC_SETGAMEMODE` as described above.
- **`CVAR_CAMPAIGNLOCK`**: while a campaign is active and `sv_cheats` is off, setting it is refused with "instagib cannot be changed during a campaign." (`src/c_cvars.cpp:229-236`).
- **`CVAR_GAMEPLAYSETTING`**: the cvar is eligible to be set (and locked) from a map's `GAMEMODE` lump "game settings" block (`src/gamemode.cpp:309-319`) — cvars without this flag are rejected there with a script error. When the current game mode locks it and `sv_cheats` is off, setting it is refused with "instagib cannot be changed in this game mode." (`src/c_cvars.cpp:283-287`). *(Corrected: this is not a menu-visibility flag as the previous wording implied.)*

Clients cannot change this cvar locally — the server is authoritative. A client with RCON access has its change forwarded to the server instead.

## Zandronum-specific: Instagib game mode

UZDoom/GZDoom has no `instagib` cvar, no `MODIFIER_INSTAGIB` concept, and none of the surrounding server game-mode-modifier infrastructure this cvar depends on. `CVAR_CAMPAIGNLOCK`, `CVAR_GAMEPLAYSETTING` and the `GAMEMODE` lump don't exist there at all. This is Zandronum/Skulltag-lineage server functionality with no UZDoom counterpart, not merely a differently-implemented equivalent. A UZDoom-based mod wanting instagib-style play would need to build it itself (e.g. a ZScript event handler forcing hitscan damage, gated on a mod-defined cvar) rather than relying on an engine cvar.
