# `sv_allowprivatechat`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Controls whether clients can send private (one-to-one) messages to each other or to the server host.

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Private messaging is disabled. No player can send private messages at all. |
| 1 | Players are allowed to privately chat with anyone on the server, including the host. |
| 2 | Players are only allowed to privately chat with their teammates. They cannot message the host or players on other teams. |

Default is 1 (full private messaging allowed).

## Network and storage

Marked `CVAR_SERVERINFO`, so the setting is replicated to clients so they know which messaging modes are available.

## Related cvars

- **`sv_allowvoicechat`** — controls voice chat (audio), separate from text private messaging.
- **`sv_markchatlines`** — tags chat messages in the server log for parsing (affects all chat, including private messages).

## Engine-family divergence

`sv_allowprivatechat` does not exist in UZDoom at all — confirmed absent from the engine's source
(no matching `CVAR`/`CUSTOM_CVAR` declaration, and no bare mention of the name anywhere in the
tree), not merely undocumented.

Setting it under UZDoom — from the console, a config file, or ACS's `ConsoleCommand()` — prints
`Unknown command "sv_allowprivatechat"` to the console/log and does nothing else: visible if
someone's watching the console at the time, easy to miss if triggered from an unattended server
startup script, since the attempted write silently fails to apply and no cvar of this name is ever
created. Consequently a UZDoom server administrator has no way to restrict private one-to-one
messaging to teammates-only or disable it outright — UZDoom's private chat, if any exists, is not
gated by a scoping cvar the way Zandronum's is.
