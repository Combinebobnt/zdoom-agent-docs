# `sv_defaultdmflags`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes — no UZDoom/GZDoom-family equivalent found; see "Zandronum-specific" section below.
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) and game-mode initialization logic in `src/*.cpp` (mode-specific dmflags preset); `src/g_game.cpp:2815-2846`, gametype cvar callbacks in `src/team.cpp`/`src/deathmatch.cpp`, skirmish call at `src/menu/multiplayermenu.cpp:314`, `src/campaign.cpp:180-192`.

When enabled, automatically sets certain dmflags appropriate to the current game mode, without requiring manual cvar configuration.

## Zandronum-specific: no UZDoom/GZDoom-family equivalent

`sv_defaultdmflags` and the function it drives, `GAME_SetDefaultDMFlags()`, are Zandronum-only. A full-tree search of the local UZDoom checkout turns up no `sv_defaultdmflags` cvar and no equivalent "auto-configure dmflags from the active gametype" logic anywhere in `src/g_game.cpp` or elsewhere. This tracks with what the mechanism does: it auto-configures dmflags for Zandronum/Skulltag-lineage gametype cvars (`teamgame`, `duel`, CTF/Skulltag/one-flag modes) that don't have a matching concept in the GZDoom-family engine's multiplayer model.

## Automatic dmflags per game mode

When `sv_defaultdmflags` is true, `GAME_CheckMode()` calls `GAME_SetDefaultDMFlags()` (`src/g_game.cpp:2815-2846`) once per map load. It is skipped while `CAMPAIGN_InCampaign()` is true (`g_game.cpp:3022`), which can only happen offline: `CAMPAIGN_AllowCampaign()` returns false on a server (`src/campaign.cpp:180-192`). `GAME_CheckMode()` also returns early on clients. The function only ever ORs bits in (or tries to clear them, for coop); other `dmflags`/`dmflags2` bits are left as they were.

The branches key on the `deathmatch`, `duel` and `teamgame` cvars. Setting a mode cvar forces these: `teamplay`, `duel`, `terminator`, `lastmanstanding`, `teamlms`, `possession` and `teampossession` all set `deathmatch` true (`src/deathmatch.cpp`), while `ctf`, `oneflagctf`, `skulltag` and `domination` set `teamgame` true, and `teamgame` in turn forces `deathmatch` false (`src/team.cpp`).

- **Deathmatch-family, non-duel** (`deathmatch` true, `duel` false: plain deathmatch, team deathmatch, terminator, (team) LMS, (team) possession):
  - Weapons stay enabled (`DF_WEAPONS_STAY`)
  - Items respawn (`DF_ITEMS_RESPAWN`)
  - Monsters disabled (`DF_NO_MONSTERS`)
  - Crouching disabled (`DF_NO_CROUCH`)
  - Players spawn farthest from other players (`DF_SPAWN_FARTHEST`)
  - Double ammo (`DF2_YES_DOUBLEAMMO`)

- **Duel** (`deathmatch` and `duel` both true):
  - Same as above **except** `DF_SPAWN_FARTHEST` is not set. The source comment at `g_game.cpp:2822` reads "Don't do 'spawn farthest' for duels."

- **Team games** (`teamgame` true, so `deathmatch` false: CTF, one-flag CTF, Skulltag, domination):
  - Same set as duel: weapons stay, items respawn, no monsters, no crouch, double ammo. `DF_SPAWN_FARTHEST` is not set (`g_game.cpp:2830-2834`).

- **Cooperative modes** (neither `deathmatch` nor `teamgame`):
  - The evident intent is to clear `DF_WEAPONS_STAY`, `DF_ITEMS_RESPAWN`, `DF_NO_MONSTERS`, `DF_NO_CROUCH` from `dmflags`, and `DF2_YES_DOUBLEAMMO` from `dmflags2`. The `dmflags2` clear works as written (`flags2 &= ~DF2_YES_DOUBLEAMMO;`, `g_game.cpp:2838`).
  - **The `dmflags` clear is a no-op due to an operator-precedence bug in the source.** The line is `flags &= ~DF_WEAPONS_STAY | ~DF_ITEMS_RESPAWN | ~DF_NO_MONSTERS | ~DF_NO_CROUCH;` (`g_game.cpp:2837`). Unary `~` binds tighter than binary `|`, so this parses as `flags &= ((~A) | (~B) | (~C) | (~D))`, which by De Morgan's law equals `flags &= ~(A & B & C & D)`. `DF_WEAPONS_STAY`, `DF_ITEMS_RESPAWN`, `DF_NO_MONSTERS`, and `DF_NO_CROUCH` are distinct, non-overlapping single bits (`1<<2`, `1<<14`, `1<<12`, `1<<22` respectively, per `src/doomdef.h`), so `A & B & C & D` is always `0`, making the mask always `0xFFFFFFFF` — the `&=` changes nothing. In practice, switching to cooperative through this mechanism leaves whatever `DF_WEAPONS_STAY`/`DF_ITEMS_RESPAWN`/`DF_NO_MONSTERS`/`DF_NO_CROUCH` bits `dmflags` already had (e.g. carried over from a prior deathmatch map, or set explicitly by the server operator) untouched, rather than clearing them as the surrounding code's own intent implies. This is a plain bug in Zandronum's own source, not a cross-engine or wiki-vs-engine divergence.

When false, map loads leave `dmflags`/`dmflags2` alone; they keep whatever was set explicitly (offline, a CMPGNINF campaign entry for the map can also set them). Exception: starting an offline skirmish game from the menu calls `GAME_SetDefaultDMFlags()` unconditionally, whatever this cvar says (`src/menu/multiplayermenu.cpp:314`).

## Rationale and convenience

This cvar simplifies game-mode setup: a server operator can pick a mode by setting its gametype cvar (e.g. `deathmatch 1` or `ctf 1`) and let `sv_defaultdmflags` add the standard weapons-stay, respawn-items and no-monsters bits, rather than setting dmflags by hand each time.

## Storage and replication

**Correction:** this cvar carries no flags at all. The declaration is `CVAR( Bool, sv_defaultdmflags, false, 0 )` (`src/sv_main.cpp:272`) — the trailing `0` is the flags argument. It is not `CVAR_ARCHIVE` (not saved to the server config), not `CVAR_SERVERINFO` (not sent to clients / not added to serverinfo), and not `CVAR_GAMEPLAYSETTING` (not exposed as a GAMEMODE-lump-configurable gameplay setting) — despite directly controlling gameplay-rule bitfields. A server operator has to set it explicitly every session (e.g. via an autoexec or server-config `set` command); it does not persist across restarts, and clients have no visibility into whether it's enabled.

## Related cvars and flags

- **`dmflags`** / **`dmflags2`**: the gameplay-rule bitfields this cvar may populate automatically. It never touches **`zadmflags`**.
- **`sv_usemapsettingswavelimit`**: server-side "use map settings" control that takes the invasion wave limit from the map's CMPGNINF entry (`src/g_level.cpp:1617-1626`). Unrelated to dmflags.
- **`sv_usemapsettingspossessionholdtime`**: the same for (team) possession hold time (`src/g_level.cpp:1628-1637`).

See `console/concepts/dmflags.md` for detailed explanation of individual dmflags, 2-bit fields, and engine-family divergence.
