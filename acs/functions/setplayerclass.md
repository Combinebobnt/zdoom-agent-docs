# `bool SetPlayerClass(int player, str class, bool respawn)`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `SetPlayerClass - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://wiki.zandronum.com/w/index.php?title=SetPlayerClass&oldid=1669`) + source-verified (`p_acs.cpp:7594-7676`, `p_interaction.cpp:3006-3023`, `team.cpp:1526-1538`, `network.cpp:1552-1555`, `d_netinfo.cpp:708-719`, `gi.h:147`, `gi.cpp:388`). The wiki's signature, parameter meanings, and general pass/fail framing hold; the missing true-spectator check (wiki says spectators are rejected, they aren't), the client-mode guard, the same-class-always-fails case, and the random-path's team-check bypass are this doc's source-verified additions/corrections, not from the wiki.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Changes the player class a player is using. Extension function (`ACSF_SetPlayerClass`, index
-135 in `zcommon.bcs:1768`), implementation at the Zandronum source's `src/p_acs.cpp:7594-7676`
(case body itself is 7594-7644; the read of interest ends there, the remainder handles the
respawn-with-new-class side effects).

```cpp
case ACSF_SetPlayerClass:
{
    const ULONG ulPlayer = static_cast<ULONG>( args[0] );
    const char *classname = FBehavior::StaticLookupString( args[1] );
    const bool bRespawn = !!args[2];

    // [AK] Don't allow the clients to change the player's class.
    if ( NETWORK_InClientMode() )
        return 0;

    // [AK] Ignore invalid players.
    if ( PLAYER_IsValidPlayer( ulPlayer ) == false )
        return 0;

    player_t *player = &players[ulPlayer];

    if ( stricmp( classname, "random" ) == 0 )
    {
        // [AK] Stop if choosing random player classes is forbidden.
        if ( gameinfo.norandomplayerclass )
            return 0;

        player->userinfo.PlayerClassNumChanged( -1 );
    }
    else
    {
        const PClass *playerclass = PClass::FindClass( classname );

        // [AK] Stop if the class provided doesn't exist or isn't a descendant of PlayerPawn.
        // Also check if the player isn't already playing as the same class.
        if ( playerclass == NULL || !playerclass->IsDescendantOf( RUNTIME_CLASS( APlayerPawn )) || player->cls == playerclass )
            return 0;

        // [AK] Don't change the player's class if it's not allowed.
        if ( !TEAM_IsActorAllowedForPlayer( GetDefaultByType( playerclass ), player ) )
            return 0;

        player->userinfo.PlayerClassChanged( playerclass->Meta.GetMetaString( APMETA_DisplayName ));
    }
    // ... (see below for the rest: singleplayer/server sync, then optional respawn)
}
```

- **`player`** — validated by `PLAYER_IsValidPlayer` (`p_interaction.cpp:3006-3014`), which only
  checks `ulPlayer < MAXPLAYERS` and `playeringame[ulPlayer]`. **The wiki's claim that "the player
  must exist and not a true spectator" is wrong for Zandronum** — there is no
  `PLAYER_IsTrueSpectator` check anywhere in this case (contrast with `ForceToSpectate`, which
  does check it — see `forcetospectate.md`). A true spectator is a valid target here; their
  `userinfo` class cvar is changed the same as any other player's, it just has no visible effect
  until they stop spectating and spawn in.
- **Clientside guard:** `NETWORK_InClientMode()` (true if `NETSTATE_CLIENT` or during demo
  playback, `network.cpp:1552-1555`) makes the whole call a no-op returning `0` on a client — same
  pattern as other server-authoritative Zandronum ACSF calls (see `forcetospectate.md`). Not
  mentioned on the wiki. In the common case (map/library scripts run server-side) this
  doesn't matter, but a `CLIENTSIDE`-scripted call would silently fail.
