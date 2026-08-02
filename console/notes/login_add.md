# `login_add`

**Tier:** B
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/network/cl_auth.cpp:403-410` (CCMD definition and conditional compilation).

Store login credentials in the system credential manager for automatic authentication to account servers.

## Syntax

`login_add <username> <password>`

Stores the given username and password for later retrieval by `login <username>` when the same username is used.

## Platform availability

This command is only available when the engine is compiled with credential storage support:

- **Windows** — always available; uses Windows Credential Manager (DPAPI-protected storage in the Windows Vault)
- **Linux** — available only when compiled with `USE_LIBSECRET` support; uses the system libsecret keyring
- **Other platforms** — not available

Attempting to use `login_add` on a platform without support will produce a compilation error or "unknown command" message at runtime.

## Behavior

The wiki claims this command updates the `login_default_user` cvar, but the actual implementation does not. It stores the password only; you must separately set `login_default_user` if you want automatic authentication on startup.
