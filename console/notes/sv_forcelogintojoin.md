# `SV_ForceLoginToJoin`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes — an external-account login system built on the SRP
protocol; UZDoom/GZDoom has no equivalent login/account infrastructure at all (see
"Zandronum-specific" below).
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) and client-authentication logic in `src/sv_main.cpp` and `src/cl_main.cpp`, verified against account-server integration.

When enabled, requires clients to authenticate against a configured account server before they can join and play. Unauthenticated clients are forced to spectate until they authenticate.

*(Corrected: the actual login/account protocol lives in `src/network/sv_auth.cpp` and
`src/network/cl_auth.cpp`/`cl_auth.h`, not directly in `sv_main.cpp`/`cl_main.cpp` — those two files
own only the join-gate check (`server_CheckLogin()`, `sv_main.cpp:7573-7580`) and the client-side
auto-login convenience cvars (`cl_autologin`, `login_default_user`; `cl_main.cpp:275-281,3601-3602`)
respectively. This doesn't change the file's `Provenance` citation, just clarifies where the
protocol itself is implemented.)*

## Authentication flow and client states

When `sv_forcelogintojoin` is true:

1. **Connecting client:**
   - Connects to the server (connection accepted).
   - Immediately forced to spectator mode (cannot select a playable team/class) —
     `PLAYER_ShouldSpawnAsSpectator()`, `src/p_interaction.cpp:3066-3078`.

2. **Authentication attempt:**
   - The client sends a login username to the *game* server (`CLC_SRP_USER_REQUEST_LOGIN`), not
     directly to an account server. The game server relays the request over UDP to the external
     auth server named by the `authhostname` cvar (default `auth.zandronum.com:16666`,
     `src/network/sv_auth.cpp:120`) and acts as a relay for the rest of the exchange.
   - Authentication itself uses the **SRP (Secure Remote Password) protocol**
     (`src/network/sv_auth.cpp`, `SERVER_ProcessSRPClientCommand()` /
     `SERVER_AUTH_ParsePacket()`): a multi-step challenge/response handshake
     (`CLC_SRP_USER_REQUEST_LOGIN` → `CLC_SRP_USER_START_AUTHENTICATION` →
     `CLC_SRP_USER_PROCESS_CHALLENGE`, mirrored server\<->auth-server as
     `SERVER_AUTH_NEGOTIATE`/`SRP_STEP_TWO`/`SRP_STEP_FOUR`) in which the client's password itself
     is never transmitted to either the game server or the auth server — only cryptographic proofs
     derived from it. *(Corrected: the previous "sends authentication credentials to the account
     server" wording implied a simpler, more direct credential-transmission model than what the
     source actually implements.)*

3. **On success:**
   - The auth server confirms the session (`AUTH_SERVER_SRP_STEP_FOUR`); the game server sets the
     client's `loggedIn` flag (`src/network/sv_auth.cpp:346`) and, unless the client set
     `WantHideAccount`, announces the player's account name to other clients
     (`SERVERCOMMANDS_SetPlayerAccountName`). Client is authenticated; can join teams and play
     normally.

4. **On failure or no attempt:**
   - Client remains spectating indefinitely until authenticated.

This prevents anonymous/unauthenticated play on servers requiring verified identities (useful for clan servers, admin-controlled servers, or competitive leagues).

## Related account-server configuration

- **`authhostname`** — the hostname (optionally `host:port`) of the auth server the *game server*
  negotiates with on the client's behalf; defaults to Zandronum's own official auth server
  (`auth.zandronum.com:16666`) and is a `CVAR_ARCHIVE | CVAR_GLOBALCONFIG` cvar, so it is normally
  left at its default rather than something a server admin must set up from scratch.
  *(Corrected: the previous `AuthHostName` spelling didn't match the actual declared cvar name, and
  the framing implied a mandatory per-server admin setup step rather than an optional override of
  an already-working default.)*
- **`login_default_user`** / **`cl_autologin`** — client-side cvars (`src/cl_main.cpp:277`,
  `src/network/cl_auth.h:71`) that automatically retry a login for a saved account on connect;
  only compiled in when `ENABLE_AUTH_STORAGE` is defined (Windows, or Linux built with
  `USE_LIBSECRET`).

## Distinction from password protection

This cvar is **different from `sv_forcepassword`**:
- **`sv_forcepassword`** — requires a password to join at all; wrong password = connection rejected.
- **`sv_forcelogintojoin`** — allows connection but forces spectate until account authentication succeeds; wrong credentials = spectate indefinitely.

The former is basic access control; the latter is identity verification.

## Network and storage

Marked `CVAR_ARCHIVE | CVAR_NOSETBYACS` (`src/sv_main.cpp:288`) — persists to the server's config
file, and cannot be changed via ACS's `SetCVar`/`ConsoleCommand`. *(Corrected: the previous
`CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING` claim doesn't match the actual declaration; in particular,
without `CVAR_SERVERINFO` the cvar's own value is not automatically replicated to clients — a
client only learns login is required indirectly, from the "You need to login before joining."
message `server_CheckLogin()` prints when it rejects a join attempt, `src/sv_main.cpp:7578`.)*

## Related ACS functions

Two extension functions expose this same client state to ACS: `PlayerIsLoggedIn(int player)`
(`ACSF_PlayerIsLoggedIn`, `src/p_acs.cpp:7257-7264`) returns the client's `loggedIn` flag directly,
and `GetPlayerAccountName(int player)` (`ACSF_GetPlayerAccountName`, `src/p_acs.cpp:7267-7277`)
returns the authenticated username (empty string if not logged in). Neither requires
`sv_forcelogintojoin` to be enabled — they read the same per-client login state regardless of
whether joining is gated on it.

## Related cvars

- **`authhostname`** — auth server hostname; defaults to Zandronum's own official auth server, see above.
- **`sv_forcepassword`** — server password requirement (distinct from account authentication).
- **`sv_joinpassword`** / **`sv_forcejoinpassword`** — separate password for joining (play) vs. joining (spectate).

## Zandronum-specific: SRP-based external account login

The entire login/account-authentication subsystem this cvar gates — `sv_forcelogintojoin`,
`authhostname`, the per-client `loggedIn`/`username` state, the SRP handshake in
`src/network/sv_auth.cpp`/`cl_auth.cpp`, and the `PlayerIsLoggedIn`/`GetPlayerAccountName` ACS
functions — is confirmed entirely absent from the UZDoom source tree: no `sv_forcelogintojoin` or
`authhostname` cvar declaration, no `sv_auth`/`cl_auth`/SRP source files, and no bare mention of
`loggedIn`-style account state anywhere in the checkout. UZDoom/GZDoom's multiplayer model has no
built-in concept of a player "account" verified against an external service at all — this is
Zandronum-lineage server infrastructure (tied to Zandronum's own account server,
`auth.zandronum.com`) with no UZDoom counterpart to diverge from, not a differently-implemented
equivalent.
