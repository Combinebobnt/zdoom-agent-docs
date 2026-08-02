# `bool KickFromGame(int player, str reason)` — wiki name `ForceToSpectate`

**Tier:** A.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD; the `ACSF_ForceToSpectate` naming and behavior predate the 3.2.1 version-bump commit `28f736fb3` by about nine years — see "Why the names disagree" above).
**Provenance:** wiki page `ForceToSpectate - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=2375`) + source-verified (`p_acs.cpp:5451-5458,7206-7215`, `sv_main.cpp:3942-3965`, `p_interaction.cpp:2441-2453,3006-3014`, `network.cpp:1552-1554`, commit `7791e2d44`). The wiki's signature and pass/fail semantics hold; the client-mode guard, the dead-spectator carve-out, the broadcast-not-private `reason`, and — most importantly — the **wrong callable name for this toolchain** are this doc's source-verified additions.
**Bucket:** extension function (`ACSF_ForceToSpectate`, index -106), implementation at the Zandronum source's `src/p_acs.cpp:7206-7215`.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

**The wiki's function name does not exist in this toolchain.** The Zandronum wiki documents this
extension function as `ForceToSpectate(int player, str reason)`, matching the engine's internal
enum name (`ACSF_ForceToSpectate`, index 106 → -106 in the extension-function table). But
`zt-bcc`'s `zcommon.bcs` (`lib/zcommon.bcs:1739`) exposes the same index under a different,
older name:

```
-106:KickFromGame(int,str):bool,
```

**Call it as `KickFromGame(player, reason)` with `zt-bcc` — `ForceToSpectate(...)` will fail
to compile** (undeclared identifier). Confirmed by grepping the entire the zt-bcc source tree:
`ForceToSpectate` appears nowhere in it, not even as an alias.

## Why the names disagree

The engine-side name was itself renamed in commit `7791e2d44` ("Renamed kickfromgame and friends
to forcespec for consistency", 2016-02-11): `ACSF_KickFromGame` → `ACSF_ForceToSpectate`, and the
matching console commands `kickfromgame`/`kickfromgame_idx` → `forcespec`/`forcespec_idx` (the old
command names survive only as thin aliases). That rename touched the C++ enum and the console
commands, but **never propagated to `zt-bcc`'s `zcommon.bcs`**, which still declares the ACS-level
name from before the 2016 rename. A stale comment block just above the real enum in
`p_acs.cpp:5451-5458` (`/* Zandronum's - these must be skipped when we reach 99! ... -106 :
KickFromGame(2), */`) is a leftover of the same pre-rename naming and was likely the source the
`zcommon.bcs` entry was copied from.

This predates the 3.2.1 target by nine years (commit `7791e2d44` is 2016-02-11; the
3.2.1 version-bump commit `28f736fb3` is 2025-08-04, and `git merge-base --is-ancestor 7791e2d44
28f736fb3` confirms the rename is an ancestor) — so both the engine's current internal name
(`ForceToSpectate`) and the stale bcc-exposed name (`KickFromGame`) are equally present in
3.2.1; nothing here is a newer-than-3.2.1 addition.

## Behavior

```cpp
case ACSF_ForceToSpectate:
{
    const ULONG ulPlayer = static_cast<ULONG> ( args[0] );
    if ( ( NETWORK_InClientMode() == false ) && PLAYER_IsValidPlayer ( ulPlayer ) && ( PLAYER_IsTrueSpectator ( &players[ulPlayer] ) == false ) )
    {
        SERVER_ForceToSpectate ( ulPlayer, FBehavior::StaticLookupString ( args[1] ) );
        return 1;
    }
    else
        return 0;
}
```

- **`player`** — a player index, validated by `PLAYER_IsValidPlayer` (rejects `>= MAXPLAYERS` and
  slots where `playeringame` is false). No activator fallback; there is no `player=0`-means-self
  convention here.
- **Clientside guard:** `NETWORK_InClientMode()` (true if `NETSTATE_CLIENT` or during demo
  playback) makes the call an unconditional no-op returning `0` on a client — same pattern as
  other Zandronum-only ACSF calls that only make sense server-side. Not mentioned on the wiki.
- **Already-spectating guard:** `PLAYER_IsTrueSpectator()` blocks the call (returns `0`, does
  nothing) if the target is already a "true" spectator. This check respects the same
  `GMF_DEADSPECTATORS`-gated distinction as [`PlayerIsSpectator`](playerisspectator.md): in a game
  mode with `GMF_DEADSPECTATORS` set, a player who is only a *dead* spectator (`bDeadSpectator ==
  true`, e.g. waiting to respawn in LMS/survival) is **not** considered a true spectator, so
  `KickFromGame` can still be used on them to convert them to a real spectator; in modes without
  that flag, any spectating player already counts as "true" and blocks the call.
- **`reason`** is not private to the target — `SERVER_ForceToSpectate` (`sv_main.cpp:3942-3965`)
  broadcasts it to everyone via `NETWORK_Printf`: `"<name> has been forced to spectate! Reason:
  <reason>"`. The wiki's "the reason that will be displayed" undersells this — it's a
  server-wide chat message, not a message shown only to the affected player.
- On success, `SERVER_ForceToSpectate` calls `PLAYER_SetSpectator(&players[ulPlayer], true,
  false)` (a *true*, non-dead spectator transition — this destroys held inventory if the player
  was previously a dead spectator, ends their team affiliation, and resets score counters), then
  replicates `SERVERCOMMANDS_PlayerIsSpectator` to clients if running as a listen/dedicated
  server.
- `SERVER_ForceToSpectate` itself re-checks `PLAYER_IsValidPlayer`/`PLAYER_IsTrueSpectator` and
  prints a console message on failure — but the ACSF wrapper already short-circuits both cases to
  a silent `return 0` before reaching it, so those inner messages are effectively dead code from
  the ACS call path.

**Returns:** `bool` (really `1`/`0`) — `1` if the player was successfully forced to spectate, `0`
if in client mode, the player index is invalid, or the player is already a true spectator.
