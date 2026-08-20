# SkipJoinQueue

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `SkipJoinQueue - Zandronum Wiki.html` (`https://wiki.zandronum.com/w/index.php?title=SkipJoinQueue&oldid=2269`), verified against the Zandronum source's `src/p_acs.cpp` (ACSF_SkipJoinQueue), `src/p_interaction.cpp` (`PLAYER_IsTrueSpectator`), and `src/joinqueue.cpp` on 2026-07-29.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

`int SkipJoinQueue(int player)`

Extension function, index -181 (`zt-bcc/lib/zcommon.bcs:1809`) → `ACSF_SkipJoinQueue` in
the Zandronum source's `src/p_acs.cpp` (case at line 8914).

Forces a player currently in the join queue to join the game immediately, bypassing the normal
"pop the queue when a slot frees up" flow. Returns `1` if the player actually joined, `0`
otherwise — but "otherwise" covers several distinct failure modes the wiki page doesn't mention:

- **No-op on clients.** The whole body is gated on `NETWORK_InClientMode() == false`; a
  `CLIENTSIDE` script (or any script running on a client) always gets `0` and never touches the
  queue. Only the server (or a non-networked single-player instance) can pop a queue entry this
  way.
- **`player` must be a *true* spectator, not just spectating.** The engine checks
  `PLAYER_IsValidPlayer(player) && PLAYER_IsTrueSpectator(&players[player])`. In a game mode with
  the `GMF_DEADSPECTATORS` flag, `PLAYER_IsTrueSpectator` excludes players with `bDeadSpectator`
  set — i.e. a player who died and became a "dead spectator" (as opposed to someone who
  voluntarily spectated or hasn't joined yet) is *not* eligible and the call returns `0` even
  though they're technically in a spectating state. See `functions/playerisspectator.md` for the
  same `GMF_DEADSPECTATORS` distinction on the query side.
- **Server population cap still applies.** If running as `NETSTATE_SERVER`, the call also checks
  `SERVER_CalcNumNonSpectatingPlayers(MAXPLAYERS) >= sv_maxplayers` and returns `0` without
  joining anyone if the server is already full — `SkipJoinQueue` cannot exceed `sv_maxplayers`,
  it only lets someone jump the line within the existing slot budget.
- **Must actually be queued.** The player's position is looked up via
  `JOINQUEUE_GetPositionInLine(player)`; if it's `-1` (not in the queue at all), the call returns
  `0` even if the player is a valid true spectator. Use [`GetPlayerJoinQueuePosition`](getplayerjoinqueueposition.md) (ACSF -180,
  same family) to check queue membership first if that distinction matters.
- On success, it calls `JOINQUEUE_PlayerJoinsAtPosition(joinQueuePosition)` — the same internal
  path used when the queue naturally advances — and returns `1`.

## Engine-family divergence

`SkipJoinQueue` is bound as ACSF (CALLFUNC) index 181, inside the 100–199 range UZDoom reserves
for Zandronum's own extensions and implements none of. Under UZDoom, `CallFunction`'s dispatch
switch has no `case` for it and falls to `default: break;`, which returns `0` — no error, no log
line, script execution continues normally as if the call had simply failed.

That silent `0` is indistinguishable from the function's own legitimate failure returns documented
above (not a true spectator, server full, not actually queued, running client-side). A script
calling `SkipJoinQueue` under UZDoom gets back exactly what a real-but-ordinary rejection looks
like, with no way to tell the two apart from the return value alone — and the queue mechanism
itself never runs: `JOINQUEUE_PlayerJoinsAtPosition` is never called, so the target player is never
moved out of Zandronum's join-queue system, which doesn't exist on UZDoom in the first place. A
script written assuming a queue-jump succeeded (or that treats a `0` return as "try again later")
will instead leave that player waiting indefinitely, since there is no queue state under UZDoom for
a later call to ever resolve.

See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general
reserved-ACSF-range silent-miss mechanism this is an instance of.
