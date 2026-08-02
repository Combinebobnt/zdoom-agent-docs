# `SV_ForceLoginToJoin`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/sv_main.cpp` (CUSTOM_CVAR declaration) and client-authentication logic in `src/sv_main.cpp` and `src/cl_main.cpp`, verified against account-server integration.

When enabled, requires clients to authenticate against a configured account server before they can join and play. Unauthenticated clients are forced to spectate until they authenticate.

## Authentication flow and client states

When `SV_ForceLoginToJoin` is true:

1. **Connecting client:**
   - Connects to the server (connection accepted).
   - Immediately forced to spectator mode (cannot select a playable team/class).

2. **Authentication attempt:**
   - Client must send authentication credentials to the account server defined in `AuthHostName`.
   - The server verifies credentials against the remote authentication service.

3. **On success:**
   - Client is authenticated; can join teams and play normally.

4. **On failure or no attempt:**
   - Client remains spectating indefinitely until authenticated.

This prevents anonymous/unauthenticated play on servers requiring verified identities (useful for clan servers, admin-controlled servers, or competitive leagues).

## Related account-server configuration

- **`AuthHostName`** — the hostname or IP address of the account server the client should authenticate against. This must be configured correctly for the authentication to succeed. If undefined or incorrect, clients cannot authenticate and remain spectating.

## Distinction from password protection

This cvar is **different from `sv_forcepassword`**:
- **`sv_forcepassword`** — requires a password to join at all; wrong password = connection rejected.
- **`SV_ForceLoginToJoin`** — allows connection but forces spectate until account authentication succeeds; wrong credentials = spectate indefinitely.

The former is basic access control; the latter is identity verification.

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`. The setting persists to config and is replicated to clients so they know authentication is required.

## Related cvars

- **`AuthHostName`** — account server hostname; **must be configured for this to work**.
- **`sv_forcepassword`** — server password requirement (distinct from account authentication).
- **`sv_joinpassword`** / **`sv_forcejoinpassword`** — separate password for joining (play) vs. joining (spectate).
