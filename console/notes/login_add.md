# `login_add`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/network/cl_auth.cpp:403-410` (CCMD definition and conditional compilation), `src/network/cl_auth.h:52-54` (`ENABLE_AUTH_STORAGE` gate) and `src/CMakeLists.txt:239-259` (libsecret detection).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Store login credentials in the system credential manager for automatic authentication to account servers.

## Syntax

`login_add <username> <password>`

Stores the given username and password for later retrieval by `login <username>` when the same username is used.

## Platform availability

This command is only available when the engine is compiled with credential storage support:

- **Windows** — always available; uses Windows Credential Manager (DPAPI-protected storage in the Windows Vault)
- **Linux** — available only when compiled with `USE_LIBSECRET` support; uses the system libsecret keyring. The build defines it on non-Apple Unix when pkg-config finds `libsecret-1`, unless `NO_LIBSECRET` is set. Added after 3.2.1 (commit `878b2c985`). In 3.2.1 the command is guarded by `#ifdef _WIN32`, so it is Windows-only there.
- **Other platforms** — not available

On a build without storage support the `CCMD` is compiled out, so `login_add` gives an "unknown command" message at runtime.

## Behavior

The wiki claims this command updates the `login_default_user` cvar, but the actual implementation does not. It stores the password only; you must separately set `login_default_user` if you want automatic authentication on startup.

## Engine-family divergence

`login_add` is confirmed absent from UZDoom's source entirely — no `CCMD`/`CVAR` declaration and
no bare mention of the name anywhere in the tree. This isn't a documentation gap; UZDoom has no
account-server authentication infrastructure for a credential-storage command like this to serve.
Invoking it under UZDoom from the console or a config file hits the console dispatcher's command
lookup, then its cvar-name fallback, and when neither matches prints `Unknown command "login_add"`
to console/log and does nothing else: a visible failure at the console, but easy to miss if
triggered from an unattended context like a server startup script or `autoexec.cfg` line nobody is
watching. Calling it through ACS's `ConsoleCommand()` never gets that far: UZDoom's
`ConsoleCommand` p-codes only print a "doesn't support execution of console commands from scripts"
error and discard their arguments, so nothing reaches the dispatcher.

As a result, UZDoom has no console-driven way to store a username/password pair in the platform
credential store (Windows Credential Manager or libsecret) for later automatic retrieval by
`login` — the entire platform-gated storage mechanism this file documents simply does not run.
