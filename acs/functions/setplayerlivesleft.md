# SetPlayerLivesLeft

**Tier:** A
**Engine:** Zandronum 3.2.1 — added together with `GetPlayerLivesLeft` in the same commit `eac46667c` ("Added new ACS commands GetPlayerLivesLeft and SetPlayerLivesLeft..."), confirmed via `git merge-base --is-ancestor eac46667c 28f736fb3` (the 3.2.1 version-bump commit) to predate 3.2.1, so this is present in the 3.2.1 target, not a later addition.
**Provenance:** `SetPlayerLivesLeft - Zandronum Wiki.html` (wiki `oldid=1333`), verified against the Zandronum source's `src/p_acs.cpp`, `p_interaction.cpp`, and `gamemode.cpp` 2026-07-29.
**Bucket:** Extension function (index -105; `GetPlayerLivesLeft` at -104)

```
bool SetPlayerLivesLeft(int player, int amount)
```

## What it actually does

`p_acs.cpp` `case ACSF_SetPlayerLivesLeft`: if `player` passes `PLAYER_IsValidPlayer()`, calls
`PLAYER_SetLivesLeft(&players[player], (ULONG)amount)` and returns `1` (true); otherwise returns
`0` (false) without touching anything. Same validity gate as `GetPlayerLivesLeft` — see
`functions/getplayerlivesleft.md` for the `PLAYER_IsValidPlayer()` caveat (index-range +
`playeringame[]` only, does **not** exclude spectators; a spectator's lives count can still be set
and read back).

- The wiki's value semantics are correct: `amount` is the post-death lives count, not "lives
  remaining" — to give a player 3 lives, pass `2` (matches `GetPlayerLivesLeft`'s documented
  convention that a stored value of `N` displays as `N + 1` lives). `0` means "on their last life."
- `amount` is cast to `ULONG` before being stored in `player->ulLivesLeft`. A negative `amount`
  wraps to a huge unsigned value rather than failing or clamping to `0` — the wiki doesn't mention
  this, and there's no engine-side range check. Callers should avoid passing negative values.

## Unlike every other internal writer, this one is NOT gated on `GAMEMODE_AreLivesLimited()`

This is the most important divergence from the wiki page, which doesn't mention it at all.
`PLAYER_SetLivesLeft()` (`p_interaction.cpp:3395`) itself has no gamemode check — it's a bare
setter. Every other call site in the engine wraps it in a check before calling, e.g.:

- `p_user.cpp:3484` — gated by the caller's own `GAMEMODE_ShouldPlayerLoseLife()` check.
- `invasion.cpp`, `survival.cpp`, `gamemode.cpp`, `g_level.cpp` — all called from lives-limited
  gamemode logic (`GMF_USEMAXLIVES`) or round-reset paths.

`ACSF_SetPlayerLivesLeft` (`p_acs.cpp:7194-7202`) is the one exception: it calls
`PLAYER_SetLivesLeft()` **unconditionally**, with no `GAMEMODE_AreLivesLimited()` or
`GMF_USEMAXLIVES` check anywhere in the case block. This means an ACS script can set
`ulLivesLeft` to any value in *any* gamemode, including ones that never read it (e.g. plain
Deathmatch) — the value will simply sit unused until/unless the map's gamemode later starts
honoring lives (or until read back by `GetPlayerLivesLeft`, which has no gating either). Compare
to `functions/getplayerlivesleft.md`'s note that the field defaults to `0` and is otherwise
"only written by gated calls" — `SetPlayerLivesLeft` from ACS is the one ungated writer.

## Client sync

`PLAYER_SetLivesLeft()` takes a third parameter `informClients` (default `true`, not exposed to
ACS) — when called on a listen/dedicated server, it calls `SERVERCOMMANDS_SetPlayerLivesLeft()` to
replicate the new value to clients. The ACS call site doesn't override this default, so a
server-side `SetPlayerLivesLeft` call is synced to clients normally; no special handling needed by
script authors.

## See also

- `GetPlayerLivesLeft` (-104) — the reader counterpart; see `functions/getplayerlivesleft.md`.
- `PlayerIsSpectator` — same caveat as the getter: a spectator's lives count can be set/read, so
  don't infer spectator/alive status from a lives value alone.
