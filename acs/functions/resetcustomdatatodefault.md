# `raw ResetCustomDataToDefault(str data, int player)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** `ResetCustomDataToDefault - Zandronum Wiki.html` (wiki `https://wiki.zandronum.com/w/index.php?title=ResetCustomDataToDefault&oldid=2263`, a stub page), verified against the Zandronum source's `src/p_acs.cpp:8206-8218` and `src/scoreboard.cpp:748-767` (2026-08-18); UZDoom has no implementation of this function (grep found no `ACSF_ResetCustomDataToDefault` in `src/playsim/p_acs.cpp`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function (index -158; `SetCustomPlayerValue` at -156, `GetCustomPlayerValue` at -157)

## What it actually does

`data` looks up a `PlayerData*` in `gameinfo.CustomPlayerData` — the same key-lookup pattern as `GetCustomPlayerValue` and `SetCustomPlayerValue`, the other members of this trio. If the key is found and the `player` argument is valid (see below), the function resets that player's stored value for the column back to the column's declared default (retrieved via `PlayerData::GetDefaultValue()`).

`player` is the target player number. If `player` is negative (including -1), the function resets *all* players' values for that column in a loop, treating it identically to `MAXPLAYERS` in the underlying `PlayerData::ResetToDefault` call.

## Return value and failure cases

Returns 1 on success, 0 on failure. The function fails (returns 0) if:

- The `data` field name doesn't match any column declared via `addcustomdata` in a MAPINFO `GameInfo` block, OR
- `player` is a non-negative number that fails `PLAYER_IsValidPlayer()` — that check is a plain `playeringame[player]` test, **not** excluding spectators (unlike `PlayerCount`/`PlayerInGame`).

**Note the asymmetry with GetCustomPlayerValue:** when `player < 0`, the validity check is skipped entirely. A negative `player` always succeeds if the `data` field exists, regardless of whether any players are actually in the game — this includes an empty server with no players at all.

## Netcode caveat

The ACS function passes `true` for the `bInformClients` parameter to `PlayerData::ResetToDefault`. If the server is active (`NETWORK_GetState() == NETSTATE_SERVER`), the server will call `SERVERCOMMANDS_ResetCustomPlayerValue` to notify all connected clients of the reset. The clients' scoreboard columns will update to match. A client-side call (a multiplayer mod running ACS on a client) still succeeds but does not notify anyone else of the change.

## See also

- `GetCustomPlayerValue` (-157) — reads a player's custom column value; treats negative `player` as a failure (unlike this function).
- `SetCustomPlayerValue` (-156) — the writer counterpart; takes the new value as a third parameter; same key lookup and same player-validity rules as the getter.

## Engine-family divergence

`ResetCustomDataToDefault` is bound as ACSF (CALLFUNC) index 158 — inside the 100–199 range UZDoom's own ACSF enum reserves for Zandronum's extensions and implements none of (confirmed via `tools/engine_matrix.py ResetCustomDataToDefault`, bin `zandronum-only-silent`). UZDoom's `CallFunction` dispatcher is a plain `switch` over the ACSF index with `default: break;` falling through to `return 0` — no error, no log line, execution just continues. A Zandronum-compiled object calling `ResetCustomDataToDefault` under UZDoom silently gets `0` back in place of the reset actually happening. See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general mechanism — this function is one of the confirmed instances it names directly.

Unlike the corresponding getter, where `0` is ambiguous (a legitimate stored value, or "field/player not found," or "wrong engine"), the `0` return from this function's UZDoom fallback is unambiguous — a reset never happened.

## Wiki/engine divergence

The (stub) wiki page states "Returns 1 if the field **and player** exist." The actual engine behavior with `player < 0` is looser: the function returns 1 if the field exists alone, bypassing the player-existence check for the "reset all players" case. This is not a bug — it's the documented implementation in `PlayerData::ResetToDefault` — but it does deviate from the wiki's stated contract.
