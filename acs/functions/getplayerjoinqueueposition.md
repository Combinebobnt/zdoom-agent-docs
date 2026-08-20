# `int GetPlayerJoinQueuePosition(int player)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** `GetPlayerJoinQueuePosition - Zandronum Wiki.html` (`https://wiki.zandronum.com/w/index.php?title=GetPlayerJoinQueuePosition&oldid=2248`), verified against the Zandronum source's `src/p_acs.cpp` (ACSF_GetPlayerJoinQueuePosition → `JOINQUEUE_GetPositionInLine` call), and `src/joinqueue.cpp` (`JOINQUEUE_GetPositionInLine` definition at the end of the function list) on 2026-08-18. Source checked against 3.2.1 ancestry via `git merge-base --is-ancestor 0147651cd 28f736fb3` (exit 0).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -180 in `zcommon.bcs`'s `special` table; dispatched as `ACSF_GetPlayerJoinQueuePosition` in the Zandronum source's `src/p_acs.cpp`).

Queries a player's position in the join queue — the server-side queue of spectators or disconnected-player slots waiting to spawn into the game. Returns the zero-based position (`0` = first in line, `1` = second, etc.) or `-1` if the player is not in the queue.

## Parameters

- `player` — player number/index (0–`MAXPLAYERS-1`). The function does not validate this ID; an out-of-range or nonexistent player simply returns `-1` (same as "not queued"), matching the queue lookup's internal behavior: `JOINQUEUE_GetPositionInLine` loops through the queue checking `g_JoinQueue[i].player == player` with no prior range check. This differs from `SkipJoinQueue`, which explicitly gates on `PLAYER_IsValidPlayer(player)` before proceeding.

## Return value

- **If queued:** the player's zero-based position in the line (`0` for next-to-join, `1` for second, etc.).
- **If not queued or invalid player:** `-1`.

The `-1` sentinel covers multiple distinct cases the wiki doesn't separate: an invalid/out-of-range player ID, a valid player who is not in the queue, or a valid queued player removed between the script's last check and the call. Scripts cannot distinguish these cases from the return value alone.

## Client-side behavior

Callable from `CLIENTSIDE` scripts. The join queue is synchronized to clients via server commands (`SVC2_PUSHTOJOINQUEUE`/`SVC2_REMOVEFROMJOINQUEUE` in `src/cl_main.cpp`), so the queue state is available for read-only queries on clients. Unlike `SkipJoinQueue`, this function has no network mode check and works unconditionally once the queue state is populated.

## Engine-family divergence

`GetPlayerJoinQueuePosition` is bound as ACSF (CALLFUNC) index 180, inside the 100–199 range UZDoom reserves for Zandronum's own extensions and implements none of. Under UZDoom, `CallFunction`'s dispatch switch has no `case` for it and falls to `default: break;`, which returns `0` — no error, no log line, script execution continues normally as if the call had simply failed.

That silent `0` is indistinguishable from the function's own legitimate return values (a player with position 0 would also return `0`, though that's wrapped as queue-ordering in `int` terms, not a query-failure sentinel). A script written assuming the queue state is available (e.g. checking `if (GetPlayerJoinQueuePosition(p) == 0)` to detect next-in-line) will instead get `0` on UZDoom, making it impossible to tell the two cases apart — and the queue mechanism itself never runs: `g_JoinQueue` is never populated, so the target player's queue state cannot be queried correctly. A script written assuming a queue-join succeeded (and treating a `0` return as "player is now first") will instead leave that player waiting indefinitely under UZDoom, since there is no queue state to be updated.

See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general reserved-ACSF-range silent-miss mechanism this is an instance of.

## Wiki/source divergence

The wiki states the return value is `-1` "if the player is not in the queue **or there is no player with the given number**." The source code (Zandronum's `src/joinqueue.cpp`) has no player-ID validation step — `JOINQUEUE_GetPositionInLine(unsigned int player)` simply loops `g_JoinQueue` checking `g_JoinQueue[i].player == player` with no prior call to `PLAYER_IsValidPlayer`. The `-1` for an invalid player is therefore *incidental* (no entry matches an invalid ID) rather than a validated rejection, matching the function's documented lack of a range-check parameter. Contrast with `SkipJoinQueue`, which *does* validate via `PLAYER_IsValidPlayer(player) && PLAYER_IsTrueSpectator(&players[player])` before proceeding — the asymmetry is not accidental.

Also note the ACS/C++ type conversion: ACS passes `int player`, but the C++ signature is `JOINQUEUE_GetPositionInLine(unsigned int player)` — an ACS negative value (two's-complement `int`) is reinterpreted as a large unsigned value, so e.g. `GetPlayerJoinQueuePosition(-1)` is looking up position of (implicitly cast) `0xFFFFFFFF` in the queue. This will never match a valid queue entry (indices 0–`MAXPLAYERS-1`) and returns `-1`, but the behavior is not a range-check reject — it's a consequence of the type mismatch.
