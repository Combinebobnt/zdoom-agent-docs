# `sv_allowprivatechat`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML. Zandronum source: `src/sv_main.cpp:400` (CUSTOM_CVAR declaration and 0..2 clamp), `src/chat.cpp:1202` and `:1209` (teammates-only rule), `src/sv_main.cpp:5856` and `:5878` (server-side enforcement), `src/sv_commands.cpp:2568` and `src/cl_main.cpp:6275` (client replication), `src/sv_main.cpp:1297` (private-message logging).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Controls whether clients can send private (one-to-one) messages to each other or to the server host.

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Private messaging is disabled. No player can send private messages at all. |
| 1 | Players are allowed to privately chat with anyone on the server, including the host. |
| 2 | Players are only allowed to privately chat with their teammates. They cannot message the host or players on other teams. This applies only in game modes with players on teams. In any other game mode, 2 behaves like 1. True spectators can still message other true spectators. |

Default is 1 (full private messaging allowed). Out-of-range values are clamped to 0..2.

## Network and storage

Flags are `CVAR_ARCHIVE | CVAR_NOSETBYACS | CVAR_SERVERINFO`, so ACS cannot set it. Clients learn the value from the server's game-mode-limits command, which carries it as a byte and is resent whenever the cvar changes. The server enforces the restriction again when it receives a private message.

## Related cvars

- **`sv_allowvoicechat`** — controls voice chat (audio), separate from text private messaging.
- **`sv_markchatlines`** — tags chat messages in the server log for parsing (private messages are logged only when sent to or from the server).

## Engine-family divergence

`sv_allowprivatechat` does not exist in UZDoom at all — confirmed absent from the engine's source
(no matching `CVAR`/`CUSTOM_CVAR` declaration, and no bare mention of the name anywhere in the
tree), not merely undocumented.

Setting it under UZDoom from the console or a config file prints
`Unknown command "sv_allowprivatechat"` to the console/log and does nothing else: visible if
someone's watching the console at the time, easy to miss if triggered from an unattended server
startup script, since the attempted write silently fails to apply and no cvar of this name is ever
created. Setting it through ACS's `ConsoleCommand()` never reaches the console dispatcher at all:
UZDoom's `ConsoleCommand` p-codes only print a "doesn't support execution of console commands from
scripts" error and discard their arguments. Consequently a UZDoom server administrator has no way to restrict private one-to-one
messaging to teammates-only or disable it outright — UZDoom's private chat, if any exists, is not
gated by a scoping cvar the way Zandronum's is.