- **`class` — three cases:**
  - `"random"` (case-insensitive, `stricmp`): fails (`return 0`) if `gameinfo.norandomplayerclass`
    is set (a MAPINFO `gameinfo` flag, `gi.h:147`/`gi.cpp:388` — false for Doom-style IWADs,
    historically true for Hexen). If allowed, calls `PlayerClassNumChanged(-1)` directly.
    **This path does *not* go through `TEAM_IsActorAllowedForPlayer` at all** — the wiki's
    "or if choosing random classes is forbidden" is the only random-specific failure case it
    documents, and that's the only one that actually exists; team-restriction bypass for
    `"random"` isn't mentioned by the wiki but is real.
  - A named class: resolved with `PClass::FindClass`. Fails (`return 0`, silently, no distinct
    error) if the class doesn't exist, isn't a descendant of `PlayerPawn`, **or the player is
    already using that exact class** — this last case is a real failure the wiki doesn't mention
    at all; calling `SetPlayerClass` with the player's current class always returns `false` and
    does nothing, even if `respawn` is `true` (i.e. it can't be (ab)used as a "respawn as my
    current class" trick).
  - Team restriction (named-class path only): `TEAM_IsActorAllowedForPlayer` (`team.cpp:1526-1538`)
    passes automatically if the player isn't on a team (`bOnTeam == false`); otherwise defers to
    `TEAM_IsActorAllowedForTeam`. Matches the wiki's "restricted to a team the player isn't on"
    caveat, but only for the named-class path (see above).
  - Either successful branch only updates the `PlayerClass` `userinfo` cvar
    (`PlayerClassChanged`/`PlayerClassNumChanged`, `d_netinfo.cpp:708-719`) — the actual `PClass`
    swap on the player's pawn happens later, at respawn time, reading that cvar back.
- **Sync/singleplayer bookkeping (always runs after a successful branch):** in a non-server game
  state, `G_UpdateSinglePlayerClass` also updates the class the player would start as; on a server,
  `SERVERCOMMANDS_SetPlayerUserInfo` replicates the new `PlayerClass` userinfo field to clients.
- **`respawn`** — if `true` and the player currently has a body (`PLAYER_IsValidPlayerWithMo`,
  `p_interaction.cpp:3018-3023` — false for a spectator or a player with no `mo`), the player is
  force-respawned with the new class: subject to a lives-left check
  (`!GAMEMODE_AreLivesLimited() || GAMESTATE < GAMESTATE_INPROGRESS || ulLivesLeft > 0`), any
  active morph is undone via `MORPH_UNDOBYTIMEOUT` first, and important items (flags, skulls,
  etc.) are dropped before the old body is destroyed. If `respawn` is `false`, or the player has
  no body, the class change is deferred until the player's next normal respawn — matching the
  wiki. If `respawn` is `true` but the lives-left check fails, the class change still took effect
  (the userinfo cvar was already set) but the immediate respawn is skipped — the player keeps
  their old body until they die/respawn normally.

**Returns:** `bool` (really `1`/`0`) — `1` only on a genuine class change (random succeeded, or a
named class was found, is a `PlayerPawn` descendant, differs from the player's current class, and
passes the team check); `0` for: called from a client, invalid player, `"random"` forbidden by
gameinfo, class not found / not a `PlayerPawn` / same as current class, or team-restricted named
class.

## Engine-family divergence

Bound as ACSF (CALLFUNC) index 135 — inside the 100–199 range UZDoom's own ACSF enum reserves
for Zandronum's extensions and implements none of. A Zandronum-compiled object calling
`SetPlayerClass()` under UZDoom hits UZDoom's `CallFunction` dispatcher's `default: break;` case:
no error, no log line, the interpreter stack stays balanced, and the call just returns `0` in
place of the real success/failure result documented above — none of the checks described there
(client-mode guard, player validity, `"random"`/named-class resolution, same-class rejection,
team restriction) ever run, and neither does the `userinfo` cvar write that's supposed to record
the change.

The practical effect is that the class change never happens at all: the `PlayerClass` `userinfo`
cvar is left untouched, so there's nothing for a later respawn to read back, and — if `respawn`
was `true` — no force-respawn is triggered either. The player just keeps playing as their current
pawn/class, with no distinguishable error from ACS: `0` is exactly the same return value the
Zandronum implementation itself gives for an ordinary failure (invalid player, unknown class, or
"already this class"), so a script can't tell "this build doesn't implement `SetPlayerClass`"
from "the call legitimately failed." A class-select menu or roleplay-mode script that calls this
once and assumes success (or that only checks the return value to retry/report an error) will
silently leave every player on their starting class under UZDoom, with no diagnostic pointing at
the real cause.

See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general
reserved-ACSF-range silent-failure mechanism.
