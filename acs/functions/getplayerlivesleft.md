# GetPlayerLivesLeft

**Tier:** A
**Engine:** Zandronum 3.2.1 — added together with `SetPlayerLivesLeft` in commit `eac46667c` ("Added new ACS commands GetPlayerLivesLeft and SetPlayerLivesLeft... In game modes using sv_maxlives..."), confirmed via `git merge-base --is-ancestor eac46667c 28f736fb3` (the 3.2.1 version-bump commit) to predate 3.2.1, so this is present in the 3.2.1 target, not a later addition.
**Provenance:** `GetPlayerLivesLeft - Zandronum Wiki.html` (wiki `oldid=1351`), verified against the Zandronum source's `src/p_acs.cpp` and `p_interaction.cpp` 2026-07-29.
**Bucket:** Extension function (index -104; `SetPlayerLivesLeft` at -105)

```
int GetPlayerLivesLeft(int player)
```

## What it actually does

Returns `players[player].ulLivesLeft` (via the `PLAYER_GetLivesLeft()` helper in
`p_interaction.cpp:2961`) if `player` passes `PLAYER_IsValidPlayer()`, otherwise **returns `-1`**
— a failure-return value the wiki page doesn't mention at all (it only documents the "success"
value range).

- `PLAYER_IsValidPlayer()` is index-range (`< MAXPLAYERS`) + `playeringame[]` only — same as
  `GetCustomPlayerValue` (already documented in this repo) — **it does not exclude spectators**.
  A spectating player's `ulLivesLeft` still reads back normally.
- The wiki's value semantics are correct and confirmed: `ulLivesLeft` is decremented (not the
  "lives remaining" count itself) each time the player is forced to respawn under a lives-limited
  gamemode, so a value of `2` really does mean "3 lives left" and `0` means "on their last life"
  (see `p_user.cpp:3482` and the HUD code at `g_shared/st_hud.cpp:324`, which prints
  `ulLivesLeft + 1` as the displayed lives count).

## Only meaningful under a lives-limited gamemode

`ulLivesLeft` defaults to `0` for every player (`p_user.cpp:380`) and is otherwise only written by
`PLAYER_SetLivesLeft()` calls gated on `GAMEMODE_AreLivesLimited()` (`gamemode.cpp:1024-1027`,
true only when `sv_maxlives > 0` and the current gamemode has `GMF_USEMAXLIVES` — e.g. Invasion,
Survival, Last Man/Team Last Man Standing). Calling `GetPlayerLivesLeft` in a gamemode that
doesn't use `sv_maxlives` will just always return `0` for every in-game player — indistinguishable
from "player is on their last life" — since the field is never touched there. The wiki page
doesn't mention this precondition at all.

## See also

- `SetPlayerLivesLeft` (-105) — the writer counterpart; same `PLAYER_IsValidPlayer()` gate, returns
  `1`/`0` instead of a lives count.
- `PlayerIsSpectator` — the wiki's own suggestion for checking whether a player is dead/out, rather
  than inferring it from a lives count of `0` (a player can be on their last life and still alive).
