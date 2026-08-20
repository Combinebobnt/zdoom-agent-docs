# Login/account family

**Tier:** A for `GetPlayerAccountName` (wiki-sourced, per `shared/AUTHORING.md`'s tier-A
requirement); **B for `PlayerIsLoggedIn`** - no wiki-sourced starting point was found for it (no
matching file in the local `_intake/` archive, and the existing wiki-sourced
`GetPlayerAccountName` writeup doesn't reference a sibling page for it either), so it doesn't meet
the tier-A bar despite being grouped in this family file. This is an *absence of a found source*,
not a confirmed "no such page exists" - this tree's own rules prohibit fetching the live wiki
directly to check, so treat this as source-verified-only (tier B) unless someone supplies a real
wiki page for it via the intake pipeline.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `GetPlayerAccountName` - wiki page `GetPlayerAccountName - Zandronum Wiki.html`
(`_intake/`, retrieved 2026-07-29, `https://wiki.zandronum.com/w/index.php?title=GetPlayerAccountName&oldid=1298`) + source-verified. `PlayerIsLoggedIn` -
source-verified only, no wiki page found (see Tier note above). Both:
(`p_acs.cpp:7258-7278`, `sv_main.cpp:3190-3197, 7650-7663, 2700-2720, 5310-5325`,
`sv_commands.cpp:648-659`, `sv_main.h:385`, `network.h:270-279`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** both extension functions, adjacent `case` blocks in `src/p_acs.cpp` (`ACSF_PlayerIsLoggedIn`
index -113 at `p_acs.cpp:7258-7265`; `ACSF_GetPlayerAccountName` index -114 at `p_acs.cpp:7268-7278`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Grouped as one family under the **shared-implementation** rationale (`shared/AUTHORING.md`): both
are thin wrappers around the exact same gate (`NETWORK_GetState()==NETSTATE_SERVER &&
SERVER_IsValidClient(player)`) and the exact same underlying object (`SERVER_GetClient(player)`),
so every finding about *when* the real value is even reachable applies identically to both -
documenting them separately would duplicate that finding twice.

Zandronum's optional SRP-based login system lets a player authenticate to a server-side account
independent of their in-game name. Both functions only ever see real data when queried from
server-side script execution against Zandronum's own dedicated/listen-server networking model -
there is no equivalent concept in engines without that networking model (see the porting note
below).

**Porting note:** UZDoom/GZDoom-family engines have no dedicated-server mode and no login/account
system at all - neither function has anything to query. A port targeting those engines has no
real value to fall back to; whether to stub these as an unconditional constant (e.g. always
"logged in", a synthesized per-player name) is a project-specific design decision with no single
correct answer, since it changes what identity a stubbed value actually represents to calling
code - out of scope for this tree to prescribe, covered here only so a porting project knows
exactly what real behavior it's choosing not to replicate.

## `bool PlayerIsLoggedIn(int player)`

**Tier B** for this member specifically - see the family header's Tier note.

```cpp
case ACSF_PlayerIsLoggedIn:
{
    const ULONG ulPlayer = static_cast<ULONG> ( args[0] );
    if ( ( NETWORK_GetState( ) == NETSTATE_SERVER ) && SERVER_IsValidClient ( ulPlayer ) )
        return SERVER_GetClient ( ulPlayer )->loggedIn;
    else
        return false;
}
```

- **Server-only in effect, same gate as `GetPlayerAccountName` below.** `NETWORK_GetState()` is
  one of four states (`NETSTATE_SINGLE`, `NETSTATE_SINGLE_MULTIPLAYER`, `NETSTATE_CLIENT`,
  `NETSTATE_SERVER`, `network.h:270-279`) - a singleplayer game, a listen server's own local view,
  and any `CLIENTSIDE` script all fall outside the `NETSTATE_SERVER` check and get the `else`
  branch's plain `false`, **regardless of whether the queried player is actually logged in** on
  whatever server they're connected to. No wiki page was found to check this claim against (see
  the family header's Tier note) - this is source-derived only, and isn't guessable from the name
  alone regardless.
- **`SERVER_IsValidClient`** (`sv_main.cpp:3190-3197`) also silently fails closed to `false`: an
  out-of-range `player` index, a player not currently `playeringame`, or a bot (`pSkullBot`) all
  return `false` here too, indistinguishable from "valid client, genuinely not logged in." Check
  `PlayerInGame()`/`PlayerIsBot()` first if that distinction matters.
- Unlike `GetPlayerAccountName`, this one reads a plain `bool` field (`CLIENT_s::loggedIn`)
  directly, not through `GetAccountName()`'s formatting - so it has no `WantHideAccount`-style
  bypass gap; a hidden account name still reports `loggedIn == true` correctly, since login state
  and the opt-in-hidden *name* are orthogonal (`sv_main.h:385`'s `WantHideAccount` only affects the
  string, per `GetPlayerAccountName`'s own entry below).
- Not gated behind any cvar of its own - any script (with server-side execution context) can call
  this freely, same as `GetPlayerAccountName`.

**Returns:** `bool` — `true` only if the call runs server-side (`NETSTATE_SERVER`) *and* the given
player is a valid, in-game, non-bot client *and* that client's connection is actually logged in.
`false` in every other case, including singleplayer, listen-server local view, `CLIENTSIDE`
scripts, and any invalid/out-of-range/bot/not-in-game player - **most practical UZDoom/GZDoom-style
single-player or no-login-server sessions will see `false` unconditionally for every player,
every time**, since those contexts never reach `NETSTATE_SERVER` with a genuinely logged-in client
at all.

## `str GetPlayerAccountName(int player)`

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

- **Server-only in effect** - the exact same gate as `PlayerIsLoggedIn` above. A singleplayer
  game, a listen server's own local view, and any `CLIENTSIDE` script all fall outside that check
  and get the untouched default-constructed `FString` — i.e. **`""`, not a meaningful value** —
  regardless of whether the queried player is logged in. This is a real fork-specific gotcha the
  wiki page doesn't mention at all.
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

## Engine-family divergence

Both members are bound at ACSF (CALLFUNC) indices in the 100–199 range UZDoom's own ACSF enum
reserves for Zandronum's extensions and implements none of (see
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md)) — Zandronum's account/
login system (a server-side username/password store, gated behind `authhostname`) has no UZDoom
equivalent at all; UZDoom has no concept of a logged-in account distinct from an in-game player. A
Zandronum-compiled object calling either function under UZDoom hits UZDoom's `CallFunction`
dispatcher's `default: break;` case: no error, no log line, execution continues with `0` in place
of the real return value.

For `PlayerIsLoggedIn` (a `bool`), the silent `0`/`false` is exactly what a genuinely-never-logged-
in player already returns on Zandronum — coincidentally correct on every server, since there is no
login system for anyone to be logged into. `GetPlayerAccountName` is a `str` return, so the
fallback `0` is not a valid pool-origin string handle at all (the same mismatch documented on
`acs/functions/getplayercountry.md`) — a caller gets an unrelated string-table lookup instead of
the `""` this family's own Zandronum-side "not logged in" case actually returns.
