# GetPlayerLivesLeft

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `GetPlayerLivesLeft - Zandronum Wiki.html` (wiki `https://wiki.zandronum.com/w/index.php?title=GetPlayerLivesLeft&oldid=1351`), verified against the Zandronum source's `src/p_acs.cpp` and `p_interaction.cpp` 2026-07-29.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function (index -104; `SetPlayerLivesLeft` at -105)

```text
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

## Engine-family divergence

`GetPlayerLivesLeft` is bound as ACSF (CALLFUNC) index 104 — inside the 100–199 range UZDoom's own
ACSF enum reserves for Zandronum's extensions and implements none of (confirmed via
`tools/engine_matrix.py GetPlayerLivesLeft`, bin `zandronum-only-silent`). UZDoom's `CallFunction`
dispatcher is a plain `switch` over the ACSF index with `default: break;` falling through to
`return 0` — no error, no log line, execution just continues. A Zandronum-compiled object calling
`GetPlayerLivesLeft` under UZDoom silently gets `0` back in place of a real lives count. See
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general mechanism
— this function is one of the confirmed instances it names directly.

That silent `0` is a worse fit here than for most reserved-range functions: `0` is also this
function's own **legitimate** in-range return, meaning "on their last life" — and it's what
`ulLivesLeft` already reads by default for every player before any lives-limited gamemode logic
ever touches it (see "Only meaningful under a lives-limited gamemode" above). A UZDoom caller
can't distinguish "player is down to their last life" from "this build doesn't implement the call
at all" from "no lives-limited gamemode is active" — all three read back identically as `0`, unlike
the function's documented `-1` failure return, which stays visibly distinguishable from a real
lives count on the engine that actually implements it.
