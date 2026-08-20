# `sv_defaultdmflags`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes — no UZDoom/GZDoom-family equivalent found; see "Zandronum-specific" section below.
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) and game-mode initialization logic in `src/*.cpp` (mode-specific dmflags preset).

When enabled, automatically sets certain dmflags appropriate to the current game mode, without requiring manual cvar configuration.

## Zandronum-specific: no UZDoom/GZDoom-family equivalent

`sv_defaultdmflags` and the function it drives, `GAME_SetDefaultDMFlags()`, are Zandronum-only. A full-tree search of the local UZDoom checkout turns up no `sv_defaultdmflags` cvar and no equivalent "auto-configure dmflags from the active gametype" logic anywhere in `src/g_game.cpp` or elsewhere. This tracks with what the mechanism does: it auto-configures dmflags for Zandronum/Skulltag-lineage gametype cvars (`teamgame`, `duel`, CTF/Skulltag/one-flag modes) that don't have a matching concept in the GZDoom-family engine's multiplayer model.

## Automatic dmflags per game mode

When `sv_defaultdmflags` is true, `GAME_CheckMode()` calls `GAME_SetDefaultDMFlags()` (`src/g_game.cpp:2815-2846`) once per map load — skipped entirely while `CAMPAIGN_InCampaign()` is true (`g_game.cpp:3022`):

- **Deathmatch, non-duel** — plain deathmatch, CTF, Skulltag, one-flag CTF, and other team games (anything with `deathmatch` or `teamgame` true and `duel` false):
  - Weapons stay enabled (`DF_WEAPONS_STAY`)
  - Items respawn (`DF_ITEMS_RESPAWN`)
  - Monsters disabled (`DF_NO_MONSTERS`)
  - Crouching disabled (`DF_NO_CROUCH`)
  - Players spawn farthest from other players (`DF_SPAWN_FARTHEST`)
  - Double ammo (`DF2_YES_DOUBLEAMMO`)

- **Duel mode** (`deathmatch` and `duel` both true):
  - Same as above **except** `DF_SPAWN_FARTHEST` is deliberately left unset. The source comment at `g_game.cpp:2822` reads "Don't do 'spawn farthest' for duels." **Correction:** an earlier version of this note had this backwards, claiming duel adds spawn-farthest on top of plain deathmatch. It's the reverse: only non-duel deathmatch/team games get `DF_SPAWN_FARTHEST`; duel specifically excludes it.

- **Cooperative modes** (neither `deathmatch` nor `teamgame`):
  - The evident intent is to clear `DF_WEAPONS_STAY`, `DF_ITEMS_RESPAWN`, `DF_NO_MONSTERS`, `DF_NO_CROUCH` from `dmflags`, and `DF2_YES_DOUBLEAMMO` from `dmflags2`. The `dmflags2` clear works as written (`flags2 &= ~DF2_YES_DOUBLEAMMO;`, `g_game.cpp:2838`).
  - **The `dmflags` clear is a no-op due to an operator-precedence bug in the source.** The line is `flags &= ~DF_WEAPONS_STAY | ~DF_ITEMS_RESPAWN | ~DF_NO_MONSTERS | ~DF_NO_CROUCH;` (`g_game.cpp:2837`). Unary `~` binds tighter than binary `|`, so this parses as `flags &= ((~A) | (~B) | (~C) | (~D))`, which by De Morgan's law equals `flags &= ~(A & B & C & D)`. `DF_WEAPONS_STAY`, `DF_ITEMS_RESPAWN`, `DF_NO_MONSTERS`, and `DF_NO_CROUCH` are distinct, non-overlapping single bits (`1<<2`, `1<<14`, `1<<12`, `1<<22` respectively, per `src/doomdef.h`), so `A & B & C & D` is always `0`, making the mask always `0xFFFFFFFF` — the `&=` changes nothing. In practice, switching to cooperative through this mechanism leaves whatever `DF_WEAPONS_STAY`/`DF_ITEMS_RESPAWN`/`DF_NO_MONSTERS`/`DF_NO_CROUCH` bits `dmflags` already had (e.g. carried over from a prior deathmatch map, or set explicitly by the server operator) untouched, rather than clearing them as the surrounding code's own intent implies. This is a plain bug in Zandronum's own source, not a cross-engine or wiki-vs-engine divergence.

When false, dmflags are not automatically adjusted; the server uses whatever values are explicitly set via `dmflags`/`dmflags2` or map-specific MAPINFO settings.

## Rationale and convenience

This cvar simplifies game-mode setup: a server operator can enable deathmatch by setting a gametype cvar (e.g., `sv_gametype deathmatch`) and let `sv_defaultdmflags` automatically configure standard weapons-stay, respawn-items, and no-monsters behavior, rather than manually setting dmflags each time.

Map-specific MAPINFO flags still take precedence where they exist (depending on other cvar settings like `sv_usemapsettingswavelimit`).

## Storage and replication

**Correction:** this cvar carries no flags at all. The declaration is `CVAR( Bool, sv_defaultdmflags, false, 0 )` (`src/sv_main.cpp:272`) — the trailing `0` is the flags argument. It is not `CVAR_ARCHIVE` (not saved to the server config), not `CVAR_SERVERINFO` (not sent to clients / not added to serverinfo), and not `CVAR_GAMEPLAYSETTING` (not exposed as a GAMEMODE-lump-configurable gameplay setting) — despite directly controlling gameplay-rule bitfields. A server operator has to set it explicitly every session (e.g. via an autoexec or server-config `set` command); it does not persist across restarts, and clients have no visibility into whether it's enabled.

## Related cvars and flags

- **`dmflags`** / **`dmflags2`** / **`zadmflags`** — the actual gameplay-rule bitfields that this cvar may populate automatically.
- **`sv_usemapsettingswavelimit`** — similar "use map settings" control for wave limits in invasion/survival modes.
- **`sv_usemapsettingspossessionholdtime`** — similar "use map settings" control for possession-mode hold time.

See `console/concepts/dmflags.md` for detailed explanation of individual dmflags, 2-bit fields, and engine-family divergence.
