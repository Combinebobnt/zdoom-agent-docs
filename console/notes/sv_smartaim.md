# `sv_smartaim`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/p_map.cpp` (CVAR declaration) + verified against engine auto-aim logic.

Controls how the engine's automatic aiming system selects targets, with four modes that trade off between ease-of-use and avoid-friendly-fire safety. The cvar is declared identically on UZDoom: an archived, server-replicated Int defaulting to 0 (Zandronum `src/p_map.cpp:94`; UZDoom `src/playsim/p_map.cpp:66`), with the four-way filtering logic implemented in each engine's aim-trace candidate loop (Zandronum `src/p_map.cpp:3965-3997`; UZDoom `src/playsim/p_map.cpp:4474-4505`) — see "Engine-family divergence" below for the one place the two loops actually disagree.

## Value meanings

- **0 (default):** Auto-aim targets the **nearest shootable actor**, regardless of whether it's a friend, ally, or monster. Classic behavior with no filtering.
- **1:** Tries to **avoid targeting allies and non-monster actors** (e.g., players on friendly fire, breakables), but still aims at them if no pure monsters are available. Moderate friendly-fire avoidance.
- **2:** Auto-aim **never targets friends** (teammates in team mode), only monsters and enemies. Still may target non-monster hazards.
- **3:** Auto-aim **only targets hostile monsters**, avoiding all players and non-hostile actors. Maximum friendly-fire safety.

## Per-actor friendliness determination

Both engines use `AActor::IsFriend()` (Zandronum `src/p_mobj.cpp:7657-7681`; UZDoom `src/playsim/p_mobj.cpp:8266-8285`) as the base friendliness test: two actors are friends only if both carry `MF_FRIENDLY`, and in deathmatch/teamgame it further requires `IsTeammate()` or a matching `FriendPlayer`. The filtering itself runs per-candidate inside each engine's aim-trace loop and respects the `sv_smartaim` value during line-attack and hitscan tracing — but see the divergence below: Zandronum's smart-aim path layers an additional player-vs-player check on top of `IsFriend()` that UZDoom's does not have.

## Interaction with other aiming cvars

- **`autoaim` (client cvar)** — separate cvar controlling the vertical aim-cone (pitch) tolerance used to find candidates in the first place; orthogonal to `sv_smartaim`, which only decides which candidate among those found gets picked. See `console/notes/autoaim.md` for the full breakdown, including a UZDoom-vs-Zandronum divergence in that cone's ceiling.
- **`cl_doautoaim` (client cvar)** — **correction to a prior claim in this file:** this does *not* disable auto-aim entirely. Per `console/notes/autoaim.md`'s verified finding (Zandronum `src/p_map.cpp:3865`; UZDoom `src/playsim/p_map.cpp:4353-4354`, both cited there), it only controls whether actors flagged `MF6_NOTAUTOAIMED` are excluded from autoaim consideration. With it false (the default), such actors are skipped regardless of `sv_smartaim`; with it true, they're eligible like any other actor. It does not gate `sv_smartaim` or autoaim as a whole, on either engine.
- **`sv_noautoaim` (server DMFlag, `DF2_NOAUTOAIM`)** — **correction to a prior claim in this file:** rather than disabling auto-aiming outright, it makes `GetAimDist()` return 0, which collapses the *vertical* aim-cone search but (per `autoaim.md`) still leaves a residual 0.5° cone along the exact firing yaw due to an unconditional floor clamp in both engines. Practically, `sv_smartaim`'s friend/monster preference filtering becomes near-moot once the cone is that narrow (there's rarely more than one candidate left to choose between), but the flag doesn't literally turn `sv_smartaim` off — the candidate-selection code the CVAR controls still runs on whatever the (tiny) cone finds.

## Engine-family divergence: player-vs-player friend exclusion in smart-aim

At `sv_smartaim` values below 2, both engines skip an `IsFriend()`-true candidate rather than targeting it — but Zandronum's smart-aim block adds an extra condition when *both* the shooter and the candidate are players, that UZDoom's does not have:

- Zandronum (`src/p_map.cpp:3969-3973`) only treats a friendly player-vs-player pair as excludable if the candidate is also a teammate of the shooter per `IsTeammate()` (`src/p_mobj.cpp:7568-7591`), or if either side isn't a player at all — i.e., for two players, `IsFriend()` alone isn't enough. An inline `[BB]` comment at that line explains this was added deliberately, as a narrow smart-aim-only carve-out, rather than folded into `IsFriend()` itself.
- UZDoom's equivalent block (`src/playsim/p_map.cpp:4478`) tests `IsFriend()` alone, with no additional player-vs-player teammate check and no call into `IsTeammate()` on this path at all.

In plain cooperative play (no team-based game mode active) the two resolve the same way in practice, because Zandronum's `IsTeammate()` (`src/p_mobj.cpp:7574-7587`) also returns true trivially for two players outside deathmatch/teamgame unless the current game mode sets `GMF_PLAYERSONTEAMS` (`src/gamemode_enums.h:73`) and the two players are on different or no teams. `GMF_PLAYERSONTEAMS` and the team-based game modes that set it (e.g. Zandronum's Skulltag-derived team modes) are Zandronum-only — UZDoom has no equivalent concept, confirmed by an empty grep for `GMF_PLAYERSONTEAMS`/`GAMEMODE_GetCurrentFlags` under UZDoom's `src/`. So the divergence only becomes observable in a Zandronum team-based mode where two players are both `MF_FRIENDLY` toward each other (`IsFriend()` true) but not currently teammates: Zandronum's `sv_smartaim < 2` would *not* exclude that player from being auto-aimed at, while the same scenario on UZDoom (if it could exist there) would be excluded on `IsFriend()` alone.

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_SERVERINFO`, so it persists to the config file and replicates to clients. Server-side enforcement: the value is applied during server-side weapon fire calculations.

## Related cvars

- **`autoaim`** — client-side cvar controlling the vertical aim-cone tolerance auto-aim searches within; see `console/notes/autoaim.md`.
- **`cl_doautoaim`** — client-side boolean; see "Interaction with other aiming cvars" above for its actual (narrower) effect.
