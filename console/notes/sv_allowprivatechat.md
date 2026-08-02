# `sv_allowprivatechat`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML.

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
