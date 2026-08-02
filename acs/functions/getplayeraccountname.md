# `str GetPlayerAccountName(int player)`

Returns the given player's account name from Zandronum's optional SRP-based login system.
Extension function (`ACSF_GetPlayerAccountName`, index -114 in `zcommon.bcs`), implementation at
the Zandronum source's `src/p_acs.cpp:7268-7278`. Companion function `PlayerIsLoggedIn` is
`ACSF_PlayerIsLoggedIn`, index -113, at `p_acs.cpp:7258-7265`.

**Bucket:** extension function.

```cpp
case ACSF_GetPlayerAccountName:
{
    FString work;
    const ULONG ulPlayer = static_cast<ULONG> ( args[0] );
    // [BB] If the sanity checks fail, we'll return an empty string.
    if ( ( NETWORK_GetState( ) == NETSTATE_SERVER ) && SERVER_IsValidClient ( ulPlayer ) )
    {
        work = SERVER_GetClient( ulPlayer )->GetAccountName();
    }
    return ACS_PushAndReturnDynamicString ( work );
}
```

- **Server-only in effect.** The account name is only ever looked up when
  `NETWORK_GetState() == NETSTATE_SERVER` (one of four states — `NETSTATE_SINGLE`,
  `NETSTATE_SINGLE_MULTIPLAYER`, `NETSTATE_CLIENT`, `NETSTATE_SERVER`, `network.h:270-279`). A
  singleplayer game, a listen server's own local view, and any `CLIENTSIDE` script all fall
  outside that check and get the untouched default-constructed `FString` — i.e. **`""`, not a
  meaningful value** — regardless of whether the queried player is logged in. This is a real
  fork-specific gotcha the wiki page doesn't mention at all.
- **`SERVER_IsValidClient`** (`sv_main.cpp:3190-3197`) also silently fails closed to `""`: an
  out-of-range `player` index, a player not currently `playeringame`, or a bot (`pSkullBot`) all
  return `false` here, same as the not-logged-in-and-not-server case above. There is no way to
  distinguish "invalid player" from "server-but-not-logged-in" from the return value alone —
  check `PlayerInGame()`/`PlayerIsBot()` first if that distinction matters.
- **The wiki's `n@localhost` claim is correct** and comes from `CLIENT_s::GetAccountName()`
  (`sv_main.cpp:7650-7663`): a logged-in client returns its `username`; otherwise it formats
  `"%td@localhost"` with the player's slot index. But this formatting only ever runs on the
  branch described above — it requires `NETSTATE_SERVER` and a valid, in-game, non-bot client;
  it is not a universal fallback the function guarantees in every calling context.
- **Undocumented privacy gap: this function ignores the client's own "hide account name" opt-in.**
  Zandronum has a separate client-side privacy toggle (`CLC_SETWANTHIDEINFO` with
  `HIDEINFO_ACCOUNTNAME`, `sv_main.cpp:5310-5325`) that sets `CLIENT_s::WantHideAccount`
  (`sv_main.h:385`). That flag *is* respected by the normal network broadcast path
  (`SERVERCOMMANDS_SetPlayerAccountName`, `sv_commands.cpp:648-659`, sends `""` to other clients
  when the flag is set) — but `ACSF_GetPlayerAccountName` reads
  `SERVER_GetClient(ulPlayer)->GetAccountName()` directly and never checks `WantHideAccount`.
  A server-side script can therefore read a player's real account name via ACS even when that
  player has explicitly opted to hide it from other players over the normal netcode path. Nothing
  in `zcommon.bcs` or the wiki flags this asymmetry; worth knowing before using this in any script
  that displays or logs account names.
- Not gated behind any cvar — any script (with server-side execution context) can call this
  freely; the login system itself is opt-in per-server (`authhostname` must be configured) and
  per-client (`login` CCMD), but the ACS function has no cvar guard of its own.

**Returns:** `str` — the account name (`username`) if the player is logged in and the call runs
server-side; `"n@localhost"` (n = player slot) if server-side but not logged in; `""` in every
other case (client-side, singleplayer, invalid/out-of-range player, bot, or player not in game).

**Provenance:** wiki page `GetPlayerAccountName - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=1298`) + source-verified (`p_acs.cpp:7258-7278`, `sv_main.cpp:3190-3197,
7650-7663, 2700-2720, 5310-5325`, `sv_commands.cpp:648-659`, `sv_main.h:385`, `network.h:270-279`).
The wiki's signature and `n@localhost` claim both hold; the `NETSTATE_SERVER`-only gate, the
silent-`""` failure modes, and the `WantHideAccount` bypass are this doc's source-verified
additions, not on the wiki. **Engine:** Zandronum 3.2.1 — the account/login feature (and both
`GetPlayerAccountName`/`PlayerIsLoggedIn`) was added in commit `e125faf2a` (2014-06-09), confirmed
via `git merge-base --is-ancestor e125faf2a 28f736fb3` (the 3.2.1 version-bump commit) to predate
the 3.2.1 target, so this is a genuine pre-3.2.1 feature, not a `3.3-alpha`-only addition. **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
