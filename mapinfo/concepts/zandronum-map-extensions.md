# Zandronum map-definition extensions

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25) — note that some properties postdate the Zandronum 3.2.1 release; see "Version availability" below
**Provenance:** Zandronum Wiki [`MAPINFO`](https://wiki.zandronum.com/w/index.php?title=MAPINFO&oldid=2514) (retrieved 2026-09-09) + verified against Zandronum engine source (`src/g_mapinfo.cpp`, `src/g_level.h`; corrections from `src/g_mapinfo.cpp:1379-1381`, `src/p_setup.cpp:4364-4373`, `src/duel.cpp:108-110`, `src/wi_stuff.cpp:450-456`, `src/teaminfo.cpp:75-93`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

## Zandronum-specific: Map-definition extensions

Zandronum extends MAPINFO's `map` definition block with several properties unavailable in UZDoom/GZDoom-family engines. These fall into two categories: multiplayer/campaign features (`islobby`, `nobotnodes`), and intermission customization (`gamemode`, `winnerpic`, `loserpic`, `winnermusic`, `losermusic`).

## Multiplayer and campaign properties

### `islobby` / `lobby`

**Marks a map as a lobby**, invoking special behaviors used in multiplayer campaign mode. A lobby is a matchmaking/intermission map, not a playable level. The behaviors include:

- In duel, the pre-duel countdown and map reset are skipped; the duel starts immediately. Other modes' countdowns (e.g. LMS) are not skipped at this checkout.
- Bots already in the game are removed at map setup (`P_SetupLevel`, which checks the `LEVEL_ZA_ISLOBBY` flag directly, so the `lobby` cvar route below does not trigger it).
- Teams are cleared on map start, even with `ZADF_YES_KEEP_TEAMS` set.
- Exiting the map does not kill the player when `DF_NO_EXIT` is set.
- Time limits are disabled (`GAMEMODE_IsTimelimitActive()` returns false).

Two key names exist: `islobby` is the original form; `lobby` is an alias with identical behavior, and the source comments mark it as the preferred spelling (both set the `LEVEL_ZA_ISLOBBY` flag). Additionally, the `lobby` console cvar can name a default lobby map by name, so `GAMEMODE_IsLobbyMap()` checks both the flag and whether the current map matches that cvar value.

**Availability:** Pre-3.2.1 (in early Zandronum forks, ported with the ZDoom MAPINFO merge).

### `nobotnodes`

**Disables bot-node generation on the current level.** When disabled, Zandronum's pathfinding bots cannot navigate the map and will not spawn. This is useful for very large or structurally complex maps where generating a full node tree is impractical or causes performance issues.

Internally, disabling bot nodes is implemented by setting the `LEVEL_ZA_NOBOTNODES` flag. When it is set, `P_SetupLevel` skips its `ASTAR_BuildNodes()` call (otherwise made only outside client mode and when bots are already in game) and removes all bots, and the `addbot` console command refuses with a message.

**Availability:** Pre-3.2.1 (in early Zandronum forks, ported with the ZDoom MAPINFO merge).

## Intermission and game-mode customization

### `gamemode = "<gamemode>"`

**Locks the map to a specific game mode** (deathmatch, team deathmatch, LastManStanding, Survival, CTF, Domination, etc., depending on the Zandronum build's supported modes). When a map is loaded, if its `gamemode` property is set and the current game mode differs, Zandronum automatically calls `GAMEMODE_SetCurrentMode()` to switch to the locked mode. The game mode must be a valid `GAMEMODE_e` enum value, given as a string without the `GAMEMODE_` prefix. It is case-insensitive: `MustGetEnumName(..., "GAMEMODE_", ...)` prepends the prefix and upper-cases the name, and an unknown name is a script error.

Two more parse-time script errors: `gamemode` requires the new (braced) MAPINFO format, and a map whose campaign information forces a different game mode is rejected.

Default: `NUM_GAMEMODES` (not locked; map plays in whatever mode is current).

**Availability:** 3.3-alpha and above only (postdates Zandronum 3.2.1; added in `7aa633182`).

### `winnerpic = "<picname>"` / `loserpic = "<picname>"`

**Customizes the intermission background graphic** shown to players after the map ends, depending on whether the console player won or lost. They are used only in the Doom game type, only in deathmatch or team-game modes (classic deathmatch included; cooperative excluded), and only while the `ZACOMPATF_OLDINTERMISSION` compat flag is off. Otherwise the normal `INTERPIC` is used.

Both keys accept lump names (8-character identifiers or longer names) for flat/patch graphics. The engine checks for a team-specific override first (the `WinnerPic` / `LoserPic` keys of the `TEAMINFO` lump, used only when the player is on a team); if none exists, the map-level property is used as a fallback. If the chosen graphic does not exist (and is not a `$`-prefixed name), the engine falls back to `INTERPIC`.

Defaults: `winnerpic` defaults to `"WINERPIC"`; `loserpic` defaults to `"LOSERPIC"`. Zandronum itself ships neither lump, so the defaults show `INTERPIC` unless a mod supplies them.

**Availability:** 3.3-alpha and above only (postdates Zandronum 3.2.1; added in `95735f243`).

### `winnermusic = "<musicname>"` / `losermusic = "<musicname>"`

**Customizes the intermission music** played during the victory or defeat intermission screen. These properties work like `winnerpic` and `loserpic`, with the same game-type, game-mode and compat-flag gating: the map-level setting is consulted after checking for team-specific overrides (the `WinnerTheme` / `LoserTheme` keys of the `TEAMINFO` lump).

Both keys accept a music name (e.g., `"d_stwin"`, `"d_stlose"`) with an optional track number, written either after a colon inside the string (`"d_stwin:1"`) or as a separate number after it (`"d_stwin" 1`), as with other MAPINFO music keys. If the resolved name is still the map-level value and no music lump of that name exists, the engine falls back to the normal intermission music.

Defaults: `winnermusic` defaults to `"d_stwin"`; `losermusic` defaults to `"d_stlose"`.

**Availability:** 3.3-alpha and above only (postdates Zandronum 3.2.1; added in `95735f243`).

## Version availability

Properties documented in this section are available on different Zandronum release lines:

| Property | Availability |
|---|---|
| `islobby` / `lobby` | Pre-3.2.1 (early Zandronum forks / ZDoom MAPINFO merge) |
| `nobotnodes` | Pre-3.2.1 (early Zandronum forks / ZDoom MAPINFO merge) |
| `gamemode` | 3.3-alpha and above only (`7aa633182`) |
| `winnerpic` / `loserpic` | 3.3-alpha and above only (`95735f243`) |
| `winnermusic` / `losermusic` | 3.3-alpha and above only (`95735f243`) |

Maps targeting Zandronum 3.2.1 or earlier should not use the `gamemode`, `winnerpic`, `loserpic`, `winnermusic`, or `losermusic` properties. Older clients skip them, but not silently: each prints a red "Unknown property ... found in map definition" script error to the console. The `islobby` / `lobby` and `nobotnodes` properties are safe to use on 3.2.1 and later.

## Interaction with GameInfo custom data

Custom player scoreboard columns (`AddCustomData` in the `gameinfo` block) are accessible in ACS via `GetPlayerData()` / `SetPlayerData()` during round-based game modes, including lobbies. See [`gameinfo-block.md`](gameinfo-block.md)'s Zandronum-specific keys section for the `AddCustomData` property and its type constraints.

## Cross-engine divergence note

None of these properties exist in UZDoom/GZDoom-family engines; they are Zandronum-only extensions. A map using any of these keys will silently ignore them on UZDoom/GZDoom clients if the keys are encountered, provided the engine's parser recognizes unknown keys without fatal errors (both Zandronum and UZDoom skip unknown properties during MAPINFO parsing, though with different logging behavior).
